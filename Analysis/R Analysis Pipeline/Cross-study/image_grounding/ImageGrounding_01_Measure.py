#!/usr/bin/env python3
"""How closely does each written explanation describe the picture it explains?

Exploratory. Specified on 6 November 2026, after every registered result was known, at the lead
author's request for a measure of the explanations that uses no word list. It changes no
registered verdict.

CLIP is a network that OpenAI trained to match pictures with their captions. It turns a picture
and a piece of text into lists of numbers (embeddings) such that a caption lies close to the
picture it describes. Here each explanation is treated as a caption and compared with the
pictures of the study:

* grounding: the CLIP similarity (cosine) of the explanation to the picture it explains, minus its
  average similarity to the other nine artworks at the same edit level. It is above zero when the
  text describes its own picture more than pictures in general, so it removes what any text about
  any of these images shares.
* edit pull (secondary works only): the similarity to the picture shown (the Slight or Dramatic
  version) minus the similarity to that artwork's original. It is above zero when the text
  describes the edited picture more than the original it was made from. At None the two pictures
  are the same, so it is zero by construction and is not analysed.
* hit: whether, of the ten artworks at that edit level, the explanation's own picture is the one
  CLIP places closest to it (chance is 1 in 10).

The step is blind: it reads four kinds of column from each study's long data file (the
participant, the picture, the question and the text) and never the label, the conditions or the
rating; the analysis step joins those afterwards. Pictures are the 30 stimulus files of
``../image_check/stimuli/``, checked against their manifest, fed to CLIP as in the image check's
primary variant ("whole image": resized to 224 by 224 pixels without cropping). CLIP is
``openai/clip-vit-base-patch32`` at the revision the image check pins, read from the local
Hugging Face cache only. Text longer than CLIP's 77 tokens is cut at 77.

It stops unless every long data file has the checksum its study's registered run recorded and
every picture has the checksum of the stimulus manifest.

Run from this folder:  python3 ImageGrounding_01_Measure.py
Writes nlp/image_grounding_scores.csv (one row per explanation; left out of the public copy
because Study 1 labels participants by their participant numbers) and tables/ run records.
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
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402
from transformers import CLIPModel, CLIPProcessor  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PIPELINE = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir))
STIMULI = os.path.join(PIPELINE, "Cross-study", "image_check", "stimuli")
NLP = os.path.join(HERE, "nlp")
TABLES = os.path.join(HERE, "tables")
MODEL = "openai/clip-vit-base-patch32"
REVISION = "3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268"  # as pinned by ../image_check
SIZE = 224
STATUS = ("exploratory; specified on 6 November 2026, after every registered result was known; "
          "changes no registered verdict")
PAPER = {1: 1, 2: 3, 3: 2, 4: 4, 5: 5}
ARTWORKS = [f"{n}{k}" for n in range(1, 6) for k in ("Figure", "NonFigure")]
VERSION_OF_LEVEL = {"original": "original", "None": "original", "Slight": "slight", "Dramatic": "dramatic"}


def stop(message):
    raise SystemExit("ImageGrounding_01_Measure.py stopped: " + message)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def recorded_sha(study):
    path = os.path.join(PIPELINE, f"Study {study}", "tables", f"study{study}_quant_run_manifest.csv")
    with open(path, encoding="utf-8", newline="") as fh:
        hits = [r["sha256"] for r in csv.DictReader(fh) if r["file"] == f"study{study}_long_with_text.csv"]
    if len(hits) != 1:
        stop(f"Study {study}'s quant run manifest does not list its long data file once")
    return hits[0]


def read_study(study):
    """The explanations of one study: participant, artwork, edit level, question, text."""
    path = os.path.join(PIPELINE, f"Study {study}", f"study{study}_long_with_text.csv")
    if sha256_file(path) != recorded_sha(study):
        stop(f"study{study}_long_with_text.csv does not have the checksum its registered run recorded")
    header = pd.read_csv(path, nrows=0).columns
    if study == 1:
        cols = ["id", "stimulus_id", "dimension", "response_text"]
        d = pd.read_csv(path, usecols=cols, dtype=str, keep_default_na=False)
        num = d["stimulus_id"].str.extract(r"^(Figure|NonFigure)_(\d)$")
        d["artwork"] = num[1] + num[0]
        d["level"] = "original"
    elif study == 3:
        cols = ["id", "stimulus_id", "dimension", "response_text"]
        d = pd.read_csv(path, usecols=cols, dtype=str, keep_default_na=False)
        d["artwork"] = d["stimulus_id"]
        d["level"] = "original"
    else:
        cols = ["id", "work_id", "dimension", "response_text"]
        missing = [c for c in cols if c not in header]
        if missing:
            stop(f"Study {study}: no column {missing}")
        d = pd.read_csv(path, usecols=cols, dtype=str, keep_default_na=False)
        parts = d["work_id"].str.extract(r"^(\d(?:Figure|NonFigure))_(None|Slight|Dramatic)$")
        d["artwork"], d["level"] = parts[0], parts[1]
    if d["artwork"].isna().any() or not set(d["artwork"]) <= set(ARTWORKS):
        stop(f"Study {study}: a picture could not be matched to a stimulus file")
    d = d[d["response_text"].str.contains(r"[A-Za-z]", regex=True)].copy()
    d["study_pipeline"] = study
    d["study_paper"] = PAPER[study]
    return d[["study_pipeline", "study_paper", "id", "artwork", "level", "dimension", "response_text"]]


def load_pictures():
    manifest = pd.read_csv(os.path.join(STIMULI, "stimuli_manifest.csv"), dtype=str, keep_default_na=False)
    pictures = {}
    for _, r in manifest.iterrows():
        path = os.path.join(STIMULI, r["file"])
        if not os.path.isfile(path) or sha256_file(path) != r["file_sha256"]:
            stop(f"stimulus {r['file']} is missing or differs from the manifest")
        version = r["version"].lower()
        pictures[(r["artwork"], version)] = Image.open(path).convert("RGB")
    for a in ARTWORKS:
        for v in ("original", "slight", "dramatic"):
            if (a, v) not in pictures:
                stop(f"no stimulus file for {a} {v}")
    return pictures


@torch.inference_mode()
def main():
    torch.manual_seed(0)
    torch.set_num_threads(8)
    model = CLIPModel.from_pretrained(MODEL, revision=REVISION, local_files_only=True).eval()
    processor = CLIPProcessor.from_pretrained(MODEL, revision=REVISION, local_files_only=True)

    pictures = load_pictures()
    keys = [(a, v) for a in ARTWORKS for v in ("original", "slight", "dramatic")]
    pixel = processor(images=[pictures[k].resize((SIZE, SIZE), resample=Image.Resampling.BICUBIC) for k in keys],
                      do_resize=False, do_center_crop=False, return_tensors="pt")["pixel_values"]
    img = model.get_image_features(pixel_values=pixel).to(torch.float64)
    img = (img / img.norm(dim=1, keepdim=True)).numpy()
    IMG = {k: img[i] for i, k in enumerate(keys)}

    data = pd.concat([read_study(s) for s in (1, 2, 3, 4, 5)], ignore_index=True)
    texts = data["response_text"].tolist()
    vecs = []
    for start in range(0, len(texts), 256):
        tok = processor.tokenizer(texts[start:start + 256], padding=True, truncation=True, max_length=77,
                                  return_tensors="pt")
        t = model.get_text_features(**tok).to(torch.float64)
        vecs.append((t / t.norm(dim=1, keepdim=True)).numpy())
    T = np.vstack(vecs)

    grounding, edit_pull, hit, own = [], [], [], []
    for i, r in enumerate(data.itertuples(index=False)):
        version = VERSION_OF_LEVEL[r.level]
        sims = {a: float(T[i] @ IMG[(a, version)]) for a in ARTWORKS}
        s_own = sims[r.artwork]
        others = [sims[a] for a in ARTWORKS if a != r.artwork]
        own.append(s_own)
        grounding.append(s_own - float(np.mean(others)))
        hit.append(int(max(sims, key=sims.get) == r.artwork))
        edit_pull.append(s_own - float(T[i] @ IMG[(r.artwork, "original")]) if version != "original" else np.nan)
    data["similarity_own"] = own
    data["grounding"] = grounding
    data["edit_pull"] = edit_pull
    data["hit"] = hit
    data["n_tokens_kept"] = [min(len(processor.tokenizer(t)["input_ids"]), 77) for t in texts]
    data = data.drop(columns=["response_text"])

    os.makedirs(NLP, exist_ok=True)
    os.makedirs(TABLES, exist_ok=True)
    out = os.path.join(NLP, "image_grounding_scores.csv")
    data.to_csv(out, index=False)

    env = [("analysis_status", STATUS), ("python", platform.python_version()), ("platform", platform.platform()),
           ("model", MODEL), ("model_revision", REVISION), ("image_input", "whole image, 224 x 224, no crop"),
           ("text_truncation", "77 CLIP tokens")]
    for pkg in ("torch", "transformers", "numpy", "pandas", "pillow"):
        env.append((pkg, importlib.metadata.version(pkg)))
    pd.DataFrame(env, columns=["item", "value"]).to_csv(os.path.join(TABLES, "image_grounding_measure_environment.csv"),
                                                        index=False)
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rows = [(run_id, os.path.relpath(out, HERE), sha256_file(out))]
    for s in (1, 2, 3, 4, 5):
        p = os.path.join(PIPELINE, f"Study {s}", f"study{s}_long_with_text.csv")
        rows.append((run_id, os.path.relpath(p, HERE), sha256_file(p)))
    rows.append((run_id, os.path.relpath(os.path.abspath(__file__), HERE), sha256_file(os.path.abspath(__file__))))
    pd.DataFrame(rows, columns=["run_id", "file", "sha256"]).to_csv(
        os.path.join(TABLES, "image_grounding_measure_run_manifest.csv"), index=False)
    print(f"scored {len(data)} explanations; overall hit rate {np.mean(hit):.3f} (chance 0.100)")


if __name__ == "__main__":
    sys.exit(main())
