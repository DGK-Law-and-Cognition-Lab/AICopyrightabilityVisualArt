# Stimulus image check

**This is a check of the stimuli, specified on 10 October 2026, after every registered result was known. No registration names it, and it changes no registered verdict. Its comparison of distances with ratings is description only. Every table says so in its last column, `analysis_status`, and each figure says so in two lines at its foot.**

## What it checks and why

Studies 2, 4 and 5 showed participants a first artwork and a second work that the artist Alex made from it, at three levels of modification: None (the first work shown again unchanged), Slight (described in the registrations as colour and contrast adjustments) and Dramatic (substantial changes by hand). Participants rated how transformative the second work was, how much its essence had changed and how much creativity went into it. The design takes three properties of the pictures for granted, and no analysis had measured them:

1. the ten first artworks differ from one another;
2. each artwork's Slight second work is closer to it than its Dramatic second work is;
3. each second work, however much Alex changed it, is still closer to its own first artwork than to any of the other nine.

The third carries the most weight. If a Dramatic second work stood nearer to another artwork than to the one it was made from, a question about how far the second work moved from the first would rest on a pairing that the pictures do not support.

The check measures the distance between two images in three ways that notice different things.

- **DINOv2** is a vision network that Meta trained without labels, by teaching it to give matching numbers to different views of the same photograph, so that the list of numbers it gives an image, the image's *embedding*, describes its layout, shapes and content.
- **CLIP** is a vision network that OpenAI trained to match images with their captions, so its embedding reflects what a picture would be described as.
- **Colour** uses no network. It counts how the image's pixels fall into a fixed grid of colours in CIELAB, a colour space in which equal steps look roughly equally different to the eye, and divides each count by the number of pixels, so the 512 shares of the grid's cells sum to 1. This table of shares is the image's colour histogram.

For each network the distance is 1 minus the cosine similarity of two embeddings, where the cosine similarity is 1 when the two lists of numbers point the same way, 0 when they are unrelated and negative when they point in opposite directions, so the distance runs from 0 to 2. For colour it is the Hellinger distance between the two sets of shares, the square root of 1 minus the sum, over the cells, of the square root of the product of the two shares; it is 0 when two images have the same mix of colours and 1 when they share no cell of the grid. No person and no language model judges, labels or codes any image or any response. The two networks turn each image into numbers and do nothing else.

Each network sees an image of 224 by 224 pixels, fed to it in two ways. The primary input, the *whole image*, is the whole picture resized to 224 by 224 pixels, so nothing near an edge is lost and a picture that is not square is squeezed into the square. The robustness input, the *standard crop*, is each network's own preprocessing, the steps it was trained with: it resizes the shorter side and keeps the central 224 by 224 square, so it drops the edges of a picture that is not square.

Each check has a rule fixed in code before any distance is computed. Check 1 passes on a measure when the smallest distance between two different originals is larger than the largest distance between any original and its own Slight version. Check 2 asks, for each artwork, whether the Slight version is closer to the original than the Dramatic version, and passes when all ten are. Check 3 ranks the ten originals by their distance to each of the 20 edited images and passes when every edited image's own original ranks first. `ImageCheck.ipynb` defines every term and every step again where it is used.

## The files

| File | What it does |
|---|---|
| `extract_stimuli.py` | Run once. Takes the 30 stimulus images out of the printout of the Study 5 survey without re-encoding them, names each by its artwork and version with the survey files as the authority, cross-checks it against the local image files, and writes `stimuli/`. |
| `ImageCheck.ipynb` | A Jupyter notebook, a file of Python cells run in order. It checks every input, computes the three distances between every pair of the 30 images, applies the three checks, sets the distances beside the ratings of Studies 2, 4 and 5, draws two figures, and writes `tables/` and `figures/`. |
| `requirements.txt` | Every Python package the two code files import, the Jupyter packages that run the notebook from the command line, and every package these depend on under macOS, and under Linux with the CPU-only build of PyTorch; the default Linux build of PyTorch adds 12 nvidia-*-cu12 packages and triton 3.1.0, which PyTorch pins itself, each at the version installed for the run. |
| `stimuli/` | The 30 images, named like `1Figure_original.png`, `1Figure_slight.png` and `1Figure_dramatic.jpg`, each stored as PNG (a compressed image format that discards nothing) or JPEG (one that discards a little detail); `stimuli_manifest.csv`, one row per image; `extraction_checks.csv`, one row per check the extraction made; and `extraction_run_manifest.csv`, the size and SHA-256 checksum (a 64-character fingerprint of a file's exact bytes) of every file the extraction read and wrote. The 30 images are kept in the repository with the code, on GitHub (the website that hosts it), so the check reruns without the printout, and the notebook checks every image against the checksum recorded in these CSV files (comma-separated values, a plain-text table). |
| `tables/`, `figures/` | What the notebook writes. |
| `README.md` | This file. |
| `CHANGELOG.md` | The edit history of the two code files, which carry none themselves. |

## How to run it from a fresh copy

The notebook needs Python 3.12, the packages in `requirements.txt`, the two networks in the local model cache, and six files of the pipeline folder, the folder two levels up from this one, which each study's own pipeline writes:

- `Study 2/study2_long_with_text.csv` and `Study 2/tables/study2_quant_run_manifest.csv`;
- `Study 4/study4_long_with_text.csv` and `Study 4/tables/study4_quant_run_manifest.csv`;
- `Study 5/study5_long_with_text.csv` and `Study 5/tables/study5_quant_run_manifest.csv`.

The long data files hold one row per participant, item and rating question; each run manifest is the record of a study's real run, and the notebook checks each long data file against it. The notebook runs on the computer's main processor (CPU) and needs no graphics card.

The run was made on macOS on Apple silicon. PyTorch 2.5.1, the library that does the networks' arithmetic, is published for Apple silicon Macs, for Linux and for Windows, but not for Macs with Intel processors, so `requirements.txt` cannot be installed on an Intel Mac. Linux was not tested. The commands below are for a macOS or Linux shell, the program that runs typed commands; on Windows, run them in WSL (the Windows Subsystem for Linux, a Linux shell inside Windows). The native Windows setup was not tested, and `requirements.txt` does not cover it.

1. **Make a Python 3.12 environment and install the packages.** From this folder:

   ```sh
   python3.12 -m venv ~/.venvs/image_check
   source ~/.venvs/image_check/bin/activate
   python -m pip install -r requirements.txt
   ```

   A virtual environment is a private copy of Python that holds these packages apart from any others on the machine. It is made outside the repository, so git, the version-control tool that keeps the repository's history, does not track it. On Linux, the default install of PyTorch brings large libraries for graphics cards; adding `--extra-index-url https://download.pytorch.org/whl/cpu` to the install line fetches the build for the CPU alone, version `2.5.1+cpu`, which the notebook accepts.

2. **Register the environment with Jupyter** under the kernel name the notebook names, `python312`. A kernel is the entry that tells Jupyter which Python to start.

   ```sh
   python -m ipykernel install --user --name python312 --display-name "Python 3.12"
   ```

   This replaces any kernel already named `python312`. To keep an existing one, register the environment under another name and add `--ExecutePreprocessor.kernel_name=` with that name to the command in step 4.

3. **Fetch the two networks once**, at their pinned revisions, the fixed snapshots of their files. This downloads about 950 MB from Hugging Face, the site that hosts the two networks' files: DINOv2's `model.safetensors` (346 MB) and CLIP's `pytorch_model.bin` (605 MB), with their small settings files. The last line lets transformers, the library that loads the two networks, write `version.txt`, the small file that marks the cache as up to date, so the notebook's first run prints no message about the cache.

   ```sh
   python - <<'EOF'
   from huggingface_hub import hf_hub_download
   for repo, revision, files in [
       ("facebook/dinov2-base", "f9e44c814b77203eaa57a6bdbbd535f21ede1415",
        ["config.json", "preprocessor_config.json", "model.safetensors"]),
       ("openai/clip-vit-base-patch32", "3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268",
        ["config.json", "preprocessor_config.json", "pytorch_model.bin"]),
   ]:
       for name in files:
           hf_hub_download(repo, name, revision=revision)
   import transformers
   EOF
   ```

   The files go to the Hugging Face cache, the folder where these libraries keep downloaded models: `~/.cache/huggingface/hub` unless the environment variable `HF_HOME` or `HF_HUB_CACHE` names another (an environment variable is a named setting the shell passes to a program). The notebook reads only that cache and never downloads anything. If a file is missing, it stops and points here. Each of the six files must have the SHA-256 checksum that the notebook holds for it, so a damaged or altered copy stops the run.

4. **Run the notebook.** From this folder:

   ```sh
   jupyter nbconvert --to notebook --execute --inplace ImageCheck.ipynb
   ```

   or open it in Jupyter on the `python312` kernel and run every cell from the top. It stops at its first cell if the Python version or any analysis package differs from `requirements.txt`; setting `IMAGE_CHECK_ALLOW_OTHER_VERSIONS=1` lets it go on and records the difference. It checks each of the 30 images in `stimuli/` against the checksum in `stimuli/stimuli_manifest.csv`, and stops, naming the image, if one is missing or differs.

5. **Re-extracting the stimuli is optional.** It makes the 30 images in `stimuli/` again from the printout, and `stimuli/extraction_run_manifest.csv` records the checksum of every file the extraction read. The script needs these files. The printout and the draft survey are in the repository, in the folder `Stimuli/` at its top.

   | Input | Default place | Variable that names another place |
   |---|---|---|
   | The printout, `Qualtrics Survey Software.pdf` | `Stimuli/` under the project root | `IMAGE_CHECK_PRINTOUT` |
   | The draft Study 5 survey, `Draft_-_AI_Copyright_-_Study_5.qsf` | `Stimuli/` under the project root | `IMAGE_CHECK_DRAFT_SURVEY` |
   | The five final surveys, `Final_-_AI_Copyright_-_Study_1.qsf` to `_5.qsf` | `Exported Studies/` in the pipeline folder | `IMAGE_CHECK_SURVEY_DIR` |
   | The local image folder, for the cross-check only (optional) | `Stimuli/Images/` under the project root | `IMAGE_CHECK_LOCAL_IMAGES` |

   The project root is the folder that holds `Analysis` and `Stimuli`; when the pipeline folder does not sit in a folder named `Analysis`, as in a repository whose top folder is the pipeline folder, the pipeline folder serves as the project root. Before it extracts anything, the script compares the checksum of the printout and of each survey file with the one recorded in `stimuli/extraction_run_manifest.csv` by the run that made the deposited images (the printout's is `373814afe3399f6f03aa848baaa43231a49aab9bb613084ddd46e8a5717dca28`, 71,074,423 bytes), records each comparison in `stimuli/extraction_checks.csv`, and prints a warning if one differs. A file that differs can still be extracted, and the notebook then checks the images against the new manifest. Without the local image folder, the script skips the cross-check, records that it did, and leaves the manifest's local columns empty; nothing the notebook uses changes.

   The script also needs poppler, a set of command-line tools for PDF files, for this step only: `brew install poppler` on macOS, or `sudo apt-get install poppler-utils` on Debian or Ubuntu Linux. Then, from this folder, with the variables set only for files kept elsewhere:

   ```sh
   export IMAGE_CHECK_PRINTOUT="/path/to/Qualtrics Survey Software.pdf"
   export IMAGE_CHECK_DRAFT_SURVEY="/path/to/Draft_-_AI_Copyright_-_Study_5.qsf"
   export IMAGE_CHECK_SURVEY_DIR="/path/to/Exported Studies"
   export IMAGE_CHECK_LOCAL_IMAGES="/path/to/Stimuli/Images"
   python extract_stimuli.py
   ```

   The run used poppler 26.04.0. Another version of poppler can write the PNG files with other bytes and the same pixels; the manifest records both checksums, and the notebook checks both against the manifest the extraction wrote. The script writes into a staging folder first and moves the files into `stimuli/` only when every check has passed, so a run that stops leaves `stimuli/` as it was.

**Time.** On 10 October 2026 the notebook took about 25 seconds and the extraction about 45 seconds on an Apple silicon Mac. On 11 October 2026 the final runs of the notebook took 26 seconds to 2 minutes. One extraction that day, run while the Mac was heavily loaded and the project sat on a drive synced from cloud storage, took 72 minutes while using 93 seconds of processor time; the final extraction, later that day, took about a minute.

**The same numbers on every run.** The networks run in float32 (32-bit floating point, about seven significant digits) on one thread, one strand of computation, so the order in which numbers are added never changes. PyTorch's deterministic setting is on, which stops a run at any operation whose result could vary from run to run. Tables give six decimal places. Five runs of the notebook on 11 October 2026 wrote byte-identical copies of every table except the run manifest, which records the time of the run, and of every figure. Two runs of the extraction, one into a separate test folder, wrote byte-identical images, `stimuli_manifest.csv` and `extraction_checks.csv`. Later that day the extraction gained 7 checks and ran again, and the notebook ran four more times: the images, `stimuli_manifest.csv`, every table of results and both figures came out byte-identical again, and only `extraction_checks.csv`, `image_check_input_checks.csv`, which records that file's checksum, and the run manifests changed. On a different kind of processor the sixth decimal place can differ.

## What the extraction does

The local folder `Stimuli/Images` cannot identify versions. `NonFigures/1_nonfigure_orignial copy 2.png` is byte-identical to `Training_NonFigures/1_nonfigure_minimal.png`; `Training_NonFigures/2_nonfigure_minimal.png` is a PDF file with a `.png` name; several files named `minimal` are PDF or Photoshop files; and no local file has the size of the 3813 by 3784 JPEG the survey showed as `1NonFigure`'s Slight version. The survey decides which picture is which.

Qualtrics, the survey platform, stores each picture as a graphic with an ID of the form `IM_xxxx`, and the survey file (`.qsf`) says which graphic each question displays. The printout, `Stimuli/Qualtrics Survey Software.pdf`, is a Chrome print of the Study 5 survey from the survey editor, made on 6 October 2025, 98 pages long, with each picture embedded at the pixel size Qualtrics served. The displayed wording of the draft and the final Study 5 survey differs in three questions: QID163 and QID164 insert, as the page is shown, the value of the field `${e://Field/ArtistHr}` in the draft where the final inserts `${e://Field/ArtistHr_Source}`, and QID17 reads "He decided to produce" in the draft where the final reads "He decided to produced". The printout has the draft's wording at all three. It is a print of the draft, or of the final survey before those three edits, since the final was made as a copy of the draft. The two display the same graphic, at the same stated size, in every question of every stimulus block (a block being Qualtrics' name for a group of questions shown together), so the identification does not depend on which; so do the final surveys of Studies 2 and 4. Studies 1 and 3 display the ten originals only, each alone. All six survey files name the same 31 graphics: the 30 stimuli and the survey's logo.

`extract_stimuli.py` names an image only when three signals agree, and stops with a message, leaving `stimuli/` as it was, if one disagrees.

1. **Printout text and survey order.** The printout prints every block's name and the words FIRST WORK and SECOND WORK above each picture. Laying the survey's 70 displays of stimulus graphics end to end in the printout's block order, and the printout's 70 stimulus images end to end in page order, pairs them one to one. Each image must lie on a page between its own printed label and the next one.
2. **The sharing pattern.** Where the survey shows one graphic in several questions, the printout must show one embedded image in the same places, and different graphics must be different images. The 70 displays come down to 30 graphics and 30 embedded images, one to one.
3. **Pixel size.** Where the survey's page code, the HTML (the markup language of web pages) that a question displays, states a graphic's size, it must equal the embedded image's width and height in pixels. It states it for 29 of the 30 graphics; for `3Figure`'s Slight version (`IM_0oM0iJEDXudibHw`) it states none, and the first two signals carry the identification.

The images are taken out with poppler's `pdfimages`, which writes JPEG data as the JPEG bytes stored in the PDF file and every other image as a PNG file. The script reads each image's stored data directly from the PDF file and confirms that each JPEG equals the stored bytes and that each PNG holds the stored values exactly. Chrome tagged every stimulus image in the print with the same sRGB colour profile of its own, a profile being the standard description of a colour space that a file carries, so the printed values are sRGB values, the standard colours of screens and the web; the extracted files carry no profile and are read as sRGB, which the colour measure assumes. The 11 JPEGs are the bytes Qualtrics served: each carries the comment `CREATOR: gd-jpeg` and the same compression tables, the mark of gd, a graphics library for web servers, so Qualtrics re-encoded every JPEG uploaded to it. For the 19 images stored with lossless compression, Chrome decoded what Qualtrics served and stored the decoded values, so these files keep the pixels the survey showed but not the served bytes; for several, the pixels equal those of a local WebP file (another compressed web format). The script makes 538 checks, 531 on the printout, the surveys and the images and 7 that compare its inputs with the run that made the deposited images; `stimuli/extraction_checks.csv` lists them, and `stimuli/extraction_run_manifest.csv`, written last, gives the size and checksum of the printout, the six survey files, the 68 local image files, and every file written.

**The None second work.** In all three derivative surveys, the text each None block displays as its second work names the original's graphic. Qualtrics also stores a second copy of each question's page code (`QuestionText_Unsafe`), and in all ten None blocks that copy names the artwork's Slight graphic, which the survey did not display. The printout shows the original's embedded image at every None second work, never the Slight one, and the ratings agree: the mean ratings at None lie between 1.04 and 1.27 on the five-point scale. In the check, the None second work has the original's graphic ID and decodes to the original's pixels for all ten artworks.

**The Slight versions also change the frame.** Seven Slight versions differ from their original in pixel size and in the ratio of width to height: `2Figure`, `4Figure` and `1NonFigure` to `5NonFigure` (the sizes are in the table below). These edits also cropped or resized the picture, beyond any change of colour and contrast.

**The local files**, compared and never used to decide. Each stimulus is set beside every local image of the same size, including the images inside local PDF files but not their transparency masks (the part of a file that says how see-through each pixel is), and `stimuli_manifest.csv` records the closest one with the mean absolute difference of their red, green and blue values on the 0 to 255 scale, the number of pixels that differ by more than 40 in some channel, and the box of rows and columns that holds those pixels. It also scales each stimulus and every local image of nearly the same shape (a ratio of width to height within 2 percent) to 256 pixels wide and records the closest local image at that scale, whatever its size.

- Thirteen of the 30 stimuli have a local file with identical pixels: the originals of `1Figure`, `4Figure`, `5Figure` and `1NonFigure` to `5NonFigure`, and the Slight versions of `3Figure`, `4Figure` and `3NonFigure` to `5NonFigure`. The originals of `2Figure` (1.21) and `3Figure` (1.32) differ slightly from theirs.
- Nine of the ten Dramatic JPEGs differ from the local file of the same name and size only by small differences spread over the picture: a mean absolute difference of 1.27 to 2.78, with at most 80 pixels differing by more than 40. `4Figure`'s differs in one area. All 26,135 of its pixels that differ by more than 40 lie in a box of 128 by 531 pixels near the lower right corner (rows 1560 to 1687, columns 2438 to 2968), where the local file's picture varies strongly and the survey's is nearly flat; outside that box the two agree closely. Its overall mean, 1.05, comes almost wholly from that box, which covers 1.3 percent of the picture; outside it the two differ by 0.0025 on average, less than any other Dramatic pair, and it is the only one of the ten local files with the same JPEG compression tables as the survey's copy.
- The Slight versions of `1Figure`, `2Figure` and `2NonFigure` are closest to the image inside the local PDF named for them (mean absolute differences 4.06, 1.56 and 5.54, with 2,456, 10 and 5,789 pixels differing by more than 40). These are near copies, not the pixels the survey showed; in `1Figure`'s, every pixel that differs by more than 40 lies in one area (rows 447 to 657, columns 266 to 704). Saving the survey images again with these PDFs' own compression settings changes them by only 0.35 to 0.48, so the local PDFs are not compressed copies of what the survey showed, and no local file holds the exact pixels the survey showed for these three.
- The Slight version of `5Figure` is closest to the local original, at 12.39, so no local file holds the Slight picture the survey showed.
- No local file has the size of `1NonFigure`'s Slight version. Its closest local image at a common scale is the one inside `Stimuli/Images/Archive/nonfigurestimulus1moreedit.pdf`, a 915 by 908 copy at about a quarter of the size, 0.55 from it once both are 256 pixels wide. Neither local file named `minimal` for `1NonFigure` (`NonFigures/1_nonfigure_minimal.jpg`, and `Training_NonFigures/1_nonfigure_minimal.png`, which is byte-identical to `NonFigures/1_nonfigure_orignial copy 2.png`) is the closest local image to the survey's original or to its Slight version.

## What the notebook writes

In `tables/`, each a CSV file (comma-separated values, a plain-text table) whose last column, `analysis_status`, gives the status above:

- `image_check_input_checks.csv`: every check the run made, 188 in all, with the expected and observed value;
- `image_check_stimuli.csv`: the manifest fields the notebook uses;
- `image_check_distances.csv`: the distance between every pair of the 30 images on each measure and input, 435 pairs times five, 2,175 rows;
- `image_check_check1_originals.csv`, `image_check_check2_steps.csv` and `image_check_check3_ties.csv`: the three checks, row by row, with each verdict;
- `image_check_ratings_by_image.csv`: for each of the 30 images, over all participants and within each arm (the participants told that Alex made the first artwork by prompting an AI system, AI, or with design and sketching tools, Human), the five distances from the original beside the pooled mean rating of each question (the mean of the three study means), the number of ratings and each study's own mean;
- `image_check_ratings_correlations.csv`: the Spearman correlations (correlations computed on the ranks of the values) between each distance and each pooled mean rating, 135 rows;
- `image_check_models.csv`: each network's repository, pinned revision, weight file, size and SHA-256 checksum, embedding size, both inputs, the device and number format of its weights as observed, and the number of images for which its standard crop equals the whole-image input, with a row for the colour measure;
- `image_check_package_versions.csv`: the Python and package versions beside `requirements.txt`, the thread count, the deterministic setting, and the device and number format of the networks' weights;
- `image_check_run_manifest.csv`, written last: every input, every model file read and every output, with its size and checksum. The notebook deletes the old manifest when it starts, so a manifest on disk means the run reached its end. It is the one table that records a time.

Several tables hold the level `None`. pandas, the Python library for tables, reads that word as a missing value by default, so read them with `keep_default_na=False` and `na_values=[""]`, which keeps `None` as text and reads empty cells as missing. R's `read.csv` and the `read_csv` of readr, R's package for reading tables, keep `None` as text by default and need no option.

In `figures/`, each as PDF and PNG, in greyscale in the style of Study 1's figures, with two lines at its foot that give the status above:

- `image_check_fig1_distances`: for each measure, each artwork's distance from its original to its Slight and to its Dramatic version, with the range of distances between different originals shaded;
- `image_check_fig2_ratings`: the pooled mean rating against the distance from the original for the 20 edited images, one panel per measure and question, Slight and Dramatic marked differently.

## The results

### The 30 images

Each cell gives the graphic ID, the size in pixels (width by height) and the printout pages where the graphic appears. The original appears five times: alone, as the first work at None, Slight and Dramatic, and as the None second work.

| Artwork | Original | Slight | Dramatic |
|---|---|---|---|
| `1Figure` | `IM_bOzN9fgiJO3ptLU`, 1024x1024, p. 4, 5, 6, 8, 11 | `IM_4IwodriFx62n9Rk`, 1024x1024, p. 9 | `IM_bO3ekOr5r7la3Bk`, 1024x1020, p. 12 |
| `2Figure` | `IM_eWdgkf3hxs7b2JM`, 1024x1024, p. 15, 16, 17, 19, 22 | `IM_ekyXascckzWqseO`, 995x949, p. 20 | `IM_4GdGR6Tn8gjPh0q`, 3072x3072, p. 23 |
| `3Figure` | `IM_ctKw8eiHzUSiSTY`, 1024x1024, p. 25, 26, 27, 29, 32 | `IM_0oM0iJEDXudibHw`, 1024x1024, p. 30 | `IM_9ojy226JbgUDzGS`, 3072x3072, p. 33 |
| `4Figure` | `IM_5hlohEMvRATrRZ4`, 1792x1024, p. 35, 35, 36, 38, 40 | `IM_3ISpfovBUNB7IdE`, 1682x944, p. 38 | `IM_5o2r3anepQVecGW`, 3072x1752, p. 41 |
| `5Figure` | `IM_b9GRnfPJa6fulEO`, 800x800, p. 43, 44, 45, 47, 50 | `IM_38bsQn1ag3WCg4K`, 800x800, p. 48 | `IM_3KwloPp89J0mo8S`, 3072x3072, p. 51 |
| `1NonFigure` | `IM_816VB5B9iksfbLw`, 1024x1024, p. 53, 54, 55, 57, 60 | `IM_1Tvrnxdyj57mAt0`, 3813x3784, p. 58 | `IM_3Dh8TUqJtQ9ISSq`, 3072x3072, p. 61 |
| `2NonFigure` | `IM_cCHJHlug7s6hPiS`, 1024x1024, p. 63, 64, 65, 67, 70 | `IM_1Cb8O2F0Ip6KJVA`, 1024x1005, p. 68 | `IM_3Wc46wQQZg2tLOC`, 3072x3072, p. 71 |
| `3NonFigure` | `IM_0Tn55Rj36YbIXjw`, 1792x1024, p. 73, 73, 74, 76, 78 | `IM_brwXZy89iaJCGH4`, 1490x973, p. 76 | `IM_1SIStDCfkaOJahU`, 1024x1022, p. 79 |
| `4NonFigure` | `IM_enRMxMXmr3IjqLA`, 1792x1024, p. 81, 81, 82, 84, 86 | `IM_a8WoqS3cIrVvosm`, 1650x967, p. 84 | `IM_0jkPg0TITgLwI0m`, 3072x1752, p. 87 |
| `5NonFigure` | `IM_1NRv2xHy52jZoMK`, 1792x1024, p. 89, 89, 90, 92, 94 | `IM_eqUOPXmXcRjARjo`, 1710x1024, p. 92 | `IM_2rj9rPiGCEQe6RU`, 3072x1752, p. 95 |

The ten originals and nine of the Slight versions are stored as PNG; the ten Dramatic versions and `1NonFigure`'s Slight version are JPEG.

### The three checks

On both networks, with both inputs, all three checks pass, and no verdict differs between the whole image and the standard crop. The colour measure fails checks 1 and 3 and passes nine of ten artworks on check 2.

**Check 1, distinct artworks.** On DINOv2 with the whole image, the two closest originals are `1Figure` and `2NonFigure`, at 0.619, and the largest distance from an original to its own Slight version is `2Figure`'s, 0.113, a margin of 0.506. With the standard crop the figures are 0.593 and 0.099 (`2Figure`). On CLIP, the closest originals are again `1Figure` and `2NonFigure`, at 0.168 with either input (both are square, so CLIP's two inputs are the same for them), against a largest Slight distance of 0.055 (`1NonFigure`) with the whole image and 0.053 (`4Figure`) with the crop. On colour, the closest originals are `2Figure` and `3Figure`, at 0.292, while `5NonFigure`'s Slight version lies 0.606 from its original, and eight of the ten Slight distances exceed 0.292. The check fails on colour. The largest distance between two originals is 0.977 on DINOv2 with the whole image and 1.013 with the crop, 0.509 and 0.523 on CLIP, and 0.956 on colour. Seventeen DINOv2 distances in the table, all between pictures of different artworks, lie slightly above 1, the largest 1.041.

**Check 2, ordered steps.** For all ten artworks, the None second work has the original's graphic ID and identical pixels, and its distance from the original is 0 on every measure: a second, separate pass of the original through each network and histogram gives the same numbers bit for bit, and the cosine arithmetic leaves at most 2.2 x 10^-16, which the tables print as 0. On DINOv2 and CLIP, with either input, the Slight version is closer than the Dramatic version for all ten artworks. With the whole image, DINOv2's Slight distances run from 0.007 to 0.113 and its Dramatic distances from 0.094 to 0.439; CLIP's run from 0.016 to 0.055 and from 0.087 to 0.267. The steps are ordered within each artwork but overlap across artworks: `3Figure`'s Dramatic version (0.094 on DINOv2) is closer to its original than `2Figure`'s Slight version (0.113) is to its own. On colour, nine of ten pass; `5NonFigure`'s Slight version (0.606) is farther from the original than its Dramatic version (0.560).

**Check 3, edits stay tied to their own original.** On DINOv2 and CLIP, with either input, all 20 edited images are closest to their own original. The narrowest margin on DINOv2 with the whole image is `2NonFigure`'s Dramatic version, 0.238 from its own original and 0.582 from the next closest, `1Figure`; with the crop it is `1Figure`'s Dramatic version, 0.271 against 0.557 (`2NonFigure`). On CLIP it is `2NonFigure`'s Dramatic version with either input, 0.151 against 0.236 (`1Figure`); that image and both originals are square, so CLIP's two inputs agree here by construction. On colour, 10 of 20 pass. The failures are the Slight versions of `1Figure` and `3Figure` and the Dramatic versions of `1Figure`, `2Figure`, `3Figure`, `4Figure` and `1NonFigure` to `4NonFigure`. The widest is `4NonFigure`'s Dramatic version, whose own original ranks tenth of ten, at 0.928, while `2Figure`'s original lies at 0.354.

**Which measure moves most at Slight.** The median ratio of the Slight distance to the Dramatic distance across the ten artworks is 0.110 on DINOv2 (0.130 with the crop), 0.223 on CLIP (0.251) and 0.527 on colour. The Slight edits changed colour and contrast and, for seven artworks, the framing, and the colour measure registers them as about half a Dramatic edit, where DINOv2 registers about a tenth. That is why colour fails checks 1 and 3: a Slight edit moves an image's colour mix farther than the two most similar originals lie apart, and a Dramatic edit can leave an image with a colour mix nearer another artwork's. The two networks, which describe layout, content and what a picture shows, place every edit near its own original.

### The ratings beside the distances, description only

Each image's mean rating on a question is computed within each study, and the pooled mean is the mean of the three study means, so Studies 2, 4 and 5 each count once whatever their size. Averaged over the ten images (nine for transformativeness at None and at Slight), the pooled mean rating of transformativeness, essence change and creativity is 1.06, 1.06 and 1.17 at None, 1.97, 2.00 and 1.85 at Slight, and 3.53, 3.62 and 3.37 at Dramatic. The image means at Slight run from 1.54 to 2.54 and at Dramatic from 2.81 to 4.13, so every Dramatic image is rated above every Slight image on every question. Each image mean rests on 432 to 443 ratings over all participants, and on 214 to 227 within an arm. Transformativeness of `1NonFigure` at None and at Slight was asked on a six-point scale in every study and has no five-point mean. `image_check_ratings_by_image.csv` gives every mean, each study's own and the counts.

A Spearman correlation is the ordinary correlation computed on the ranks of the values, so it asks only whether images farther from their original tend to be rated higher. Over all participants and with the whole image, across the 20 edited images (19 for transformativeness, since `1NonFigure` has no five-point transformativeness rating at Slight):

| Measure | Transformativeness | Essence change | Creativity |
|---|---|---|---|
| DINOv2 | 0.78 | 0.78 | 0.73 |
| CLIP | 0.85 | 0.82 | 0.85 |
| Colour | 0.74 | 0.78 | 0.78 |

Most of this comes from the level, since the Dramatic images are as a group both farther and rated higher. Within a level, across its ten images (nine for transformativeness at Slight):

| Measure | Level | Transformativeness | Essence change | Creativity |
|---|---|---|---|---|
| DINOv2 | Slight | 0.35 | 0.16 | 0.19 |
| CLIP | Slight | 0.67 | 0.28 | 0.41 |
| Colour | Slight | 0.37 | 0.47 | 0.45 |
| DINOv2 | Dramatic | 0.04 | 0.19 | -0.25 |
| CLIP | Dramatic | 0.20 | 0.22 | 0.39 |
| Colour | Dramatic | -0.04 | 0.07 | 0.05 |

Within a level the correlations are mostly small and change with the measure, the input and the arm; with the standard crop, CLIP's correlation with transformativeness at Slight is 0.47 rather than 0.67. Across the 20 images the two arms look alike (for example, DINOv2 with transformativeness, 0.80 in the AI arm and 0.77 in the Human arm). No p-value, the probability of a correlation at least this strong if there were no relation, is reported. With 20 and 10 images these correlations describe the stimuli and test nothing.

## Limits

- Both networks were trained on photographs and their captions. Neither was trained on judgments of art or of artistic change, and neither distance measures what the participants saw or judged. The checks ask whether the pictures are arranged as the design assumes, as two networks with different training describe them.
- The colour measure ignores where colours lie in the picture, so two different pictures with the same palette are close on it. Its failure on checks 1 and 3 shows that the Slight edits changed palettes by more than the two most similar originals differ, and that some edited images have a palette nearer another artwork's; it does not show that an edited image resembles another artwork.
- A distance on one measure cannot be compared with a distance on another. Each check compares distances within one measure.
- The whole-image input squeezes an image that is not square into a square, and the standard crop drops its edges. The two inputs agree on every verdict. For CLIP, whose standard crop resizes the shorter side to 224 pixels, the crop gives the same input as the whole image for 16 images: the 14 square ones and the Dramatic versions of `1Figure` (1024 by 1020) and `3NonFigure` (1024 by 1022), so nearly square that resizing the shorter side to 224 pixels leaves the longer side at 224 too, so CLIP's two inputs differ only for the other 14 images. For DINOv2 they differ for all 30.
- The pixels are those of the printout of the Study 5 survey. The survey files show that Studies 2, 4 and 5 named the same graphics, but they cannot show that Qualtrics served the same bytes on the dates each study ran. The printout is the only record of served pixels.
- The printout is the survey editor's print view. That the None second work showed the original rests on the displayed field of the survey file, on the printout and on the ratings near the floor at None; no copy of the live survey pages was kept.
- There are ten artworks and 20 edited images. The ratings comparison is description only, the pooled means count each study once whatever its size, and the comparison was specified after every registered result was known.

## Environment and paths

Python 3.12.3 with PyTorch 2.5.1, torchvision 0.20.1 (PyTorch's image tools), transformers 4.46.2 (the library that loads the two networks), Pillow 10.3.0 (the image library), NumPy 1.26.4 (arrays of numbers), pandas 2.2.2 (tables), SciPy 1.13.0 (the Spearman correlations) and matplotlib 3.8.4 (the figures); `requirements.txt` lists every version, and `tables/image_check_package_versions.csv` records those of a run. On this Mac the `jupyter` command belongs to a separate Python 3.11 install (nbconvert 7.16.1), which started the `python312` kernel for four of the first five runs of 11 October; the fifth and every run after it, which made the deposited outputs, used the pinned nbconvert 7.17.1 of the Python 3.12 environment (`python3.12 -m nbconvert`, same arguments) and wrote the same tables of results and figures. In a fresh environment made as above, `jupyter` is the pinned one.

Paths are found from each file's own folder. These environment variables name other places:

| Variable | What it names |
|---|---|
| `IMAGE_CHECK_DIR` | this folder |
| `PIPELINE_DIR` | the analysis pipeline folder, two levels up |
| `IMAGE_CHECK_PROJECT_ROOT` | the project root, the folder that holds `Analysis` and `Stimuli`; in a copy laid out differently, the pipeline folder serves as the root |
| `IMAGE_CHECK_PRINTOUT` | the printout (extraction only) |
| `IMAGE_CHECK_DRAFT_SURVEY` | the draft Study 5 survey file (extraction only) |
| `IMAGE_CHECK_SURVEY_DIR` | the folder of the five final survey files (extraction only) |
| `IMAGE_CHECK_LOCAL_IMAGES` | the local image folder for the cross-check (extraction only) |
| `HF_HOME`, `HF_HUB_CACHE` | the Hugging Face model cache |

Printed and recorded paths are relative to the project root, and a model file is given relative to the model cache, so no output names a folder particular to one machine. A file that an environment variable places outside the project root is given relative to that folder, with the folder's label in angle brackets, such as `<local images>/Figures/1_figure_original.webp`; the local-file columns of `stimuli_manifest.csv` then read differently from the committed copy, and nothing else does.
