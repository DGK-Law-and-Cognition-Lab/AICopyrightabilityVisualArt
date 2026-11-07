"""The agency rule: who an explanation says made or changed the work.

flags(text, nlp) -> {"person_maker": bool, "machine_maker": bool,
                     "agentless_making": bool, "triggers": str}

The three flags are defined in agency_codebook.md. The rule reads the
explanation's grammar with spaCy's English pipeline (en_core_web_sm) and, for
every verb of making or changing the work, finds its doer: the subject of an
active verb, the by-phrase or AI instrument of a passive or participle, or the
subject that controls a subject-less infinitive or gerund. A person doer sets
person_maker, an AI or machine doer sets machine_maker, and no doer sets
agentless_making. A doer the explanation denies ("Alex didn't draw this",
"doesn't look like AI made it") sets neither of the first two flags. A few
fixed phrases are read before the parse: "AI-generated" and the like for a
machine, "hand-drawn" and "by hand" for a person.

The dependency logic follows the rule built on 2 September 2026
(Study 1/nlp/agency_rule_candidates/rule_hybrid.py), extended from making to
changing so that it reads explanations of second works, and changed from one
label per explanation to three flags. Deterministic: the same text and the same
spaCy model give the same flags.
"""

import re

__all__ = ["flags", "load_model", "FLAGS", "SPACY_MODEL"]

FLAGS = ("person_maker", "machine_maker", "agentless_making")
SPACY_MODEL = "en_core_web_sm"

# ---------------------------------------------------------------------------
# Words
# ---------------------------------------------------------------------------
MAKE_LEMMAS = {
    "make", "create", "generate", "produce", "draw", "paint", "sketch", "design",
    "render", "build", "craft", "compose", "illustrate", "animate", "doodle",
    "sculpt", "color", "colour", "shade",
}
CHANGE_LEMMAS = {
    "edit", "change", "alter", "modify", "adjust", "add", "remove", "transform",
    "enhance", "recolor", "recolour", "brighten", "darken", "crop", "tweak",
    "rework", "redo", "retouch", "revise", "convert", "manipulate", "saturate",
    "desaturate", "blur", "sharpen", "tint", "warp", "distort", "rearrange",
    "replace", "erase", "delete", "insert", "flip", "rotate", "resize", "stretch",
    "fix", "improve", "update", "touch", "lighten", "filter",
}
ACT_LEMMAS = MAKE_LEMMAS | CHANGE_LEMMAS
# Verbs that also describe a change of state ("the colors changed", "they both
# changed a lot"): without a real object they are not an act of changing.
STATE_CHANGE = {"change", "transform", "alter", "improve", "brighten", "darken", "lighten",
                "blur", "sharpen", "stretch", "rotate", "flip", "warp", "distort", "update"}
AMOUNT_WORDS = {"lot", "lots", "much", "little", "bit", "deal", "ton", "tons", "plenty"}
# Nouns for an act of changing: they count only with a possessive or a
# by-phrase that names the doer ("Alex's changes", "edits by the AI").
ACT_NOUNS = {"change", "edit", "addition", "alteration", "modification", "adjustment",
             "tweak", "enhancement", "revision", "creation", "edition"}
# "do" is a making act only with these objects ("the AI did all the work").
DO_OBJECTS = {"work", "job", "everything", "it", "this", "that", "most", "all",
              "rest", "editing", "changes", "change", "edits", "edit", "part", "details",
              "detail", "shading", "coloring", "lines", "art", "artwork", "piece", "image",
              "painting", "drawing", "picture", "background"}
# The objects of "make" that show it means causing a thought or feeling in a
# viewer ("makes me feel", "makes you think").
VIEWER_WORDS = {"me", "you", "us", "people", "viewer", "viewers", "one", "someone",
                "audience", "everyone", "anyone", "them"}
EASE_WORDS = {"easy", "easier", "hard", "harder", "possible", "impossible", "difficult",
              "simple", "simpler", "quick", "quicker", "faster"}

PERSON_WORDS = {
    "he", "she", "they", "them", "him", "her", "someone", "somebody", "person",
    "human", "humans", "artist", "artists", "author", "creator", "creators",
    "designer", "designers", "painter", "painters", "illustrator", "photographer",
    "individual", "man", "woman", "guy", "alex", "axel", "alexs", "themselves",
    "himself", "herself", "whoever", "somone", "creater", "editor", "maker",
}
# Doers that are hypothetical or generic rather than the maker of this work.
GENERIC_WORDS = {"anyone", "anybody", "everyone", "everybody", "one", "you", "people",
                 "kid", "kids", "child", "children", "toddler", "monkey", "we", "us"}
SELF_WORDS = {"i", "me", "myself"}
# Machines that can be the doer of an act.
MACHINE_WORDS = {
    "ai", "a.i.", "a.i", "ais", "intelligence", "computer", "computers", "machine",
    "machines", "program", "programs", "software", "algorithm", "algorithms", "bot",
    "bots", "robot", "robots", "chatgpt", "gpt", "midjourney", "dalle", "dall-e",
    "generator", "generators", "technology", "tech", "model", "system", "app",
    "filter", "filters", "photoshop",
}
# Machines that count when they are only the means of the act ("made with AI").
# Ordinary tools in a person's hands (software, Photoshop, a computer, a
# filter) do not.
AI_MEANS = {"ai", "a.i.", "a.i", "ais", "intelligence", "algorithm", "algorithms", "bot",
            "bots", "robot", "robots", "chatgpt", "gpt", "midjourney", "dalle", "dall-e",
            "generator", "generators", "machine", "machines"}
MEANS_PREPS = {"with", "using", "through", "via", "by"}
PERSON_POSS = {"his", "her", "their"}

# Objects that show the verb is not about making or changing the work.
NON_WORK_OBJECTS = {
    "prompt", "prompts", "input", "inputs", "code", "instruction", "instructions",
    "sense", "point", "points", "sure", "difference", "judgment", "judgement",
    "comment", "comments", "assumption", "mistake", "mistakes", "guess", "argument",
    "case", "living", "description", "descriptions", "keyword", "keywords", "command",
    "commands", "query", "request", "requests", "mind", "opinion", "opinions", "view",
    "views", "perspective", "decision", "decisions", "choice", "choices", "statement",
    "rating", "ratings", "answer", "connection", "connections", "impression",
}
# Verbs under which a denied main clause denies the act it governs
# ("I don't think he drew it", "it doesn't look like AI made it").
STANCE_LEMMAS = {"think", "believe", "look", "seem", "appear", "feel", "say", "know",
                 "guess", "imagine", "suppose", "sound"}
NEGATORS = {"not", "n't", "no", "never", "isnt", "isn't", "wasnt", "wasn't", "arent",
            "aren't", "doesnt", "doesn't", "dont", "don't", "didnt", "didn't", "cant",
            "can't", "hardly", "barely", "nothing", "neither", "nor", "without"}
OBJECT_CONTROL = {"prompt", "tell", "ask", "instruct", "force", "allow", "let", "enable",
                  "cause", "direct", "command", "get", "have", "order", "use", "utilize"}

MACHINE_RX = (r"(?:a\.?i\.?|ai|artificial intelligence|computer|machine|robot|algorithm|"
              r"chatgpt|midjourney|dall ?e|generator|software|program)")
SURFACE = [
    ("machine", re.compile(r"\b" + MACHINE_RX + r"\s+(?:generated|generation|made|created|produced|"
                           r"drawn|rendered|edited|enhanced|altered|modified|assisted|designed)\b")),
    ("machine", re.compile(r"\b(?:generated|made|created|produced|drawn|rendered|edited|enhanced|"
                           r"altered|modified|designed)\s+(?:entirely\s+|mostly\s+|completely\s+|"
                           r"fully\s+|just\s+|only\s+)?(?:by|with|using|through|via)\s+(?:an?\s+|the\s+)?"
                           r"(?:a\.?i\.?|ai|artificial intelligence|robot|algorithm|chatgpt|midjourney|"
                           r"dall ?e|generator)\b")),
    ("machine", re.compile(r"\b(?:generated|created|made|produced|rendered)\s+(?:a\.?i\.?|ai)\s+"
                           r"(?:image|picture|art|artwork|piece|work|photo|drawing|painting)\b")),
    ("person", re.compile(r"\b(?:hand\s+(?:drawn|painted|made|crafted|sketched|done|edited|"
                          r"colou?red|created)|handmade|handcrafted|by\s+hand|with\s+(?:his|her|their)"
                          r"\s+own\s+hands?|(?:hu)?man\s+made(?!\s+(?:of|up|from|out)\b)|manually\s+(?:\w+\s+)?(?:drawn|"
                          r"painted|made|created|edited|done|changed|added|adjusted|colou?red))\b")),
]


def load_model():
    import spacy
    return spacy.load(SPACY_MODEL)


# ---------------------------------------------------------------------------
# The surface layer
# ---------------------------------------------------------------------------
def _normalise(text):
    t = (text or "").replace("’", "'").replace("‘", "'")
    t = t.replace("“", '"').replace("”", '"').replace("—", " ").replace("–", " ")
    t = t.replace("-", " ").replace("/", " / ")
    return re.sub(r"\s+", " ", t).strip().lower()


def _denied_before(norm, start):
    """A negating word among the four words before `start`, in the same clause,
    or "rather than" or "instead of" just before it."""
    clause = re.split(r"[,.;:!?]| but | because | however ", norm[:start])[-1]
    if re.search(r"\b(?:rather than|instead of|as opposed to)\s*$", clause):
        return True
    return any(w.strip("\"'") in NEGATORS for w in clause.split()[-4:])


def _surface(norm):
    """Fixed phrases, each with the words it covers; a denied phrase covers its
    words too, so the grammar layer does not read them as an act with no doer."""
    found, covered = [], set()
    for kind, rx in SURFACE:
        for m in rx.finditer(norm):
            covered.update(re.findall(r"[a-z]+", m.group(0)))
            if not _denied_before(norm, m.start()):
                found.append((kind, "phrase:" + m.group(0)))
    return found, covered


# ---------------------------------------------------------------------------
# The grammar layer
# ---------------------------------------------------------------------------
def _low(tok):
    return tok.text.lower().strip(".,;:!?'\"")


def _doer_class(tok):
    """PERSON, MACHINE, GENERIC, SELF or OTHER for a noun or pronoun."""
    w = _low(tok)
    if w in SELF_WORDS:
        return "SELF"
    if w in MACHINE_WORDS:
        return "MACHINE"
    if w in GENERIC_WORDS:
        return "GENERIC"
    if w in PERSON_WORDS or w.startswith("alex"):
        return "PERSON"
    for ch in tok.children:                      # "the ai program", "a human artist"
        if ch.dep_ in ("compound", "amod", "nmod", "poss"):
            cw = _low(ch)
            if cw in MACHINE_WORDS and ch.dep_ != "poss":
                return "MACHINE"
            if cw in PERSON_WORDS or cw.startswith("alex"):
                return "PERSON" if ch.dep_ != "poss" else "OTHER"
    if tok.pos_ == "PROPN" and tok.ent_type_ == "PERSON":
        return "PERSON"
    return "OTHER"


def _subjects(tok):
    return [c for c in tok.children if c.dep_ in ("nsubj", "nsubjpass", "csubj")]


def _objects(tok):
    return [c for c in tok.children if c.dep_ in ("dobj", "obj", "attr")]


def _is_passive(tok):
    if any(c.dep_ in ("nsubjpass", "auxpass") for c in tok.children):
        return True
    if _objects(tok):
        return False
    if tok.tag_ == "VBN" and not _subjects(tok) and not any(c.dep_ == "aux" for c in tok.children):
        return tok.dep_ in ("acl", "amod", "advcl", "relcl", "conj", "ROOT", "pcomp", "ccomp", "xcomp", "oprd")
    return False


def _pobj(prep):
    for g in prep.children:
        if g.dep_ == "pobj":
            return g
    return None


def _by_phrase(tok):
    for c in tok.children:
        if c.dep_ == "agent" or (c.dep_ == "prep" and _low(c) == "by"):
            return _pobj(c)
    return None


def _ai_means(tok):
    """An AI named as the means of the act: 'made with AI', 'created using AI'."""
    for c in tok.children:
        if c.dep_ == "prep" and _low(c) in MEANS_PREPS:
            g = _pobj(c)
            if g is not None and (_low(g) in AI_MEANS or
                                  any(_low(x) in AI_MEANS for x in g.children if x.dep_ == "compound")):
                return g
        if c.lemma_.lower() in ("use", "utilize") and c.dep_ in ("advcl", "xcomp", "prep", "acl"):
            for o in _objects(c):
                if _low(o) in AI_MEANS or any(_low(x) in AI_MEANS for x in o.children if x.dep_ == "compound"):
                    return o
    head = tok.head                               # "he used AI to make it"
    if head is not tok and head.lemma_.lower() in ("use", "utilize") and tok.dep_ in ("xcomp", "advcl"):
        for o in _objects(head):
            if _low(o) in AI_MEANS or any(_low(x) in AI_MEANS for x in o.children if x.dep_ == "compound"):
                return o
    return None


def _rather_than(tok):
    """'digital rather than hand-drawn', 'instead of drawing it'."""
    start = min([tok.idx] + [c.idx for c in tok.children if c.i < tok.i and c.dep_ in
                             ("npadvmod", "compound", "nsubj", "nmod", "punct")])
    before = tok.doc.text[tok.sent.start_char:start].lower()
    return re.search(r"\b(?:rather than|instead of|as opposed to)\s*$", before) is not None


def _denied(tok):
    """The act is denied: a negation on the verb or its auxiliaries, or on a
    stance verb above it, or 'rather than' just before it."""
    if any(c.dep_ == "neg" for c in tok.children) or _rather_than(tok):
        return True
    if any(c.dep_ in ("aux", "auxpass") and any(g.dep_ == "neg" for g in c.children)
           for c in tok.children):
        return True
    head = tok.head
    if head is not tok and head.pos_ in ("VERB", "AUX"):
        if tok.dep_ in ("xcomp",) and _denied(head):
            return True
        if tok.dep_ == "conj" and not any(_low(c) in ("but", "yet") for c in head.children
                                          if c.dep_ == "cc") and _denied(head):
            return True
    cur = tok
    for _ in range(6):
        if cur.head is cur:
            break
        cur = cur.head
        if cur.lemma_.lower() in STANCE_LEMMAS and any(c.dep_ == "neg" for c in cur.children):
            return True
    return False


def _controller(tok):
    """The doer of a subject-less infinitive or gerund: the object of an
    object-control verb above it, or the nearest subject above it."""
    cur = tok
    for _ in range(8):
        if cur.dep_ in ("csubj", "csubjpass"):
            return None                           # inside a clausal subject: no doer
        if cur.head is cur:
            return None
        cur = cur.head
        if cur.pos_ == "NOUN":                    # "Alex's time spent doing"
            for c in cur.children:
                if c.dep_ == "poss" and (_low(c) in PERSON_POSS or _doer_class(c) in ("PERSON", "MACHINE")):
                    return c
        if cur.pos_ in ("VERB", "AUX") and cur.lemma_.lower() in OBJECT_CONTROL - {"use", "utilize"}:
            objs = _objects(cur)
            if objs:
                return objs[0]
        subs = [s for s in _subjects(cur) if s.i != tok.i and _low(s) != "there"]
        if subs:
            return subs[0]
        if cur.pos_ in ("NOUN", "PROPN"):
            return None
    return None


def _not_about_the_work(tok):
    lemma = tok.lemma_.lower()
    if any(_low(o) in NON_WORK_OBJECTS for o in _objects(tok)):
        return True
    if lemma == "make":
        objs = [_low(o) for o in _objects(tok)]
        result = [c for c in tok.children if c.dep_ in ("oprd", "acomp", "ccomp") or
                  (c.dep_ == "xcomp" and not any(g.dep_ == "aux" and _low(g) == "to" for g in c.children))]
        if result:
            # "makes me feel", "makes you think", "makes it easy": not about the work.
            # "made it brighter", "making the colors darker": a change to it. The
            # parser often makes the changed thing the subject of the result.
            objs = objs + [_low(s) for r in result for s in _subjects(r)]
            if any(o in VIEWER_WORDS for o in objs) or not objs:
                return True
            if any(_low(r) in EASE_WORDS for r in result):
                return True
        nxt = tok.nbor(1) if tok.i + 1 < len(tok.doc) else None
        if nxt is not None and _low(nxt) in ("sense", "sure", "up", "for", "out"):
            return True
        if any(c.dep_ == "prt" and _low(c) in ("up", "out") for c in tok.children):
            return True
        if any(c.dep_ == "prep" and _low(c) == "of" for c in tok.children) and not _objects(tok):
            return True                           # "a man made of stone"
    if lemma == "touch" and not any(c.dep_ == "prt" and _low(c) == "up" for c in tok.children):
        return True
    if lemma == "draw" and any(c.dep_ in ("prep", "prt") and _low(c) in ("to", "in", "into", "toward",
                                                                       "towards") for c in tok.children) \
            and not _objects(tok):
        return True
    if lemma == "do" and tok.head.pos_ == "ADJ" and tok.dep_ == "xcomp" and \
            _low(tok.head) in EASE_WORDS | {"tough", "tedious", "complicated", "challenging"}:
        return False                              # "incredibly difficult to do"
    if lemma == "do":
        objs = [_low(o) for o in _objects(tok)] + \
               [_low(c) for o in _objects(tok) for c in o.children if c.dep_ == "compound"]
        if not objs or not any(o in DO_OBJECTS for o in objs):
            return True
    if lemma == "draw" and any(_low(o) in ("attention", "eye", "eyes", "conclusion", "conclusions",
                                           "line", "comparison", "inspiration") for o in _objects(tok)):
        return True
    return False


def _act(tok):
    """(kind, trigger) for one verb of making or changing, kind being person,
    machine, agentless, or None when the verb is not such an act or its doer
    is denied, generic, the writer or inanimate."""
    tag = "%s/%s" % (_low(tok), tok.dep_)
    if tok.pos_ not in ("VERB", "AUX") and not (tok.tag_ == "VBN" and tok.pos_ == "ADJ"):
        return []
    if tok.pos_ == "AUX" and tok.lemma_.lower() != "do":
        return []
    if tok.dep_ == "aux":
        return []
    if tok.dep_ == "conj" and tok.tag_ == "VBN" and tok.head.pos_ not in ("VERB", "AUX"):
        return []                                 # "black and white added ..." misread
    if tok.tag_ == "VBG" and tok.dep_ in ("nmod", "compound", "amod", "npadvmod", "pobj", "poss",
                                          "dobj", "nsubj", "attr", "appos") and not _objects(tok):
        return []                                 # "coloring changes", "with coloring"
    if _not_about_the_work(tok):
        return []
    if tok.lemma_.lower() in STATE_CHANGE and not _is_passive(tok) and tok.tag_ != "VBN" and \
            not [o for o in _objects(tok) if _low(o) not in AMOUNT_WORDS]:
        return []                                 # "the colors changed", "they changed a lot"
    out = []
    denied = _denied(tok)
    fused = _fused_doer(tok)
    if fused is not None:                         # "hand-drawn", "AI-generated"
        cls = _doer_class(fused) if _low(fused) != "hand" else "PERSON"
        if cls in ("PERSON", "MACHINE") and not denied:
            out.append((cls.lower(), "fused=%s:%s" % (_low(fused), tag)))
        return out
    means = _ai_means(tok)
    if means is not None and not denied:
        out.append(("machine", "means=%s:%s" % (_low(means), tag)))
    if _is_passive(tok):
        by = _by_phrase(tok)
        if by is not None:
            cls = _doer_class(by)
            if cls in ("PERSON", "MACHINE") and not denied:
                out.append((cls.lower(), "passive_by=%s:%s" % (_low(by), tag)))
            return out
        if means is None:
            out.append(("agentless", "passive:" + tag))
        return out
    subs = _subjects(tok)
    if not subs and tok.dep_ in ("acl", "relcl") and tok.tag_ in ("VBD", "VBZ", "VBP") \
            and tok.head.pos_ in ("NOUN", "PROPN", "PRON"):
        subs = [tok.head]                         # "another person created this"
    doer = subs[0] if subs else _controller(tok)
    if doer is None:
        if means is None:
            out.append(("agentless", "no_doer:" + tag))
        return out
    cls = _doer_class(doer)
    if doer.i > 0 and _low(tok.doc[doer.i - 1]) in ("not", "never"):
        denied = True                             # "not them sitting ... drawing"
    if cls in ("PERSON", "MACHINE"):
        if not denied:
            out.append((cls.lower(), "doer=%s:%s" % (_low(doer), tag)))
    elif cls == "OTHER" and not subs and _low(doer) in ("it", "this", "that"):
        # "it took hours to draw": the subject is the work, the drawing has no doer
        out.append(("agentless", "work_controls:" + tag))
    return out


def _fused_doer(tok):
    """A doer joined to a participle just before it: 'hand-drawn', 'AI-generated',
    'computer made'."""
    if tok.tag_ != "VBN":
        return None
    if tok.dep_ == "amod" and tok.head.pos_ == "NOUN":
        for c in tok.head.children:
            if c.dep_ in ("compound", "amod", "nmod") and c.i != tok.i and _doer_class(c) == "MACHINE" \
                    and _low(c) in AI_MEANS | {"computer", "computers"}:
                return c
    for c in tok.children:
        if c.i < tok.i and c.dep_ in ("npadvmod", "compound", "nsubj", "nmod", "nsubjpass") \
                and tok.i - c.i <= 2 and (_low(c) == "hand" or _doer_class(c) in ("PERSON", "MACHINE")):
            return c
    return None


def _act_noun(tok):
    """'Alex's changes', 'his edits', 'edits by the AI'."""
    if tok.pos_ != "NOUN" or tok.lemma_.lower() not in ACT_NOUNS:
        return []
    for c in tok.children:
        if c.dep_ == "poss":
            w = _low(c)
            if w in PERSON_POSS or w.startswith("alex") or _doer_class(c) == "PERSON":
                return [("person", "possessive=%s:%s" % (w, _low(tok)))]
            if _doer_class(c) == "MACHINE":
                return [("machine", "possessive=%s:%s" % (w, _low(tok)))]
        if c.dep_ == "prep" and _low(c) == "by":
            g = _pobj(c)
            if g is not None and _doer_class(g) in ("PERSON", "MACHINE"):
                return [(_doer_class(g).lower(), "noun_by=%s:%s" % (_low(g), _low(tok)))]
    return []


def flags(text, nlp, doc=None):
    """The three flags for one explanation. `doc` is the explanation already
    parsed by `nlp` (stripped of surrounding white space), when the caller
    parses many at once with nlp.pipe()."""
    raw = "" if text is None else str(text).strip()
    out = {f: False for f in FLAGS}
    triggers = []
    if not raw:
        out["triggers"] = ""
        return out
    found, covered = _surface(_normalise(raw))
    if doc is None:
        doc = nlp(raw)
    assert doc.text == raw
    for tok in doc:
        lemma = tok.lemma_.lower()
        low = _low(tok)
        if tok.pos_ == "NOUN":
            found.extend(_act_noun(tok))
        elif lemma in ACT_LEMMAS or low in ACT_LEMMAS or lemma == "do" or \
                (lemma == "put" and any(_low(c) == "together" for c in tok.children)):
            acts = _act(tok)
            if _low(tok) in covered:              # the doer is in a fixed phrase
                acts = [a for a in acts if a[0] != "agentless"]
            found.extend(acts)
    for kind, trig in found:
        out[{"person": "person_maker", "machine": "machine_maker",
             "agentless": "agentless_making"}[kind]] = True
        triggers.append(trig)
    out["triggers"] = " | ".join(triggers)
    return out
