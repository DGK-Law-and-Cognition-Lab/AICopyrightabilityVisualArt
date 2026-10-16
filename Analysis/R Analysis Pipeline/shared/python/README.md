# Shared text measurement

This folder holds the text measurement that every study in the project applies to its written justifications, and a test that it reproduces Study 1.

| File | What it is |
|---|---|
| `study_text.py` | The measurement half of the Study 1 text notebook (`Study 1/Study1_02_Text.ipynb`), as a module that a study's own notebook imports. |
| `test_reproduces_study1.py` | A test that runs the module on the Study 1 data and compares every output with the file the Study 1 notebook deposited. |

## What the module measures

The registrations for Studies 2 to 5 say that Study 1's eight word lists run unchanged. The module is where they live, so that each study imports one copy instead of pasting its own. Each word list is a rule: a search pattern (a written list of words and phrases, in any of their ordinary forms) applied by the computer in the same way to every response. No person and no language model labels, codes or judges any response.

The module holds the following, moved from the notebook without changing any pattern or rule:

- the eight rules, each with its plain-language description and its grounding note (the construct the rule measures and the literature that reading comes from);
- the negation window (the 30 characters before a matched phrase, cut back to the start of its clause), the negating words, the quantity words that deny an amount, the clause boundaries, the size reading of *little*, and the words that open a supposition;
- the readings built on them: prior exposure (asserted, negated or neither), the polarity of detail, time, skill and concept talk (whether the matched phrase was claimed or denied), and the machine-made reading (asserted, not asserted or neither);
- the function-word list (words such as *the* and *of* that carry grammar rather than content), the task vocabulary (the words the instrument put in front of every participant), and the tokenizer that splits a response into content words;
- the word counts, the content-word lists, the affect and concreteness scores from published word norms, and the topic model with its rule for choosing the number of topics;
- the agreement check, in which one pretrained sentence-embedding model turns each response into a list of 768 numbers so that a grouping by meaning can be compared with the topics. The model gives no response a label, and no measure is built from it;
- the full text of the rules, written to `text_rules.txt`, and its SHA-256 checksum (a 64-character string computed from the exact bytes of the text, which changes if one character changes);
- a writer that saves each file under a temporary name and renames it once it is complete;
- `set_text_seed(seed)`, which sets the seed of every random step in the topic model and the agreement check (a seed is the number that starts a random-number generator), and `text_seeds()`, which reports the seeds in force. Study 1 used the module's defaults; Studies 2 and 3 call `set_text_seed(20260421)`, the Study 1 seed their registrations name for resampling, and Studies 4 and 5 call `set_text_seed(20260903)`, the seed their registrations name for the text code. The seed alone does not make a rerun give the same numbers. The module also runs the k-means step of the agreement check, which splits the responses into groups of similar meaning, on one processor thread (one strand of computation): `KMEANS_OPENMP_THREADS = 1`, applied through `threadpool_limits()` from the threadpoolctl package, which scikit-learn installs with it. On several threads, scikit-learn's k-means adds up its numbers in pieces, one per thread, and combines the pieces in the order the threads finish, which changes from run to run; since rounding depends on that order, the groups, and with them the agreement index, can differ between runs. The seed and the single thread together make a rerun give the same numbers. Each study's text environment table records the thread count as `kmeans_openmp_threads`.

The rules were written against the Study 1 corpus, and the comments beside them give reasons that come from that corpus. The module applies them unchanged in every study.

The module does not hold the notebook's printed reports (the matched responses for each rule and the candidate-word list), nor the tables that need the condition or the rating (the distinctive-word tables and the corpus summary). Those stay in each study's own notebook.

## The blind frame

Every function that reads responses takes a blind frame: a data frame (a table held in memory by the pandas library) with the columns `id`, `stimulus_id`, `dimension` and `response_text`, and beside them only columns whose names begin with `stimulus_`. `check_blind()` stops with a message if the frame carries anything else. A column named for the condition, the rating or a demographic (`type`, `rating`, `condition`, `arm`, `age`, `gender`, `race`, `language` or `experience`, compared in lower case, or any name containing `rating` or `condition`) is refused by name. Any other column outside the list is refused as well, so a manipulated factor stored under its own name, such as Study 5's `deriv_effort`, cannot pass. Every function in the module that takes a frame of responses calls `check_blind()` before it reads anything.

The key (`id`, `stimulus_id`, `dimension`) must name one response per row. The measures read three columns only: `response_text`; `id`, by which the topic model's stability check leaves participants out; and `dimension`, because the topic model is fitted to each question separately. Every other column passes through to the outputs as an identifier and is never read.

The check reads column names, not contents. A condition stored under a `stimulus_` name would pass it, so which columns describe the work shown is settled where each study builds its blind frame.

## The exports

Each output file has one function. It takes the blind frame and returns the frame or the text to write. The study's notebook names the files.

| Function | File it returns | Rows |
|---|---|---|
| `measures_frame` | `nlp/study<N>_text_measures.csv` | one per response: the identifiers, the word count, the eight measures, the machine-made reading and the four polarity columns |
| `wordcounts_frame` | `nlp/study<N>_text_wordcounts.csv` | one per response and content word that appears in at least two responses |
| `vocabulary_frame` | `nlp/study<N>_text_vocabulary.csv` | one per word in the word-count table, with the number of responses it appears in |
| `tokens_frame` | `nlp/study<N>_text_tokens.csv` | one per response: its distinct content words, sorted |
| `affect_frame` | `nlp/study<N>_text_affect.csv` | one per response: valence, arousal, dominance and concreteness |
| `topics_frame` | `nlp/study<N>_text_topics.csv` | one per response and topic: the response's weight on the topic |
| `topic_top_words_frame` | `tables/text_topics_top_words.csv` | the ten heaviest words of every topic |
| `topic_stability_frame` | `tables/text_topics_stability.csv` | the stability of every number of topics from 3 to 10, and the one chosen |
| `embedding_agreement_frame` | `tables/text_topics_embedding_agreement.csv` | for each question, the agreement between topics and embedding groups |
| `rules_text` | `tables/text_rules.txt` | the rules in full |
| `rules_checksum_text` | `tables/text_rules.sha256` | the checksum line, in the format `shasum -a 256 -c` reads |
| `grounding_text` | `tables/text_rules_grounding.txt` | one grounding note per rule |

`rules_text`, `rules_checksum_text` and `grounding_text` also take the study's name, such as `"Study 3"`. Every line of `text_rules.txt` is the same in every study except two: the title line, which names the study, and the line that gives the number of responses. The checksum therefore differs from study to study, and comparing two studies' `text_rules.txt` shows only those two lines. The test checks that.

The topic model is fitted once for each blind frame and the fit is kept, so `topics_frame`, `topic_top_words_frame`, `topic_stability_frame` and `embedding_agreement_frame` share it. On the Study 1 data the fit takes under a minute, and so does the agreement check.

A study's notebook uses the module along these lines, with the paths built relative to the study's own folder:

```python
import os, sys
sys.path.insert(0, os.path.join(os.pardir, "shared", "python"))
import study_text

# long_file is the study's long data, one row per response
blind = long_file[["id", "stimulus_id", "stimulus_type", "dimension", "response_text"]].copy()
study_text.write_csv_atomic(os.path.join("nlp", "study3_text_measures.csv"),
                            study_text.measures_frame(blind))
study_text.write_text_atomic(os.path.join("tables", "text_rules.txt"),
                             study_text.rules_text(blind, "Study 3"))
```

## The test

`test_reproduces_study1.py` loads `Study 1/study1_long_with_text.csv`, builds the blind slice exactly as the notebook does (the six columns `id`, `stimulus_id`, `stimulus_num`, `stimulus_type`, `dimension` and `response_text`), runs every export function on it, writes each result with the module's own writer into a temporary folder, and compares it with the deposited file.

A comparison decides the result in these cases:

1. The input file, and every file the Study 1 run manifest (`Study 1/tables/study1_text_run_manifest.csv`) lists, match the SHA-256 the manifest records, so the comparison is with the outputs of the recorded run.
2. Every function in the module with a parameter named `blind` refuses four frames outside the contract: the full long file, the blind slice with the rating added, the blind slice with the condition added, and the blind slice with `deriv_effort` added. The test finds these functions by that parameter, so a function added later with a `blind` parameter is checked too.
3. The constructed sentences (thirteen sentences written for the check, not taken from any corpus) are read as the rules say.
4. The rules text written for another study differs from Study 1's only in the title line and the response-count line.
5. Each of the eight CSV files is byte-identical to the deposited file. If the bytes differ, the two are read back and must have the same columns and rows, equal text cells, and numeric cells that differ by at most 1e-12.
6. `text_rules.txt` and `text_rules.sha256` are exactly equal to the deposited files, and the checksum equals the one the run manifest records.

Two further files are compared and reported without deciding the result: `text_rules_grounding.txt`, and `text_topics_embedding_agreement.csv` when the embedding model is on the machine.

Run it from this folder:

```sh
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python3 test_reproduces_study1.py
```

It takes one to two minutes. It exits with status 0 and prints `Every decisive comparison passed.` when every decisive comparison passes, and exits with status 1 otherwise. It writes nothing outside its temporary folder, and it writes no bytecode cache beside the module.

## The environment

Byte identity is expected with the software recorded in `Study 1/tables/study1_text_environment.csv`: Python 3.12.3, pandas 2.2.2, NumPy 1.26.4, scikit-learn 1.5.2, SciPy 1.13.0, sentence-transformers 3.3.1 and torch 2.5.1. Another version of NumPy, scikit-learn or SciPy may change the topic model's numbers. The test then falls back to the comparison with a tolerance and reports the largest difference it finds, and it fails if any difference exceeds 1e-12. The Jupyter kernel named `python312` runs this interpreter.

Paths are found relative to the files themselves, and these environment variables (settings passed to the program from the shell) change them:

| Variable | What it does |
|---|---|
| `STUDY_TEXT_NORMS_DIR` | The folder holding the two word-norm files. The default is `Study 1/nlp/norms`, whose README says where each file comes from; the files are cited, not redistributed. |
| `STUDY1_DIR` | The Study 1 folder the test reads. The default is `../../Study 1` from this folder. |
| `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE` | Set to `1`, they stop the Hugging Face libraries that load the embedding model from reaching the internet. The module sets both to `1` before it loads the model unless they are already set. |

The embedding model, `sentence-transformers/all-mpnet-base-v2`, is loaded only from a copy already in the machine's Hugging Face cache, and it runs on the processor rather than on a graphics card. Nothing is ever downloaded. Without a local copy the agreement table holds empty values, the reason is kept beside it, and every other output is unaffected.

Printed output gives paths relative to the Study 1 folder or the pipeline root, so it carries no account name and no folder particular to one machine.
