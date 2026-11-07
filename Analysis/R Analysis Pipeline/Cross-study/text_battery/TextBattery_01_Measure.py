"""Text battery, step 1: count the words of every explanation, blind.

Exploratory. Specified on 31 October 2026, after every registered result was
known. No registration names it, and it changes no registered verdict.

For each of the five studies this step reads four columns of the study's long
data file (the participant, the work, the question and the text) and nothing
else, so the label, the time condition and the rating never reach it. It
builds the shared module's blind frame, which study_text.check_blind() refuses
if any other column is present, and counts every content word of every
explanation with study_text.tokenize(): the lower-cased words of two letters
or more left once the fixed list of function words (the, was, of and the
like) is removed.

Each study's own nlp/studyN_text_wordcounts.csv keeps only the words found in
at least two responses. This step keeps every word, so the distinctive-word
scores of step 2 count every word, as section 8 of the Study 1 text notebook
did, and step 2 can check that it reproduces that section's tables.

It also applies the agency rule (agency/agency_rule.py), once the rule has
been frozen (agency/agency_freeze.md): for every explanation, whether it
presents a person as having made or changed the work, a machine, or an act of
making or changing with no doer stated. The rule reads the text only, and this
step stops if the rule differs from the frozen one.

Writes, in this folder:
    nlp/text_battery_wordcounts.csv
        one row per study, response and content word: study (the pipeline's
        number), id, stimulus_id, dimension, word, count. A response with no
        content word has no row.
    nlp/text_battery_agency.csv
        one row per study and response: study, id, stimulus_id, dimension,
        person_maker, machine_maker, agentless_making (once the rule is frozen).
    tables/text_battery_measure_environment.csv
    tables/text_battery_measure_run_manifest.csv  (written last)

Study numbers follow the pipeline's folders. The paper swaps two: the
pipeline's Study 2 is the paper's Study 3, and its Study 3 is the paper's
Study 2.

Run from this folder:  python3 TextBattery_01_Measure.py
"""

import datetime
import hashlib
import os
import platform
import sys
import uuid
from collections import Counter

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PIPELINE = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir))
SHARED_PYTHON = os.environ.get("STUDY_SHARED_PYTHON", os.path.join(PIPELINE, "shared", "python"))
sys.path.insert(0, SHARED_PYTHON)
import study_text as st  # noqa: E402

ANALYSIS_STATUS = ("exploratory: specified on 31 October 2026, after every registered result "
                   "was known; no registration names it")
NLP_DIR = os.path.join(HERE, "nlp")
TAB_DIR = os.path.join(HERE, "tables")
OUT_WORDCOUNTS = os.path.join(NLP_DIR, "text_battery_wordcounts.csv")
OUT_AGENCY = os.path.join(NLP_DIR, "text_battery_agency.csv")
AGENCY_DIR = os.path.join(HERE, "agency")
AGENCY_RULE = os.path.join(AGENCY_DIR, "agency_rule.py")
AGENCY_FREEZE = os.path.join(AGENCY_DIR, "agency_freeze.md")
OUT_ENVIRONMENT = os.path.join(TAB_DIR, "text_battery_measure_environment.csv")
OUT_MANIFEST = os.path.join(TAB_DIR, "text_battery_measure_run_manifest.csv")

# The column that names the work in each long data file. In Studies 1 and 3 a
# participant rated each image once, so the image is the work. In Studies 2, 4
# and 5 a participant rated one source image at several modification levels,
# so the work is the image at one level, work_id.
WORK_COLUMN = {1: "stimulus_id", 2: "work_id", 3: "stimulus_id", 4: "work_id", 5: "work_id"}
N_RESPONSES = {1: 2220, 2: 20659, 3: 1530, 4: 6318, 5: 10638}


def sha256_of(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def relative(path):
    return os.path.relpath(path, PIPELINE)


def long_path(study):
    return os.path.join(PIPELINE, "Study %d" % study, "study%d_long_with_text.csv" % study)


def blind_frame(study):
    """The study's responses with the four columns the measurement may read."""
    work = WORK_COLUMN[study]
    raw = pd.read_csv(long_path(study), usecols=["id", work, "dimension", "response_text"],
                      dtype=str, keep_default_na=False)
    blind = raw.rename(columns={work: "stimulus_id"})[st.REQUIRED_COLUMNS]
    st.check_blind(blind)
    assert len(blind) == N_RESPONSES[study], (
        "Study %d: expected %d responses, found %d." % (study, N_RESPONSES[study], len(blind)))
    return blind


def word_counts(study, blind):
    rows = []
    for rid, sid, dim, text in zip(blind["id"], blind["stimulus_id"], blind["dimension"],
                                   st.response_texts(blind)):
        for word, count in Counter(st.tokenize(text)).items():
            rows.append((study, rid, sid, dim, word, count))
    out = pd.DataFrame(rows, columns=["study", "id", "stimulus_id", "dimension", "word", "count"])
    return out.sort_values(["study", "id", "stimulus_id", "dimension", "word"]).reset_index(drop=True)


def frozen_rule_sha():
    """The agency rule's checksum as the freeze record gives it, or None."""
    if not os.path.exists(AGENCY_FREEZE):
        return None
    for line in open(AGENCY_FREEZE, encoding="utf-8"):
        if line.startswith("agency_rule.py SHA-256:"):
            return line.split(":", 1)[1].strip().strip("`")
    return None


def agency_flags(study, blind, rule, nlp):
    texts = [t.strip() for t in st.response_texts(blind)]
    docs = iter(nlp.pipe([t for t in texts if t], batch_size=256))
    rows = []
    for rid, sid, dim, text in zip(blind["id"], blind["stimulus_id"], blind["dimension"], texts):
        f = rule.flags(text, nlp, next(docs)) if text else rule.flags(text, nlp)
        rows.append((study, rid, sid, dim) + tuple(f[k] for k in rule.FLAGS))
    return pd.DataFrame(rows, columns=["study", "id", "stimulus_id", "dimension"] + list(rule.FLAGS))


def main():
    os.makedirs(NLP_DIR, exist_ok=True)
    os.makedirs(TAB_DIR, exist_ok=True)
    # A run that stops part way leaves no manifest.
    if os.path.exists(OUT_MANIFEST):
        os.remove(OUT_MANIFEST)
    started = datetime.datetime.now(datetime.timezone.utc)
    inputs = [long_path(s) for s in range(1, 6)] + [os.path.join(SHARED_PYTHON, "study_text.py")]
    frozen = frozen_rule_sha()
    if frozen is not None:
        assert frozen == sha256_of(AGENCY_RULE), "agency/agency_rule.py differs from the frozen rule."
        inputs += [AGENCY_RULE, AGENCY_FREEZE]
        sys.path.insert(0, AGENCY_DIR)
        import agency_rule as rule
        import spacy
        nlp = rule.load_model()
    else:
        print("The agency rule is not frozen yet, so no agency flags are written.")
    input_sha = [sha256_of(p) for p in inputs]
    run_id = "%s-%s" % (started.strftime("%Y%m%dT%H%M%SZ"),
                        hashlib.sha256("\n".join(input_sha).encode()).hexdigest()[:8])

    frames, agency = [], []
    for study in range(1, 6):
        blind = blind_frame(study)
        if frozen is not None:
            agency.append(agency_flags(study, blind, rule, nlp))
        counts = word_counts(study, blind)
        # Every token of every response is counted: the counts add up to the
        # number of content words the tokenizer finds in the study's texts.
        n_tokens = sum(len(st.tokenize(t)) for t in st.response_texts(blind))
        assert counts["count"].sum() == n_tokens
        print("Study %d: %d responses, %d content words, %d distinct words, %d responses with no "
              "content word" % (study, len(blind), n_tokens, counts["word"].nunique(),
                                len(blind) - counts.groupby(["id", "stimulus_id", "dimension"]).ngroups))
        frames.append(counts)
    wordcounts = st.check_output(pd.concat(frames, ignore_index=True), "the word counts")
    st.write_csv_atomic(OUT_WORDCOUNTS, wordcounts)
    outputs = [OUT_WORDCOUNTS]
    if frozen is not None:
        agency = st.check_output(pd.concat(agency, ignore_index=True), "the agency flags")
        st.write_csv_atomic(OUT_AGENCY, agency)
        outputs.append(OUT_AGENCY)
        print("Agency flags:", {k: int(agency[k].sum()) for k in rule.FLAGS}, "of", len(agency))

    # study_text imports these besides pandas and NumPy; the word counts use
    # none of them, but the module does not load without them.
    import scipy
    import sklearn
    import threadpoolctl
    environment = pd.DataFrame([
        ("run_id", run_id),
        ("python", platform.python_version()),
        ("platform", platform.platform()),
        ("pandas", pd.__version__),
        ("numpy", np.__version__),
        ("scipy", scipy.__version__),
        ("scikit-learn", sklearn.__version__),
        ("threadpoolctl", threadpoolctl.__version__),
        ("study_text.py sha256", input_sha[-1]),
        ("tokenizer", "study_text.tokenize(): lower-cased runs of [a-z][a-z']+ with "
                      "study_text.FUNCTION_WORDS removed"),
        ("function words", str(len(st.FUNCTION_WORDS))),
    ] + ([("spacy", spacy.__version__), ("spaCy model", "%s %s" % (rule.SPACY_MODEL, nlp.meta["version"])),
          ("agency_rule.py sha256", frozen)] if frozen is not None else []),
        columns=["item", "value"])
    environment.insert(0, "analysis", ANALYSIS_STATUS)
    st.write_csv_atomic(OUT_ENVIRONMENT, environment)

    outputs.append(OUT_ENVIRONMENT)
    manifest = pd.DataFrame(
        [(run_id, "input", relative(p), os.path.getsize(p), s) for p, s in zip(inputs, input_sha)]
        + [(run_id, "output", relative(p), os.path.getsize(p), sha256_of(p)) for p in outputs],
        columns=["run_id", "role", "file", "bytes", "sha256"])
    st.write_csv_atomic(OUT_MANIFEST, manifest)
    print("Run %s complete: %d word-count rows written." % (run_id, len(wordcounts)))


if __name__ == "__main__":
    main()
