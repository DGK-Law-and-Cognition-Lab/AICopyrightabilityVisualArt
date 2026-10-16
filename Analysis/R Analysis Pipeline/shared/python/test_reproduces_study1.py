"""Test that study_text reproduces the deposited Study 1 text outputs.

The test loads Study 1/study1_long_with_text.csv, builds the blind slice
exactly as Study1_02_Text.ipynb does (the six columns id, stimulus_id,
stimulus_num, stimulus_type, dimension and response_text), runs every export
function of study_text on it, writes each result with the module's own
writers into a temporary folder, and compares it with the file deposited in
Study 1/nlp/ or Study 1/tables/.

A CSV passes if it is byte-identical to the deposited file. If the bytes
differ, the two are read back as data frames (tables held in memory by the
pandas library) and pass only if they have the same columns and rows, every
non-numeric cell is equal, and every numeric cell differs by at most 1e-12
(empty cells must be empty in both). The rules text and its checksum (the
SHA-256 fingerprint of the text, a 64-character string that changes if one
character changes) must be exactly equal, and the checksum must also equal
the one the Study 1 run manifest records.

Four checks come before the comparisons. Every deposited file must match the
SHA-256 the Study 1 run manifest records for it, so that the comparison is
with the outputs of the recorded run. Every function in study_text that takes
a blind frame must refuse a frame that carries the condition, the rating, a
demographic or a column outside the blind contract; the test finds those
functions by their parameter named "blind". The constructed sentences must be
read as the rules say. The rules text written for another study must differ
from the Study 1 text only in the title line and in the line that gives the
number of responses.

Two further files are compared and reported but do not decide the result:
text_rules_grounding.txt, and text_topics_embedding_agreement.csv when the
sentence-embedding model is on the machine.

Paths are found relative to this file. The environment variable STUDY1_DIR
names another Study 1 folder instead. Printed paths are relative to the Study
1 folder, and an error is printed with its file names relative to the
pipeline root. The test writes no bytecode cache beside the module.

Run it with
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python3 test_reproduces_study1.py
It exits with status 0 when every decisive comparison passes and 1 otherwise.
"""

import sys

sys.dont_write_bytecode = True

import difflib  # noqa: E402
import hashlib  # noqa: E402
import inspect  # noqa: E402
import os  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import study_text  # noqa: E402

STUDY1_DIR_VARIABLE = "STUDY1_DIR"
STUDY1_DIR = os.path.normpath(os.environ.get(STUDY1_DIR_VARIABLE)
                              or os.path.join(HERE, os.pardir, os.pardir, "Study 1"))
INPUT_NAME = "study1_long_with_text.csv"
MANIFEST = os.path.join("tables", "study1_text_run_manifest.csv")
STUDY = "Study 1"
BLIND_COLUMNS = ["id", "stimulus_id", "stimulus_num", "stimulus_type", "dimension", "response_text"]
FLOAT_TOLERANCE = 1e-12

# The deposited file each export is compared with, and the function that
# builds it. Every entry here decides the result.
CSV_EXPORTS = [
    ("nlp/study1_text_measures.csv", study_text.measures_frame),
    ("nlp/study1_text_wordcounts.csv", study_text.wordcounts_frame),
    ("nlp/study1_text_vocabulary.csv", study_text.vocabulary_frame),
    ("nlp/study1_text_tokens.csv", study_text.tokens_frame),
    ("nlp/study1_text_affect.csv", study_text.affect_frame),
    ("nlp/study1_text_topics.csv", study_text.topics_frame),
    ("tables/text_topics_top_words.csv", study_text.topic_top_words_frame),
    ("tables/text_topics_stability.csv", study_text.topic_stability_frame),
]
TEXT_EXPORTS = [
    ("tables/text_rules.txt", lambda blind: study_text.rules_text(blind, STUDY)),
    ("tables/text_rules.sha256", lambda blind: study_text.rules_checksum_text(blind, STUDY)),
]


def shown(path):
    """`path` relative to the Study 1 folder, for printing."""
    return os.path.relpath(path, STUDY1_DIR)


def file_sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def same_bytes(path_a, path_b):
    with open(path_a, "rb") as a, open(path_b, "rb") as b:
        return a.read() == b.read()


def compare_as_frames(new_path, old_path):
    """(equal, note): the two CSVs compared as data frames, floats to FLOAT_TOLERANCE."""
    new = pd.read_csv(new_path)
    old = pd.read_csv(old_path)
    if list(new.columns) != list(old.columns):
        return False, "columns differ: %s against %s" % (list(new.columns), list(old.columns))
    if new.shape != old.shape:
        return False, "shape differs: %s against %s" % (new.shape, old.shape)
    largest = 0.0
    for column in new.columns:
        a, b = new[column], old[column]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b) \
                and not pd.api.types.is_bool_dtype(a):
            a_values, b_values = a.to_numpy(dtype=float), b.to_numpy(dtype=float)
            if not (np.isnan(a_values) == np.isnan(b_values)).all():
                return False, "%s: empty cells differ" % column
            both = ~np.isnan(a_values)
            if both.any():
                difference = float(np.max(np.abs(a_values[both] - b_values[both])))
                largest = max(largest, difference)
                if difference > FLOAT_TOLERANCE:
                    return False, "%s: largest difference %.3g" % (column, difference)
        elif not (a.astype(str) == b.astype(str)).all():
            return False, "%s: %d cells differ" % (column, int((a.astype(str) != b.astype(str)).sum()))
    return True, "equal as data frames; largest numeric difference %.3g" % largest


def check_manifest(manifest):
    """Every deposited file the manifest lists, against the SHA-256 recorded for it."""
    mismatched = []
    for relative, recorded in zip(manifest["file"], manifest["sha256"]):
        path = os.path.join(STUDY1_DIR, relative)
        if not os.path.exists(path) or file_sha256(path) != recorded:
            mismatched.append(relative)
    return mismatched


def blind_functions():
    """Every function defined in study_text with a parameter named "blind"."""
    found = []
    for name, function in inspect.getmembers(study_text, inspect.isfunction):
        if function.__module__ == study_text.__name__ \
                and "blind" in inspect.signature(function).parameters:
            found.append((name, function))
    return found


def call_with_frame(function, frame, measures):
    """Call `function` with `frame` as its blind frame, filling the other
    required parameters: the study name, and a measures file for check_measures."""
    arguments = {}
    for parameter in inspect.signature(function).parameters.values():
        if parameter.name == "blind":
            arguments["blind"] = frame
        elif parameter.default is inspect.Parameter.empty:
            arguments[parameter.name] = {"study": STUDY, "frame": measures}[parameter.name]
    return function(**arguments)


def check_refusals(raw, blind, measures):
    """Every function that takes a blind frame must refuse a frame outside the contract."""
    bad_frames = [
        ("the full long file (condition, rating, demographics)", raw),
        ("the blind slice plus rating", blind.assign(rating=raw["rating"].values)),
        ("the blind slice plus Type", blind.assign(Type=raw["Type"].values)),
        ("the blind slice plus a column outside the contract", blind.assign(deriv_effort="x")),
    ]
    functions = blind_functions()
    failures = []
    for label, frame in bad_frames:
        for name, function in functions:
            try:
                call_with_frame(function, frame, measures)
            except AssertionError:
                continue
            failures.append("%s was accepted by %s" % (label, name))
    return bad_frames, functions, failures


def check_rules_text_across_studies(blind):
    """The lines in which another study's rules text differs from Study 1's.

    The other study is named "Study 3" and given the first 100 responses, so
    that both the name and the number of responses differ."""
    study1 = study_text.rules_text(blind, STUDY).splitlines()
    other = study_text.rules_text(blind.iloc[:100], "Study 3").splitlines()
    changed = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, study1, other, autojunk=False).get_opcodes():
        if tag != "equal":
            changed.append((tag, study1[i1:i2], other[j1:j2]))
    return changed


def print_error(error):
    """Print an error with its file names relative to the pipeline root."""
    root = study_text.PIPELINE_ROOT
    print("The test stopped with an error:")
    for frame in traceback.extract_tb(error.__traceback__):
        filename = frame.filename
        if os.path.abspath(filename).startswith(root):
            filename = os.path.relpath(filename, root)
        else:
            filename = os.path.basename(filename)
        print("  %s, line %d, in %s" % (filename, frame.lineno, frame.name))
    print("%s: %s" % (type(error).__name__, error))


def main():
    started = time.time()
    input_path = os.path.join(STUDY1_DIR, INPUT_NAME)
    manifest_path = os.path.join(STUDY1_DIR, MANIFEST)
    print("study_text against the deposited Study 1 outputs")
    print("Study 1 folder: found; paths below are relative to it")
    for path in [input_path, manifest_path]:
        if not os.path.exists(path):
            print("Missing: %s. Set %s to the Study 1 folder." % (shown(path), STUDY1_DIR_VARIABLE))
            return 1
    print("Input:", shown(input_path))

    results = []   # (name, decisive, passed, how)

    # 1. the deposited files are the outputs of the recorded run
    raw = pd.read_csv(input_path)
    manifest = pd.read_csv(manifest_path)
    input_sha = file_sha256(input_path)
    input_ok = input_sha == manifest["input_sha256"].iloc[0]
    results.append(("input file", True, input_ok,
                    "SHA-256 equals the one run %s recorded" % manifest["run_id"].iloc[0] if input_ok
                    else "SHA-256 DIFFERS from the one the run manifest records"))
    mismatched = check_manifest(manifest)
    results.append(("deposited files", True, not mismatched,
                    "all %d match the run manifest" % len(manifest) if not mismatched
                    else "DIFFER from the run manifest: %s" % mismatched))
    print("Run manifest: run %s, %d files" % (manifest["run_id"].iloc[0], len(manifest)))

    # the blind slice, built as the notebook builds it
    blind = raw[BLIND_COLUMNS].copy()
    present = [c for c in blind.columns if c in ["Type", "rating", "condition", "arm"]]
    assert not present and list(blind.columns) == BLIND_COLUMNS
    print("Blind slice: %d rows, columns %s" % (len(blind), list(blind.columns)))
    print()

    # 2. the blind contract
    measures = study_text.measures_frame(blind)
    bad_frames, functions, failures = check_refusals(raw, blind, measures)
    print("REFUSAL CHECK: %d functions take a blind frame; each is given %d frames outside the contract"
          % (len(functions), len(bad_frames)))
    print("  functions: " + ", ".join(name for name, _function in functions))
    for label, _frame in bad_frames:
        print("  refused by every function: " + label if not any(f.startswith(label) for f in failures)
              else "  NOT refused by every function: " + label)
    for failure in failures:
        print("  NOT REFUSED:", failure)
    results.append(("blind contract", True, not failures,
                    "%d functions each refuse all %d frames" % (len(functions), len(bad_frames))
                    if not failures else "%d acceptances" % len(failures)))
    print()

    # 3. the constructed sentences
    try:
        rows = study_text.check_constructed_sentences()
        results.append(("constructed sentences", True, True,
                        "%d sentences read as the rules say" % len(rows)))
    except AssertionError as error:
        results.append(("constructed sentences", True, False, str(error)))

    # 4. the rules text in another study
    changed = check_rules_text_across_studies(blind)
    print("RULES TEXT FOR ANOTHER STUDY (named Study 3, given 100 responses), lines that differ:")
    for _tag, old_lines, new_lines in changed:
        for line in old_lines:
            print("  Study 1: " + line)
        for line in new_lines:
            print("  Study 3: " + line)
    only_header = (len(changed) == 2
                   and all(len(old) == 1 and len(new) == 1 for _tag, old, new in changed)
                   and "TEXT MEASURES: THE RULES IN FULL" in changed[0][1][0]
                   and "responses, identically," in changed[1][1][0])
    results.append(("rules text across studies", True, only_header,
                    "only the title line and the response-count line differ" if only_header
                    else "%d changed blocks, not only the two header lines" % len(changed)))
    print()

    run_id = study_text.new_run_id()
    with tempfile.TemporaryDirectory() as scratch:
        # 5. the CSV exports
        for relative, function in CSV_EXPORTS:
            tick = time.time()
            deposited = os.path.join(STUDY1_DIR, relative)
            written = study_text.write_csv_atomic(
                os.path.join(scratch, os.path.basename(relative)), function(blind), run_id)
            if same_bytes(written, deposited):
                passed, how = True, "byte-identical"
            else:
                passed, how = compare_as_frames(written, deposited)
            results.append((relative, True, passed, how))
            print("  %-42s %-52s %5.1f s" % (relative, how, time.time() - tick))

        # 6. the rules and their checksum
        for relative, function in TEXT_EXPORTS:
            deposited = os.path.join(STUDY1_DIR, relative)
            written = study_text.write_text_atomic(
                os.path.join(scratch, os.path.basename(relative)), function(blind), run_id)
            passed = same_bytes(written, deposited)
            results.append((relative, True, passed, "exactly equal" if passed else "DIFFERENT"))
            print("  %-42s %s" % (relative, "exactly equal" if passed else "DIFFERENT"))
        checksum = study_text.sha256_text(study_text.rules_text(blind, STUDY))
        agrees = (checksum == file_sha256(os.path.join(STUDY1_DIR, "tables", "text_rules.txt"))
                  and checksum == manifest["rules_sha256"].iloc[0])
        results.append(("rules checksum", True, agrees,
                        "%s, equal to the deposited file's SHA-256 and to the manifest's" % checksum
                        if agrees else "DIFFERENT from the deposited checksum"))

        # 7. further comparisons, reported without deciding the result
        relative = "tables/text_rules_grounding.txt"
        written = study_text.write_text_atomic(
            os.path.join(scratch, "text_rules_grounding.txt"),
            study_text.grounding_text(blind, STUDY), run_id)
        passed = same_bytes(written, os.path.join(STUDY1_DIR, relative))
        results.append((relative, False, passed, "exactly equal" if passed else "DIFFERENT"))
        print("  %-42s %s" % (relative, "exactly equal" if passed else "DIFFERENT"))

        relative = "tables/text_topics_embedding_agreement.csv"
        tick = time.time()
        agreement = study_text.embedding_agreement_frame(blind)
        status = agreement.attrs.get("embedding_status", "")
        if agreement["ari"].isna().all():
            results.append((relative, False, None, "not compared: embedding model %s" % status))
        else:
            deposited = os.path.join(STUDY1_DIR, relative)
            written = study_text.write_csv_atomic(
                os.path.join(scratch, os.path.basename(relative)), agreement, run_id)
            if same_bytes(written, deposited):
                passed, how = True, "byte-identical"
            else:
                passed, how = compare_as_frames(written, deposited)
            results.append((relative, False, passed, how))
        print("  %-42s %-52s %5.1f s" % (relative, results[-1][3], time.time() - tick))
        print("  embedding model: %s" % status)

    # the summary
    print()
    print("=" * 100)
    print("RESULT (CSV tolerance for numeric cells, used only if the bytes differ: %g)" % FLOAT_TOLERANCE)
    print("=" * 100)
    for name, decisive, passed, how in results:
        verdict = "skipped" if passed is None else ("pass" if passed else "FAIL")
        print("  %-7s %-44s %s%s" % (verdict, name, how, "" if decisive else "   (reported only)"))
    decisive_ok = all(passed for _name, decisive, passed, _how in results if decisive)
    print()
    print("Every decisive comparison passed." if decisive_ok
          else "At least one decisive comparison failed.")
    print("Elapsed: %.0f s" % (time.time() - started))
    return 0 if decisive_ok else 1


if __name__ == "__main__":
    try:
        status = main()
    except Exception as error:
        print_error(error)
        status = 1
    sys.exit(status)
