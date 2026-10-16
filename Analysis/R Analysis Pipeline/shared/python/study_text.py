"""Text measurement shared by every study in the project.

This module holds the measurement half of the Study 1 text notebook
(Study 1/Study1_02_Text.ipynb), so that Studies 2 to 5 apply the same eight
rules and write the same measurement files. A rule is a search pattern: a
written list of words and phrases, applied by the computer in the same way to
every response. No person and no language model labels, codes or judges any
response. One pretrained sentence-embedding model (a network trained
beforehand on other text, which turns a sentence into a list of numbers) is
used for one purpose only: the check of whether the topic model groups the
responses the way a grouping by meaning does.

Every function that reads responses takes a blind frame: a data frame (a
table held in memory by the pandas library) with the columns id,
stimulus_id, dimension and response_text, and beside them only columns whose
names begin with "stimulus_". check_blind() refuses any other column, so the
experimental condition, the rating and the demographics cannot reach the
measurement. The key (id, stimulus_id, dimension) must name one response per
row. The measures read three columns only: response_text, id (the topic
model's stability check leaves participants out by it) and dimension (the
topic model is fitted to each question separately). Every other column passes
through to the outputs as an identifier and is never read.

Each export has one function. It takes the blind frame and returns the frame
or the text to write:

    measures_frame             study<N>_text_measures.csv
    wordcounts_frame           study<N>_text_wordcounts.csv
    vocabulary_frame           study<N>_text_vocabulary.csv
    tokens_frame               study<N>_text_tokens.csv
    affect_frame               study<N>_text_affect.csv
    topics_frame               study<N>_text_topics.csv
    topic_top_words_frame      text_topics_top_words.csv
    topic_stability_frame      text_topics_stability.csv
    embedding_agreement_frame  text_topics_embedding_agreement.csv
    rules_text                 text_rules.txt
    rules_checksum_text        text_rules.sha256
    grounding_text             text_rules_grounding.txt

text_rules.sha256 holds a checksum of text_rules.txt: a 64-character string
computed from the exact bytes of a text by the SHA-256 recipe, so that
changing one character of the text changes the string. Every line of
text_rules.txt is the same in every study except the title line, which names
the study, and the line that gives the number of responses.

write_csv_atomic() and write_text_atomic() write a file under a temporary name
in its own folder and rename it once it is complete, so that a run that stops
partway never leaves a half-written file under a final name.
"""

import datetime
import hashlib
import os
import re
import textwrap
import uuid
import warnings
from collections import Counter
from itertools import combinations

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import NMF
from sklearn.exceptions import ConvergenceWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from threadpoolctl import threadpool_limits


# ---------------------------------------------------------------------------
# Paths.
#
# Every path is found relative to this file. The pipeline root is the folder
# two levels up (shared/python sits inside it). The word norms are two
# published tables in which groups of raters scored single English words: one
# for how pleasant a word is, how excited it makes a reader feel and how much
# in control it makes a reader feel, and one for how concrete it is. They are
# read from Study 1/nlp/norms under the pipeline root. The environment variable STUDY_TEXT_NORMS_DIR (a setting passed to the
# program from the shell) names another folder instead. display_path() writes
# a path relative to the pipeline root, so that printed output and error
# messages carry no account name and no folder particular to one machine.
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
PIPELINE_ROOT = os.path.normpath(os.path.join(HERE, os.pardir, os.pardir))
NORMS_DIR_VARIABLE = "STUDY_TEXT_NORMS_DIR"
DEFAULT_NORMS_DIR = os.path.join(PIPELINE_ROOT, "Study 1", "nlp", "norms")


def display_path(path):
    """`path` written relative to the pipeline root, for printing."""
    return os.path.relpath(os.path.abspath(path), PIPELINE_ROOT)


def norms_dir():
    """The folder holding the two word-norm files."""
    return os.path.normpath(os.environ.get(NORMS_DIR_VARIABLE) or DEFAULT_NORMS_DIR)


# ---------------------------------------------------------------------------
# The blind frame.
#
# The measurement sees the response identifiers, the stimulus, the question
# and the text, and nothing else. check_blind() enforces that in two steps.
# A column named for the condition, the rating or a demographic is refused by
# name first, so that the message says what went wrong. Any other column that
# is neither required nor named "stimulus_..." is then refused because it is
# not on the list; a study's manipulated factor stored under its own name
# (Study 5's deriv_effort, for example) is stopped there. Names are compared
# in lower case. The check reads names, not contents, so a condition stored
# under a stimulus_ name would pass it. Which columns describe the work shown
# is settled where each study builds its blind frame.
#
# Every function in this module that takes a frame of responses calls
# check_blind() on it before reading it.
# ---------------------------------------------------------------------------
KEY = ["id", "stimulus_id", "dimension"]
REQUIRED_COLUMNS = ["id", "stimulus_id", "dimension", "response_text"]
METADATA_PREFIX = "stimulus_"
FORBIDDEN_NAMES = ["type", "rating", "condition", "arm",
                   "age", "gender", "race", "language", "experience"]
FORBIDDEN_FRAGMENTS = ["rating", "condition"]


def _forbidden(column):
    name = str(column).lower()
    return name in FORBIDDEN_NAMES or any(fragment in name for fragment in FORBIDDEN_FRAGMENTS)


def check_blind(blind):
    """Stop unless `blind` is a blind frame, with a message saying why."""
    assert isinstance(blind, pd.DataFrame), "The measurement takes a pandas data frame."
    columns = [str(c) for c in blind.columns]
    named = [c for c in columns if _forbidden(c)]
    assert not named, (
        "The text measurement must never see the condition, the rating or a "
        "demographic, and this frame carries %s. Build the frame from the "
        "identifiers, the stimulus columns, the question and the text only." % named)
    assert len(set(columns)) == len(columns), "The frame repeats a column name."
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    assert not missing, "The frame lacks the required column(s) %s." % missing
    extra = [c for c in columns if c not in REQUIRED_COLUMNS and not c.startswith(METADATA_PREFIX)]
    assert not extra, (
        "The frame carries %s. A blind frame holds id, stimulus_id, dimension and "
        "response_text, and otherwise only columns named stimulus_... . Leave a "
        "manipulated factor out; rename a genuine stimulus attribute to stimulus_<name>."
        % extra)
    n_repeated = int(blind.duplicated(KEY).sum())
    assert n_repeated == 0, (
        "%d rows repeat an (id, stimulus_id, dimension) key. Each row must be one "
        "response, so each work a participant answered about needs its own "
        "stimulus_id." % n_repeated)
    return blind


def check_output(frame, label):
    """Stop if an output carries the condition, the rating, a demographic or the text."""
    present = [c for c in frame.columns if _forbidden(c) or str(c) == "response_text"]
    assert not present, "%s carries a column it must never carry: %s." % (label, present)
    return frame


# ---------------------------------------------------------------------------
# The eight rules.
#
# Each rule is a dictionary with five fields:
#   name       the column it produces in the measures file
#   plain      a one-line description in ordinary words
#   grounding  a note on the construct the rule measures and the literature
#              that reading comes from. It is not part of the pattern, and the
#              checksum on text_rules.txt does not cover it.
#   include    the search pattern for phrases that count
#   exclude    the search pattern for places where those phrases mean
#              something else (an empty string excludes nothing)
#
# The rules were written against the Study 1 corpus, and the reasons given
# below come from that corpus. The module applies them unchanged in every
# study.
#
# The patterns are regular expressions (a compact notation for "any of these
# words or phrases, in any of their ordinary forms") written in verbose mode,
# switched on by the (?x) at the start. In verbose mode the matcher ignores
# spaces and line breaks inside the pattern, so a literal space is written as
# "\ " or "\s". Notation:
#   \b          a word boundary, so "\bart\b" matches "art" but not "artist"
#   (?:a|b)     either a or b
#   ?           the preceding piece is optional
#   [^.]{0,25}  up to 25 characters that are not a full stop: a few words
#               later in the same sentence
# Every pattern is applied to the lower-cased response.
# ---------------------------------------------------------------------------

RULES = []

# --- 1. Detail talk -----------------------------------------------------------
# Visible properties of the picture surface. The last two alternatives catch
# the quantity-of-content idiom ("a lot going on", "many different parts").
# The quantity phrases are tied to a content noun, because "a lot of effort"
# is effort talk and not detail talk.
RULES.append(dict(
    name="says_detail",
    plain="mentions visible detail, intricacy, complexity, texture, shading, brushwork, "
          "or quantity of content",
    grounding="Detail talk is the visible-work reading of effort: the marks on the picture "
              "surface from which a viewer infers how much labour went in, since the labour "
              "itself cannot be seen. Buell and Norton (2011) call the value people add to an "
              "identical result when they can see work being done on it the labour illusion, "
              "and Kruger, Wirtz, Van Boven and Altermatt (2004) show that judged quality "
              "follows believed effort most strongly when quality is hard to assess on its "
              "own, which a picture from an unfamiliar maker is. The rule records the cue and "
              "not the inference: a writer who names the detail is counted whether or not they "
              "went on to say it took work.",
    include=r"""(?x)
      \b detail (?:s|ed|ing)? \b
    | \b intricat (?:e|ely) \b | \b intricac (?:y|ies) \b
    | \b complex (?:ity)? \b | \b complicated \b
    | \b elaborate \b
    | \b textur (?:e|es|ed|al) \b
    | \b shading \b | \b shadow (?:s|ing)? \b | \b hatching \b
    | \b brush \s? (?: work | stroke s? ) \b | \b stroke s? \b
    | \b line \s? work \b | \b fine \s lines? \b
    | \b meticulous (?:ly)? \b | \b precise (?:ly)? \b | \b precision \b
    | \b layer (?:s|ed|ing)? \b
    | \b (?: a\ lot | lots | so\ much | too\ much | much | plenty | a\ great\ deal )
        \b [^.]{0,25}? \b going \s on \b
    | \b (?: many | multiple | numerous | several | so\ many
           | a\ lot\ of | lots\ of | tons\ of | ton\ of | plenty\ of )
        \s+ (?: different\s+ | small\s+ | little\s+ | tiny\s+ | minor\s+ )?
        (?: parts | elements | components | aspects | objects | things | pieces
          | layers | colou?rs | shapes | features | items | figures | details ) \b
    """,
    exclude=r"",
))

# --- 2. Time talk -------------------------------------------------------------
# Duration and industriousness, in either direction: a claim that something
# took seconds is a claim about duration with the sign reversed. Several Study 1
# artworks show an hourglass and one shows a Christmas scene, so "hour glass",
# "time passing", "time running out", "carrying time" and "Christmas time"
# describe the picture and are excluded. "Minute details" uses "minute" to mean
# small. "At the same time", "day to day" and "end of the day" are idioms.
RULES.append(dict(
    name="says_time",
    plain="mentions time, hours, duration, speed, or tediousness",
    grounding="Time talk is the elapsed-labour reading of effort: how long the making took, or "
              "how quickly it could have been done. This is the cue Kruger, Wirtz, Van Boven "
              "and Altermatt (2004) manipulated to show the effort heuristic, the rule of "
              "thumb by which a poem, a painting or a suit of armour is rated better and worth "
              "more when it is said to have taken longer, and Chinander and Schweitzer (2003) "
              "show the same reliance on time as an input measure even where it has no bearing "
              "on the outcome being judged. Of the three effort readings this is the one "
              "closest to the labour that Feist declined to protect, so the rule catches "
              "duration claims in either direction, including the claim that something took no "
              "time at all.",
    include=r"""(?x)
      \b time \b
    | \b hours \b | \b an \s hour \b | \b minutes \b | \b a \s minute \b | \b seconds? \b
    | \b days \b | \b weeks \b | \b all \s day \b
    | \b a \s while \b | \b awhile \b
    | \b tedious (?:ness|ly)? \b | \b painstaking (?:ly)? \b
    | \b laborious \b | \b arduous \b | \b labor \b
    | \b spen[dt] (?:s|ing)? \b
    | \b took \b [^.]{0,25}? \b (?: hours? | days? | long ) \b
    | \b quick (?:ly|er)? \b | \b fast \b | \b instant (?:ly|aneous(?:ly)?)? \b
    | \b immediat (?:e|ely) \b | \b rapid (?:ly)? \b | \b in \s no \s time \b
    """,
    exclude=r"""(?x)
      christmas \s? time
    | \b time \s (?: thing | passing | as \s fire | running \s out )
    | carrying \s time
    | \b at \s the \s same \s time \b
    | \b day \s to \s day \b | \b end \s of \s the \s day \b | \b during \s the \s day \b
    | \b hour \s? glass \b
    | \b minute \s detail
    """,
))

# --- 3. Skill talk ------------------------------------------------------------
# Ability acquired by training, and the claim that something was done by hand.
# "Technically" is excluded because in the Study 1 corpus it is a hedge ("it
# technically is novel"), not a claim about craft.
RULES.append(dict(
    name="says_skill",
    plain="mentions skill, craft, technique, talent, training, mastery, or hand execution",
    grounding="Skill talk is the execution reading of effort: ability acquired by training, "
              "and the craft with which something was done. Amabile's componential model "
              "(1983, 1996) treats domain-relevant skills, meaning technical skill and craft "
              "knowledge in a field, as one ingredient of creative work and keeps them apart "
              "from the creativity-relevant skills that make the work new, and her consensual "
              "assessment technique (1982) asks judges to rate creativity and technical "
              "goodness as separate dimensions and finds them related but not the same. The "
              "rule records that a writer located effort in ability rather than in time or in "
              "the picture surface; it does not record how much ability they thought was "
              "shown.",
    include=r"""(?x)
      \b skill (?:s|ed|ful|fully)? \b
    | \b craft (?:s|ed|ing|smanship|manship)? \b
    | \b techniqu e s? \b | \b technical \b
    | \b talent (?:s|ed)? \b
    | \b train (?:ed|ing) \b
    | \b master (?:y|ed|ful|ing)? \b
    | \b expert (?:ise|s)? \b
    | \b artistry \b
    | \b artistic \s (?: skill s? | abilit (?:y|ies) | talent | training ) \b
    | \b practic (?:e|ed|ing) \b | \b proficien (?:t|cy) \b
    | \b know [-\s] how \b
    | \b professional \b
    | \b good \s at \b
    | \b execut (?:ed|ion) \b
    | \b hand [-\s]? (?: drawn | painted | made | crafted ) \b | \b by \s hand \b
    | \b human \s abilities \b
    """,
    exclude=r"""(?x) \b technically \b | \b in \s practice \b """,
))

# --- 4. Concept talk ----------------------------------------------------------
# What the work is about rather than what it looks like: the idea, the meaning,
# the message, the story, the symbolism, the thought behind it. It is written
# to pair with detail talk. Detail talk locates effort in the picture surface;
# concept talk locates creativity in something decided before any of the
# picture was rendered.
#
# Three restrictions come from how the Study 1 corpus uses the words. The bare
# word "thought" is not counted, because there it is almost always the past
# tense of "think"; only the phrases in which "thought" is a noun about the
# making count. The noun "expression" is not counted, because several artworks
# show faces and the noun nearly always means a face; only the verb forms are
# listed. "Imaginative" and "imagination" are left out, because they say that a
# work is creative rather than what its creativity consists of.
RULES.append(dict(
    name="says_concept",
    plain="mentions the idea, meaning, message, story, symbolism, or thought behind the work",
    grounding="Concept talk locates creativity in the idea behind the work rather than in the "
              "picture surface. The construct is the lay implicit theory of creativity, "
              "meaning what ordinary people take the word to consist of when nobody hands them "
              "a definition: Sternberg (1985) found that laypeople's picture of a creative "
              "person turns on unconventional thinking and on imagination and aesthetic sense, "
              "which he found absent from their picture of intelligence, and Runco and Bahleda "
              "(1986) found that the picture differs by domain, so artistic creativity carries "
              "a profile of its own. Leder, Belke, Oeberst and Augustin (2004) place "
              "interpretation, the viewer's attempt to make sense of what a work is about, "
              "among the stages of taking in a work of art, which is why words for meaning, "
              "message and story sit beside words for the idea. The rule counts a mention of "
              "the idea; it does not judge whether the idea was any good.",
    include=r"""(?x)
      \b idea s? \b
    | \b concept (?: s | ual | ually )? \b
    | \b meaning (?: s | ful | fully )? \b
    | \b message s? \b
    | \b symbol (?: s | ic | ically | ism | ize | izes | ized | izing )? \b
    | \b metaphor (?: s | ical | ically )? \b
    | \b theme s? \b | \b thematic \b
    | \b stor (?: y | ies | yline | ytelling ) \b | \b backstory \b
    | \b narrative s? \b
    | \b represent (?: s | ed | ing | ation | ations )? \b
    | \b convey (?: s | ed | ing )? \b
    | \b express (?: es | ed | ing ) \b
    | \b interpret (?: s | ed | ing | ation | ations )? \b
    | \b intent (?: ion | ions | ional | ionality )? \b
    | \b vision (?: ary )? \b
    | \b thoughtful (?: ly | ness )? \b
    | \b thought [-\s] (?: provoking | out | through | up | behind | process | put ) \b
    | \b (?: much | little | some | any | no | more | a\ lot\ of | lots\ of
           | a\ great\ deal\ of | plenty\ of ) \s+ thought \b
    | \b well [-\s] thought \b
    """,
    exclude=r"""(?x) \b (?: have | had | has | i ) \s+ no \s+ idea \b """,
))

# --- 5. Prompt talk -----------------------------------------------------------
# Any mention of operating a machine to make the picture: prompting, typing,
# generating, or naming a machine, a program or an image generator. The bare
# noun "type" ("a type of painting") is not counted; only the verb forms and
# the typing-at-a-machine phrases are.
RULES.append(dict(
    name="says_prompt",
    plain="mentions prompting, typing, generating, or names a machine or image generator",
    grounding="Prompt talk is a written trace of what the participant believed about how the "
              "picture was made. The instrument carries no manipulation check, meaning no "
              "question asking whether the participant took in the vignette, and there is "
              "support for leaving one out: a check placed inside a study is an intervention "
              "as well as a measure and can change what follows it (Hauser, Ellsworth and "
              "Gonzalez 2018), and a question that asks whether a cover story was believed is "
              "itself a demand characteristic, Orne's (1962) term for a cue that tells a "
              "participant what the study is about. Chamberlain, Mullin, Scheerlinck and "
              "Wagemans (2018) found that viewers could not tell computer-made pictures from "
              "hand-made ones and still rated pictures lower when told a computer made them, "
              "so a participant told a person made these could plausibly doubt it. The rule "
              "records any mention of a machine or of operating one, in either arm. It does not "
              "record what the writer believed about who made the pictures.",
    include=r"""(?x)
      \b prompt (?:s|ed|ing)? \b
    | \b typ (?: ing | ed ) \b
    | \b type \s (?: in | into | out | commands? | words? | some
                   | a\ prompt | a\ sentence | a\ description | a\ few\ words ) \b
    | \b (?: just | only | but | was ) \s type \b
    | \b generat (?: e|ed|es|ing|or|ors|ion|ive ) \b
    | \b a \.? i \.? \b | \b artificial \s intelligence \b
    | \b machine s? \b | \b computer (?:s|ized)? \b | \b algorithm (?:s|ic)? \b
    | \b software \b | \b program (?:s|med|ming)? \b | \b robot (?:s|ic)? \b
    | \b chat \s? gpt \b | \b midjourney \b | \b dall [-\s]? e \b | \b stable \s diffusion \b
    | \b input (?:s|ed|ted|ting)? \b
    """,
    exclude=r"",
))

# --- 6. Prior-exposure talk ---------------------------------------------------
# The claim that the work is already familiar: seen before, generic, typical,
# common, derivative, a cliche. It takes three values (asserted, negated,
# neither), because "I have seen this before" and "I have never seen anything
# like this" are opposite claims about the same thing. "Haven't", "hasn't" and
# "hadn't" are listed in their own right, because there is no word boundary
# between "haven" and "'t" for the bare "n't" alternative to find.
#
# "Similar to each other" is excluded, because in the Study 1 corpus it
# describes repetition inside one picture. "Been done" must be followed by a
# before-word, because "more could have been done" is not a familiarity claim.
# "Replicate" is not listed, because in that corpus it means "reproduce by
# hand", a claim about difficulty.
RULES.append(dict(
    name="prior_exposure",
    plain="says the work looks familiar, already seen, generic or derivative "
          "(asserted), explicitly denies it (negated), or neither",
    grounding="Prior-exposure talk records a familiarity judgment: the claim that the work has "
              "been seen before, is generic or typical, or the explicit denial of that. "
              "Familiarity is a criterion in its own right in the literature on aesthetic "
              "preference, through mere exposure, the finding that repeated encounters with a "
              "thing raise liking for it (Zajonc 1968), and through typicality, the closeness "
              "of a thing to the usual example of its kind, which Hekkert, Snelders and van "
              "Wieringen (2003) show works alongside novelty in shaping preference while "
              "pulling against it. On the creativity side the standard definition requires "
              "originality as well as effectiveness (Runco and Jaeger 2012), and Diedrich, "
              "Benedek, Jauk and Neubauer (2015) find that judged creativity leans more on "
              "novelty than on usefulness, so a rater who reaches for newness is applying a "
              "criterion the field itself uses. The rule takes three values because asserting "
              "familiarity and denying it are different claims about the same thing.",
    include=r"""(?x)
      \b (?: have | had | has | haven'?t | hasn'?t | hadn'?t | i'?ve | i'?d | never | not | n't
           | ever | already )
        \s (?:\w+\s){0,2} seen \b
    | \b seen \b [^.]{0,25}? \b (?: before | already | elsewhere | previously
                                  | times | everywhere ) \b
    | \b familiar (?:ity)? \b | \b unfamiliar \b
    | \b reminds? \s me \s of \b | \b reminiscent \b
    | \b similar \s to \b
    | \b generic (?:ally)? \b | \b clich [eé] (?:d|s)? \b
    | \b overdone \b | \b overused \b | \b cookie [-\s]? cutter \b
    | \b common (?:ly|place)? \b | \b typical (?:ly)? \b | \b ordinary \b | \b standard \b
    | \b unoriginal \b | \b derivative \b | \b copied \b | \b copying \b
    | \b recycled \b
    | \b done \s before \b
    | \b been \s done \s (?: before | already | many | several | a \s \w+ ) \b
    | \b nothing \s new \b | \b not \s new \b
    | \b i \s recognize \b
    """,
    exclude=r"""(?x)
      \b similar \s to \s (?: each \s other | one \s another | the \s others? \b )
    """,
))

# --- 7. Anchor echo -----------------------------------------------------------
# The rating scale's labels were "No / Minimal / Moderate / Significant / A
# great deal of creativity (or effort) involved", with "A lot of effort
# involved" as an alternative wording of the fourth point. The rule fires on
# that wording wherever it appears, including in a response that goes on to
# give a reason.
RULES.append(dict(
    name="anchor_echo",
    plain="contains the rating scale's own wording",
    grounding="Anchor echo records an explanation that contains the rating scale's own labels. "
              "The motivation is satisficing, Krosnick's (1991) term for giving an answer that "
              "is acceptable rather than the best one can, of which the least effortful form "
              "for an open question is to hand back the words already supplied, joined to "
              "Schwarz's (1999) observation that respondents read the wording of a scale as a "
              "guide to what an acceptable answer looks like. The rule does not measure "
              "satisficing. It fires on the scale's wording wherever the wording appears, "
              "including in an explanation that goes on to give a full reason, so it records "
              "that the wording is present and nothing about what else the explanation "
              "carries. It is a check on the corpus rather than one of the three questions.",
    include=r"""(?x)
      \b (?: no | minimal | moderate | significant | a\ lot\ of | a\ great\ deal\ of )
        \s+ (?: creativity | effort ) \b (?: \s+ involved )?
    | \b (?: creativity | effort ) \s+ (?: was \s+ | is \s+ )? involved \b
    """,
    exclude=r"",
))

# --- 8. Machine-made talk -----------------------------------------------------
# A narrow companion to prompt talk. It fires only on a phrase about a machine
# making the work. Three shapes count: a machine noun followed in the same
# sentence by a making verb ("the AI generated it"); a making verb followed by
# "by", "with", "using" or "from" and a machine noun ("made with AI"); and the
# fixed compounds "ai-generated", "computer generated", "machine-made", "ai
# art" and "ai image".
#
# MACHINE_NOUN and MAKING_VERB are written once and dropped into the pattern in
# three places, so the three shapes share one vocabulary. "Creat" is spelled
# out as its verb forms and the noun "creation", because the bare stem would
# also match "creative". "Did" carries a word boundary, so "didn't" is not a
# making verb.
#
# The exclusion removes a sentence in which a person is the agent of tool use
# ("Alex used AI to paint it"), from the person to the end of the sentence. The
# flag records the phrase whatever is said with it; classify_machine_made()
# reads whether the phrase was stated, denied or supposed.
MACHINE_NOUN = r"""(?: a\.?i | artificial \s intelligence | computer | algorithm | machine | bot
      | software | program | generator | neural \s network | midjourney | dall [-\s]? e
      | stable \s diffusion | chat \s? gpt ) s?"""
MAKING_VERB = r"""(?: generat | creat (?: e | es | ed | ing | ion | ions ) \b | produc
      | mak (?: e | es | ing | er ) \b | made \b | draw | drew \b | paint | render | design
      | did \b | done \b | built \b | output )"""
RULES.append(dict(
    name="says_machine_made",
    plain="mentions a machine, a program or an image generator making the work, whether "
          "stated, denied or supposed",
    grounding="Machine-made talk records a mention of a machine making the work: a phrase such "
              "as 'AI generated' or 'made by a computer', however it is used. The reading "
              "column beside it separates statements that a machine made the work, hedged "
              "impressions such as 'probably AI' among them, from denials ('this does not "
              "look AI generated') and suppositions ('if this were AI generated'). Neither "
              "the flag nor the statements measure disbelief in the vignette. The instrument "
              "has no manipulation check, a participant can doubt the story without writing "
              "so, and a participant can write that a picture looks machine-made while "
              "accepting what they were told about who made it; the counts describe what was "
              "written.",
    include=r"""(?x)
      \b %(noun)s
      \b [^.]{0,25}? \b
      %(verb)s
    | \b %(verb)s
      \w* [^.]{0,20}? \b (?: by | with | using | from ) \s+ (?: (?: a | an | the ) \s+ )?
      \b %(noun)s
      \b
    | \b (?: ai | computer ) [-\s] generated \b
    | \b (?: machine | ai ) [-\s] made \b
    | \b ai \s (?: art | image | artwork ) \b
    """ % dict(noun=MACHINE_NOUN, verb=MAKING_VERB),
    exclude=r"""(?x)
      (?: \b %(verb)s
          \w* \s+ by \s+ )?
      \b (?: alex | he | she | they | the \s artist | someone | a \s person | humans? ) \s+
      (?: used | using | use | uses | utiliz \w* | employ \w* ) \s+ (?: an? \s+ )?
      (?: ai | computer | software | program | algorithm | generator | machine ) [^.]*
    """ % dict(verb=MAKING_VERB),
))

# --- the negation window ------------------------------------------------------
# The 30 characters immediately before a matched phrase. A negating word there,
# in the same clause as the phrase, means the phrase is denied. Three readings
# use the window: the prior-exposure rule; the polarity reading, a column
# beside each of the detail, time, skill and concept flags that records
# whether the matched phrase was claimed (asserted) or denied (negated); and
# the machine-made reading.
NEGATION_WINDOW = 30
NEGATION_PATTERN = r"""(?x)
  \b not \b | \b never \b | n't \b | \b no \b | \b nothing \b | \b none \b
| \b hardly \b | \b rarely \b | \b unlike \b | \b without \b
| \b cannot \b | \b can't \b | \b barely \b | \b nowhere \b
"""

# --- quantity words that deny an amount ---------------------------------------
# Used by the polarity reading of detail, time, skill and concept talk, beside
# the negating words. "Little detail" and "lack of skill" deny their topic
# through a word for a small amount. Prior-exposure talk does not use this list.
QUANTIFIER_NEGATION = r"""(?x)
  \b little \b | \b not \s much \b | \b not \s a \s lot \b | \b not \s many \b
| \b lack \b | \b lacking \b | \b lacks \b
| \b no \b | \b minimal \b | \b barely \b | \b hardly \b | \b without \b | \b low \b
"""

# --- clause boundaries --------------------------------------------------------
# A negating word counts only in the same clause as the phrase. The window is
# cut at the last of these markers, and only the text after it is searched.
CLAUSE_BOUNDARY = r"""(?x)
  , | ; | \. | \b because \b | \b but \b | \b however \b | \b since \b
| \b although \b | \b though \b | \b whereas \b | \b so \s that \b
"""

# A phrase that carries its own negation in its spelling ("unfamiliar").
SELF_NEGATING = r"""(?x) ^ (?: unfamiliar | never | un [-] )"""

# Two phrases assert familiarity through a negating word. They are read as
# asserted before any negation reading is applied.
FAMILIARITY_ASSERTED = r"""(?x) ^ (?: nothing | not ) \s new $"""

# "Little" denies an amount only where it names one ("very little", "little to
# no"). It names a size, and denies nothing, when the words directly before it
# match this pattern ("a little", "the little details"). The pattern is tested
# against the text that ends where "little" begins.
LITTLE_AS_SIZE = r"""(?x)
  \b (?: a | the | some | such | many | so \s many | a \s lot \s of | lots \s of
       | all \s the | small | tiny ) \s+ $
"""

# --- words that open a supposition --------------------------------------------
# Used by the reading of machine-made talk. "If", "whether" and "unless" open a
# supposition. An "if" directly after "as" does not count, because "as if"
# puts the impression forward.
CONDITIONAL_MARKER = r"""(?x)
  (?<! \b as \s ) \b if \b | \b whether \b | \b unless \b
"""


# ---------------------------------------------------------------------------
# The function-word list.
#
# tokenize() removes these words before the word counts, the content-word
# lists, the affect scores and the topic model. Function words carry grammar,
# not content. The list holds articles, pronouns, prepositions, conjunctions,
# auxiliary and copular verbs and bare numbers, and no content word.
# scikit-learn's built-in English stop list is not used, because it contains
# content words such as "detail", "take", "many", "much", "show", "made" and
# "part".
# ---------------------------------------------------------------------------
FUNCTION_WORDS = sorted(set("""
a about above after again against all almost along already also although always am among an and
another any anything are aren't around as at
be because been before being below between both but by
came can can't cannot could couldn't
did didn't do does doesn't doing don't down during
each either else enough even ever every everything except
few for from further
had hadn't has hasn't have haven't having he he's her here hers herself him himself his how however
i i'd i'll i'm i've if in into is isn't it it's its itself
just
let let's like
may maybe me might mine more most must my myself
near neither never nevertheless no nor not nothing now
of off often on once one only onto or other others ought our ours ourselves out over own
per perhaps
quite
rather really
same seem seemed seems shall she she's should shouldn't since so some someone something sometimes
still such
than that that's the their theirs them themselves then there there's therefore these they they're
this those though through thus to too toward towards
under until up upon us
very
was wasn't we we're well were weren't what whatever when where whereas whether which while who whom
whose why will with within without won't would wouldn't
yet you you're your yours yourself
two three four five six seven eight nine ten
""".split()))

for _content_word in ["detail", "take", "many", "much", "show", "made", "part", "time", "skill"]:
    assert _content_word not in FUNCTION_WORDS, \
        "%s is a content word and must not be in the ignore list" % _content_word

# ---------------------------------------------------------------------------
# The task vocabulary.
#
# The words of the Study 1 instrument: the vignette's name, the words of the
# two rating questions ("How much effort was involved in the production of
# this work?", and the same for creativity), the words of their scale anchors,
# and the words describing the artworks. They are in the responses because the
# instrument put them there. The affect scores and the topic model remove them,
# with their plurals.
# ---------------------------------------------------------------------------
TASK_VOCABULARY = ["alex", "art", "artwork", "image", "picture", "piece", "work",
                   "effort", "effortful", "creative", "creativity", "rating", "rate",
                   "involved", "production", "much",
                   "minimal", "moderate", "significant", "great", "deal", "lot"]


def is_task_vocabulary(word):
    """True for a task word, or for the plural of one."""
    return word in TASK_VOCABULARY or (word.endswith("s") and word[:-1] in TASK_VOCABULARY)


# ---------------------------------------------------------------------------
# Tokens.
#
# A token is a run of letters and apostrophes, of two characters or more,
# starting with a letter, taken from the lower-cased text. tokenize() keeps
# every token that is not a function word, each occurrence in order.
# ---------------------------------------------------------------------------
WORD_RE = re.compile(r"[a-z][a-z']+")
IGNORE = set(FUNCTION_WORDS)


def tokenize(text):
    """Lower-cased words of two letters or more, with function words removed."""
    return [w for w in WORD_RE.findall(text.lower()) if w not in IGNORE]


def response_texts(blind):
    """The response texts, with a missing response read as an empty string."""
    check_blind(blind)
    return blind["response_text"].fillna("").astype(str).tolist()


def lower_texts(blind):
    """The lower-cased response texts. Every pattern is written against these."""
    check_blind(blind)
    return blind["response_text"].fillna("").astype(str).str.lower().tolist()


# ---------------------------------------------------------------------------
# The rules in full, as text.
#
# format_rules() returns the text written to text_rules.txt, and the checksum
# in text_rules.sha256 is computed from it. The text names the study and the
# number of responses; every other line is the same in every study.
# ---------------------------------------------------------------------------
def format_rules(rules, study, n_responses):
    """Return the full text of every rule in `rules`, ready to print or to save."""
    out = []
    out.append("=" * 100)
    out.append("%s TEXT MEASURES: THE RULES IN FULL" % study.upper())
    out.append("=" * 100)
    out.append("")
    out.append("Every measure below is applied by computer to all {:,} responses, identically,"
               .format(n_responses))
    out.append("with the response text lower-cased first. No response is judged individually.")
    out.append("Patterns are written in verbose mode: spaces and line breaks inside a pattern are")
    out.append("ignored by the matcher, so a literal space is written as \\  or \\s.")
    out.append("")
    for i, rule in enumerate(rules, start=1):
        out.append("-" * 100)
        out.append("RULE %d OF %d: %s" % (i, len(rules), rule["name"]))
        out.append("-" * 100)
        out.append("In plain words: " + rule["plain"])
        out.append("")
        out.append("COUNTS AS A MATCH:")
        for line in rule["include"].strip().splitlines():
            out.append("    " + line.strip())
        if rule["exclude"].strip():
            out.append("")
            out.append("DOES NOT COUNT, even though the words above appear "
                       "(these mean something else in this corpus):")
            for line in rule["exclude"].strip().splitlines():
                out.append("    " + line.strip())
        out.append("")
    out.append("-" * 100)
    out.append("THE NEGATION WINDOW (used by prior_exposure AND by the four polarity readings:")
    out.append("detail_polarity, time_polarity, skill_polarity, concept_polarity)")
    out.append("-" * 100)
    out.append("The window is the %d characters immediately before a matched phrase. For a"
               % NEGATION_WINDOW)
    out.append("prior-exposure phrase, a negating word from the first list below inside that")
    out.append("window means the response is recorded as 'negated' rather than 'asserted'. For a")
    out.append("detail, time, skill or concept phrase, the same window is searched for the same")
    out.append("negating words and also for the quantifier negations in the second list, which")
    out.append("name a small amount rather than deny a fact. Thirty characters is about five or")
    out.append("six words: long enough to reach back over 'I do not think I have', short enough not to")
    out.append("reach far into the sentence.")
    out.append("")
    out.append("Negating words, used by prior_exposure and by all four polarity readings:")
    for line in NEGATION_PATTERN.strip().splitlines():
        out.append("    " + line.strip())
    out.append("")
    out.append("Quantifier negations, used by the four polarity readings only, never by")
    out.append("prior_exposure ('little' or 'low' before 'familiar' is not a denial of familiarity):")
    for line in QUANTIFIER_NEGATION.strip().splitlines():
        out.append("    " + line.strip())
    out.append("")
    out.append("'little' is a quantifier negation only where it names an amount ('little detail',")
    out.append("'very little', 'too little', 'little to no'). It is not read as one when the words")
    out.append("directly before it match this pattern, which marks it as a size ('a little', 'the")
    out.append("little details', 'many small little parts'):")
    for line in LITTLE_AS_SIZE.strip().splitlines():
        out.append("    " + line.strip())
    out.append("")
    out.append("A negating word counts only if it sits in the same clause as the phrase it")
    out.append("negates. The window is therefore cut at the nearest of these clause markers,")
    out.append("and only the text after the last one is searched for a negating word:")
    for line in CLAUSE_BOUNDARY.strip().splitlines():
        out.append("    " + line.strip())
    out.append("")
    out.append("For prior_exposure, a negating word from the first list sitting inside the matched")
    out.append("phrase itself ('have never seen', 'haven't seen') also records it as 'negated', and")
    out.append("so does a phrase that carries its own negation in its spelling:")
    out.append("    " + SELF_NEGATING.strip())
    out.append("Two phrases assert familiarity through a negating word and are recorded as")
    out.append("'asserted' before either reading is applied:")
    out.append("    " + FAMILIARITY_ASSERTED.strip())
    out.append("")
    out.append("-" * 100)
    out.append("THE POLARITY READING (says_detail, says_time, says_skill, says_concept)")
    out.append("-" * 100)
    out.append("Each of these four flags records a topic, whatever the writer said about it. A")
    out.append("separate polarity column beside each flag records whether the matched phrase was")
    out.append("claimed or denied: 'negated' if a negating word or a quantifier negation from the")
    out.append("two lists under THE NEGATION WINDOW above sits in the same clause-cut window")
    out.append("before the phrase or begins the phrase itself; 'asserted' otherwise; 'neither'")
    out.append("when the flag is false. The quantifier negations deny an amount rather than a")
    out.append("fact, which is why they are kept apart from the negating words and are not used")
    out.append("for prior-exposure talk.")
    out.append("")
    out.append("-" * 100)
    out.append("THE MACHINE-MADE READING (machine_made_reading, beside says_machine_made)")
    out.append("-" * 100)
    out.append("says_machine_made records a phrase about a machine making the work, however it is")
    out.append("used. machine_made_reading reads every such phrase in the response, outside the")
    out.append("rule's exclusions. A phrase is not asserted if a negating word from the first list")
    out.append("under THE NEGATION WINDOW sits inside it or in the same clause-cut window before it,")
    out.append("or if a word that opens a supposition, from the list below, sits in that window;")
    out.append("otherwise it is asserted, hedged impressions ('probably AI', 'looks AI generated')")
    out.append("included. The response is 'asserted' if any of its phrases is asserted,")
    out.append("'not_asserted' if it has phrases and none is asserted, and 'neither' exactly when")
    out.append("says_machine_made is false.")
    out.append("")
    out.append("Words that open a supposition ('as if' does not count):")
    for line in CONDITIONAL_MARKER.strip().splitlines():
        out.append("    " + line.strip())
    out.append("")
    out.append("-" * 100)
    out.append("THE FUNCTION-WORD IGNORE LIST (used only in sections 8 to 11)")
    out.append("-" * 100)
    out.append("Function words only. It contains no content words, and in particular it does not")
    out.append("contain 'detail', 'take', 'many', 'much', 'show', 'made' or 'part', all of which")
    out.append("appear in scikit-learn's built-in English stop list and would be deleted by it.")
    out.append(textwrap.fill(" ".join(FUNCTION_WORDS), width=96,
                             initial_indent="    ", subsequent_indent="    "))
    out.append("")
    return "\n".join(out)


def format_grounding(rules, study):
    """Return the grounding note of every rule in `rules`, ready to save."""
    out = []
    out.append("=" * 100)
    out.append("%s TEXT MEASURES: WHAT EACH RULE IS GROUNDED IN" % study.upper())
    out.append("=" * 100)
    out.append("")
    out.append("One note per rule, naming the construct the rule measures, the reading of effort or")
    out.append("creativity it stands for, the literature that reading comes from, and what the rule")
    out.append("does and does not record. The notes are not part of the patterns: the patterns are in")
    out.append("text_rules.txt, and its checksum covers that file alone.")
    out.append("")
    for i, rule in enumerate(rules, start=1):
        out.append("-" * 100)
        out.append("RULE %d OF %d: %s" % (i, len(rules), rule["name"]))
        out.append("-" * 100)
        out.append("In plain words: " + rule["plain"])
        out.append("")
        out.append(textwrap.fill(rule["grounding"], width=96))
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Matching.
#
# find_match() returns the first phrase that matches a rule's include pattern
# and does not sit inside a phrase its exclude pattern matched, with its start
# and end positions in the lower-cased text, or None. all_matches() returns
# every such phrase, in order.
# ---------------------------------------------------------------------------
def compile_rule(rule):
    """A rule's include and exclude patterns, compiled once."""
    inc = re.compile(rule["include"])
    exc = re.compile(rule["exclude"]) if rule["exclude"].strip() else None
    return inc, exc


NEG_RE = re.compile(NEGATION_PATTERN)
QUANT_NEG_RE = re.compile(QUANTIFIER_NEGATION)
SELF_NEG_RE = re.compile(SELF_NEGATING)
FAMILIARITY_ASSERTED_RE = re.compile(FAMILIARITY_ASSERTED)
CLAUSE_RE = re.compile(CLAUSE_BOUNDARY)
LITTLE_AS_SIZE_RE = re.compile(LITTLE_AS_SIZE)
CONDITIONAL_RE = re.compile(CONDITIONAL_MARKER)


def find_match(text, include_re, exclude_re):
    """First matching phrase that is not inside an excluded phrase.

    Returns (phrase, start, end) or None. Positions are into the lower-cased
    text, which is what the patterns are written against.
    """
    blocked = [m.span() for m in exclude_re.finditer(text)] if exclude_re is not None else []
    for m in include_re.finditer(text):
        start, end = m.span()
        if any(start >= b0 and end <= b1 for b0, b1 in blocked):
            continue
        return (m.group(0), start, end)
    return None


def all_matches(text, include_re, exclude_re):
    """Every matching phrase that is not inside an excluded phrase, in order.
    The first of them is the phrase find_match() returns."""
    blocked = [m.span() for m in exclude_re.finditer(text)] if exclude_re is not None else []
    found = []
    for m in include_re.finditer(text):
        start, end = m.span()
        if any(start >= b0 and end <= b1 for b0, b1 in blocked):
            continue
        found.append((m.group(0), start, end))
    return found


# ---------------------------------------------------------------------------
# Reading a matched phrase as claimed or denied.
#
# The window before a phrase is NEGATION_WINDOW characters long and is cut
# back to the start of the clause the phrase sits in.
# ---------------------------------------------------------------------------
def clause_window_start(text, start):
    """Where the window before a phrase that begins at position `start` starts:
    NEGATION_WINDOW characters back, moved forward to just after the last
    clause boundary in that stretch."""
    lo = max(0, start - NEGATION_WINDOW)
    boundaries = [m.end() for m in CLAUSE_RE.finditer(text[lo:start])]
    return lo + (boundaries[-1] if boundaries else 0)


def clause_window(text, start):
    """The stretch of text searched for a negating word before a phrase that
    begins at position `start`."""
    return text[clause_window_start(text, start):start]


def classify_prior_exposure(text, match):
    """asserted, negated or neither, for the prior-exposure phrase `match`.

    No phrase gives neither. "Nothing new" and "not new" give asserted. A
    negating word in the window or inside the phrase, or a phrase that negates
    itself, gives negated. Every other phrase gives asserted. The quantity
    words are not consulted.
    """
    if match is None:
        return "neither"
    phrase, start, _end = match
    if FAMILIARITY_ASSERTED_RE.match(phrase):
        return "asserted"
    window = clause_window(text, start)
    if SELF_NEG_RE.match(phrase) or NEG_RE.search(phrase) or NEG_RE.search(window):
        return "negated"
    return "asserted"


def quantifier_denies(text, position, word, little_as_size=True):
    """Whether the quantity word `word`, found at `position` in `text`, denies
    an amount. Every quantity word does, except "little" used for a size.
    little_as_size=False reads every "little" as a denial."""
    if word != "little" or not little_as_size:
        return True
    return LITTLE_AS_SIZE_RE.search(text[:position]) is None


def classify_polarity(text, match, little_as_size=True):
    """asserted, negated or neither, for the detail, time, skill or concept
    phrase `match`.

    No phrase gives neither. A negating word in the window, or one that begins
    the phrase, gives negated. A quantity word that denies an amount, in the
    window or at the start of the phrase, gives negated. Every other phrase
    gives asserted.
    """
    if match is None:
        return "neither"
    phrase, start, _end = match
    window_start = clause_window_start(text, start)
    window = text[window_start:start]
    if NEG_RE.search(window) or NEG_RE.match(phrase):
        return "negated"
    for found in QUANT_NEG_RE.finditer(window):
        if quantifier_denies(text, window_start + found.start(), found.group(0), little_as_size):
            return "negated"
    found = QUANT_NEG_RE.match(phrase)
    if found and quantifier_denies(text, start, found.group(0), little_as_size):
        return "negated"
    return "asserted"


def read_machine_phrase(text, phrase, start):
    """asserted or not_asserted, for one machine-making phrase.

    A negating word inside the phrase or in the window before it gives
    not_asserted. So does a supposition word that starts inside the window.
    The supposition words are searched for in the whole text, so that the "as
    if" exception sees an "as" just outside the window. Every other phrase,
    hedged impressions included, gives asserted.
    """
    window_start = clause_window_start(text, start)
    if NEG_RE.search(phrase) or NEG_RE.search(text[window_start:start]):
        return "not_asserted"
    if any(window_start <= found.start() < start for found in CONDITIONAL_RE.finditer(text)):
        return "not_asserted"
    return "asserted"


def classify_machine_made(text, matches):
    """The response's reading and the phrase that decided it: the first
    asserted phrase if there is one, otherwise the first phrase found."""
    if not matches:
        return "neither", None
    for phrase, start, end in matches:
        if read_machine_phrase(text, phrase, start) == "asserted":
            return "asserted", (phrase, start, end)
    return "not_asserted", matches[0]


# The four flags that carry a polarity column, in the order of the export.
POLARITY_COLUMNS = {
    "says_detail":  "detail_polarity",
    "says_time":    "time_polarity",
    "says_skill":   "skill_polarity",
    "says_concept": "concept_polarity",
}


# ---------------------------------------------------------------------------
# Applying the rules.
#
# apply_rules() returns a frame with one row per response, holding the blind
# frame's columns, the flags, prior_exposure, the four polarity columns,
# machine_made_reading and n_words (the number of whitespace-separated words).
# It also returns the matched phrase with its position, for every rule and
# response, under the rule's name. Under the key machine_made_reading it keeps
# the phrase that decided each reading.
# ---------------------------------------------------------------------------
def apply_rules(blind, rules=None):
    """Apply `rules` (by default RULES) to the blind frame."""
    check_blind(blind)
    rules = RULES if rules is None else rules
    lower_text = lower_texts(blind)
    compiled = {rule["name"]: compile_rule(rule) for rule in rules}
    spans = {}
    for rule in rules:
        inc, exc = compiled[rule["name"]]
        spans[rule["name"]] = [find_match(t, inc, exc) for t in lower_text]

    frame = blind.copy()

    # the true/false flags
    for rule in rules:
        if rule["name"] == "prior_exposure":
            continue
        frame[rule["name"]] = [m is not None for m in spans[rule["name"]]]

    # the three-valued familiarity measure
    frame["prior_exposure"] = [
        classify_prior_exposure(t, m)
        for t, m in zip(lower_text, spans["prior_exposure"])
    ]

    # the four polarity columns, each "neither" exactly when its flag is false
    for flag, column in POLARITY_COLUMNS.items():
        frame[column] = [classify_polarity(t, m) for t, m in zip(lower_text, spans[flag])]
        assert ((frame[column] == "neither") == ~frame[flag]).all(), (
            "%s is 'neither' on a response where %s is true, or the reverse." % (column, flag))

    # the machine-made reading, "neither" exactly when its flag is false
    if "says_machine_made" in compiled:
        inc, exc = compiled["says_machine_made"]
        readings = [classify_machine_made(t, all_matches(t, inc, exc)) for t in lower_text]
        frame["machine_made_reading"] = [reading for reading, _ in readings]
        spans["machine_made_reading"] = [span for _, span in readings]
        assert ((frame["machine_made_reading"] == "neither") == ~frame["says_machine_made"]).all(), (
            "machine_made_reading is 'neither' on a response where says_machine_made is true, "
            "or the reverse.")

    frame["n_words"] = blind["response_text"].fillna("").astype(str).str.split().str.len()
    return frame, spans


# ---------------------------------------------------------------------------
# Constructed sentences.
#
# Sentences written for this check, not taken from any corpus, each with the
# reading the rules give it. check_constructed_sentences() runs them through
# the compiled rules and the reading functions and stops if any is read
# otherwise. The first group covers the machine-made reading; the second
# covers the size reading of "little" in detail talk.
# ---------------------------------------------------------------------------
MACHINE_PROBES = [
    ("This does not look AI generated.", "not_asserted"),
    ("AI didn't make this.", "not_asserted"),
    ("If this were AI generated, it would be less creative.", "not_asserted"),
    ("I wonder whether AI made this.", "not_asserted"),
    ("It looks AI generated.", "asserted"),
    ("This was probably made by AI.", "asserted"),
    ("It looks as if a computer made it.", "asserted"),
]
DETAIL_PROBES = [
    ("The little details are extraordinary.", "asserted"),
    ("There are a lot of small little details.", "asserted"),
    ("It has a little detail in the corner.", "asserted"),
    ("There is very little detail.", "negated"),
    ("Too little detail for a painting.", "negated"),
    ("Little to no detail anywhere.", "negated"),
]


def _rule(name):
    return next(r for r in RULES if r["name"] == name)


def check_constructed_sentences():
    """Read every constructed sentence and return (column, reading, sentence)
    rows. Stops if a sentence is read otherwise than the rules say."""
    machine_inc, machine_exc = compile_rule(_rule("says_machine_made"))
    detail_inc, detail_exc = compile_rule(_rule("says_detail"))
    rows = []
    for sentence, expected in MACHINE_PROBES:
        probe = sentence.lower()
        reading, _span = classify_machine_made(probe, all_matches(probe, machine_inc, machine_exc))
        assert reading == expected, "%r is read as %s; the rules say %s." % (sentence, reading, expected)
        rows.append(("machine_made_reading", reading, sentence))
    for sentence, expected in DETAIL_PROBES:
        probe = sentence.lower()
        polarity = classify_polarity(probe, find_match(probe, detail_inc, detail_exc))
        assert polarity == expected, "%r is read as %s; the rules say %s." % (sentence, polarity, expected)
        rows.append(("detail_polarity", polarity, sentence))
    return rows


# ---------------------------------------------------------------------------
# Export 1: the measures file.
#
# One row per response. The columns are the blind frame's columns other than
# response_text, in their order, then MEASURE_COLUMNS. For Study 1 that is the
# nineteen columns of study1_text_measures.csv.
# ---------------------------------------------------------------------------
MEASURE_COLUMNS = [
    "n_words",
    "says_detail", "says_time", "says_skill", "says_concept", "says_prompt", "says_machine_made",
    "machine_made_reading",
    "prior_exposure", "anchor_echo",
    "detail_polarity", "time_polarity", "skill_polarity", "concept_polarity",
]
TRUE_FALSE_FLAGS = ["says_detail", "says_time", "says_skill", "says_concept", "says_prompt",
                    "says_machine_made", "anchor_echo"]
THREE_VALUES = {"asserted", "negated", "neither"}
READING_VALUES = {"asserted", "not_asserted", "neither"}


def export_columns(blind):
    """The columns of the measures file, in order, for this blind frame."""
    check_blind(blind)
    return [c for c in blind.columns if c != "response_text"] + MEASURE_COLUMNS


def check_measures(frame, blind, label="measures file"):
    """Every check the measures file passes before it is written."""
    check_blind(blind)
    assert list(frame.columns) == export_columns(blind), \
        "%s: export columns are wrong: %s" % (label, list(frame.columns))
    assert len(frame) == len(blind), \
        "%s: expected %d rows, found %d." % (label, len(blind), len(frame))
    check_output(frame, label)
    assert set(frame["prior_exposure"]) <= THREE_VALUES, \
        "%s: prior_exposure has an unexpected value." % label
    for flag in TRUE_FALSE_FLAGS:
        assert frame[flag].dtype == bool, "%s: %s should be true/false." % (label, flag)
    for flag, column in POLARITY_COLUMNS.items():
        assert set(frame[column]) <= THREE_VALUES, \
            "%s: %s has an unexpected value." % (label, column)
        assert ((frame[column] == "neither") == ~frame[flag]).all(), \
            "%s: %s must be 'neither' exactly when %s is false." % (label, column, flag)
    assert set(frame["machine_made_reading"]) <= READING_VALUES, \
        "%s: machine_made_reading has an unexpected value." % label
    assert ((frame["machine_made_reading"] == "neither") == ~frame["says_machine_made"]).all(), \
        "%s: machine_made_reading must be 'neither' exactly when says_machine_made is false." % label
    assert frame.duplicated(KEY).sum() == 0, \
        "%s: the export has duplicated participant/stimulus/question rows." % label
    return frame


def measures_frame(blind):
    """The measures file: identifiers, word count, eight measures, the
    machine-made reading and the four polarity columns."""
    measures, _spans = apply_rules(blind)
    export = measures[export_columns(blind)].copy()
    return check_measures(export, blind)


# ---------------------------------------------------------------------------
# Exports 2 and 3: the word-count table and its vocabulary.
#
# The vocabulary is every content word that appears in at least
# WORDCOUNT_MIN_RESPONSES (two) responses, with the number of responses it
# appears in, sorted by that number (largest first) and then by the word. The
# word-count table has one row per response and vocabulary word with a
# positive count, in the order of the blind frame and then of the word. A
# response with no vocabulary word has no row.
# ---------------------------------------------------------------------------
WORDCOUNT_MIN_RESPONSES = 2
WORDCOUNT_COLUMNS = ["id", "stimulus_id", "dimension", "word", "count"]
VOCABULARY_COLUMNS = ["word", "n_responses"]


def _response_tokens(blind):
    return [tokenize(t) for t in response_texts(blind)]


def _vocabulary(response_tokens):
    responses_per_word = Counter(w for tokens in response_tokens for w in set(tokens))
    vocabulary = pd.DataFrame(
        sorted(((w, n) for w, n in responses_per_word.items() if n >= WORDCOUNT_MIN_RESPONSES),
               key=lambda pair: (-pair[1], pair[0])),
        columns=VOCABULARY_COLUMNS,
    )
    return vocabulary


def vocabulary_frame(blind):
    """The vocabulary file: each kept word and the number of responses it appears in."""
    check_blind(blind)
    vocabulary = _vocabulary(_response_tokens(blind))
    check_output(vocabulary, "vocabulary file")
    assert list(vocabulary.columns) == VOCABULARY_COLUMNS
    assert (vocabulary["n_responses"] >= WORDCOUNT_MIN_RESPONSES).all(), \
        "A word appearing in too few responses reached the vocabulary."
    return vocabulary


def wordcounts_frame(blind):
    """The word-count file: one row per response and vocabulary word, with its count."""
    check_blind(blind)
    response_tokens = _response_tokens(blind)
    vocabulary = _vocabulary(response_tokens)
    kept = set(vocabulary["word"])
    rows = []
    for (rid, sid, dim), tokens in zip(blind[KEY].itertuples(index=False), response_tokens):
        counts = Counter(w for w in tokens if w in kept)
        for word, count in sorted(counts.items()):
            rows.append((rid, sid, dim, word, count))
    wordcounts = pd.DataFrame(rows, columns=WORDCOUNT_COLUMNS)

    check_output(wordcounts, "word-count file")
    assert list(wordcounts.columns) == WORDCOUNT_COLUMNS
    assert (wordcounts["count"] > 0).all(), "Every row of the word-count table must have a positive count."
    assert set(wordcounts["word"]) <= kept, "A word outside the vocabulary reached the word-count table."
    assert wordcounts.duplicated(KEY + ["word"]).sum() == 0, \
        "The word-count table has more than one row for the same response and word."
    recount = wordcounts.groupby("word").size().reindex(vocabulary["word"])
    assert (recount.values == vocabulary["n_responses"].values).all(), \
        "The word-count table and the vocabulary disagree about how many responses a word appears in."
    return wordcounts


# ---------------------------------------------------------------------------
# Export 4: the content-word lists.
#
# One row per response: its distinct content words from tokenize(), sorted and
# joined with single spaces, or an empty string when it has none.
# ---------------------------------------------------------------------------
TOKENS_COLUMNS = ["id", "stimulus_id", "dimension", "content_words"]


def tokens_frame(blind):
    """The content-word file: each response's distinct content words, sorted."""
    check_blind(blind)
    response_tokens = _response_tokens(blind)
    frame = pd.DataFrame({
        "id": blind["id"].values,
        "stimulus_id": blind["stimulus_id"].values,
        "dimension": blind["dimension"].values,
        "content_words": [" ".join(sorted(set(tokens))) for tokens in response_tokens],
    }, columns=TOKENS_COLUMNS)

    check_output(frame, "content-word file")
    assert len(frame) == len(blind), "Expected one row per response, found %d rows." % len(frame)
    assert frame.duplicated(KEY).sum() == 0, \
        "The content-word table has more than one row for the same response."
    for words in frame["content_words"]:
        listed = words.split()
        assert listed == sorted(set(listed)), "A word list is not sorted, or repeats a word."
        assert not set(listed) & IGNORE, "A function word reached the content-word lists."
        assert words == words.lower(), "A word list is not in lower case."
    return frame


# ---------------------------------------------------------------------------
# Export 5: affect and concreteness.
#
# Warriner, Kuperman and Brysbaert (2013) give 13,915 English words a mean
# rating from 1 to 9 of valence (how pleasant the word is), arousal (how calm
# or excited it makes a reader feel) and dominance (how much in control it
# makes a reader feel), in the columns V.Mean.Sum, A.Mean.Sum and D.Mean.Sum.
# Brysbaert, Warriner and Kuperman (2014) give about 40,000 English words a
# mean rating of concreteness from 1 (abstract) to 5 (concrete), in the column
# Conc.M. Both files are read with keep_default_na=False, because each holds
# the word "null". Where two entries share a lower-case form, the entry spelled
# in lower case is kept. The returned frame carries, in its attrs dictionary
# (notes that pandas keeps with a frame and does not write to the CSV), the
# entry "unmatched_vad_words": a count of the words found in neither form in
# the valence norms.
#
# A response's words are its tokens with the task vocabulary removed, every
# occurrence counted. A word is looked up as written; if it is not found, one
# final "ing", "ed", "es" or "s" is stripped, in that order, and the first
# shortened form of at least two letters found in the norms is used. A score is
# the mean over the matched occurrences, rounded to four decimals. A response
# with no matched word gets an empty score, not a zero.
# ---------------------------------------------------------------------------
VAD_FILE = "Warriner_et_al_2013_VAD.csv"
CONCRETENESS_FILE = "Concreteness_ratings_Brysbaert_et_al_BRM.txt"
VAD_COLUMNS = ["V.Mean.Sum", "A.Mean.Sum", "D.Mean.Sum"]
NORM_ENDINGS = ["ing", "ed", "es", "s"]
AFFECT_COLUMNS = ["id", "stimulus_id", "dimension", "n_content_words", "n_vad_matched",
                  "valence", "arousal", "dominance", "n_conc_matched", "concreteness"]
_NORMS_CACHE = {}


def read_norms(path, sep, columns):
    """One norm file as a dictionary from lower-case word to its scores."""
    table = pd.read_csv(path, sep=sep, usecols=["Word"] + columns, keep_default_na=False)
    table["spelled"] = table["Word"].astype(str).str.strip()
    table["lower"] = table["spelled"].str.lower()
    table["spelled_lower"] = table["spelled"] == table["lower"]
    table = (table.sort_values("spelled_lower", ascending=False, kind="stable")
                  .drop_duplicates("lower", keep="first"))
    scores = table[columns].apply(pd.to_numeric, errors="raise")
    return dict(zip(table["lower"], scores.itertuples(index=False, name=None)))


def load_norms(folder=None):
    """The valence, arousal and dominance norms and the concreteness norms."""
    folder = norms_dir() if folder is None else folder
    if folder not in _NORMS_CACHE:
        vad_path = os.path.join(folder, VAD_FILE)
        concreteness_path = os.path.join(folder, CONCRETENESS_FILE)
        for path in [vad_path, concreteness_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(
                    "A word-norm file is missing: %s. Study 1/nlp/norms/README.md says where "
                    "each file comes from; set %s to the folder that holds both."
                    % (display_path(path), NORMS_DIR_VARIABLE))
        _NORMS_CACHE[folder] = (read_norms(vad_path, ",", VAD_COLUMNS),
                                read_norms(concreteness_path, "\t", ["Conc.M"]))
    return _NORMS_CACHE[folder]


def norm_entry(word, norms):
    """The norm entry for `word`, or for `word` with one ending stripped, or None."""
    if word in norms:
        return norms[word]
    for ending in NORM_ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= 2:
            shorter = word[:-len(ending)]
            if shorter in norms:
                return norms[shorter]
    return None


def mean_or_empty(values):
    return round(float(np.mean(values)), 4) if values else np.nan


def affect_frame(blind, norms_folder=None):
    """The affect file: one row per response, with its affect and concreteness scores."""
    check_blind(blind)
    vad_norms, concreteness_norms = load_norms(norms_folder)
    rows = []
    unmatched_vad = Counter()
    for (rid, sid, dim), tokens in zip(blind[KEY].itertuples(index=False), _response_tokens(blind)):
        words = [w for w in tokens if not is_task_vocabulary(w)]
        vad = [norm_entry(w, vad_norms) for w in words]
        unmatched_vad.update(w for w, entry in zip(words, vad) if entry is None)
        vad = [entry for entry in vad if entry is not None]
        concreteness = [entry[0] for entry in (norm_entry(w, concreteness_norms) for w in words)
                        if entry is not None]
        rows.append(dict(
            id=rid, stimulus_id=sid, dimension=dim, n_content_words=len(words),
            n_vad_matched=len(vad),
            valence=mean_or_empty([v[0] for v in vad]),
            arousal=mean_or_empty([v[1] for v in vad]),
            dominance=mean_or_empty([v[2] for v in vad]),
            n_conc_matched=len(concreteness),
            concreteness=mean_or_empty(concreteness),
        ))
    affect = pd.DataFrame(rows, columns=AFFECT_COLUMNS)

    check_output(affect, "affect file")
    assert len(affect) == len(blind), "Expected one row per response, found %d rows." % len(affect)
    assert affect.duplicated(KEY).sum() == 0, "The affect table has more than one row for the same response."
    assert (affect["n_vad_matched"] <= affect["n_content_words"]).all()
    assert (affect["n_conc_matched"] <= affect["n_content_words"]).all()
    assert (affect["valence"].isna() == (affect["n_vad_matched"] == 0)).all(), \
        "A valence score is empty where words matched, or present where none did."
    assert (affect["concreteness"].isna() == (affect["n_conc_matched"] == 0)).all(), \
        "A concreteness score is empty where words matched, or present where none did."
    for column, low, high in [("valence", 1, 9), ("arousal", 1, 9), ("dominance", 1, 9),
                              ("concreteness", 1, 5)]:
        assert affect[column].dropna().between(low, high).all(), \
            "%s fell outside %d to %d." % (column, low, high)
    affect.attrs["unmatched_vad_words"] = unmatched_vad
    return affect


# ---------------------------------------------------------------------------
# Exports 6 to 8: topics.
#
# A topic model finds groups of words that tend to occur in the same
# responses. The model here is non-negative matrix factorisation (NMF), fitted
# separately to each question. Each response becomes a row of tf-idf weights
# (a word's count in the response, multiplied by a factor that grows the fewer
# responses the word appears in) over the content words, task vocabulary
# removed, that appear in at least TOPIC_MIN_DF (five) responses to that
# question. scikit-learn's TfidfVectorizer computes the weights with its
# defaults, which scale each row to length one. NMF (at most 1,000
# iterations) writes the response-by-word table as the product of a
# response-by-topic table W and a topic-by-word table H, both non-negative.
# Its starting values, the setting "nndsvda", are computed from the data by a
# singular value decomposition (a standard way of breaking a table into its
# main directions) rather than drawn at random.
#
# The number of topics, k. For each k from 3 to 10 the model is refitted ten
# times, with the seeds 0 to 9 (a seed is the number that starts a random
# number generator, so that the same seed gives the same draws). Each seed
# draws a random 80 per cent of the participants, and the refit uses their
# responses over the whole question's vocabulary. Refits on identical data
# would come back nearly identical at every k, because the starting values are
# computed from the data; leaving a fifth of the participants out is what lets
# them differ. The topics of two refits are paired one to one by the Hungarian
# algorithm (scipy's linear_sum_assignment, which finds the pairing with the
# largest total similarity), and their agreement is the mean cosine similarity
# (1 when two topics weight the same words in the same proportions, 0 when
# they share no word) over the pairs. Stability at k is the mean agreement over
# all 45 pairs of refits, with its standard deviation. The k with the highest
# stability, rounded to three decimals, is chosen; a tie goes to the smaller k.
#
# The final model is fitted once, at the chosen k, to every response to the
# question, with the seed 20260421. Topics are numbered from 1 in order of
# their mean weight, largest first. A response's weights are its row of W
# divided by the row's sum. A response with no kept word, or with no weight on
# any topic, gets empty weights.
#
# The questions are taken in sorted order of the dimension column. fit_topics()
# keeps one fit per blind frame, so the export functions below share it.
#
# The seeds above are Study 1's, and they are the defaults. A study whose
# registration names its own seed for the text code calls set_text_seed()
# before the first fit. The ten refits then use that seed and the nine numbers
# after it, and the final fit and the k-means grouping of the agreement check
# use the seed itself.
# ---------------------------------------------------------------------------
TOPIC_MIN_DF = 5
TOPIC_K_RANGE = range(3, 11)
TOPIC_SEEDS = 10
TOPIC_STABILITY_SEED_BASE = 0
TOPIC_SHARE_KEPT = 0.8
TOPIC_MAX_ITER = 1000
TOPIC_FINAL_SEED = 20260421
TOPIC_TOP_WORDS = 10
TOPICS_COLUMNS = ["id", "stimulus_id", "dimension", "topic", "weight"]
TOP_WORDS_COLUMNS = ["dimension", "topic", "rank", "word", "weight"]
STABILITY_COLUMNS = ["dimension", "k", "stability_mean", "stability_sd", "chosen"]
_TOPIC_CACHE = {}


def topic_words(text):
    """Content words for the topic model: tokenize() without the task vocabulary."""
    return [w for w in tokenize(text) if not is_task_vocabulary(w)]


def unit_rows(matrix):
    """Each row divided by its length, so that the product of two rows is their cosine."""
    lengths = np.linalg.norm(matrix, axis=1, keepdims=True)
    lengths[lengths == 0] = 1.0
    return matrix / lengths


def topic_agreement(topics_a, topics_b):
    """Mean cosine similarity of two sets of topics, paired one to one by the
    Hungarian algorithm so that the total similarity of the pairs is as large
    as it can be."""
    similarity = unit_rows(topics_a) @ unit_rows(topics_b).T
    rows, cols = linear_sum_assignment(-similarity)
    return float(similarity[rows, cols].mean())


def fit_nmf(matrix, k, seed):
    """One NMF fit, and whether it finished inside the iteration limit."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        model = NMF(n_components=k, init="nndsvda", max_iter=TOPIC_MAX_ITER, random_state=seed)
        weights = model.fit_transform(matrix)
    converged = not any(issubclass(w.category, ConvergenceWarning) for w in caught)
    return model, weights, converged


def frame_fingerprint(blind):
    """SHA-256 of the blind frame's column names and contents, written out as
    CSV. fit_topics() keys its stored fits by it, so that the export functions
    below share one fit of the same frame."""
    check_blind(blind)
    digest = hashlib.sha256()
    digest.update("|".join(map(str, blind.columns)).encode("utf-8"))
    digest.update(blind.to_csv(index=False).encode("utf-8"))
    return digest.hexdigest()


def fit_topics(blind):
    """Fit the topic model to every question and return the fit.

    The result holds the three export frames under "topics", "top_words" and
    "stability", and, under "by_dimension", each question's chosen k, its
    texts, which responses have weights, the weights, the vocabulary size, the
    number of refits that reached the iteration limit and whether the final
    fit settled.
    """
    check_blind(blind)
    fingerprint = frame_fingerprint(blind)
    if fingerprint in _TOPIC_CACHE:
        return _TOPIC_CACHE[fingerprint]

    texts_all = response_texts(blind)
    stability_rows, top_word_rows, topic_rows = [], [], []
    by_dimension = {}

    for dim in sorted(blind["dimension"].unique()):
        rows_of_dim = np.where((blind["dimension"] == dim).values)[0]
        texts = [texts_all[i] for i in rows_of_dim]
        vectorizer = TfidfVectorizer(analyzer=topic_words, min_df=TOPIC_MIN_DF)
        matrix = vectorizer.fit_transform(texts)
        vocab = vectorizer.get_feature_names_out()
        person = blind["id"].values[rows_of_dim]
        people = np.array(sorted(set(person)))
        n_kept = int(round(TOPIC_SHARE_KEPT * len(people)))

        # the stability of every k, from ten refits on 80 per cent of the participants
        results, n_short = [], 0
        for k in TOPIC_K_RANGE:
            topic_sets = []
            for seed in range(TOPIC_STABILITY_SEED_BASE, TOPIC_STABILITY_SEED_BASE + TOPIC_SEEDS):
                kept = np.random.default_rng(seed).choice(people, size=n_kept, replace=False)
                model, _, converged = fit_nmf(matrix[np.isin(person, kept)], k, seed)
                topic_sets.append(model.components_)
                n_short += int(not converged)
            agreements = [topic_agreement(a, b) for a, b in combinations(topic_sets, 2)]
            results.append((k, float(np.mean(agreements)), float(np.std(agreements, ddof=1))))
        chosen_k = max(results, key=lambda r: (round(r[1], 3), -r[0]))[0]
        for k, mean, sd in results:
            stability_rows.append(dict(dimension=dim, k=k, stability_mean=round(mean, 4),
                                       stability_sd=round(sd, 4), chosen=bool(k == chosen_k)))

        # the final model, at the chosen k, on every response to the question
        model, weights, final_converged = fit_nmf(matrix, chosen_k, TOPIC_FINAL_SEED)
        sums = weights.sum(axis=1)
        has_weight = sums > 0
        shares = np.full(weights.shape, np.nan)
        shares[has_weight] = weights[has_weight] / sums[has_weight, None]
        order = np.argsort(-np.nanmean(shares, axis=0), kind="stable")
        shares, components = shares[:, order], model.components_[order]

        for t in range(chosen_k):
            top = np.argsort(-components[t], kind="stable")[:TOPIC_TOP_WORDS]
            for rank, j in enumerate(top, start=1):
                top_word_rows.append(dict(dimension=dim, topic=t + 1, rank=rank, word=vocab[j],
                                          weight=round(float(components[t, j]), 4)))
        for position, i in enumerate(rows_of_dim):
            for t in range(chosen_k):
                topic_rows.append(dict(
                    id=blind["id"].iloc[i], stimulus_id=blind["stimulus_id"].iloc[i], dimension=dim,
                    topic=t + 1,
                    weight=round(float(shares[position, t]), 4) if has_weight[position] else np.nan))

        by_dimension[dim] = dict(k=chosen_k, texts=texts, has_weight=has_weight, shares=shares,
                                 n_vocab=len(vocab), n_short=n_short,
                                 n_refits=TOPIC_SEEDS * len(TOPIC_K_RANGE),
                                 final_converged=final_converged)

    topics_long = pd.DataFrame(topic_rows, columns=TOPICS_COLUMNS)
    top_words = pd.DataFrame(top_word_rows, columns=TOP_WORDS_COLUMNS)
    stability = pd.DataFrame(stability_rows, columns=STABILITY_COLUMNS)

    check_output(topics_long, "topics file")
    rows_per_response = topics_long.groupby(KEY).size()
    assert len(rows_per_response) == len(blind), "Not every response has topic rows."
    for dim, fitted in by_dimension.items():
        assert (rows_per_response.xs(dim, level="dimension") == fitted["k"]).all(), \
            "A %s response does not have exactly one row per topic." % dim
    assert topics_long["weight"].dropna().between(0, 1).all(), "A topic weight fell outside 0 to 1."
    weight_sums = topics_long.groupby(KEY)["weight"].sum(min_count=1).dropna()
    assert ((weight_sums - 1).abs() < 1e-3).all(), "A response's topic weights do not sum to one."
    assert (stability.groupby("dimension")["chosen"].sum() == 1).all(), "Each question needs one chosen k."

    fit = dict(topics=topics_long, top_words=top_words, stability=stability,
               by_dimension=by_dimension)
    _TOPIC_CACHE[fingerprint] = fit
    return fit


def topics_frame(blind):
    """The topics file: one row per response and topic, with the response's weight."""
    return fit_topics(blind)["topics"].copy()


def topic_top_words_frame(blind):
    """The ten words with the largest weight in every topic, for each question."""
    return fit_topics(blind)["top_words"].copy()


def topic_stability_frame(blind):
    """The stability of every k from 3 to 10, for each question, and the k chosen."""
    return fit_topics(blind)["stability"].copy()


# ---------------------------------------------------------------------------
# Export 9: the agreement check on the topics.
#
# Each response with topic weights is turned into a list of 768 numbers by the
# sentence-embedding model all-mpnet-base-v2, which places sentences of
# similar meaning near one another. It assigns no label and writes no text,
# and nothing it produces is kept beyond the agreement figure. The numbers are
# scaled to length one. The responses to each question are split into as many
# groups as that question has topics by k-means (scikit-learn's KMeans, seed
# 20260421 unless set_text_seed() names another, ten starting points, the
# best kept, run on one processor thread), which puts each response in
# the group whose centre it is nearest. The split is compared with each
# response's dominant topic (the topic with its largest weight) by the
# adjusted Rand index: the agreement between two groupings of the same items
# beyond what chance gives, 0 for chance agreement and 1 for identical
# groupings.
#
# The model is loaded only from a copy already on the machine. The
# environment variables HF_HUB_OFFLINE and TRANSFORMERS_OFFLINE are set to 1,
# which stops the Hugging Face libraries that load the model from reaching the
# internet, so nothing is downloaded. The model runs on the processor, so the
# numbers do not depend on a graphics card. If the package or the copy is
# missing, the agreement is left empty and the entry "embedding_status" in the
# frame's attrs dictionary says why.
# ---------------------------------------------------------------------------
EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_SEED = 20260421
# Multithreaded k-means adds partial sums in a varying order, so only one thread repeats exactly.
KMEANS_OPENMP_THREADS = 1
AGREEMENT_COLUMNS = ["dimension", "k", "ari"]
_EMBEDDER_CACHE = {}


def set_text_seed(seed):
    """Make `seed` the seed of every random step in the topic model and the
    agreement check.

    The ten stability refits use `seed` to `seed` + 9, and the final topic fit
    and the k-means grouping use `seed`. Fits already kept are dropped, so the
    next export refits with the new seeds. Returns the seeds now in force.
    """
    global TOPIC_STABILITY_SEED_BASE, TOPIC_FINAL_SEED, EMBEDDING_SEED
    seed = int(seed)
    TOPIC_STABILITY_SEED_BASE = seed
    TOPIC_FINAL_SEED = seed
    EMBEDDING_SEED = seed
    _TOPIC_CACHE.clear()
    return text_seeds()


def text_seeds():
    """The seeds in force: the first and last stability refit, the final topic
    fit and the k-means grouping."""
    return dict(stability_refits_first=TOPIC_STABILITY_SEED_BASE,
                stability_refits_last=TOPIC_STABILITY_SEED_BASE + TOPIC_SEEDS - 1,
                final_topic_fit=TOPIC_FINAL_SEED,
                kmeans_grouping=EMBEDDING_SEED)


def load_embedder(model_name=EMBEDDING_MODEL_NAME):
    """The sentence-embedding model, or None, and a note saying how it loaded."""
    if model_name not in _EMBEDDER_CACHE:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_name, device="cpu", local_files_only=True)
            status = "loaded from the local copy"
        except Exception as error:
            model = None
            message = str(error).strip()
            reason = message.splitlines()[0][:200] if message else ""
            reason = reason.replace(os.path.expanduser("~"), "~")
            status = "not run (%s: %s)" % (type(error).__name__, reason)
        _EMBEDDER_CACHE[model_name] = (model, status)
    return _EMBEDDER_CACHE[model_name]


def embedding_agreement_frame(blind):
    """The agreement check: for each question, the adjusted Rand index between
    each response's dominant topic and k-means groups of its sentence embedding."""
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score

    fit = fit_topics(blind)
    embedder, status = load_embedder()
    rows = []
    for dim, fitted in fit["by_dimension"].items():
        ari = np.nan
        if embedder is not None:
            has_weight = fitted["has_weight"]
            texts = [t for t, keep in zip(fitted["texts"], has_weight) if keep]
            vectors = embedder.encode(texts, batch_size=64, normalize_embeddings=True,
                                      show_progress_bar=False)
            with threadpool_limits(limits=KMEANS_OPENMP_THREADS, user_api="openmp"):
                groups = KMeans(n_clusters=fitted["k"], random_state=EMBEDDING_SEED,
                                n_init=10).fit_predict(vectors)
            dominant = np.argmax(fitted["shares"][has_weight], axis=1)
            ari = round(float(adjusted_rand_score(dominant, groups)), 4)
        rows.append(dict(dimension=dim, k=fitted["k"], ari=ari))
    frame = pd.DataFrame(rows, columns=AGREEMENT_COLUMNS)
    frame.attrs["embedding_status"] = status
    return frame


# ---------------------------------------------------------------------------
# Exports 10 to 12: the rules, their checksum and their grounding notes.
#
# rules_text() is the content of text_rules.txt. rules_checksum_text() is the
# line written to text_rules.sha256: the SHA-256 checksum of that content and
# the file name, in the format `shasum -a 256 -c` reads. grounding_text() is
# the content of text_rules_grounding.txt; it uses the study name only.
# ---------------------------------------------------------------------------
def sha256_text(text):
    """SHA-256 of a string's bytes in UTF-8, the standard encoding of text as bytes."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rules_text(blind, study):
    """The content of text_rules.txt, for the study named `study` (e.g. "Study 1")."""
    check_blind(blind)
    return format_rules(RULES, study=study, n_responses=len(blind)) + "\n"


def rules_checksum_text(blind, study):
    """The content of text_rules.sha256."""
    return "%s  text_rules.txt\n" % sha256_text(rules_text(blind, study))


def grounding_text(blind, study):
    """The content of text_rules_grounding.txt."""
    check_blind(blind)
    return format_grounding(RULES, study=study) + "\n"


# ---------------------------------------------------------------------------
# Writing files.
#
# A run identifier is the time the run started, in UTC (Coordinated Universal
# Time), followed by eight random characters, so that two runs started in the
# same second still differ. The writers put a file under a temporary name in
# the folder it belongs in, then rename it to its final name. A rename inside
# one folder happens completely or not at all. If the write fails, the
# temporary file is removed and the error is raised.
# ---------------------------------------------------------------------------
def new_run_id():
    """A run identifier: UTC start time and eight random characters."""
    return (datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            + "-" + uuid.uuid4().hex[:8])


def _atomic_write(path, write, run_id):
    temporary = "%s.tmp-%s" % (path, run_id or new_run_id())
    try:
        write(temporary)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.remove(temporary)
        raise
    return path


def write_text_atomic(path, content, run_id=None):
    """Write the string `content` to `path` through a temporary file and a rename."""
    def write(target):
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(content)
    return _atomic_write(path, write, run_id)


def write_csv_atomic(path, frame, run_id=None):
    """Write the data frame `frame` to `path` as CSV, through a temporary file and a rename."""
    return _atomic_write(path, lambda target: frame.to_csv(target, index=False), run_id)
