#!/usr/bin/env python3
"""Can the label be read from what people meant, over and above their rating?

Exploratory. Specified on 6 November 2026, after every registered result was known, at the lead
author's request for a test of the explanations that uses no word list. It changes no registered
verdict. It mirrors the registered recoverability check of each study, which asks how well the
label can be predicted from the words of the explanations beyond the rating, but replaces word
counts with sentence embeddings: a pretrained sentence-embedding model turns each explanation
into a list of numbers whose distances reflect differences in meaning, so two explanations that
say the same thing in different words lie close together.

The label is fixed for each participant, so the unit is the participant. For each study and
question, each participant is described by the average embedding of their explanations, their
average rating and their average explanation length (log of the word count). Three logistic
regressions predict the label:

* rating and length only;
* meaning, rating and length: the embedding enters as its first 20 principal components,
  computed on the training participants of each fold only;
* meaning only.

Predictions are made for participants left out of the fit (10 folds, stratified by label,
repeated 5 times; each participant's five out-of-fold predictions are averaged). The result is the
area under the ROC curve (AUC: the chance that a randomly chosen AI-label participant scores
above a randomly chosen Human-label one; 0.5 is chance), with a 95 percent interval from 2,000
resamples of participants. The interval holds each participant's out-of-fold prediction fixed, so
it leaves out the variation that comes from fitting and is somewhat too narrow.

The gain is the AUC from meaning, rating and length minus the AUC from rating and length. Its
null distribution keeps whatever meaning shares with the rating and length and removes only what
it might add: each embedding dimension is regressed on rating and length across participants
(no label is used), and in each of 100 null runs the residuals are shuffled across participants
and added back to the fitted values (the Freedman-Lane method). The null runs use the same folds
and repeats as the real fit. The gain counts as shown when it exceeds the 95th percentile of the
null gains. (A first version shuffled the labels instead, which also breaks the link between label
and rating and so tested whether the text predicts the label at all; corrected on 6 November 2026.)

Two checks are run beside the main analysis:

* without mentions: the same analysis on the explanations that do not mention prompting or a
  machine (the shared word list says_prompt), so that explanations restating the label's own words
  cannot carry the prediction;
* other models: the same analysis of all explanations with two newer sentence-embedding models,
  bge-large-en-v1.5 and mxbai-embed-large-v1, to check that the result does not depend on the
  model. all-mpnet-base-v2 stays the primary model: the registered text checks used it.

Inputs are checked against the checksums each study's registered run recorded. Every model is
read from the local cache only, at a fixed revision. The embeddings are cached in nlp/, one file
per model, keyed on the model, its revision and the exact texts.

Run from this folder:  python3 LabelFromMeaning.py
Writes tables/label_from_meaning.csv and run records. The per-explanation embeddings are kept in
nlp/ (left out of the public copy, since Study 1 labels participants by their participant numbers).
"""

import csv
import datetime
import hashlib
import importlib.metadata
import os
import platform
import sys

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# One numerical thread per process: the fits are small, and many threads per fit compete and slow
# them down. The null runs are spread over processes instead (N_JOBS below).
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_var, "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from joblib import Parallel, delayed  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PIPELINE = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir))
sys.path.insert(0, os.path.join(PIPELINE, "shared", "python"))
import study_text  # noqa: E402

NLP, TABLES = os.path.join(HERE, "nlp"), os.path.join(HERE, "tables")
# (short name, Hugging Face id, revision, role)
MODELS = [
    ("all-mpnet-base-v2", "sentence-transformers/all-mpnet-base-v2", "e8c3b32edf5434bc2275fc9bab85f82640a19130", "primary"),
    ("bge-large-en-v1.5", "BAAI/bge-large-en-v1.5", "d4aa6901d3a41ba39fb536a557fa166f842b0e09", "robustness"),
    ("mxbai-embed-large-v1", "mixedbread-ai/mxbai-embed-large-v1", "b33106f585b9ce46904ad7443a3b52b7a63e231c", "robustness"),
]
ALL, WITHOUT = "all", "without mentions of prompting or a machine"
STATUS = ("exploratory; specified on 6 November 2026, after every registered result was known; "
          "changes no registered verdict")
NULL = "Freedman-Lane: residuals of meaning on rating and length shuffled across participants"
PAPER = {1: 1, 2: 3, 3: 2, 4: 4, 5: 5}
LABEL_COL = {1: "Type", 2: "source", 3: "Type", 4: "label", 5: "source"}
SEED, N_COMPONENTS, FOLDS, REPEATS, BOOT, PERMS = 20260421, 20, 10, 5, 2000, 100
# Processes for the null runs; the results do not depend on this number.
N_JOBS = max(1, (os.cpu_count() or 2) - 2)
_PROMPT = study_text.compile_rule(study_text._rule("says_prompt"))


def stop(message):
    raise SystemExit("LabelFromMeaning.py stopped: " + message)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_study(study):
    path = os.path.join(PIPELINE, f"Study {study}", f"study{study}_long_with_text.csv")
    with open(os.path.join(PIPELINE, f"Study {study}", "tables", f"study{study}_quant_run_manifest.csv"),
              encoding="utf-8", newline="") as fh:
        want = [r["sha256"] for r in csv.DictReader(fh) if r["file"] == f"study{study}_long_with_text.csv"]
    if len(want) != 1 or sha256_file(path) != want[0]:
        stop(f"study{study}_long_with_text.csv does not have the checksum its registered run recorded")
    d = pd.read_csv(path, dtype={"id": str}, keep_default_na=False, low_memory=False)
    if "k_points" in d:
        d = d[d["k_points"].astype(str) == "5"]
    d = d[(d["rating"].astype(str) != "") & d["response_text"].str.contains(r"[A-Za-z]", regex=True)].copy()
    d["rating"] = d["rating"].astype(float)
    d["label"] = d[LABEL_COL[study]]
    if set(d["label"]) != {"Human", "AI"}:
        stop(f"Study {study}: unexpected labels {set(d['label'])}")
    d["study_pipeline"] = study
    return d[["study_pipeline", "id", "label", "dimension", "rating", "response_text"]].reset_index(drop=True)


def says_prompt(text):
    return study_text.find_match(text.lower(), *_PROMPT) is not None


def embeddings(name, model_id, revision, texts):
    """The model's embedding of every text, from the cache in nlp/ when it holds these exact texts."""
    import sentence_transformers
    key = hashlib.sha256("\n".join([model_id, revision, sentence_transformers.__version__] + texts)
                         .encode("utf-8")).hexdigest()
    cache = os.path.join(NLP, f"label_from_meaning_embeddings_{name}.npy")
    keyfile = cache.replace(".npy", ".sha256")
    if os.path.exists(cache) and os.path.exists(keyfile) and open(keyfile).read().strip() == key:
        return np.load(cache)
    model = sentence_transformers.SentenceTransformer(model_id, revision=revision, device="cpu", local_files_only=True)
    E = model.encode(texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    np.save(cache, E)
    with open(keyfile, "w") as fh:
        fh.write(key)
    return E


def oof_scores(X, y, cols_meaning, cols_other, which, rng_seed, repeats=REPEATS):
    """Average out-of-fold P(AI) per participant over the repeated folds."""
    pred = np.zeros(len(y)); count = np.zeros(len(y))
    for rep in range(repeats):
        cv = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=rng_seed + rep)
        for tr, te in cv.split(X, y):
            if which == "other":
                pre = ColumnTransformer([("o", StandardScaler(), cols_other)])
            elif which == "meaning":
                pre = ColumnTransformer([("m", make_pipeline(StandardScaler(), PCA(N_COMPONENTS, random_state=0)),
                                          cols_meaning)])
            else:
                pre = ColumnTransformer([("m", make_pipeline(StandardScaler(), PCA(N_COMPONENTS, random_state=0)),
                                          cols_meaning), ("o", StandardScaler(), cols_other)])
            model = make_pipeline(pre, LogisticRegression(max_iter=2000))
            model.fit(X[tr], y[tr])
            pred[te] += model.predict_proba(X[te])[:, 1]; count[te] += 1
    return pred / count


def null_gain(M_fit, R, perm, other, y, auc_other, seed):
    """The gain for one null run: meaning's residuals on rating and length shuffled across participants."""
    X = np.hstack([M_fit + R[perm], other])
    cm, co = list(range(M_fit.shape[1])), [M_fit.shape[1], M_fit.shape[1] + 1]
    return roc_auc_score(y, oof_scores(X, y, cm, co, "both", seed)) - auc_other


def analyse(data, E, study, dim, explanations, model_name, role):
    sub = data[(data.study_pipeline == study) & (data.dimension == dim)]
    if explanations == WITHOUT:
        sub = sub[~sub["mentions_prompt"]]
    people = sub.groupby("id")
    ids = list(people.groups.keys())
    M = np.vstack([E[people.groups[i]].mean(axis=0) for i in ids])
    other = people[["rating", "log_words"]].mean().loc[ids].to_numpy()
    y = (people["label"].first().loc[ids] == "AI").to_numpy().astype(int)
    X = np.hstack([M, other])
    cm, co = list(range(M.shape[1])), [M.shape[1], M.shape[1] + 1]
    base_seed = SEED + 1000 * study + len(dim)
    p_other = oof_scores(X, y, cm, co, "other", base_seed)
    p_both = oof_scores(X, y, cm, co, "both", base_seed)
    p_mean = oof_scores(X, y, cm, co, "meaning", base_seed)
    preds = (("rating and length", p_other), ("meaning, rating and length", p_both), ("meaning only", p_mean))
    auc = {k: roc_auc_score(y, p) for k, p in preds}
    gain = auc["meaning, rating and length"] - auc["rating and length"]
    rng = np.random.default_rng(base_seed)
    boots = {k: [] for k in list(auc) + ["gain"]}
    for _ in range(BOOT):
        s = rng.integers(0, len(y), len(y))
        if len(set(y[s])) < 2:
            continue
        a = {k: roc_auc_score(y[s], p[s]) for k, p in preds}
        for k in a:
            boots[k].append(a[k])
        boots["gain"].append(a["meaning, rating and length"] - a["rating and length"])
    # Freedman-Lane null: keep what meaning shares with rating and length, shuffle the rest.
    Z = np.column_stack([np.ones(len(y)), other])
    B, *_ = np.linalg.lstsq(Z, M, rcond=None)
    M_fit = Z @ B
    R = M - M_fit
    perms = [rng.permutation(len(y)) for _ in range(PERMS)]
    null = np.array(Parallel(n_jobs=N_JOBS)(delayed(null_gain)(M_fit, R, perm, other, y, auc["rating and length"], base_seed)
                                            for perm in perms))
    rows = []
    for k in list(auc) + ["gain"]:
        val = gain if k == "gain" else auc[k]
        rows.append(dict(analysis_status=STATUS, model=model_name, model_role=role, explanations=explanations,
                         study_pipeline=study, study_paper=PAPER[study],
                         part="originals" if study in (1, 3) else "secondary works", measure=dim,
                         quantity="AUC" if k != "gain" else "AUC gain from adding meaning",
                         predictors=k if k != "gain" else "meaning, rating and length minus rating and length",
                         estimate=val, ci95_low=np.percentile(boots[k], 2.5), ci95_high=np.percentile(boots[k], 97.5),
                         null=NULL if k == "gain" else "",
                         null_mean=null.mean() if k == "gain" else np.nan,
                         null_95th=np.percentile(null, 95) if k == "gain" else np.nan,
                         p_permutation=(1 + int((null >= gain).sum())) / (1 + PERMS) if k == "gain" else np.nan,
                         participants=len(y), participants_ai=int(y.sum()), explanations_n=len(sub)))
    print(f"{model_name} | {explanations} | Study {PAPER[study]} {dim}: AUC rating+length {auc['rating and length']:.3f}, "
          f"+meaning {auc['meaning, rating and length']:.3f}, meaning only {auc['meaning only']:.3f}, "
          f"gain {gain:+.3f} (null mean {null.mean():+.3f}, 95th {np.percentile(null, 95):+.3f})", flush=True)
    return rows


def main():
    os.makedirs(NLP, exist_ok=True); os.makedirs(TABLES, exist_ok=True)
    data = pd.concat([read_study(s) for s in (1, 2, 3, 4, 5)], ignore_index=True)
    data["log_words"] = np.log(data["response_text"].str.split().str.len().clip(lower=1))
    data["mentions_prompt"] = [says_prompt(t) for t in data["response_text"]]
    texts = data["response_text"].tolist()
    rows = []
    for name, model_id, revision, role in MODELS:
        E = embeddings(name, model_id, revision, texts)
        for explanations in ((ALL, WITHOUT) if role == "primary" else (ALL,)):
            for study in (1, 3, 2, 4, 5):
                for dim in sorted(data.loc[data.study_pipeline == study, "dimension"].unique()):
                    rows += analyse(data, E, study, dim, explanations, name, role)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(TABLES, "label_from_meaning.csv"), index=False)
    env = [("analysis_status", STATUS), ("python", platform.python_version()), ("components", N_COMPONENTS),
           ("folds", FOLDS), ("repeats", REPEATS), ("bootstrap", BOOT), ("null runs", PERMS), ("null", NULL),
           ("seed", SEED)]
    env += [(f"model {name}", f"{model_id} at {revision} ({role})") for name, model_id, revision, role in MODELS]
    for pkg in ("sentence-transformers", "transformers", "torch", "scikit-learn", "numpy", "pandas"):
        env.append((pkg, importlib.metadata.version(pkg)))
    pd.DataFrame(env, columns=["item", "value"]).to_csv(os.path.join(TABLES, "label_from_meaning_environment.csv"),
                                                        index=False)
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    files = [os.path.join(TABLES, "label_from_meaning.csv"), os.path.abspath(__file__),
             os.path.join(PIPELINE, "shared", "python", "study_text.py")] + \
            [os.path.join(PIPELINE, f"Study {s}", f"study{s}_long_with_text.csv") for s in (1, 2, 3, 4, 5)]
    pd.DataFrame([(run_id, os.path.relpath(f, HERE), sha256_file(f)) for f in files],
                 columns=["run_id", "file", "sha256"]).to_csv(os.path.join(TABLES, "label_from_meaning_run_manifest.csv"),
                                                              index=False)


if __name__ == "__main__":
    main()
