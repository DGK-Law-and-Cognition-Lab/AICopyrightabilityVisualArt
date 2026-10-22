# Supplementary tables for the Study 2 to Study 5 and cross-study sections (`suppB_*.tex`)

Five tables, each `\input` by one section of the Supplementary Information. Each table holds
labels, column headings, captions and notes, and number macros from `generated/numbers.tex`. No
table holds a typed result. When the pipeline is rerun, run `tools/make_numbers.py` and rebuild;
these files need no change unless a macro is renamed. They are not written by
`tools/make_tables.py`, so edit them by hand.

Every macro below is listed, with its row, column and printed value, in
`generated/numbers_check.csv`. The paths are relative to `Analysis/R Analysis Pipeline`. The
SHA-256 checksum (a fingerprint that changes if the file changes) is the one `numbers_check.csv`
recorded when `tools/make_numbers.py` last ran.

| Table file | Input by | Contents | Pipeline tables behind its macros (macros; SHA-256) |
|---|---|---|---|
| `suppB_study2.tex` | `supplement/sections/study2.tex` | Study 2: predicted means by label and level, the label difference at each level (exploratory), the registered tests of H1 with the ordinal check | `Study 2/tables/study2_emmeans.csv` (24; `be45032e59ff1110231b87286a2a2dc86957058d7c2e390812d986a0b0109dd9`); `Study 2/tables/study2_source_by_modification.csv` (36; `395f3e25fc73eb8ded5908877fa73051ccfffef49f27297245e791c57013f85d`); `Study 2/tables/study2_confirmatory_family.csv` (48; `30d059dd01ba54bad087095a9d425f5130953c240fee144156a32f0e8ad1bd08`); `Study 2/tables/study2_clmm_check.csv` (8; `a559f09a787782d9397bf8b838f8c77a04f10e4ffec510d949abbd2c3b6c2547`) |
| `suppB_study4.tex` | `supplement/sections/study4.tex` | Study 4: the registered tests of H1 and H3 with the ordinal check, the registered secondary tests of the hours stated for the original, the predicted means | `Study 4/tables/study4_confirmatory_family.csv` (60; `362720caa0ed71b4a484e5bcf5b4bdfda82465b27f469f535cf906c3d4f7bd2b`); `Study 4/tables/study4_clmm_check.csv` (30; `1449447a821091077dbc14ba84942f76fe4c7fa783579c4acb9d05a14db8ae8b`); `Study 4/tables/study4_secondary_label_by_source_time.csv` (6; `fcada47db4841577170cb902d952b4e5a48dd524d990d6a98546050cb728e952`); `Study 4/tables/study4_secondary_time_equivalence.csv` (12; `ff7e51e7b0987beef5ba2b11ea7704237f981438e45c59b00a74674677c7d85e`); `Study 4/tables/study4_emmeans_marginal.csv` (15; `24de33ccd41eb822ba52b33b4ce10c6afb06f7fd7c4808c47a1b8b970196d497`); `\SourceBound` from `Study 2/tables/study2_equivalence.csv` (1; `95071e82e2eea108d7f282e3a12ad5bda960ccb9407af44bfc317c273d5a8d1d`) |
| `suppB_study5.tex` | `supplement/sections/study5.tex` | Study 5: the six registered confirmatory tests with the rescaled analysis, the registered secondary equivalence tests of editing time, the predicted means | `Study 5/tables/study5_confirmatory_family.csv` (30; `589cc76339beecb6dc5048a6b8322ca41077eba448cddc1933adb996b436ea9a`); `Study 5/tables/study5_rescaled_family.csv` (12; `0344a318cfcdf26c277027ac91db4019d9a40be9bd33908d6fd1648456620c24`); `Study 5/tables/study5_equivalence_editing_time.csv` (16; `699640b8d26e47ce9f38865359b5fffb2c59ca1689170d02e25df152efa213bc`); `Study 5/tables/study5_emmeans_source_by_modification.csv` (18; `93f7e65d6a46a6c0f253c511c20a84f767a16c544cacb6f6a39e766b1a90d373`); `Study 5/tables/study5_emmeans_editing_time.csv` (9; `e6985c57be88f64596c7834d2531689d6dbc0da74f0958976d430f13c8c2fb8b`) |
| `suppB_study5_breakdown.tex` | `supplement/sections/study5.tex` | Exploratory: Study 5's label penalty at each stated editing time and level, on all three measures | `Cross-study/tables/crossstudy_time_check.csv` (54; `2698c90d325d9fdba905f3a2c5396f7bffcf2634f01225733dc8a4f4856ec285`); `\SFiveNCellMin` and `\SFiveNCellMax`, derived by `make_numbers.py` from `Study 5/tables/study5_cell_counts_registered.csv` (2; `ac64b6a59423040aae270ccad2df50d557ba374b3e940840533a794b6a9c2cbb`) |
| `suppB_xs_trend.tex` | `supplement/sections/crossstudy.tex` | Exploratory: slope and curvature of the label's penalty across levels, in each of Studies 2, 4 and 5 and pooled | `Cross-study/tables/crossstudy_penalty_trend.csv` (48; `7baf27dcf114625d89fe883b83530e2c3134d9aa32ce542aeca58285615bbb38`) |

Status of the numbers, as `notes/results_ledger.md` gives it: the H1 and H3 tests and the Study 5 editing-time
F tests are registered confirmatory; the ordinal checks, the Study 5 rescaled analysis, the
Study 4 label-by-hours tests and both time equivalence tests are registered secondary; the Study 2
label difference at each level and both cross-study tables are exploratory; the predicted means
are descriptive. Each caption says so.
