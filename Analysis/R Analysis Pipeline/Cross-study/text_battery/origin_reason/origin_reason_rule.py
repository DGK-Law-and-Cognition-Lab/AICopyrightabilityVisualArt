"""The origin-as-reason rule: does an explanation give how the work was made as a reason for its rating?

code(text, nlp, doc=None) -> {"origin_reason": bool, "direction": "lowers" | "raises" | "unclear" | "none"}

The definition is origin_reason_codebook.md. The rule:

1. finds the explanation's mentions of how a work was made: the shared word list says_prompt
   (prompting, generating, AI, a machine or program), and phrases of making by hand or by a person
   ("drew it", "drawn", "hand-drawn", "by hand", "made it himself");
2. drops a mention that sits in a concessive clause ("although it is AI, ...") or that only names
   the original a change is measured from ("different from the AI image");
3. counts a remaining mention as a reason when its sentence ties it to the rating, by a causal or
   conditional connective or by a judgment of creativity, effort or change, or when the
   explanation is short and the mention is its substance;
4. gives the direction from the judgment words of the sentence that holds the reason; when they
   lean neither way, a reason of AI making lowers the rating and a reason of making by hand raises
   it, so the rule never answers "unclear".

Adjusted on the development sample only (6 November 2026): a verdict that the work looks
machine-made counts as the judgment; making by hand includes "hand painted" and "made by a human";
the sentence before a mention may hold the judgment; "generates new perceptions" is not making;
"of AI art" is not a description of the original.

It reads only the text. Deterministic: the same text and the same spaCy model give the same code.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, os.pardir, os.pardir, os.pardir, "shared", "python")))
import study_text  # noqa: E402

SPACY_MODEL = "en_core_web_sm"
_PROMPT = study_text.compile_rule(study_text._rule("says_prompt"))
_HAND = re.compile(r"\b(?:drew|drawn|draws|drawing it|hand[- ]?drawn|hand[- ]?made|handmade|by hand|hand[- ]?painted|"
                   r"made by (?:a |an )?(?:human|person|someone|people|artist)|human[- ]made|by a human|"
                   r"(?:made|did|created|painted|drew) (?:it|this|them)? ?(?:him|her)self|"
                   r"(?:his|her) own (?:hands|skills?|drawing))\b")
_CONCESSIVE = re.compile(r"\b(?:although|though|even though|even if|despite|regardless of|while|whereas|even with)\b")
_CAUSAL = re.compile(r"\b(?:because|since|so|as|therefore|thus|hence|which|that is why|this is why|due to|given that|"
                     r"if|means|meaning|making|makes|made me|then|resulting)\b|,? ?so\b|\bcause\b")
_JUDGE = re.compile(r"\b(?:creativ\w*|effort\w*|transform\w*|essence|chang\w*|original\w*|skill\w*|work|thought|"
                    r"took|amount|simple|complex|"
                    r"time|easy|easier|hard|difficult|little|minimal|lazy|nothing|none|no|not|less|lack\w*|"
                    r"lot|lots|much|many|great|high|low|significant\w*|requir\w*|tak\w+|need\w*|involv\w*|"
                    r"contribut\w*|credit|deserv\w*|value|worth|real|genuine|copy|copied|own)\b")
_DESCRIBES_ORIGINAL = re.compile(
    r"\b(?:from|than|unlike|compared to|compared with|versus|vs\.?)\s+(?:the\s+|an?\s+|its\s+)?"
    r"(?:original\s+|first\s+)?(?:ai|a\.i\.|ai[- ]generated|ai[- ]made|generated|computer[- ]generated)"
    r"(?:'s)?\s*(?:\w+\s+){0,2}(?:image|work|piece|picture|art|artwork|version|one|style|original|output|creation)\b"
    r"|\b(?:original|first)\s*,?\s*(?:ai|ai[- ]generated|generated)\s+(?:image|work|piece|picture|art|artwork|version)\b")
_LOWER = re.compile(r"\b(?:no|not|n't|little|minimal|less|least|lack\w*|easy|easier|lazy|only|just|nothing|none|"
                    r"low|lower|barely|hardly|copy|copied|doesn't|didn't|wasn't|isn't|cannot|can't|without|"
                    r"zero|minimum|simple|simply|quick|quickly|dislike|decreas\w*|reduc\w*|fewer|easily|"
                    r"basic|generic|merely|same thing|anyone|anybody|still|missing|lacking)\b")
_RAISE = re.compile(r"\b(?:a lot|lots|much thought|great|significant\w*|high|more|many|hard|difficult|skill\w*|"
                    r"careful\w*|detailed|impressive|requires? (?:a lot|thought|skill|effort)|required|had to|"
                    r"extremely|very creative|moderate\w*|thought\w*|complicated|complex|effort into|put in)\b")
_WORD = re.compile(r"[A-Za-z']+")
# A verdict that the work looks, seems or is machine-made, said as the judgment itself.
_LOOKS_MADE = re.compile(r"\b(?:looks?|looked|seems?|seemed|feels?|felt|appears?|is|was|vibe of|giving)\b"
                         r"[^.;]{0,30}\b(?:ai|a\.i\.|computer|machine|generated|hand[- ]?(?:drawn|painted|made))\b")
# "generates new perceptions" and the like are not about making the work.
_GENERATE_OTHER = re.compile(r"\bgenerat\w*\s+(?:new\s+|a\s+)?(?:perception|meaning|feeling|idea|interest|emotion|curiosity)")


def load_model():
    import spacy
    return spacy.load(SPACY_MODEL)


def _mentions(low):
    blocked = [m.span() for m in _GENERATE_OTHER.finditer(low)]
    spans = [(m[1], m[2]) for m in study_text.all_matches(low, *_PROMPT)
             if not any(b0 <= m[1] < b1 for b0, b1 in blocked)]
    spans += [m.span() for m in _HAND.finditer(low)]
    return sorted(spans)


def _sentence_of(doc, start):
    for sent in doc.sents:
        if sent.start_char <= start < sent.end_char:
            return sent
    return doc[:]


def _in_concession(sent_low, rel):
    """A mention whose clause opens with a concessive word, and the sentence goes on past a comma."""
    before = sent_low[:rel]
    m = list(_CONCESSIVE.finditer(before))
    if not m:
        return False
    last = m[-1]
    between = before[last.end():]
    return "," not in between and ("," in sent_low[rel:] or " but " in sent_low[rel:] or ";" in sent_low[rel:])


def _describes_original(low, start, end):
    window = low[max(0, start - 30):min(len(low), end + 40)]
    return _DESCRIBES_ORIGINAL.search(window) is not None


def _direction(text_low, by_hand):
    """From the judgment words; with no lead either way, AI making lowers and making by hand raises."""
    lower = len(_LOWER.findall(text_low))
    raise_ = len(_RAISE.findall(text_low))
    if lower > raise_:
        return "lowers"
    if raise_ > lower:
        return "raises"
    return "raises" if by_hand else "lowers"


def code(text, nlp, doc=None):
    low = text.lower()
    mentions = _mentions(low)
    if not mentions:
        return {"origin_reason": False, "direction": "none"}
    doc = doc if doc is not None else nlp(text)
    n_words = len(_WORD.findall(text))
    for start, end in mentions:
        sent = _sentence_of(doc, start)
        s_low = sent.text.lower()
        rel = start - sent.start_char
        if _in_concession(s_low, rel):
            continue
        if _describes_original(low, start, end):
            continue
        sents = list(doc.sents)
        k = next((i for i, x in enumerate(sents) if x.start == sent.start), 0)
        before = sents[k - 1].text.lower() if k > 0 else ""
        linked = _CAUSAL.search(s_low) is not None and _JUDGE.search(s_low + " " + before) is not None
        short = n_words <= 15
        verdict = _LOOKS_MADE.search(s_low) is not None
        if linked or short or verdict or _JUDGE.search(s_low[max(0, rel - 60):rel + 80]):
            by_hand = _HAND.search(low[start:end + 1]) is not None
            return {"origin_reason": True, "direction": _direction(s_low if not short else low, by_hand)}
    return {"origin_reason": False, "direction": "none"}
