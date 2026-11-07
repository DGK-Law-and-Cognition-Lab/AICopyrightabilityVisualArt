"""Validation of the agency rule: who the explanation says made or changed the work.

Exploratory. Specified on 31 October 2026, after every registered result was
known. No registration names it.

The agency rule (agency_rule.py) reads an explanation's grammar and records
three flags: a person made or changed the work (person_maker), a machine did
(machine_maker), or the work was made or changed with no doer stated
(agentless_making). This script tests the rule against model annotators who
code the same explanations from a written codebook (agency_codebook.md):

    python3 AgencyValidation.py draw
        Draws two disjoint samples of explanations from the five studies,
        stratified by study and label: a development sample of 250, on which
        the rule may be adjusted, and a validation sample of 400, on which the
        frozen rule is tested once. Writes samples/<set>_items.csv (an item
        number and the text, nothing else) and samples/<set>_key.csv (the
        study, the row of the study's long data file, the label and the
        question; never shown to an annotator).
    python3 AgencyValidation.py annotate <set> <openai|gemini>
        Has one model code every item of a sample, one item per request, with
        the codebook as its instructions and the explanation as the only other
        input. Every request and response is kept in annotations/cache_*.jsonl,
        so a second run sends nothing and returns the same codes.
    python3 AgencyValidation.py score <set>
        Takes each flag's reference code as the majority of the three
        annotators (OpenAI, Google and Claude; the Claude codes are written by
        a separate annotator run, see README.md), and scores the rule and the
        memo's pattern form against it.

The label, the rating and the participant's code never reach an annotator or
the rule. Study numbers follow the pipeline's folders.

Run from this folder. The API keys are read from the environment variables
OPENAI_API_KEY_AICOPYRIGHT and GEMINI_API_KEY_AICOPYRIGHT, only when a request is not in the
cache, and never written.
"""

import concurrent.futures
import datetime
import hashlib
import json
import os
import random
import sys
import time

import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
PIPELINE = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))
SAMPLES = os.path.join(HERE, "samples")
ANNOTATIONS = os.path.join(HERE, "annotations")
TABLES = os.path.join(HERE, "tables")
CODEBOOK_PATH = os.path.join(HERE, "agency_codebook.md")
ANALYSIS_STATUS = ("exploratory: specified on 31 October 2026, after every registered result "
                   "was known; no registration names it")

SEED = 20261031
SIZES = {"development": 25, "validation": 40}   # per study and label
PREFIX = {"development": "d", "validation": "v"}
LABEL_COLUMN = {1: "Type", 2: "source", 3: "Type", 4: "label", 5: "source"}
WORK_COLUMN = {1: "stimulus_id", 2: "work_id", 3: "stimulus_id", 4: "work_id", 5: "work_id"}
FLAGS = ["person_maker", "machine_maker", "agentless_making"]
# gemini-2.5-pro, the stable release first chosen, was closed to new users by
# 31 October 2026; Google names gemini-3.1-pro-preview as its replacement.
MODELS = {"openai": "gpt-5.5-2026-04-23", "gemini": "gemini-3.1-pro-preview"}
KEYS = {"openai": "OPENAI_API_KEY_AICOPYRIGHT", "gemini": "GEMINI_API_KEY_AICOPYRIGHT"}
SCHEMA = {"type": "object",
          "properties": {f: {"type": "boolean"} for f in FLAGS},
          "required": FLAGS, "additionalProperties": False}
# Items sampled for the rule's first development on 2 September 2026
# (Study 1 only), left out of both samples here; written by `draw` from the
# working files of that development, as rows of Study 1's long data file.
EARLIER = os.path.join(SAMPLES, "earlier_sample_rows.csv")
EARLIER_SOURCES = [os.path.join(PIPELINE, "Study 1", "nlp", "agency_rule_candidates", f)
                   for f in ("gold_sample.json", "validation_key_DO_NOT_SHOW_ANNOTATORS.json")]


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def codebook():
    with open(CODEBOOK_PATH, encoding="utf-8") as handle:
        return handle.read()


# ---------------------------------------------------------------------------
# draw
# ---------------------------------------------------------------------------
def population():
    """Every analyzed explanation: at least one letter, on a five-point item."""
    frames = []
    for s in range(1, 6):
        # The samples were drawn on 31 October 2026, when Study 5's analyzed
        # sample was its registered sample of 223; that file holds it.
        name = "study5_long_registered_sample.csv" if s == 5 else "study%d_long_with_text.csv" % s
        long = pd.read_csv(os.path.join(PIPELINE, "Study %d" % s, name), dtype=str,
                           keep_default_na=False)
        d = pd.DataFrame({"study": s, "row": range(len(long)), "id": long["id"],
                          "stimulus_id": long[WORK_COLUMN[s]], "label": long[LABEL_COLUMN[s]],
                          "dimension": long["dimension"], "text": long["response_text"]})
        keep = d["text"].str.contains(r"[A-Za-z]", regex=True)
        if "k_points" in long.columns:
            keep &= long["k_points"] == "5"
        frames.append(d[keep])
    return pd.concat(frames, ignore_index=True)


def earlier_rows(pop):
    """Rows of Study 1 sampled on 2 September 2026."""
    if os.path.exists(EARLIER):
        return set(pd.read_csv(EARLIER)["row"])
    keys = set()
    for path in EARLIER_SOURCES:
        for rec in json.load(open(path)):
            keys.add((str(rec["id"]), rec["stimulus_id"], rec["dimension"]))
    s1 = pop[pop["study"] == 1]
    hit = s1[[(i, w, d) in keys for i, w, d in zip(s1["id"], s1["stimulus_id"], s1["dimension"])]]
    assert len(hit) == len(keys), "every earlier item must be found once"
    pd.DataFrame({"study": 1, "row": sorted(hit["row"])}).to_csv(EARLIER, index=False)
    return set(hit["row"])


def draw():
    os.makedirs(SAMPLES, exist_ok=True)
    targets = [os.path.join(SAMPLES, "%s_%s.csv" % (s, k)) for s in SIZES for k in ("items", "key")]
    assert not any(os.path.exists(p) for p in targets), (
        "The samples exist already. They are drawn once; delete them only to start the validation again.")
    pop = population()
    skip = earlier_rows(pop)
    pop = pop[~((pop["study"] == 1) & pop["row"].isin(skip))]
    rng = random.Random(SEED)
    chosen = {s: [] for s in SIZES}
    for (study, label), g in pop.groupby(["study", "label"], sort=True):
        rows = sorted(g.index)
        rng.shuffle(rows)
        start = 0
        for s, n in SIZES.items():
            chosen[s].extend(rows[start:start + n])
            start += n
    for s in SIZES:
        sample = pop.loc[chosen[s]].copy()
        order = list(range(len(sample)))
        rng.shuffle(order)               # item numbers carry no study or label
        sample = sample.iloc[order].reset_index(drop=True)
        sample["uid"] = ["%s%03d" % (PREFIX[s], i + 1) for i in range(len(sample))]
        sample[["uid", "text"]].to_csv(os.path.join(SAMPLES, "%s_items.csv" % s), index=False)
        sample[["uid", "study", "row", "label", "dimension"]].to_csv(
            os.path.join(SAMPLES, "%s_key.csv" % s), index=False)
        print("%s: %d items, %s" % (s, len(sample),
              sample.groupby(["study", "label"]).size().to_dict()))


# ---------------------------------------------------------------------------
# annotate
# ---------------------------------------------------------------------------
def request_openai(text, system, key):
    body = {"model": MODELS["openai"],
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": "Explanation: " + text}],
            "response_format": {"type": "json_schema",
                                "json_schema": {"name": "agency", "strict": True, "schema": SCHEMA}}}
    r = requests.post("https://api.openai.com/v1/chat/completions", json=body, timeout=180,
                      headers={"Authorization": "Bearer " + key})
    r.raise_for_status()
    j = r.json()
    return j["choices"][0]["message"]["content"], j.get("model")


def request_gemini(text, system, key):
    schema = {"type": "OBJECT", "properties": {f: {"type": "BOOLEAN"} for f in FLAGS},
              "required": FLAGS, "propertyOrdering": FLAGS}
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": "Explanation: " + text}]}],
            "generationConfig": {"responseMimeType": "application/json", "responseSchema": schema}}
    r = requests.post("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
                      % MODELS["gemini"], json=body, timeout=180, headers={"x-goog-api-key": key})
    r.raise_for_status()
    j = r.json()
    return j["candidates"][0]["content"]["parts"][0]["text"], j.get("modelVersion")


def parse(raw):
    out = json.loads(raw)
    assert set(out) == set(FLAGS) and all(isinstance(out[f], bool) for f in FLAGS)
    return out


def annotate(sample, annotator):
    assert annotator in MODELS
    # The key is needed only for a request the cache cannot answer (checked below), so a replay
    # of the cached annotations runs without one and sends nothing.
    key = os.environ.get(KEYS[annotator])
    os.makedirs(ANNOTATIONS, exist_ok=True)
    system = codebook()
    items = pd.read_csv(os.path.join(SAMPLES, "%s_items.csv" % sample), dtype=str,
                        keep_default_na=False)
    cache_path = os.path.join(ANNOTATIONS, "cache_%s.jsonl" % annotator)
    cache = {}
    if os.path.exists(cache_path):
        for line in open(cache_path, encoding="utf-8"):
            rec = json.loads(line)
            cache[rec["request_sha256"]] = rec

    def request_key(text):
        return sha256_text(json.dumps([MODELS[annotator], system, text]))

    todo = sorted({t for t in items["text"] if request_key(t) not in cache})
    print("%s, %s: %d items, %d new requests" % (sample, annotator, len(items), len(todo)))
    assert key or not todo, "Set %s in the environment: %d items are not in the cache." % (
        KEYS[annotator], len(todo))
    call = request_openai if annotator == "openai" else request_gemini

    def work(text):
        for attempt in range(6):
            try:
                raw, version = call(text, system, key)
                parse(raw)
                return {"request_sha256": request_key(text), "model": MODELS[annotator],
                        "model_version": version, "codebook_sha256": sha256_text(system),
                        "text_sha256": sha256_text(text), "response": raw,
                        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
            except Exception as error:      # network, rate limit or a malformed answer
                last = repr(error)[:300].replace(key, "<key>")
                time.sleep(2 ** attempt)
        raise RuntimeError("%s failed after retries: %s" % (annotator, last))

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool, \
            open(cache_path, "a", encoding="utf-8") as out:
        for rec in pool.map(work, todo):
            cache[rec["request_sha256"]] = rec
            out.write(json.dumps(rec) + "\n")
            out.flush()
    codes = [dict(uid=u, **parse(cache[request_key(t)]["response"]))
             for u, t in zip(items["uid"], items["text"])]
    out_path = os.path.join(ANNOTATIONS, "%s_%s.csv" % (sample, annotator))
    frame = pd.DataFrame(codes)
    frame["annotator"] = annotator
    frame["model"] = MODELS[annotator]
    frame["codebook_sha256"] = sha256_text(system)
    frame.to_csv(out_path, index=False)
    print("written:", os.path.relpath(out_path, HERE),
          {f: int(frame[f].sum()) for f in FLAGS})


# ---------------------------------------------------------------------------
# score
# ---------------------------------------------------------------------------
ANNOTATORS = ["openai", "gemini", "claude"]


def fleiss_kappa(votes):
    """votes: n_items x n_raters array of 0/1."""
    n = votes.shape[1]
    p_yes = votes.mean(axis=1)
    agree = (p_yes ** 2 + (1 - p_yes) ** 2 - 1.0 / n) * n / (n - 1)
    p_bar = agree.mean()
    p = votes.mean()
    p_e = p ** 2 + (1 - p) ** 2
    return (p_bar - p_e) / (1 - p_e) if p_e < 1 else float("nan")


def wilson(k, n, z=1.959963984540054):
    """The Wilson 95 percent interval of the proportion k / n."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return centre - half, centre + half


def load_codes(sample):
    frames = []
    for a in ANNOTATORS:
        f = pd.read_csv(os.path.join(ANNOTATIONS, "%s_%s.csv" % (sample, a)))
        frames.append(f[["uid"] + FLAGS].set_index("uid").add_prefix(a + ":"))
    codes = pd.concat(frames, axis=1)
    assert not codes.isna().any().any(), "every annotator must code every item"
    return codes.astype(bool)


def score(sample, rule_flags=None, pattern_flags=None):
    """Agreement of the annotators, and of the rule (and pattern form) with
    their majority. rule_flags and pattern_flags are data frames indexed by uid."""
    codes = load_codes(sample)
    key = pd.read_csv(os.path.join(SAMPLES, "%s_key.csv" % sample)).set_index("uid")
    part = key["study"].map({1: "originals", 3: "originals", 2: "second works",
                             4: "second works", 5: "second works"})
    rows = []
    reference = pd.DataFrame(index=codes.index)
    for f in FLAGS:
        votes = codes[["%s:%s" % (a, f) for a in ANNOTATORS]].astype(int).to_numpy()
        reference[f] = votes.sum(axis=1) >= 2
        pair = [(codes["%s:%s" % (a, f)] == codes["%s:%s" % (b, f)]).mean()
                for i, a in enumerate(ANNOTATORS) for b in ANNOTATORS[i + 1:]]
        rows.append(dict(flag=f, what="annotators", scope="all items", n=len(codes),
                         reference_yes=int(reference[f].sum()),
                         fleiss_kappa=fleiss_kappa(votes), mean_pairwise_agreement=sum(pair) / 3,
                         unanimous=float((votes.sum(axis=1) % 3 == 0).mean())))
    for name, pred in (("rule", rule_flags), ("pattern form", pattern_flags)):
        if pred is None:
            continue
        pred = pred.loc[codes.index]
        for f in FLAGS:
            for scope, mask in (("all items", pd.Series(True, index=codes.index)),
                                ("originals", part == "originals"),
                                ("second works", part == "second works")):
                ref, got = reference.loc[mask, f], pred.loc[mask, f].astype(bool)
                yes, no = ref, ~ref
                n_ok, n_all = int((ref == got).sum()), int(mask.sum())
                hit_yes, hit_no = int((got & yes).sum()), int((~got & no).sum())
                a_lo, a_hi = wilson(n_ok, n_all)
                y_lo, y_hi = wilson(hit_yes, int(yes.sum()))
                n_lo, n_hi = wilson(hit_no, int(no.sum()))
                rows.append(dict(flag=f, what=name, scope=scope, n=n_all,
                                 reference_yes=int(yes.sum()),
                                 agreement=n_ok / n_all, agreement_lo=a_lo, agreement_hi=a_hi,
                                 recall_yes=hit_yes / yes.sum() if yes.sum() else float("nan"),
                                 recall_yes_lo=y_lo, recall_yes_hi=y_hi,
                                 recall_no=hit_no / no.sum() if no.sum() else float("nan"),
                                 recall_no_lo=n_lo, recall_no_hi=n_hi,
                                 precision_yes=float((got & yes).sum() / got.sum()) if got.sum() else float("nan")))
    out = pd.DataFrame(rows)
    out.insert(0, "sample", sample)
    out.insert(0, "analysis", ANALYSIS_STATUS)
    return out, reference


FREEZE = os.path.join(HERE, "agency_freeze.md")
RULE_PATH = os.path.join(HERE, "agency_rule.py")


def frozen_rule_sha():
    """The rule's checksum as agency_freeze.md records it, or None."""
    if not os.path.exists(FREEZE):
        return None
    for line in open(FREEZE, encoding="utf-8"):
        if line.startswith("agency_rule.py SHA-256:"):
            return line.split(":", 1)[1].strip().strip("`")
    return None


def run_score(sample):
    """Score the rule and the pattern form on one sample and write the table.
    The validation sample is scored only by the frozen rule."""
    if sample == "validation":
        recorded = frozen_rule_sha()
        assert recorded is not None, "Freeze the rule (agency_freeze.md) before scoring the validation sample."
        assert recorded == sha256_file(RULE_PATH), "agency_rule.py differs from the frozen rule."
    import agency_pattern
    import agency_rule
    nlp = agency_rule.load_model()
    items = pd.read_csv(os.path.join(SAMPLES, "%s_items.csv" % sample), dtype=str,
                        keep_default_na=False).set_index("uid")
    rule = pd.DataFrame({u: {f: agency_rule.flags(t, nlp)[f] for f in FLAGS}
                         for u, t in items["text"].items()}).T
    pattern = pd.DataFrame({u: agency_pattern.flags(t) for u, t in items["text"].items()}).T
    table, reference = score(sample, rule, pattern)
    os.makedirs(TABLES, exist_ok=True)
    table.to_csv(os.path.join(TABLES, "agency_%s_scores.csv" % sample), index=False)
    out = reference.add_prefix("reference:").join(rule.add_prefix("rule:"))
    out.reset_index().rename(columns={"index": "uid"}).to_csv(
        os.path.join(TABLES, "agency_%s_codes.csv" % sample), index=False)
    return table


def freeze():
    """Write agency_freeze.md: the checksums that fix the rule before it reads
    any validation item, and its scores on the development sample."""
    assert not os.path.exists(FREEZE), "The rule is frozen already."
    assert not os.path.exists(os.path.join(TABLES, "agency_validation_scores.csv")), \
        "The validation sample has been scored; the rule can no longer be frozen."
    import spacy
    import agency_rule
    nlp = agency_rule.load_model()
    dev = run_score("development")
    dev = dev[(dev["what"] == "rule") & (dev["scope"] == "all items")]
    lines = ["# The agency rule, frozen", "",
             "Frozen on %s UTC, after the rule was adjusted on the development sample and before "
             "it read any item of the validation sample. Nothing in these files changes afterwards."
             % datetime.datetime.now(datetime.timezone.utc).strftime("%d %B %Y, %H:%M"), "",
             "agency_rule.py SHA-256: `%s`" % sha256_file(RULE_PATH),
             "agency_pattern.py SHA-256: `%s`" % sha256_file(os.path.join(HERE, "agency_pattern.py")),
             "agency_codebook.md SHA-256 (of its text): `%s`" % sha256_text(codebook()),
             "spaCy: %s; model %s %s" % (spacy.__version__, agency_rule.SPACY_MODEL, nlp.meta["version"]),
             "", "Scores on the 250 development items, against the majority of the three annotators:", ""]
    for r in dev.itertuples():
        lines.append("- %s: agreement %.3f, recall %.3f of %d yes and %.3f of no, precision %.3f"
                     % (r.flag, r.agreement, r.recall_yes, r.reference_yes, r.recall_no, r.precision_yes))
    with open(FREEZE, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "draw":
        draw()
    elif command == "freeze":
        freeze()
    elif command == "annotate":
        annotate(sys.argv[2], sys.argv[3])
    elif command == "score":
        pd.set_option("display.width", 200)
        t = run_score(sys.argv[2])
        cols = ["flag", "what", "scope", "n", "reference_yes", "fleiss_kappa", "mean_pairwise_agreement",
                "agreement", "recall_yes", "recall_no", "precision_yes"]
        print(t[[c for c in cols if c in t.columns]].round(3).to_string(index=False))
    else:
        sys.exit(__doc__)
