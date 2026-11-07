# The agency rule, frozen

Frozen on 01 November 2026, 06:48 UTC, after the rule was adjusted on the development sample and before it read any item of the validation sample. Nothing in these files changes afterwards.

agency_rule.py SHA-256: `416b86d87e650c8c508d137ec62389f356dd45c1c7715839470324bdbab76cdc`
agency_pattern.py SHA-256: `c3f6fc48eeadb5498d20246e070682ebc569ad93b2c8f7d078629f1e2299dfda`
agency_codebook.md SHA-256 (of its text): `b0c14a3bedc83e52ebf3324f659f586b1a334073175ba781496e212db43e31bc`
spaCy: 3.7.4; model en_core_web_sm 3.7.1

Scores on the 250 development items, against the majority of the three annotators:

- person_maker: agreement 0.996, recall 0.857 of 7 yes and 1.000 of no, precision 1.000
- machine_maker: agreement 1.000, recall 1.000 of 7 yes and 1.000 of no, precision 1.000
- agentless_making: agreement 1.000, recall 1.000 of 30 yes and 1.000 of no, precision 1.000
