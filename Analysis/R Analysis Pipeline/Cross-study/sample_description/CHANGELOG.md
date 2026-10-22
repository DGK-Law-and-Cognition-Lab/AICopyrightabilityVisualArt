# Sample description changelog

The edit history of the files in this folder. The script itself carries none.

## 2026-10-20, later the same day

- `README.md`, last section: "all five studies showed the same ten original images, so a second participation came after seeing them once" now reads "all five studies drew on the same ten original images, so a second participation came after seeing some of them once". Studies 3, 4 and 5 showed nine, six and six of the ten originals. Nothing else changed; the script and its outputs are as they were, so the step was not rerun.

## 2026-10-20

Added the sample description. It is descriptive: the lead author specified it on 19 October 2026, after the registered results of all five studies were known, so that the paper can print each study's age and gender and the number of people who took part in more than one study from pipeline tables. No registration names it.

- `SampleDescription.R`: takes each study's analyzed sample from the long data file its real run wrote and finds each participant in the study's Labels export. For each study it writes the number of participants, their age (mean, standard deviation, youngest and oldest) and their gender answers. Across the five studies it writes the participations, the different people, and the people analyzed in two or more studies and in each pair of studies. It checks every input against the run manifest of the study that wrote it, reproduces Study 1's own age and gender tables exactly, and stops before writing any result table if a check fails. It records its inputs, session, package versions and a run manifest with `shared/R/fit_status.R`.
- `README.md` and this file.

Run in place on 20 October 2026 with `Rscript SampleDescription.R` from this folder, in about a second.

- All 48 checks passed. Each long data file and exclusion-flow table matched its study's real run manifest; each study's participants equal the last count of its exclusion flow (111, 235, 85, 117 and 223); every analyzed participant matched exactly one export record and has a participant code; no code repeats within a study; every gender answer is one the survey offered. Study 1's number of ages, mean, standard deviation, youngest and oldest age equal `study1_demo_age.csv` as stored, and its gender counts equal `study1_demo_gender.csv`.
- The run manifest lists seven outputs, all written by the run, and no output names a folder particular to one machine.

The result, in brief. Mean ages run from 19.96 (Study 2) to 20.52 (Study 4), and every study's youngest participant is 18. Women, counted as the answer Female, are 93 of 111, 192 of 235, 60 of 85, 96 of 117 and 179 of 223 in Studies 1 to 5. The other group holds 1, 5, 2, 1 and 7 people: one answer of Other in every study but Study 2, and Prefer not to say for the rest (0, 5, 1, 0 and 6). No gender answer is blank. The five analyzed samples hold 771 participations from 747 different people. Twenty-four people were analyzed in two studies and none in three, and each of them pairs Study 5 with an earlier study: 6 with Study 1, 7 with Study 2, 3 with Study 3 and 8 with Study 4. These are counts of participant codes; the README's last section says what they cannot show.

The public copy. The step was copied into a copy of the public repository made for this check, outside the project, and run there on the de-identified data. Its three result tables, its checks table, its session information and its package versions were byte-identical to the project's. Only the run inputs and the manifest differed. They carry the run's identifier, which includes the time the run started, and the checksum of each input, and some inputs differ between the two copies: the public copy's exports and Study 1 long data file carry the replacement codes, and its studies' run manifests are not the project's. The public repository itself was not changed and does not yet hold this folder.
