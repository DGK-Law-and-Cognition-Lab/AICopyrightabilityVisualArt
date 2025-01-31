# Lay Copyrightability of Artificial Intelligence Assisted Visual Artwork

This repository contains materials for the Cognitive Science Proceedings 2025 [paper]() "Lay Copyrightability of Artificial Intelligence Assisted Visual Artwork"" by David G. Kamper, Alice Lin, and Keith J. Holyoak.

## Introduction

The emergence of generative artificial intelligence (AI) systems has disrupted longstanding legal and cognitive frameworks governing creativity and authorship. Central to this disruption is the question of whether AI-assisted visual artworks—products of iterative human-AI collaboration—can qualify for copyright protection under current law. Existing copyright doctrine, anchored in human authorship and the originality of fixed expressions, faces unprecedented challenges when confronted with works co-created by humans and autonomous AI systems. A pivotal example is the 2022 case of Jason Allen’s Théâtre D’opéra Spatial, an AI-generated artwork denied copyright registration by the U.S. Copyright Office (USCO). Despite Allen’s extensive refinement of 624 text prompts and many hours in Midjourney and post-hoc edits in Adobe Photoshop, the USCO ruled that the work’s "traditional elements of authorship" originated from the AI system, not human creativity (USCO, 2023). This decision exemplifies a legal framework that rigidly dichotomizes human and machine contributions, relegating AI-assisted outputs to unprotected "mechanical reproductions."

From a cognitive science perspective, this binary distinction raises critical questions. Empirical studies suggest that human evaluators often cannot reliably distinguish AI-generated from human-created art (Sun et al., 2022; Nightingale & Farid, 2022) and that professional artists leveraging AI tools produce works perceived as more creative than standalone AI outputs (Orwig et al., 2024). These findings conflict with legal assumptions that AI systems operate as mere "tools," instead positing human-AI collaboration as a hybrid creative process that may transcend traditional authorship paradigms.

This paper addresses two interrelated research questions:

1) Legal-Cognitive Tension: How do lay evaluations of AI-assisted artworks align with copyright law’s criteria for protection (e.g., originality, transformativeness)?

2) Creative Agency: To what extent does human effort in guiding AI systems influence perceptions of authorship and creativity?

To investigate these questions, we conducted two preregistered experiments. Study 1 employed a mixed factorial design to examine how modification level (none, slight, dramatic) and creator type (AI vs. human) shape lay evaluations of three legal criteria: transformativeness, essence change, and creativity. Study 2 extended this inquiry by manipulating creative effort (1 hour, 10 hours, 100 hours) in AI prompting versus human creation, probing whether labor invested in refining AI outputs impacts judgments of copyrightability.

## Preregistrations

Preregistrations for all experiments are available on the Open Science Framework:

- [Experiment 1]()
- [Experiment 2]()

## Repository Structure

```
.
├── README.md
├── Code
│   └──  R
├── Qualtrics
├── Data
│   ├── Study 1
│   └── Study 2
└── Figures
```

### Code

#### R

`AIArtStudy1.Rmd` and `AIArtStudy2.Rmd` are the primary analyses files. They contain the analyses and visualizations for all experiments in the paper.

### Qualtrics

Contains survey flow and questions.

### Data

Contains raw data files for each of the experiments.

### Figures

1. `paper_figures` contains data visualizations generated in R and included in the paper.

### Paper Results
All results is analyzed and in visualized `code/R/AIArtStudy1.Rmd` and `code/R/AIArtStudy2.Rmd` All paper results are included in the document. Knitted document can be viewed `code/R/AIArtStudy1.html` and `code/R/AIArtStudy2.html`

## Software versions 

Analysis was performed in R version 4.2.2.

R package versions are indicated in the knitted analysis file at `code/R/AIArtStudy1.html` and `code/R/AIArtStudy2.html`.

## CRediT author statement

[What is a CRediT author statement?](https://www.elsevier.com/researcher/author/policies-and-guidelines/credit-author-statement)

| Term                       | David G. Kamper | Alice Lin | Keith J. Holyoak |
|----------------------------|-----------------|-----------|------------------|
| Conceptualization          | X               |           | X
| Methodology                | X               | X         | X
| Software                   | X               | X         |
| Validation                 | X               | X         | X
| Formal analysis            | X               |           |
| Investigation              | X               |           |
| Resources                  | X               |           |
| Data Curation              | X               | X         |
| Writing - Original Draft   | X               |           |
| Writing - Review & Editing | X               | X         | X
| Visualization              | X               |           |
| Supervision                |                 |           | X
| Project administration     | X               |           | 
| Funding acquisition        | X               |           | X
