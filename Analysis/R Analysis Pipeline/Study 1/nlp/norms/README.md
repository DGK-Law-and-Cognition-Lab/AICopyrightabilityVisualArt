# Published word norms for the Study 1 text notebook

This folder holds two sets of published word norms: the average ratings that groups of raters gave to single English words, collected by other laboratories. The text notebook, `Study1_02_Text.ipynb`, reads both in its section 11 and scores every written justification with them. The norms were built for other purposes and published before this study existed, so nothing in them was fitted to this study's data or hypotheses. The two files are not redistributed with the project; anyone re-running the notebook places them here under the names given below.

## What the notebook reads and writes

From the valence, arousal and dominance file the notebook reads four columns: `Word`, `V.Mean.Sum`, `A.Mean.Sum` and `D.Mean.Sum`. The last three are each word's mean rating on a scale of 1 to 9 for valence (how pleasant the word is), arousal (how calm or excited it makes a reader feel) and dominance (how much in control it makes a reader feel). From the concreteness file it reads `Word` and `Conc.M`, each word's mean rating from 1 (a word known only through other words, such as *justice*) to 5 (a word known through the senses, such as *dog*).

Both files are read with pandas' automatic detection of missing values switched off, because each contains the word "null", which would otherwise be read as an empty cell. Ten words in the valence file appear twice once their letters are lower-cased ("aids" and "AIDS", "tv" and "TV"), and the entry already spelled in lower case is the one kept, so the notebook uses 13,905 of that file's 13,915 entries. It uses all 39,954 entries of the concreteness file.

A response's content words are its words of two letters or more, with function words (such as *the* and *of*) removed, and with the task vocabulary removed: the vignette's name and the words of the rating questions and their scale, such as *creative*, *effort* and *great*. Every participant was handed those words, so they say nothing about how a participant chose to write. Each content word is looked up as written. If it is not in a norm file, one final *-ing*, *-ed*, *-es* or *-s* is stripped, the endings tried in that order, and the first shortened form found in the file is used, provided it keeps at least two letters. Nothing further is tried. A response's score is the mean over its words found in the file, and a response with no word found gets an empty value rather than a zero. The scores are word by word, so "not beautiful" scores as *beautiful* does.

The scores go to `nlp/study1_text_affect.csv`, one row per response, with these ten columns:

| column | what it holds |
|---|---|
| `id`, `stimulus_id`, `dimension` | the participant, the artwork, and the question the response answers (creativity or effort) |
| `n_content_words` | the number of content words in the response, every occurrence counted |
| `n_vad_matched` | how many of them were found in the valence, arousal and dominance file |
| `valence`, `arousal`, `dominance` | the mean rating of those words, on the scale of 1 to 9 |
| `n_conc_matched` | how many content words were found in the concreteness file |
| `concreteness` | the mean rating of those words, on the scale of 1 to 5 |

The file carries no experimental condition and no rating. `Study1_03_Integration.Rmd` joins those back on and reports the scores by arm as exploratory description.

If either norm file is missing, or saved under another name, the notebook stops at the first code cell of section 11 with a message that names the missing file and points to this README. By then the data files of section 9 are already written. The affect scores, the topic weights, the flags file, the tables and the run manifest are not. The notebook deletes the previous run's manifest when a run starts, so the absence of a manifest marks the run as unfinished.

## The two files

### Concreteness: Brysbaert, Warriner and Kuperman (2014)

Brysbaert, M., Warriner, A. B., & Kuperman, V. (2014). Concreteness ratings for 40 thousand generally known English word lemmas. *Behavior Research Methods, 46*, 904–911.

- The file is the tab-separated supplementary file `Concreteness_ratings_Brysbaert_et_al_BRM.txt`; its columns include `Word`, `Conc.M`, `Conc.SD`, `Bigram` and `Percent_known`.
- It is published with the article's Electronic Supplementary Material (the files the publisher hosts beside the article on its Springer page), and on the Concreteness ratings page of the authors' site, crr.ugent.be.
- Save it as `nlp/norms/Concreteness_ratings_Brysbaert_et_al_BRM.txt`.

### Valence, arousal and dominance: Warriner, Kuperman and Brysbaert (2013)

Warriner, A. B., Kuperman, V., & Brysbaert, M. (2013). Norms of valence, arousal, and dominance for 13,915 English lemmas. *Behavior Research Methods, 45*, 1191–1207.

- The file is the supplementary CSV; its columns include `Word`, `V.Mean.Sum`, `A.Mean.Sum` and `D.Mean.Sum`.
- It is published with the article's Electronic Supplementary Material, and on the Affective ratings page of crr.ugent.be.
- Save it as `nlp/norms/Warriner_et_al_2013_VAD.csv`.

## Provenance record: files obtained and verified on 2026-09-02

Both files are present. Each was downloaded from two independent sources and the two copies were compared. Across every word they share, the largest absolute difference between their ratings is 0.000000, and the row counts match the published figures: 39,954 concreteness entries and 13,915 valence, arousal and dominance entries. Spot checks: concreteness *dog* 4.85 and *justice* 1.45; valence *happy* 8.47 and *murder* 1.48.

| file | copy used | compared against | rows |
|---|---|---|---|
| `Concreteness_ratings_Brysbaert_et_al_BRM.txt` | github.com/ArtsEngine/concreteness, the raw file on the master branch, whose values are identical to those of the Springer supplementary file | the Springer supplementary file `13428_2013_403_MOESM1_ESM.xlsx`, for the article with DOI 10.3758/s13428-013-0403-5 | 39,954 |
| `Warriner_et_al_2013_VAD.csv` | `BRM-emot-submit.csv`, from the Springer supplementary archive `13428_2012_314_MOESM1_ESM.zip`, for the article with DOI 10.3758/s13428-012-0314-x | `Ratings_Warriner_et_al.csv` from github.com/JULIELab/XANEW | 13,915 |

The SHA-256 checksum of a file is a 64-character fingerprint computed from its exact bytes, which changes if a single byte changes. The checksums of the two files in this folder are:

    0b4082dbd38585b0ee1fd258145b7a50592f8d0d98e5fc6b6844ceef3cd8ecc8  Concreteness_ratings_Brysbaert_et_al_BRM.txt
    85f6d7e35069b0eff3d9d88c4dbe08e6ae7dbdb81eac64be3f89ed0f5079d8e3  Warriner_et_al_2013_VAD.csv

Running `shasum -a 256 Concreteness_ratings_Brysbaert_et_al_BRM.txt Warriner_et_al_2013_VAD.csv` from this folder prints the same two lines when the files are the ones recorded here.

Do not commit these two files to a public repository; cite the sources above instead. Both citations belong in the manuscript's Methods and in the environment section of the preregistration.
