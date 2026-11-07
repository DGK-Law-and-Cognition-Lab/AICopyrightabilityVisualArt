#!/usr/bin/env python3
"""The most typical written explanations of each group, chosen by a fixed rule, for quoting.

Exploratory and descriptive. Specified on 6 November 2026, after every registered result was
known, at the lead author's request to quote participants' explanations in the paper without the
authors choosing which ones. It tests nothing and changes no registered verdict.

The rule, fixed before any explanation was read:

* Groups. For each Part, question and label: originals (paper Studies 1 and 2 pooled), effort and
  creativity; secondary works (paper Studies 3 to 5 pooled), creativity, at the Slight and
  Dramatic edits only (at None the picture is the original shown again, and explanations mostly
  say that nothing changed). The explanations are those every other analysis uses.
* Typical. Each explanation is placed by its sentence embedding (all-mpnet-base-v2, the
  pipeline's model, read from the label-from-meaning step's cache), so that explanations that
  mean the same thing lie close together. The group's center is the average of its participants'
  average embeddings, so each participant counts once. An explanation is the more typical the
  closer it lies to that center (cosine similarity).
* Length. Only explanations at least as long as the group's median, in words, are eligible, so a
  quote is not a one-word reply.
* One per person. The two most typical eligible explanations of a group come from two different
  participants.

The text is quoted exactly as written. The table holds no participant code.

Run from this folder:  python3 TypicalExplanations.py
Writes tables/typical_explanations.csv and tables/typical_explanations_run_manifest.csv.
"""

import datetime
import hashlib
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CROSS = os.path.dirname(HERE)
PIPELINE = os.path.dirname(CROSS)
TABLES = os.path.join(HERE, "tables")
sys.path.insert(0, os.path.join(CROSS, "label_from_meaning"))
import LabelFromMeaning as L  # noqa: E402  (reads the long files with their checksum checks, and the embedding cache)

STATUS = ("exploratory and descriptive; specified on 6 November 2026, after every registered result was known; "
          "tests nothing")
PART = {1: "originals", 3: "originals", 2: "secondary works", 4: "secondary works", 5: "secondary works"}
WORK_COL = {1: "stimulus_id", 2: "work_id", 3: "stimulus_id", 4: "work_id", 5: "work_id"}
GROUPS = [("originals", "effort"), ("originals", "creativity"), ("secondary works", "creativity")]
PER_GROUP = 2


def edit_levels(study):
    """The edit level of every explanation the analyses use, in the order read_study returns them."""
    path = os.path.join(PIPELINE, f"Study {study}", f"study{study}_long_with_text.csv")
    d = pd.read_csv(path, dtype={"id": str}, keep_default_na=False, low_memory=False)
    if "k_points" in d:
        d = d[d["k_points"].astype(str) == "5"]
    d = d[(d["rating"].astype(str) != "") & d["response_text"].str.contains(r"[A-Za-z]", regex=True)]
    if PART[study] == "originals":
        return ["original"] * len(d)
    return d[WORK_COL[study]].str.rsplit("_", n=1).str[-1].tolist()


def main():
    os.makedirs(TABLES, exist_ok=True)
    parts = []
    for s in (1, 2, 3, 4, 5):
        d = L.read_study(s)
        d["edit_level"] = edit_levels(s)
        parts.append(d)
    data = pd.concat(parts, ignore_index=True)
    name, model_id, revision, _ = L.MODELS[0]
    E = L.embeddings(name, model_id, revision, data["response_text"].tolist())
    data["study_paper"] = data["study_pipeline"].map(L.PAPER)
    data["part"] = data["study_pipeline"].map(PART)
    data["words"] = data["response_text"].str.split().str.len()
    rows = []
    for part, question in GROUPS:
        for label in ("Human", "AI"):
            g = data[(data.part == part) & (data.dimension == question) & (data.label == label)
                     & (data.edit_level.isin(["original", "Slight", "Dramatic"]))]
            people = g.groupby("id").groups
            centre = np.mean([E[idx].mean(axis=0) for idx in people.values()], axis=0)
            centre = centre / np.linalg.norm(centre)
            sim = E[g.index] @ centre  # the embeddings are of unit length
            ranked = g.assign(similarity=sim)
            ranked = ranked[ranked.words >= ranked.words.median()].sort_values("similarity", ascending=False)
            chosen = ranked.drop_duplicates("id").head(PER_GROUP)
            for rank, (_, r) in enumerate(chosen.iterrows(), start=1):
                rows.append(dict(analysis_status=STATUS, part=part, question=question, label=label, rank=rank,
                                 study_paper=int(r.study_paper), edit_level=r.edit_level, rating=r.rating,
                                 words=int(r.words), similarity=round(float(r.similarity), 4),
                                 group_explanations=len(g), group_participants=len(people),
                                 group_median_words=float(g.words.median()), text=r.response_text.strip()))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(TABLES, "typical_explanations.csv"), index=False)
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    files = [os.path.join(TABLES, "typical_explanations.csv"), os.path.abspath(__file__),
             os.path.join(CROSS, "label_from_meaning", "LabelFromMeaning.py")] + \
            [os.path.join(PIPELINE, f"Study {s}", f"study{s}_long_with_text.csv") for s in (1, 2, 3, 4, 5)]
    pd.DataFrame([(run_id, os.path.relpath(f, HERE), L.sha256_file(f)) for f in files],
                 columns=["run_id", "file", "sha256"]).to_csv(
        os.path.join(TABLES, "typical_explanations_run_manifest.csv"), index=False)
    print(f"wrote {len(out)} explanations to tables/typical_explanations.csv")


if __name__ == "__main__":
    main()
