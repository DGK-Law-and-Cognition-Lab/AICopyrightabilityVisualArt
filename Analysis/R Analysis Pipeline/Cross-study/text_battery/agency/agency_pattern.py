"""The pattern form of the agency measure, as printed in the memo
Docs/Preregistration/Study1_Text_Measures_Candidates.md, section (vi).

Three search patterns, applied to the lower-cased explanation: a person
subject list or a tool subject list, up to three intervening words and a
making verb, or a passive participle with its by-phrase (agent_person and
agent_tool); and a passive participle with no by-phrase (agent_none). The
memo asks that this form be scored beside the parser rule on the same
sample, to measure the gap between the two. The patterns are copied here
unchanged.
"""

import re

PERSON_SUBJECTS = r"""(?:alex|axel|he|she|they|someone|somebody|whoever|this\sperson
  |the\s(?:artist|person|individual|human|creator|painter|author|maker|guy|designer))"""
TOOL_SUBJECTS = r"""(?:(?:the|an|a)?\s?ai|a\.?i\.|artificial\sintelligence|technology
  |(?:the|an|a)\s(?:image\s)?generator|chat\s?gpt|midjourney|dall[-\s]?e|stable\sdiffusion
  |(?:the|a)\s(?:computer|program|software|machine|algorithm|model|tool|system|bot|robot))"""
MAKING_VERBS = r"""(?:made|make|makes|making|created?|creates|creating|drew|drawn?|draws
  |drawing|painted|paints?|designed|generated?|generates|generating|produced?|produces
  |rendered|prompted|typed|sketched|built|crafted|put\s(?:it|this|that|together)
  |came\sup\swith|come\sup\swith
  |(?:did|does|do)\s(?:everything|most|all|it|this|that|the\s(?:hard\s)?work))"""
PASSIVE_PARTICIPLES = r"""(?:made|created|generated|drawn|painted|produced|designed|rendered
  |prompted|done|built|crafted)"""
AGENCY_RULES = dict(
    agent_person=r"""(?x)
        \b%s\s(?:\w+\s){0,3}%s\b
      |\b%s\s(?:mostly\s|entirely\s|largely\s)?by\s(?:%s|him|himself|her|herself|themselves)\b
    """ % (PERSON_SUBJECTS, MAKING_VERBS, PASSIVE_PARTICIPLES, PERSON_SUBJECTS),
    agent_tool=r"""(?x)
        \b%s\s(?:\w+\s){0,3}%s\b
      |\b%s\s(?:mostly\s|entirely\s|largely\s)?(?:by|with|using|through|via)\s%s\b
      |\b(?:ai|computer|machine|digitally)[-\s]?%s\b
    """ % (TOOL_SUBJECTS, MAKING_VERBS, PASSIVE_PARTICIPLES, TOOL_SUBJECTS, PASSIVE_PARTICIPLES),
    agent_none=r"""(?x)
        \b(?:was|were|is|are|been|being|got|gets|get)\s(?:\w+ly\s)?%s\b(?!\s(?:by|with|using|through|via)\b)
    """ % PASSIVE_PARTICIPLES,
)
COMPILED = {k: re.compile(v) for k, v in AGENCY_RULES.items()}
FLAG_OF = {"agent_person": "person_maker", "agent_tool": "machine_maker",
           "agent_none": "agentless_making"}


def flags(text):
    t = (text or "").lower()
    return {FLAG_OF[k]: bool(rx.search(t)) for k, rx in COMPILED.items()}
