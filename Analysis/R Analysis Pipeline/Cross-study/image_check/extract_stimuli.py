"""Extract the 30 stimulus images from the printout of the Study 5 survey.

This is a stimulus check, specified on 10 October 2026, after every
registered result was known. No registration names it, and it changes no
registered verdict.

The script runs once. It reads the printout of the Study 5 survey that Chrome
made on 6 October 2025 (`Stimuli/Qualtrics Survey Software.pdf` under the
project root), takes out the images embedded in it with pdfimages, a tool of
poppler, a set of command-line programs for PDF files, without re-encoding
them (re-encoding would compress the pixels again and change them), and names
each stimulus image by its artwork and version (original, Slight or Dramatic).
The survey files are the authority for which graphic is which. Qualtrics, the
survey platform, stores each picture as a graphic with an ID of the form
IM_xxxx, and the survey file (`.qsf`, a text file in JSON, a standard format
for nested lists and named fields) says which graphic each question displays.

Three signals must agree before an image gets a name:

1. Printout text and survey order. The printout prints the name of every
   block of questions, and the words FIRST WORK and SECOND WORK above each
   picture. Laying the survey's displays end to end in the printout's block
   order, and the printout's images end to end in page order, pairs them one
   to one. Each image must sit on a page between the page that prints its own
   block name or label and the page that prints the next one.
2. The sharing pattern. Where the survey shows one graphic in several
   questions, the printout must show one embedded image in the same places,
   and where the survey shows different graphics, different images.
3. Pixel size. Where the survey's page code (the HTML, the markup language
   of web pages, that a question displays) states a graphic's size, it must
   equal the embedded image's width and height in pixels.

A fourth signal is recorded and never overrides the others: whether a file in
`Stimuli/Images`, the project's folder of local image files, has the same
pixels. That folder is optional; without it, the cross-check is skipped and
recorded as skipped.

It needs these inputs, found at these places unless an environment variable
(a named setting the shell passes to a program) names another:

    the printout        Stimuli/Qualtrics Survey Software.pdf under the project root
    the draft survey    Stimuli/Draft_-_AI_Copyright_-_Study_5.qsf under the project root
    the final surveys   Exported Studies/Final_-_AI_Copyright_-_Study_N.qsf, N = 1 to 5,
                        under the pipeline folder
    the local images    Stimuli/Images under the project root (optional)

It writes `stimuli/` beside this file: the 30 images, `stimuli_manifest.csv`
(one row per image), `extraction_checks.csv` (one row per check) and, last,
`extraction_run_manifest.csv`, which gives the size and SHA-256 checksum (a
64-character fingerprint of a file's exact bytes) of every input read and
every file written, with the versions of the tools used. Everything is first
written to a staging folder beside `stimuli/` and moved into `stimuli/` only
after every check has passed, so a run that stops leaves `stimuli/` as it was.

Paths are found from this file's own folder. These environment variables can
name other places:

    IMAGE_CHECK_DIR           this folder
    PIPELINE_DIR              the analysis pipeline folder, two levels up
    IMAGE_CHECK_PROJECT_ROOT  the project root, the folder that holds Analysis and Stimuli
    IMAGE_CHECK_PRINTOUT      the printout
    IMAGE_CHECK_DRAFT_SURVEY  the draft Study 5 survey file
    IMAGE_CHECK_SURVEY_DIR    the folder of the five final survey files
    IMAGE_CHECK_LOCAL_IMAGES  the folder of local image files used for the cross-check

Every path it prints or writes is relative to the project root. A path outside
the project root is written relative to the folder an environment variable
named, with that folder's label in angle brackets, for example
`<local images>/Figures/1_figure_original.webp`.
"""

import hashlib
import html
import importlib.metadata
import io
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from html.parser import HTMLParser

import numpy as np
import pandas as pd
from PIL import Image

STATUS = ("stimulus check; specified on 10 October 2026, after every registered result was known; "
          "no registration names it; changes no registered verdict; the ratings comparison is description only")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = os.path.abspath(os.environ.get("IMAGE_CHECK_DIR") or os.path.dirname(os.path.abspath(__file__)))
PIPELINE_DIR = os.path.abspath(os.environ.get("PIPELINE_DIR") or os.path.join(HERE, os.pardir, os.pardir))


def find_project_root():
    # The project root holds Analysis, and Analysis holds the pipeline folder.
    # In a copy laid out differently, the pipeline folder serves as the root.
    named = os.environ.get("IMAGE_CHECK_PROJECT_ROOT")
    if named:
        return os.path.abspath(named)
    analysis = os.path.dirname(PIPELINE_DIR)
    if os.path.basename(analysis) == "Analysis":
        return os.path.dirname(analysis)
    return PIPELINE_DIR


PROJECT_ROOT = find_project_root()
PRINTOUT = os.path.abspath(os.environ.get("IMAGE_CHECK_PRINTOUT")
                           or os.path.join(PROJECT_ROOT, "Stimuli", "Qualtrics Survey Software.pdf"))
DRAFT_SURVEY = os.path.abspath(os.environ.get("IMAGE_CHECK_DRAFT_SURVEY")
                               or os.path.join(PROJECT_ROOT, "Stimuli", "Draft_-_AI_Copyright_-_Study_5.qsf"))
SURVEY_DIR = os.path.abspath(os.environ.get("IMAGE_CHECK_SURVEY_DIR")
                             or os.path.join(PIPELINE_DIR, "Exported Studies"))
LOCAL_IMAGES = os.path.abspath(os.environ.get("IMAGE_CHECK_LOCAL_IMAGES")
                               or os.path.join(PROJECT_ROOT, "Stimuli", "Images"))
OUT_DIR = os.path.join(HERE, "stimuli")
STAGING_DIR = os.path.join(HERE, ".stimuli_staging")

# Labels for the folders an environment variable can place outside the project root.
LABELLED_FOLDERS = [(LOCAL_IMAGES, "<local images>"), (SURVEY_DIR, "<survey folder>"),
                    (os.path.dirname(PRINTOUT), "<printout folder>"),
                    (os.path.dirname(DRAFT_SURVEY), "<draft survey folder>"),
                    (HERE, "<image_check>"), (PIPELINE_DIR, "<pipeline>")]


def show(path):
    """A path for printing and writing: relative to the project root, or else to a labelled folder."""
    path = os.path.abspath(path)
    for base, label in [(PROJECT_ROOT, None)] + LABELLED_FOLDERS:
        rel = os.path.relpath(path, base)
        if not rel.startswith(os.pardir):
            if label is None:
                return rel
            return label if rel == os.curdir else os.path.join(label, rel)
    return os.path.join("<outside the project>", os.path.basename(path))


def stop(message):
    # The script ends here; the staging folder is removed and stimuli/ is left as it was.
    shutil.rmtree(STAGING_DIR, ignore_errors=True)
    sys.exit("STOPPED: " + message)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rgb_pixels(path_or_bytes):
    # Pillow decodes the file to 8-bit red, green and blue values.
    source = io.BytesIO(path_or_bytes) if isinstance(path_or_bytes, bytes) else path_or_bytes
    with Image.open(source) as image:
        return np.asarray(image.convert("RGB"))


def pixels_sha256(array):
    # The checksum covers the width, the height and every decoded value.
    header = ("%dx%dx3;" % (array.shape[1], array.shape[0])).encode()
    return sha256_bytes(header + np.ascontiguousarray(array, dtype=np.uint8).tobytes())


CHECKS = []


def check(name, expected, observed, required=True):
    # Each check is recorded; a required check that fails stops the script.
    # A row with no expected value records an observation and passes nothing.
    passed = "recorded" if expected is None else expected == observed
    CHECKS.append(dict(check=name, expected="" if expected is None else str(expected), observed=str(observed),
                       pass_=passed, required=required))
    if required and passed is False:
        stop("%s. Expected %s, observed %s." % (name, expected, observed))
    return passed


# ---------------------------------------------------------------------------
# The tools and the inputs
# ---------------------------------------------------------------------------
INSTALL_HINT = ("poppler is needed for this one-time step. On macOS: brew install poppler. "
                "On Debian or Ubuntu Linux: sudo apt-get install poppler-utils.")
for tool in ("pdfimages", "pdftotext"):
    if shutil.which(tool) is None:
        stop("%s was not found. %s" % (tool, INSTALL_HINT))
POPPLER_VERSION = subprocess.run(["pdfimages", "-v"], capture_output=True, text=True).stderr.splitlines()[0].strip()

SURVEY_FILES = {"Study %d" % n: os.path.join(SURVEY_DIR, "Final_-_AI_Copyright_-_Study_%d.qsf" % n)
                for n in range(1, 6)}
SURVEY_FILES["Study 5 draft"] = DRAFT_SURVEY
for path in [PRINTOUT] + list(SURVEY_FILES.values()):
    if not os.path.exists(path):
        stop("%s was not found. Set the environment variable named in this file's opening comment "
             "to its place." % show(path))
HAS_LOCAL = os.path.isdir(LOCAL_IMAGES)

print("Printout:", show(PRINTOUT))
print("Surveys:", ", ".join(show(p) for p in SURVEY_FILES.values()))
print("Local images:", show(LOCAL_IMAGES) if HAS_LOCAL else
      "the local image folder (%s; IMAGE_CHECK_LOCAL_IMAGES can name another) was not found; "
      "the local cross-check is skipped" % show(LOCAL_IMAGES))
print("Tool:", POPPLER_VERSION)
print()

# Every input read is listed, with its size and checksum, in the run manifest written last.
RUN_INPUTS = [("printout", PRINTOUT)] + [("survey file, %s" % name, path) for name, path in SURVEY_FILES.items()]
RUN_LOCAL = []

# Each input is compared with the checksum that the run which made the deposited images recorded for it.
# A difference is recorded and printed; it does not stop the script.
DEPOSITED_RUN = os.path.join(OUT_DIR, "extraction_run_manifest.csv")
if os.path.exists(DEPOSITED_RUN):
    deposited = pd.read_csv(DEPOSITED_RUN, dtype=str, keep_default_na=False)
    recorded = dict(zip(deposited.loc[deposited["role"] == "input", "what"],
                        deposited.loc[deposited["role"] == "input", "sha256"]))
    for what, path in RUN_INPUTS:
        if what in recorded:
            same = check("The %s has the checksum the deposited run recorded" % what, recorded[what],
                         sha256_file(path), required=False)
            if not same:
                print("WARNING: the %s differs from the one the deposited images were made from." % what)
else:
    check("Checksums of the inputs compared with a deposited run", None, "no deposited run manifest",
          required=False)

# ---------------------------------------------------------------------------
# 1. The surveys
# ---------------------------------------------------------------------------
# A stimulus block is named Image<k>_Figure or Image<k>_Nonfigure, with None,
# Min or Max after it for the second work at that level. With no level, the
# block shows the artwork alone. The item names call Slight "Min" and
# Dramatic "Max".
BLOCK_NAME = re.compile(r"^Image([1-5])_(Figure|Nonfigure)(None|Min|Max)?$")
RATING_TAG = re.compile(r"^([1-5])(Figure|NonFigure)(None|Min|Max)(Trans|Ess|Creat)$")
LEVEL_OF_SUFFIX = {None: "original", "None": "None", "Min": "Slight", "Max": "Dramatic"}
ARTWORKS = ["%dFigure" % k for k in range(1, 6)] + ["%dNonFigure" % k for k in range(1, 6)]
VERSIONS = ["original", "Slight", "Dramatic"]


class ImageTags(HTMLParser):
    """Collects each <img> tag's graphic ID and the size its style states."""

    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag != "img":
            return
        attrs = dict(attrs)
        found = re.search(r"IM=(IM_[A-Za-z0-9]+)", attrs.get("src") or "")
        style = attrs.get("style") or ""
        width = re.search(r"width:\s*(\d+)px", style)
        height = re.search(r"height:\s*(\d+)px", style)
        self.images.append(dict(graphic=found.group(1) if found else None,
                                width=int(width.group(1)) if width else None,
                                height=int(height.group(1)) if height else None))


def images_in(text):
    parser = ImageTags()
    parser.feed(text or "")
    return parser.images


def plain_text(text):
    # Tags are removed, entities are decoded and runs of white space become one space.
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def read_survey(path):
    with open(path, encoding="utf-8") as handle:
        survey = json.load(handle)
    elements = survey["SurveyElements"]
    questions = {e["Payload"]["QuestionID"]: e["Payload"] for e in elements if e["Element"] == "SQ"}
    payload = [e for e in elements if e["Element"] == "BL"][0]["Payload"]
    blocks = [b for b in (payload.values() if isinstance(payload, dict) else payload) if isinstance(b, dict)]
    shown = []
    for block in blocks:
        if block.get("Type") == "Trash":
            continue
        entries = []
        for element in block.get("BlockElements", []):
            if element.get("Type") != "Question":
                continue
            question = questions[element["QuestionID"]]
            entries.append(dict(
                qid=element["QuestionID"],
                tag=question.get("DataExportTag"),
                type=question.get("QuestionType"),
                text=plain_text(question.get("QuestionText")),
                images=images_in(question.get("QuestionText")),
                unsafe_images=images_in(question.get("QuestionText_Unsafe")),
                has_unsafe="QuestionText_Unsafe" in question))
        shown.append(dict(name=block.get("Description"), questions=entries))
    every_graphic = set(re.findall(r"IM_[A-Za-z0-9]{10,}", json.dumps(survey)))
    return dict(blocks=shown, every_graphic=every_graphic, entry=survey["SurveyEntry"])


SURVEYS = {name: read_survey(path) for name, path in SURVEY_FILES.items()}


def stimulus_blocks(survey):
    """The stimulus blocks of a survey, keyed by block name."""
    found = {}
    for block in survey["blocks"]:
        match = BLOCK_NAME.match(block["name"] or "")
        if not match:
            continue
        k, kind, suffix = match.groups()
        artwork = "%s%s" % (k, "Figure" if kind == "Figure" else "NonFigure")
        displays = []
        for q in block["questions"]:
            for image in q["images"]:
                role = ("FIRST" if "FIRST WORK" in q["text"] else
                        "SECOND" if "SECOND WORK" in q["text"] else "ALONE")
                displays.append(dict(qid=q["qid"], tag=q["tag"], role=role, **image,
                                     unsafe=[u["graphic"] for u in q["unsafe_images"]],
                                     has_unsafe=q["has_unsafe"]))
        ratings = [q["tag"] for q in block["questions"] if q["type"] == "MC" and RATING_TAG.match(q["tag"] or "")]
        if block["name"] in found:
            stop("Block %s appears twice in one survey." % block["name"])
        found[block["name"]] = dict(artwork=artwork, image_kind="Figure" if kind == "Figure" else "NonFigure",
                                    level=LEVEL_OF_SUFFIX[suffix], displays=displays, ratings=ratings)
    return found


AUTHORITY = "Study 5"
BLOCKS = stimulus_blocks(SURVEYS[AUTHORITY])

# Every survey file names the same 31 graphics; 30 are displayed by questions
# and one is the logo in the survey's look-and-feel settings.
for name, survey in SURVEYS.items():
    check("%s survey file names the same graphics as the final Study 5 survey" % name,
          sorted(SURVEYS[AUTHORITY]["every_graphic"]), sorted(survey["every_graphic"]))
check("Distinct graphics named in the final Study 5 survey", 31, len(SURVEYS[AUTHORITY]["every_graphic"]))

# The structure of the final Study 5 survey.
check("Stimulus blocks in the final Study 5 survey", 40, len(BLOCKS))
ORIGINAL_GRAPHIC = {}
for name, block in BLOCKS.items():
    if block["level"] == "original":
        check("%s displays one graphic, alone" % name, ["ALONE"], [d["role"] for d in block["displays"]])
        ORIGINAL_GRAPHIC[block["artwork"]] = block["displays"][0]["graphic"]
VERSION_GRAPHIC = {}
for name, block in BLOCKS.items():
    if block["level"] == "original":
        continue
    roles = [d["role"] for d in block["displays"]]
    check("%s displays a first work, then a second work" % name, ["FIRST", "SECOND"], roles)
    first, second = block["displays"]
    check("%s first work is the artwork's original graphic" % name, ORIGINAL_GRAPHIC[block["artwork"]],
          first["graphic"])
    level_tag = {"None": "None", "Slight": "Min", "Dramatic": "Max"}[block["level"]]
    expected_ratings = ["%s%s%s" % (block["artwork"], level_tag, d) for d in ("Trans", "Ess", "Creat")]
    check("%s asks the three rating questions about its second work" % name, expected_ratings, block["ratings"])
    if block["level"] == "None":
        check("%s second work displays the original graphic" % name, ORIGINAL_GRAPHIC[block["artwork"]],
              second["graphic"])
    else:
        VERSION_GRAPHIC[(block["artwork"], block["level"])] = second["graphic"]
edited = list(VERSION_GRAPHIC.values())
check("Distinct Slight and Dramatic graphics, none of them an original", 20,
      len(set(edited) - set(ORIGINAL_GRAPHIC.values())))
check("Distinct original graphics", 10, len(set(ORIGINAL_GRAPHIC.values())))

# The other surveys display the same graphics in the same questions.
def block_signature(blocks):
    return {name: ([(d["role"], d["graphic"], d["width"], d["height"]) for d in b["displays"]], b["ratings"])
            for name, b in blocks.items()}


for name in ("Study 2", "Study 4", "Study 5 draft"):
    check("%s survey displays the same graphics in every stimulus block as the final Study 5 survey" % name,
          True, block_signature(stimulus_blocks(SURVEYS[name])) == block_signature(BLOCKS))
for name in ("Study 1", "Study 3"):
    shown = stimulus_blocks(SURVEYS[name])
    check("%s survey displays the ten originals, each alone in its own block" % name,
          sorted(ORIGINAL_GRAPHIC.items()),
          sorted((b["artwork"], b["displays"][0]["graphic"]) for b in shown.values()
                 if b["level"] == "original" and len(b["displays"]) == 1))
    check("%s survey displays no other stimulus graphic" % name, 10,
          sum(len(b["displays"]) for b in shown.values()))

# In the three derivative surveys, the stored copy of the page code that
# Qualtrics keeps beside the displayed text (QuestionText_Unsafe) names the
# Slight graphic in each None second-work question. The displayed text names
# the original. The printout settles which one is shown (section 3).
STALE = {}
for name in ("Study 2", "Study 4", "Study 5", "Study 5 draft"):
    count = 0
    for block in stimulus_blocks(SURVEYS[name]).values():
        if block["level"] != "None":
            continue
        second = block["displays"][1]
        if second["unsafe"] == [VERSION_GRAPHIC[(block["artwork"], "Slight")]]:
            count += 1
            STALE[(block["artwork"])] = VERSION_GRAPHIC[(block["artwork"], "Slight")]
    check("%s: None second-work questions whose stored unsafe copy names the Slight graphic" % name,
          10, count, required=False)

# ---------------------------------------------------------------------------
# 2. The printout's text
# ---------------------------------------------------------------------------
pages_text = subprocess.run(["pdftotext", "-layout", PRINTOUT, "-"], capture_output=True, text=True,
                            check=True).stdout.split("\f")
if pages_text and not pages_text[-1].strip():
    pages_text = pages_text[:-1]
info = subprocess.run(["pdfinfo", PRINTOUT], capture_output=True, text=True).stdout if shutil.which("pdfinfo") else ""
page_count = int(re.search(r"Pages:\s+(\d+)", info).group(1)) if "Pages:" in info else len(pages_text)
check("Pages of text read from the printout", page_count, len(pages_text))

# Which survey the printout shows. The displayed wording of the draft and the
# final Study 5 surveys differs in three questions: QID163 and QID164 pipe in
# ${e://Field/ArtistHr} in the draft and ${e://Field/ArtistHr_Source} in the
# final, and QID17 reads "produce" in the draft and "produced" in the final.
# Each phrase must be in exactly one survey.
ALL_BLOCK_NAMES = {b["name"] for b in SURVEYS["Study 5 draft"]["blocks"]} | {b["name"] for b in SURVEYS[AUTHORITY]["blocks"]}
MARKERS = [("${e://Field/ArtistHr} working", "${e://Field/ArtistHr_Source} working"),
           ("${e://Field/ArtistHr} developing", "${e://Field/ArtistHr_Source} developing"),
           ("He decided to produce a secondary digital artwork", "He decided to produced a secondary digital artwork")]
printout_plain = re.sub(r"\s+", " ", " ".join(pages_text))
survey_plain = {name: " ".join(q["text"] for b in SURVEYS[name]["blocks"] for q in b["questions"])
                for name in ("Study 5", "Study 5 draft")}


def displayed_wording(name):
    # Each displayed question's text, with any space before a punctuation mark removed.
    return {q["qid"]: re.sub(r"\s+([.,;:!?])", r"\1", q["text"])
            for b in SURVEYS[name]["blocks"] for q in b["questions"]}


draft_wording, final_wording = displayed_wording("Study 5 draft"), displayed_wording("Study 5")
check("Displayed questions whose wording differs between the draft and the final Study 5 survey",
      ["QID163", "QID164", "QID17"],
      sorted(q for q in set(draft_wording) | set(final_wording) if draft_wording.get(q) != final_wording.get(q)))
matches_draft = 0
for draft_phrase, final_phrase in MARKERS:
    check("Phrase '%s' is in the draft and not the final survey" % draft_phrase, (True, False),
          (draft_phrase in survey_plain["Study 5 draft"], draft_phrase in survey_plain["Study 5"]))
    check("Phrase '%s' is in the final and not the draft survey" % final_phrase, (True, False),
          (final_phrase in survey_plain["Study 5"], final_phrase in survey_plain["Study 5 draft"]))
    matches_draft += (draft_phrase in printout_plain) and (final_phrase not in printout_plain)
check("Wording differences at which the printout reads as the draft Study 5 survey", len(MARKERS), matches_draft,
      required=False)

# The events of the printout in reading order: each printed block name, and
# each FIRST WORK or SECOND WORK label.
events = []
for page_number, text in enumerate(pages_text, start=1):
    for line in text.splitlines():
        line = line.strip()
        if line in ALL_BLOCK_NAMES:
            events.append(dict(page=page_number, kind="block", text=line))
        elif line in ("FIRST WORK", "SECOND WORK"):
            events.append(dict(page=page_number, kind="label", text=line))
stimulus_events = [e for e in events if e["kind"] == "block" and BLOCK_NAME.match(e["text"])]
check("Stimulus block names printed, each once", sorted(BLOCKS), sorted(e["text"] for e in stimulus_events))
check("FIRST WORK and SECOND WORK labels printed", 60, sum(e["kind"] == "label" for e in events))

# The survey's displays laid end to end in the printout's block order. Each
# display is anchored to the printed event above it: its label, or for an
# artwork shown alone, its block name.
slots = []
label_events = iter([i for i, e in enumerate(events) if e["kind"] == "label"])
for index, event in enumerate(events):
    if event["kind"] != "block" or event["text"] not in BLOCKS:
        continue
    block = BLOCKS[event["text"]]
    for display in block["displays"]:
        if display["role"] == "ALONE":
            anchor = index
        else:
            anchor = next(label_events)
            check("Label printed for %s %s work" % (event["text"], display["role"].lower()),
                  "%s WORK" % display["role"], events[anchor]["text"])
            check("Label for %s %s work printed after its block name and before any other block name"
                  % (event["text"], display["role"].lower()), True,
                  anchor > index and not any(e["kind"] == "block" for e in events[index + 1:anchor]))
        upper = events[anchor + 1]["page"] if anchor + 1 < len(events) else len(pages_text)
        slots.append(dict(block=event["text"], artwork=block["artwork"], image_kind=block["image_kind"],
                          level=block["level"], role=display["role"], qid=display["qid"], tag=display["tag"],
                          graphic=display["graphic"], stated_width=display["width"],
                          stated_height=display["height"], lowest_page=events[anchor]["page"],
                          highest_page=upper))
check("Displays of stimulus graphics in the survey, in printout order", 70, len(slots))

# ---------------------------------------------------------------------------
# 3. The printout's images
# ---------------------------------------------------------------------------
listing = subprocess.run(["pdfimages", "-list", PRINTOUT], capture_output=True, text=True, check=True).stdout
images = []
for line in listing.splitlines()[2:]:
    parts = line.split()
    if len(parts) < 12 or parts[2] != "image":
        continue
    images.append(dict(page=int(parts[0]), num=int(parts[1]), width=int(parts[3]), height=int(parts[4]),
                       encoding=parts[8], object_id=int(parts[10])))
first_stimulus_page = stimulus_events[0]["page"]
outside = [i for i in images if i["page"] < first_stimulus_page]
inside = [i for i in images if i["page"] >= first_stimulus_page]
check("Images printed before the first stimulus block, on the consent and instruction pages, left out", 2,
      len(outside), required=False)
check("Images printed from the first stimulus block on", len(slots), len(inside))

# Signal 1: each image lies on a page between its anchor and the next printed event.
for slot, image in zip(slots, inside):
    slot.update(page=image["page"], num=image["num"], object_id=image["object_id"], pixel_width=image["width"],
                pixel_height=image["height"], encoding=image["encoding"])
    check("%s %s work printed between its label and the next printed event"
          % (slot["block"], slot["role"].lower()), True,
          slot["lowest_page"] <= slot["page"] <= slot["highest_page"])

# Signal 2: one survey graphic, one embedded image, in both directions.
graphic_to_objects, object_to_graphics = {}, {}
for slot in slots:
    graphic_to_objects.setdefault(slot["graphic"], set()).add(slot["object_id"])
    object_to_graphics.setdefault(slot["object_id"], set()).add(slot["graphic"])
check("Survey graphics shown by more than one embedded image", [],
      sorted(g for g, objects in graphic_to_objects.items() if len(objects) > 1))
check("Embedded images that show more than one survey graphic", [],
      sorted(o for o, graphics in object_to_graphics.items() if len(graphics) > 1))
check("Distinct embedded stimulus images", 30, len(object_to_graphics))

# Signal 3: the size the survey states equals the embedded image's size.
stated = [s for s in slots if s["stated_width"] is not None]
for slot in stated:
    check("%s %s work: stated size equals pixel size" % (slot["block"], slot["role"].lower()),
          (slot["stated_width"], slot["stated_height"]), (slot["pixel_width"], slot["pixel_height"]))
graphics_with_size = {s["graphic"] for s in stated}
check("Graphics whose size the survey states", 29, len(graphics_with_size), required=False)

# The None second work is the original: the same survey graphic, the same
# embedded image, and not the Slight graphic named in the stored unsafe copy.
slight_object = {(s["artwork"]): s["object_id"] for s in slots if s["level"] == "Slight" and s["role"] == "SECOND"}
original_object = {s["artwork"]: s["object_id"] for s in slots if s["role"] == "ALONE"}
for slot in slots:
    if slot["level"] == "None" and slot["role"] == "SECOND":
        check("%s second work is printed with the original's embedded image" % slot["block"],
              original_object[slot["artwork"]], slot["object_id"])
        check("%s second work is not printed with the Slight embedded image" % slot["block"], True,
              slot["object_id"] != slight_object[slot["artwork"]])

# ---------------------------------------------------------------------------
# 4. The bytes in the PDF file, read directly
# ---------------------------------------------------------------------------
# A PDF file ends with a cross-reference table that gives the byte offset of
# every numbered object. Each image is such an object: a short dictionary
# that states its filter and colour space, then the stream of its data.
with open(PRINTOUT, "rb") as handle:
    PDF = handle.read()


def cross_reference(pdf):
    start = int(re.search(rb"startxref\s+(\d+)\s+%%EOF\s*$", pdf).group(1))
    if pdf[start:start + 4] != b"xref":
        stop("The printout uses a compressed cross-reference, which this script does not read.")
    offsets, position = {}, start + 4
    while True:
        header = re.match(rb"\s*(\d+) (\d+)\s*\r?\n", pdf[position:position + 40])
        if not header:
            break
        first, count = int(header.group(1)), int(header.group(2))
        position += header.end()
        for i in range(count):
            entry = pdf[position + 20 * i: position + 20 * i + 20]
            if entry[17:18] == b"n":
                offsets[first + i] = int(entry[:10])
        position += 20 * count
    return offsets


OFFSETS = cross_reference(PDF)


def pdf_object(number):
    """The dictionary and the stream bytes of one numbered object."""
    start = OFFSETS[number]
    if not PDF.startswith(b"%d 0 obj" % number, start):
        stop("Object %d is not where the cross-reference puts it." % number)
    head_end = PDF.index(b"stream", start)
    dictionary = PDF[start:head_end]
    length = re.search(rb"/Length (\d+)( 0 R)?", dictionary)
    size = int(length.group(1))
    if length.group(2):
        size = int(re.search(rb"obj\s*(\d+)", PDF[OFFSETS[size]:OFFSETS[size] + 64]).group(1))
    data_start = head_end + len(b"stream")
    data_start += 2 if PDF[data_start:data_start + 2] == b"\r\n" else 1
    return dictionary, PDF[data_start:data_start + size]


def icc_is_srgb(number):
    """Whether a colour profile has the sRGB primaries and tone curve.

    An ICC colour profile is the standard description of a colour space that
    a file carries with it. The primaries are the colours of its pure red,
    green and blue, and the tone curve maps a stored value to an amount of
    light. sRGB is the standard colour space of screens and the web.
    """
    _, stream = pdf_object(number)
    # The profile is stored compressed with zlib, the lossless compression PDF files use.
    profile = zlib.decompress(stream)
    tags = {}
    for i in range(int.from_bytes(profile[128:132], "big")):
        entry = profile[132 + 12 * i: 144 + 12 * i]
        tags[entry[:4]] = profile[int.from_bytes(entry[4:8], "big"):][:int.from_bytes(entry[8:12], "big")]

    def xyz(tag):
        return [struct.unpack(">i", tags[tag][8 + 4 * k: 12 + 4 * k])[0] / 65536 for k in range(3)]

    # The sRGB primaries as an ICC profile stores them: adapted to D50, the
    # warmer white of printed paper under standard light that every ICC profile uses as its reference.
    primaries = {b"rXYZ": [0.4361, 0.2225, 0.0139], b"gXYZ": [0.3851, 0.7169, 0.0971],
                 b"bXYZ": [0.1431, 0.0606, 0.7141]}
    close = all(abs(a - b) < 0.0005 for tag, target in primaries.items() for a, b in zip(xyz(tag), target))
    # The sRGB tone curve: exponent 2.4, offsets 1/1.055 and 0.055/1.055, linear slope 1/12.92 below 0.04045.
    curve_ok = True
    for tag in (b"rTRC", b"gTRC", b"bTRC"):
        curve = tags[tag]
        values = [struct.unpack(">i", curve[12 + 4 * k: 16 + 4 * k])[0] / 65536 for k in range(5)]
        target = [2.4, 1 / 1.055, 0.055 / 1.055, 1 / 12.92, 0.04045]
        curve_ok &= curve[:4] == b"para" and all(abs(a - b) < 0.0005 for a, b in zip(values, target))
    return close and curve_ok


# pdfimages writes each embedded image to a file: JPEG data as the JPEG bytes
# it holds, and every other image as a lossless PNG.
work = tempfile.mkdtemp(prefix="image_check_")
try:
    subprocess.run(["pdfimages", "-all", "-p", PRINTOUT, os.path.join(work, "img")], check=True)
    written = {}
    for name in os.listdir(work):
        match = re.match(r"img-(\d+)-(\d+)\.(\w+)$", name)
        if match:
            written[int(match.group(2))] = os.path.join(work, name)

    object_record = {}
    for slot in slots:
        path = written.get(slot["num"])
        if path is None:
            stop("pdfimages wrote no file for image %d on page %d." % (slot["num"], slot["page"]))
        with open(path, "rb") as handle:
            data = handle.read()
        pixels = rgb_pixels(data)
        slot.update(path=path, extension=os.path.splitext(path)[1].lstrip("."), pixels_sha256=pixels_sha256(pixels))
        if slot["object_id"] in object_record:
            continue
        dictionary, stream = pdf_object(slot["object_id"])
        colour = re.search(rb"/ColorSpace \[/ICCBased (\d+) 0 R\]", dictionary)
        if b"/DecodeParms" in dictionary or b"/Decode " in dictionary or colour is None:
            stop("Image object %d has a setting this script does not check." % slot["object_id"])
        if b"/DCTDecode" in dictionary:
            # A JPEG is kept as the bytes stored in the PDF file.
            same = slot["extension"] == "jpg" and data == stream
            kind = "JPEG bytes as stored in the printout"
        else:
            # A PNG holds the same values as the stored samples, which zlib unpacks.
            raw = np.frombuffer(zlib.decompress(stream), dtype=np.uint8)
            same = (slot["extension"] == "png" and raw.size == pixels.size
                    and np.array_equal(raw.reshape(pixels.shape), pixels))
            kind = "PNG holding the stored samples without loss"
        object_record[slot["object_id"]] = dict(same=same, kind=kind, srgb=icc_is_srgb(int(colour.group(1))))
        check("Embedded image %d written without re-encoding (%s)" % (slot["object_id"], kind), True, same)
        check("Embedded image %d carries the printout's sRGB colour profile" % slot["object_id"], True,
              object_record[slot["object_id"]]["srgb"])

    # Every printing of one embedded image decodes to the same pixels.
    for object_id in object_to_graphics:
        hashes = {s["pixels_sha256"] for s in slots if s["object_id"] == object_id}
        check("Every printing of embedded image %d decodes to the same pixels" % object_id, 1, len(hashes))

    # -----------------------------------------------------------------------
    # 5. The 30 stimuli
    # -----------------------------------------------------------------------
    stimuli = []
    for artwork in ARTWORKS:
        for version in VERSIONS:
            graphic = ORIGINAL_GRAPHIC[artwork] if version == "original" else VERSION_GRAPHIC[(artwork, version)]
            showing = [s for s in slots if s["graphic"] == graphic]
            first = showing[0]
            none_slot = [s for s in slots if s["artwork"] == artwork and s["level"] == "None"
                         and s["role"] == "SECOND"][0]
            rated_level = "None" if version == "original" else version
            rated_block = [b for b in BLOCKS.values() if b["artwork"] == artwork and b["level"] == rated_level][0]
            signals = ["printout text and survey order", "sharing pattern"]
            if graphic in graphics_with_size:
                signals.append("stated pixel size")
            stimuli.append(dict(
                file="%s_%s.%s" % (artwork, version.lower(), first["extension"]),
                artwork=artwork,
                image_kind="NonFigure" if artwork.endswith("NonFigure") else "Figure",
                version=version,
                survey_graphic_id=graphic,
                display_question_tags="; ".join("%s:%s" % (s["block"], s["tag"]) for s in showing),
                rated_item_tags="; ".join(rated_block["ratings"]),
                rated_as_level=rated_level,
                printout_pages="; ".join(str(s["page"]) for s in showing),
                printout_object_id=first["object_id"],
                stored_as=object_record[first["object_id"]]["kind"],
                colour_profile="sRGB" if object_record[first["object_id"]]["srgb"] else "other",
                pixel_width=first["pixel_width"],
                pixel_height=first["pixel_height"],
                survey_stated_size=("%dx%d" % (next(s["stated_width"] for s in showing if s["stated_width"]),
                                               next(s["stated_height"] for s in showing if s["stated_width"]))
                                    if graphic in graphics_with_size else "not stated"),
                signals_agreeing="; ".join(signals),
                pixels_sha256=first["pixels_sha256"],
                none_graphic_id=none_slot["graphic"] if version == "original" else "",
                none_printout_page=none_slot["page"] if version == "original" else "",
                none_pixels_sha256=none_slot["pixels_sha256"] if version == "original" else "",
                unsafe_copy_names=(STALE.get(artwork, "") if version == "original" else ""),
                _source=first["path"]))
    check("Stimulus images named", 30, len(stimuli))
    for row in stimuli:
        if row["version"] == "original":
            check("%s: None second work has the original's graphic ID and pixels" % row["artwork"],
                  (row["survey_graphic_id"], row["pixels_sha256"]),
                  (row["none_graphic_id"], row["none_pixels_sha256"]))

    # -----------------------------------------------------------------------
    # 6. The local files, a secondary cross-check that overrides nothing
    # -----------------------------------------------------------------------
    # Each stimulus is set beside every local image of the same size, and,
    # after both are scaled to 256 pixels wide, beside every local image whose
    # ratio of width to height is within 2 percent of its own. Only local
    # images of a size some stimulus has are kept at full size in memory.
    SHAPES = {(s["pixel_height"], s["pixel_width"], 3) for s in slots}
    THUMB_WIDTH, ASPECT_TOLERANCE, LARGE = 256, 0.02, 40
    # Each stimulus scaled to 256 pixels wide, at its own height at that width.
    THUMBS = {}
    for row in stimuli:
        with Image.open(row["_source"]) as opened:
            image = opened.convert("RGB")
        width, height = image.size
        size = (THUMB_WIDTH, max(1, int(THUMB_WIDTH * height / width + 0.5)))
        THUMBS[row["file"]] = dict(size=size, aspect=width / height,
                                   pixels=np.asarray(image.resize(size, Image.Resampling.LANCZOS), dtype=np.int16))
    SCALED = {row["file"]: [] for row in stimuli}
    local = []
    if HAS_LOCAL:
        local_work = os.path.join(work, "local")
        os.makedirs(local_work)
        for root, folders, files in os.walk(LOCAL_IMAGES):
            folders.sort()
            for name in sorted(files):
                if name.startswith("."):
                    continue
                path = os.path.join(root, name)
                RUN_LOCAL.append(path)
                with open(path, "rb") as handle:
                    is_pdf = handle.read(5) == b"%PDF-"
                if is_pdf:
                    # A PDF file is read through the images embedded in it. A
                    # transparency mask (smask or mask in the listing) is not a picture and is left out.
                    target = os.path.join(local_work, "%d" % len(RUN_LOCAL))
                    os.makedirs(target)
                    listed = subprocess.run(["pdfimages", "-list", path], capture_output=True, text=True,
                                            check=True).stdout.splitlines()[2:]
                    kind_of = {int(line.split()[1]): line.split()[2] for line in listed if len(line.split()) > 2}
                    subprocess.run(["pdfimages", "-all", path, os.path.join(target, "img")], check=True,
                                   capture_output=True)
                    sources = []
                    for inner in sorted(os.listdir(target)):
                        number = int(re.match(r"img-(\d+)\.", inner).group(1))
                        if kind_of.get(number) == "image":
                            sources.append(("%s (embedded image %d)" % (show(path), len(sources) + 1),
                                            os.path.join(target, inner)))
                else:
                    sources = [(show(path), path)]
                for label, source in sources:
                    try:
                        pixels = rgb_pixels(source)
                    except Exception:
                        local.append(dict(file=label, name=name, readable=False, pixels=None))
                        continue
                    height, width = pixels.shape[:2]
                    local.append(dict(file=label, name=name, readable=True,
                                      pixels=pixels if pixels.shape in SHAPES else None))
                    # The scaled comparison with every stimulus of nearly the same shape.
                    resized = {}
                    for file, thumb in THUMBS.items():
                        if abs((width / height) / thumb["aspect"] - 1) <= ASPECT_TOLERANCE:
                            if thumb["size"] not in resized:
                                resized[thumb["size"]] = np.asarray(Image.fromarray(pixels).resize(
                                    thumb["size"], Image.Resampling.LANCZOS), dtype=np.int16)
                            SCALED[file].append((float(np.abs(resized[thumb["size"]] - thumb["pixels"]).mean()),
                                                 label, "%dx%d" % (width, height)))
        check("Local image files read (after PDF files are opened to the images inside them)", None,
              "%d files; %d images read, %d not readable as an image" % (
                  len(RUN_LOCAL), sum(f["readable"] for f in local), sum(not f["readable"] for f in local)),
              required=False)
    else:
        check("Local image folder %s absent; cross-check skipped" % show(LOCAL_IMAGES), None, "skipped",
              required=False)

    def name_says(name):
        # The local file name's artwork and version, read from its words.
        match = re.match(r"(\d)_(figure|nonfigure)_(original|orignial|minimal|dramatic)", name.lower())
        if not match:
            return ""
        artwork = "%s%s" % (match.group(1), "Figure" if match.group(2) == "figure" else "NonFigure")
        version = {"original": "original", "orignial": "original", "minimal": "Slight",
                   "dramatic": "Dramatic"}[match.group(3)]
        return "%s %s" % (artwork, version)

    for row in stimuli:
        pixels = rgb_pixels(row["_source"])
        same_size = [f for f in local if f["pixels"] is not None and f["pixels"].shape == pixels.shape]
        differences = []
        for candidate in same_size:
            difference = np.abs(candidate["pixels"].astype(np.int16) - pixels.astype(np.int16))
            differences.append((float(difference.mean()), int(difference.max()), candidate, difference.max(axis=2)))
        differences.sort(key=lambda item: (item[0], item[2]["file"]))
        exact = [c["file"] for mean, top, c, _ in differences if top == 0]
        if differences:
            mean, top, best, largest = differences[0]
            # Where the closest local file differs by more than 40 in some channel, and the box that holds those pixels.
            rows_over, columns_over = np.nonzero(largest > LARGE)
            box = ("rows %d to %d, columns %d to %d" % (rows_over.min(), rows_over.max(), columns_over.min(),
                                                         columns_over.max()) if len(rows_over) else "")
            row.update(local_same_size_files=len(same_size), local_closest_file=best["file"],
                       local_closest_mean_abs_difference=round(mean, 4), local_closest_max_abs_difference=top,
                       local_closest_pixels_over_40=len(rows_over), local_closest_over_40_box=box,
                       local_closest_name_says=name_says(best["name"]), local_identical_files="; ".join(exact))
        else:
            row.update(local_same_size_files=0, local_closest_file="", local_closest_mean_abs_difference="",
                       local_closest_max_abs_difference="", local_closest_pixels_over_40="",
                       local_closest_over_40_box="", local_closest_name_says="", local_identical_files="")
        # The closest local image after scaling, whatever its size.
        scaled = sorted(SCALED[row["file"]])
        if scaled:
            row.update(local_scaled_closest_file=scaled[0][1], local_scaled_closest_size=scaled[0][2],
                       local_scaled_mean_abs_difference=round(scaled[0][0], 4))
        else:
            row.update(local_scaled_closest_file="", local_scaled_closest_size="",
                       local_scaled_mean_abs_difference="")
    check("Stimuli with a local file of identical pixels", None,
          "%d of 30" % sum(bool(r["local_identical_files"]) for r in stimuli), required=False)

    # -----------------------------------------------------------------------
    # 7. Writing, first to a staging folder and then into stimuli/
    # -----------------------------------------------------------------------
    shutil.rmtree(STAGING_DIR, ignore_errors=True)
    os.makedirs(STAGING_DIR)
    for row in stimuli:
        target = os.path.join(STAGING_DIR, row["file"])
        shutil.copyfile(row["_source"], target)
        row["file_sha256"] = sha256_file(target)
        if pixels_sha256(rgb_pixels(target)) != row["pixels_sha256"]:
            stop("%s does not decode to the pixels it was copied from." % row["file"])
finally:
    shutil.rmtree(work, ignore_errors=True)

COLUMNS = ["file", "artwork", "image_kind", "version", "survey_graphic_id", "display_question_tags",
           "rated_item_tags", "rated_as_level", "printout_pages", "printout_object_id", "stored_as",
           "colour_profile", "pixel_width", "pixel_height", "survey_stated_size", "signals_agreeing",
           "file_sha256", "pixels_sha256", "none_graphic_id", "none_printout_page", "none_pixels_sha256",
           "unsafe_copy_names", "local_same_size_files", "local_closest_file", "local_closest_mean_abs_difference",
           "local_closest_max_abs_difference", "local_closest_pixels_over_40", "local_closest_over_40_box",
           "local_closest_name_says", "local_identical_files", "local_scaled_closest_file",
           "local_scaled_closest_size", "local_scaled_mean_abs_difference"]
manifest = pd.DataFrame(stimuli)[COLUMNS]
manifest["analysis_status"] = STATUS
manifest.to_csv(os.path.join(STAGING_DIR, "stimuli_manifest.csv"), index=False, lineterminator="\n")

checks = pd.DataFrame(CHECKS).rename(columns={"pass_": "pass"})
checks.insert(0, "tool", POPPLER_VERSION)
checks["analysis_status"] = STATUS
checks.to_csv(os.path.join(STAGING_DIR, "extraction_checks.csv"), index=False, lineterminator="\n")

# Every check has passed. The staged files replace the old ones in stimuli/,
# and stimulus images left from an earlier run under other names are removed.
os.makedirs(OUT_DIR, exist_ok=True)
written = [row["file"] for row in stimuli] + ["stimuli_manifest.csv", "extraction_checks.csv"]
for name in os.listdir(OUT_DIR):
    if re.match(r"\d(Figure|NonFigure)_(original|slight|dramatic)\.(png|jpg)$", name) and name not in written:
        os.remove(os.path.join(OUT_DIR, name))
for name in written:
    os.replace(os.path.join(STAGING_DIR, name), os.path.join(OUT_DIR, name))
shutil.rmtree(STAGING_DIR, ignore_errors=True)

# The run manifest, written last: every input read, every file written, and the tools.
run_rows = [dict(role="tool", what="poppler (pdfimages, pdftotext, pdfinfo)", file="", bytes="",
                 sha256="", version=POPPLER_VERSION.split()[-1]),
            dict(role="tool", what="Python", file="", bytes="", sha256="", version=platform.python_version())]
run_rows += [dict(role="tool", what=package, file="", bytes="", sha256="", version=importlib.metadata.version(package))
             for package in ("numpy", "pandas", "pillow")]
for what, path in RUN_INPUTS:
    run_rows.append(dict(role="input", what=what, file=show(path), bytes=os.path.getsize(path),
                         sha256=sha256_file(path), version=""))
for path in RUN_LOCAL:
    run_rows.append(dict(role="local image file", what="cross-check only", file=show(path),
                         bytes=os.path.getsize(path), sha256=sha256_file(path), version=""))
for name in written:
    path = os.path.join(OUT_DIR, name)
    run_rows.append(dict(role="output", what="stimulus image" if name.endswith((".png", ".jpg")) else "record",
                         file=show(path), bytes=os.path.getsize(path), sha256=sha256_file(path), version=""))
run_manifest = pd.DataFrame(run_rows)
run_manifest["analysis_status"] = STATUS
run_manifest.to_csv(os.path.join(OUT_DIR, "extraction_run_manifest.csv"), index=False, lineterminator="\n")

print("Checks run: %d; required checks failed: 0." % len(CHECKS))
print("The printout reads as the draft Study 5 survey at %d of %d wording differences." % (matches_draft, len(MARKERS)))
print()
print(manifest[["file", "survey_graphic_id", "printout_pages", "pixel_width", "pixel_height",
                "survey_stated_size", "local_closest_mean_abs_difference",
                "local_closest_name_says"]].to_string(index=False))
print()
print("Wrote %d images, stimuli_manifest.csv, extraction_checks.csv and extraction_run_manifest.csv to %s."
      % (len(stimuli), show(OUT_DIR)))
print("Printout SHA-256:", sha256_file(PRINTOUT))
