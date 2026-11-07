"""Origin as reason: does an explanation give how the work was made as a reason for its rating?

Exploratory. Specified on 6 November 2026, after every registered result was known; the lead
author approved the definition (origin_reason_plan.md) the same day. It changes no registered
verdict. The rule (origin_reason_rule.py) splits an explanation into sentences with spaCy and reads
each with fixed patterns; this script draws the
samples, has model annotators code them from the codebook (origin_reason_codebook.md), scores the
rule against them, freezes the rule, and applies it to every explanation:

    python3 OriginReason.py draw
        Two disjoint samples of analyzed explanations, stratified by Part (originals or secondary
        works), label and whether the word list says_prompt fires (so that the rare yes cases are
        well represented): development (250), on which the rule may be adjusted, and validation
        (400), on which the frozen rule is scored once. samples/<set>_items.csv holds an item
        number and the text only; samples/<set>_key.csv the study, row, label, question, Part and
        stratum, and is never shown to an annotator.
    python3 OriginReason.py annotate <set> <openai|gemini>
        One model codes every item, one item per request, with the codebook as its instructions
        and the explanation as the only other input. Requests and responses are kept in
        annotations/cache_<annotator>.jsonl; a replay needs no key and sends nothing.
    python3 OriginReason.py score <set>
        The reference code is the majority of the three annotators (OpenAI, Google and Claude; the
        Claude codes come from a separate session given only the codebook and the items). Scores
        the rule against it. On the validation sample the rule must match the frozen checksum.
    python3 OriginReason.py freeze
        Records the rule's checksum and the development scores in origin_reason_freeze.md.
    python3 OriginReason.py apply
        Applies the frozen rule to every analyzed explanation of the five studies, reading only the
        text, and writes nlp/origin_reason_flags.csv (left out of the public copy: Study 1 labels
        participants by their participant numbers) and tables/origin_reason_apply_record.csv, which
        OriginReason_Analysis.R checks.

Before scoring the validation sample and before applying the rule, the script checks that the
rule and the codebook have the checksums the freeze recorded, that the shared word-list module
(shared/python/study_text.py, which supplies says_prompt) is the one the rule was frozen with, and
that spaCy and its English model are the versions the rule was built with. The validation sample
is scored once: a later score must reproduce the saved scores exactly, or the script stops.

Pass marks, fixed before the validation sample was drawn: agreement with the reference on at
least 85% of items, and recall of at least 75% of the reference's yes items and of its no items.
The API keys are read from OPENAI_API_KEY_AICOPYRIGHT and GEMINI_API_KEY_AICOPYRIGHT only when a
request is not in the cache, and never written.
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

HERE = os.path.dirname(os.path.abspath(__file__))
PIPELINE = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(PIPELINE, "shared", "python"))
import study_text  # noqa: E402

SAMPLES, ANNOTATIONS, TABLES, NLP = (os.path.join(HERE, d) for d in ("samples", "annotations", "tables", "nlp"))
CODEBOOK_PATH = os.path.join(HERE, "origin_reason_codebook.md")
RULE_PATH = os.path.join(HERE, "origin_reason_rule.py")
FREEZE = os.path.join(HERE, "origin_reason_freeze.md")
STATUS = ("exploratory; specified on 6 November 2026, after every registered result was known; "
          "changes no registered verdict")
SEED = 20261106
LABEL_COLUMN = {1: "Type", 2: "source", 3: "Type", 4: "label", 5: "source"}
# The shared word-list module the rule was frozen with: the checksum recorded by the explanation-shift
# run of 1 November 2026 and unchanged at the freeze (6 November 2026, 19:58 UTC).
STUDY_TEXT_PATH = os.path.join(PIPELINE, "shared", "python", "study_text.py")
STUDY_TEXT_SHA256 = "0ec501216b65911986500e31ae9799dae2cbc7bed9b11be43b5737e806a2883b"
SPACY_VERSIONS = {"spacy": "3.7.4", "en_core_web_sm": "3.7.1"}
WORK_COLUMN = {1: "stimulus_id", 2: "work_id", 3: "stimulus_id", 4: "work_id", 5: "work_id"}
PART = {1: "originals", 3: "originals", 2: "secondary works", 4: "secondary works", 5: "secondary works"}
# Items per stratum (Part, label, says_prompt): development, validation.
SIZES = {
    ("originals", "AI", True): (45, 70), ("originals", "Human", True): (30, 50),
    ("secondary works", "AI", True): (45, 70), ("secondary works", "Human", True): (30, 50),
    ("originals", "AI", False): (25, 40), ("originals", "Human", False): (25, 40),
    ("secondary works", "AI", False): (25, 40), ("secondary works", "Human", False): (25, 40),
}
SETS = ("development", "validation")
PREFIX = {"development": "d", "validation": "v"}
MODELS = {"openai": "gpt-5.5-2026-04-23", "gemini": "gemini-3.1-pro-preview"}  # as in ../agency
KEYS = {"openai": "OPENAI_API_KEY_AICOPYRIGHT", "gemini": "GEMINI_API_KEY_AICOPYRIGHT"}
DIRECTIONS = ["lowers", "raises", "unclear", "none"]
ANNOTATORS = ["openai", "gemini", "claude"]
PASS = {"agreement": 0.85, "recall_yes": 0.75, "recall_no": 0.75}


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def codebook():
    with open(CODEBOOK_PATH, encoding="utf-8") as handle:
        return handle.read()


_PROMPT = study_text.compile_rule(study_text._rule("says_prompt"))


def says_prompt(text):
    return study_text.find_match(text.lower(), *_PROMPT) is not None


# --------------------------------------------------------------------------- population
def population():
    """Every analyzed explanation: a rating on a five-point item and at least one letter."""
    frames = []
    for s in range(1, 6):
        long = pd.read_csv(os.path.join(PIPELINE, "Study %d" % s, "study%d_long_with_text.csv" % s), dtype=str,
                           keep_default_na=False)
        keep = long["response_text"].str.contains(r"[A-Za-z]", regex=True) & (long["rating"] != "")
        if "k_points" in long.columns:
            keep &= long["k_points"] == "5"
        d = pd.DataFrame({"study": s, "row": range(len(long)), "id": long["id"], "work": long[WORK_COLUMN[s]],
                          "label": long[LABEL_COLUMN[s]], "dimension": long["dimension"],
                          "text": long["response_text"]})[keep]
        d["part"] = PART[s]
        frames.append(d)
    pop = pd.concat(frames, ignore_index=True)
    pop["says_prompt"] = [says_prompt(t) for t in pop["text"]]
    return pop


# --------------------------------------------------------------------------- draw
def draw():
    os.makedirs(SAMPLES, exist_ok=True)
    targets = [os.path.join(SAMPLES, "%s_%s.csv" % (s, k)) for s in SETS for k in ("items", "key")]
    assert not any(os.path.exists(p) for p in targets), "The samples exist already; they are drawn once."
    pop = population()
    rng = random.Random(SEED)
    chosen = {s: [] for s in SETS}
    for stratum, (n_dev, n_val) in sorted(SIZES.items(), key=str):
        part, label, prompt = stratum
        rows = sorted(pop.index[(pop.part == part) & (pop.label == label) & (pop.says_prompt == prompt)])
        assert len(rows) >= n_dev + n_val, "stratum %s has only %d explanations" % (stratum, len(rows))
        rng.shuffle(rows)
        chosen["development"].extend(rows[:n_dev])
        chosen["validation"].extend(rows[n_dev:n_dev + n_val])
    for s in SETS:
        sample = pop.loc[chosen[s]].copy()
        order = list(range(len(sample)))
        rng.shuffle(order)  # item numbers carry no study, label or stratum
        sample = sample.iloc[order].reset_index(drop=True)
        sample["uid"] = ["%s%03d" % (PREFIX[s], i + 1) for i in range(len(sample))]
        sample[["uid", "text"]].to_csv(os.path.join(SAMPLES, "%s_items.csv" % s), index=False)
        sample[["uid", "study", "row", "label", "dimension", "part", "says_prompt"]].to_csv(
            os.path.join(SAMPLES, "%s_key.csv" % s), index=False)
        print("%s: %d items" % (s, len(sample)))


# --------------------------------------------------------------------------- annotate
def _schema():
    return {"type": "object", "properties": {"origin_reason": {"type": "boolean"},
                                             "direction": {"type": "string", "enum": DIRECTIONS}},
            "required": ["origin_reason", "direction"], "additionalProperties": False}


def request_openai(text, system, key):
    import requests
    body = {"model": MODELS["openai"],
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": "Explanation: " + text}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "origin_reason", "strict": True,
                                                                        "schema": _schema()}}}
    r = requests.post("https://api.openai.com/v1/chat/completions", json=body, timeout=180,
                      headers={"Authorization": "Bearer " + key})
    r.raise_for_status()
    j = r.json()
    return j["choices"][0]["message"]["content"], j.get("model")


def request_gemini(text, system, key):
    import requests
    schema = {"type": "OBJECT", "properties": {"origin_reason": {"type": "BOOLEAN"},
                                               "direction": {"type": "STRING", "enum": DIRECTIONS}},
              "required": ["origin_reason", "direction"], "propertyOrdering": ["origin_reason", "direction"]}
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": "Explanation: " + text}]}],
            "generationConfig": {"responseMimeType": "application/json", "responseSchema": schema}}
    r = requests.post("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODELS["gemini"],
                      json=body, timeout=180, headers={"x-goog-api-key": key})
    r.raise_for_status()
    j = r.json()
    return j["candidates"][0]["content"]["parts"][0]["text"], j.get("modelVersion")


def parse(raw):
    out = json.loads(raw)
    assert isinstance(out.get("origin_reason"), bool) and out.get("direction") in DIRECTIONS
    if not out["origin_reason"]:
        out["direction"] = "none"
    elif out["direction"] == "none":
        out["direction"] = "unclear"
    return {"origin_reason": out["origin_reason"], "direction": out["direction"]}


def annotate(sample, annotator):
    assert sample in SETS and annotator in MODELS
    key = os.environ.get(KEYS[annotator])
    os.makedirs(ANNOTATIONS, exist_ok=True)
    system = codebook()
    items = pd.read_csv(os.path.join(SAMPLES, "%s_items.csv" % sample), dtype=str, keep_default_na=False)
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
    assert key or not todo, "Set %s in the environment: %d items are not in the cache." % (KEYS[annotator], len(todo))
    call = request_openai if annotator == "openai" else request_gemini

    def work(text):
        last = ""
        for attempt in range(6):
            try:
                raw, version = call(text, system, key)
                parse(raw)
                return {"request_sha256": request_key(text), "model": MODELS[annotator], "model_version": version,
                        "codebook_sha256": sha256_text(system), "text_sha256": sha256_text(text), "response": raw,
                        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
            except Exception as error:  # network, rate limit or a malformed answer
                last = repr(error)[:300].replace(key or "", "<key>")
                time.sleep(2 ** attempt)
        raise RuntimeError("%s failed after retries: %s" % (annotator, last))

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool, open(cache_path, "a", encoding="utf-8") as out:
        for rec in pool.map(work, todo):
            cache[rec["request_sha256"]] = rec
            out.write(json.dumps(rec) + "\n")
            out.flush()
    codes = [dict(uid=u, **parse(cache[request_key(t)]["response"])) for u, t in zip(items["uid"], items["text"])]
    frame = pd.DataFrame(codes)
    frame["annotator"], frame["model"], frame["codebook_sha256"] = annotator, MODELS[annotator], sha256_text(system)
    frame.to_csv(os.path.join(ANNOTATIONS, "%s_%s.csv" % (sample, annotator)), index=False)
    print("written:", os.path.relpath(os.path.join(ANNOTATIONS, "%s_%s.csv" % (sample, annotator)), HERE),
          "yes:", int(frame["origin_reason"].sum()))


# --------------------------------------------------------------------------- score
def reference(sample):
    frames = []
    for a in ANNOTATORS:
        f = pd.read_csv(os.path.join(ANNOTATIONS, "%s_%s.csv" % (sample, a)), dtype={"uid": str})
        f["origin_reason"] = f["origin_reason"].astype(str).str.lower().eq("true")
        frames.append(f[["uid", "origin_reason", "direction"]].rename(
            columns={"origin_reason": "yes_" + a, "direction": "dir_" + a}))
    ref = frames[0]
    for f in frames[1:]:
        ref = ref.merge(f, on="uid", how="inner", validate="one_to_one")
    yes = ref[["yes_" + a for a in ANNOTATORS]]
    assert len(ref) == len(pd.read_csv(os.path.join(SAMPLES, "%s_items.csv" % sample))), "every annotator codes every item"
    ref["reference"] = yes.sum(axis=1) >= 2
    ref["unanimous"] = yes.nunique(axis=1) == 1

    def majority_direction(r):
        votes = [r["dir_" + a] for a in ANNOTATORS if r["yes_" + a]]
        top = pd.Series(votes).value_counts()
        return "none" if not r["reference"] else (top.index[0] if len(top) and (len(top) == 1 or top.iloc[0] > top.iloc[1])
                                                   else "unclear")
    ref["reference_direction"] = ref.apply(majority_direction, axis=1)
    return ref


def fleiss_kappa(votes):
    import numpy as np
    n = votes.shape[1]
    p_yes = votes.mean(axis=1)
    agree = (p_yes ** 2 + (1 - p_yes) ** 2 - 1.0 / n) * n / (n - 1)
    p = votes.mean()
    pe = p ** 2 + (1 - p) ** 2
    return float((agree.mean() - pe) / (1 - pe)) if pe < 1 else float("nan")


def frozen(field):
    """A checksum the freeze recorded ("rule" or "codebook")."""
    return [l.split("`")[1] for l in open(FREEZE, encoding="utf-8") if l.startswith("- %s sha256:" % field)][0]


def check_frozen():
    """Stop unless the rule, the codebook, the shared word lists and spaCy are as frozen."""
    import importlib.metadata
    assert os.path.exists(FREEZE), "Freeze the rule first."
    assert frozen("rule") == sha256_file(RULE_PATH), "origin_reason_rule.py differs from the frozen rule."
    assert frozen("codebook") == sha256_file(CODEBOOK_PATH), "origin_reason_codebook.md differs from the frozen codebook."
    assert sha256_file(STUDY_TEXT_PATH) == STUDY_TEXT_SHA256, "shared/python/study_text.py differs from the frozen module."
    for pkg, want in SPACY_VERSIONS.items():
        have = importlib.metadata.version(pkg)
        assert have == want, "%s is %s; the rule was frozen with %s." % (pkg, have, want)


def score(sample):
    import origin_reason_rule as rule
    if sample == "validation":
        check_frozen()
    items = pd.read_csv(os.path.join(SAMPLES, "%s_items.csv" % sample), dtype=str, keep_default_na=False)
    ref = reference(sample).merge(items, on="uid", validate="one_to_one")
    nlp = rule.load_model()
    out = [rule.code(t, nlp) for t in ref["text"]]
    ref["rule"] = [o["origin_reason"] for o in out]
    ref["rule_direction"] = [o["direction"] for o in out]
    tp = int((ref.rule & ref.reference).sum()); tn = int((~ref.rule & ~ref.reference).sum())
    n_yes, n_no = int(ref.reference.sum()), int((~ref.reference).sum())
    import numpy as np
    scores = {"items": len(ref), "reference_yes": n_yes, "agreement": (tp + tn) / len(ref),
              "recall_yes": tp / n_yes if n_yes else float("nan"), "recall_no": tn / n_no if n_no else float("nan"),
              "precision_yes": tp / int(ref.rule.sum()) if ref.rule.sum() else float("nan"),
              "annotator_kappa": fleiss_kappa(ref[["yes_" + a for a in ANNOTATORS]].to_numpy().astype(float)),
              "unanimous_share": float(ref.unanimous.mean())}
    yes_both = ref.rule & ref.reference
    scores["direction_agreement_on_shared_yes"] = float((ref.rule_direction[yes_both] == ref.reference_direction[yes_both]).mean()) if yes_both.any() else float("nan")
    scores["passes"] = all(scores[k] >= v for k, v in PASS.items())
    for a in ANNOTATORS:
        scores["agreement_" + a] = float((ref["yes_" + a] == ref.reference).mean())
    os.makedirs(TABLES, exist_ok=True)
    scores_path = os.path.join(TABLES, "origin_reason_%s_scores.csv" % sample)
    new = pd.DataFrame([dict(analysis_status=STATUS, sample=sample, **scores)])
    if sample == "validation" and os.path.exists(scores_path):
        old = pd.read_csv(scores_path)
        same = list(old.columns) == list(new.columns) and all(
            (abs(float(old[c].iloc[0]) - float(new[c].iloc[0])) < 1e-12) if isinstance(new[c].iloc[0], (int, float))
            and not isinstance(new[c].iloc[0], bool) else str(old[c].iloc[0]) == str(new[c].iloc[0]) for c in new.columns)
        assert same, "The validation sample is scored once, and this score differs from the saved one."
    new.to_csv(scores_path, index=False)
    ref[["uid", "reference", "reference_direction", "unanimous", "rule", "rule_direction"] +
        ["yes_" + a for a in ANNOTATORS]].to_csv(os.path.join(TABLES, "origin_reason_%s_codes.csv" % sample), index=False)
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in scores.items()}, indent=1))
    return ref


def freeze():
    assert not os.path.exists(FREEZE), "The rule is frozen already."
    dev = pd.read_csv(os.path.join(TABLES, "origin_reason_development_scores.csv")).iloc[0]
    with open(FREEZE, "w", encoding="utf-8") as fh:
        fh.write("# Origin-as-reason rule: freeze record\n\n")
        fh.write("- frozen (UTC): `%s`\n" % datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
        fh.write("- rule sha256: `%s`\n" % sha256_file(RULE_PATH))
        fh.write("- codebook sha256: `%s`\n" % sha256_file(CODEBOOK_PATH))
        fh.write("- development scores: agreement %.3f, recall of yes %.3f, recall of no %.3f (%d items)\n"
                 % (dev.agreement, dev.recall_yes, dev.recall_no, dev["items"]))
        fh.write("\nThe validation sample is scored once against this rule. Pass marks: agreement at least 85%, "
                 "recall of yes and of no at least 75%.\n")
    print("frozen:", sha256_file(RULE_PATH))


def apply_all():
    import importlib.metadata
    import origin_reason_rule as rule
    check_frozen()
    pop = population()
    nlp = rule.load_model()
    texts = pop["text"].tolist()
    codes = [rule.code(t, nlp, doc) for t, doc in zip(texts, nlp.pipe(texts, batch_size=256))]
    out = pop[["study", "row", "id", "work", "dimension"]].copy()
    out["origin_reason"] = [c["origin_reason"] for c in codes]
    out["direction"] = [c["direction"] for c in codes]
    os.makedirs(NLP, exist_ok=True)
    flags_path = os.path.join(NLP, "origin_reason_flags.csv")
    out.to_csv(flags_path, index=False)
    os.makedirs(TABLES, exist_ok=True)
    record = [("analysis_status", STATUS),
              ("run (UTC)", datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")),
              ("explanations", len(out)), ("origin as reason", int(out.origin_reason.sum())),
              ("flags sha256", sha256_file(flags_path)), ("rule sha256", sha256_file(RULE_PATH)),
              ("codebook sha256", sha256_file(CODEBOOK_PATH)), ("study_text sha256", sha256_file(STUDY_TEXT_PATH))]
    record += [(pkg, importlib.metadata.version(pkg)) for pkg in SPACY_VERSIONS]
    pd.DataFrame(record, columns=["item", "value"]).to_csv(os.path.join(TABLES, "origin_reason_apply_record.csv"),
                                                           index=False)
    print("coded %d explanations; %d give origin as a reason" % (len(out), int(out.origin_reason.sum())))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.path.insert(0, HERE)
    if cmd == "draw":
        draw()
    elif cmd == "annotate":
        annotate(sys.argv[2], sys.argv[3])
    elif cmd == "score":
        score(sys.argv[2])
    elif cmd == "freeze":
        freeze()
    elif cmd == "apply":
        apply_all()
    else:
        sys.exit(__doc__)
