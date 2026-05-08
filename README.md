# Policing as a Data-Generating Process: A Causal Analysis of Feedback Loops in Crime Prediction Systems

**Courtney Green**
DSAN 5450: Data Ethics and Policy, Georgetown University
Spring 2026

---

## Overview

This project analyzes whether policing activity generates the data later used to justify future policing, the core argument being that arrest records and crime incident data are not neutral measures of underlying criminal activity but outputs of an enforcement system shaped by deployment decisions, recording practices, and which communities bear the weight of proactive policing. Using nine years of administrative data from Chicago, the project tests empirically whether prior police stops predict future arrests independent of reported crime levels, and uses Chicago's Strategic Subject List (SSL) as a case study in how arrest-based data feeds into predictive systems.

---

## Repository Structure

```
.
├── code/
│   ├── build_dataset.py    # Builds the community-area-by-month dataset from raw sources
│   └── analysis.py         # Descriptive stats, plots, and OLS regression models
├── data/
│   ├── crimes_2016-present.csv
│   ├── arrests_2016-present.csv
│   ├── isr/                # Annual ISR stop report files (2016-2025)
│   ├── ACS_5_Year_Data_by_Community_Area.csv
│   ├── Strategic_Subject_List_-_Historical_20260407.csv
│   └── ca_month_dataset.csv    # Final dataset output by build_dataset.py
└── docs/
    ├── index.qmd           # Main paper (Quarto manuscript)
    ├── references.bib      # All citations
    ├── _quarto.yml         # Quarto project config
    ├── custom.scss         # Computer Modern font styling
    └── fonts/              # Local Computer Modern font files
```

---

## Data Sources

All datasets downloaded April 7, 2026.

| Dataset | Source | Description |
|---|---|---|
| Chicago Crimes 2016-present | Chicago Data Portal | Reported crime incidents from CPD CLEAR system |
| Chicago Arrests 2016-present | Chicago Data Portal | Arrest records from CPD CLEAR system |
| ISR Stop Reports 2016-2025 | Chicago Police Department | Officer-initiated investigatory stops |
| ACS 5-Year Data by Community Area | Chicago Data Portal | 2023 census demographics for all 77 community areas |
| Strategic Subject List (Historical) | Chicago Data Portal | CPD risk scoring system, August 2012-July 2016 |

---

## How to Run

**Step 1: Build the dataset**
```bash
python code/build_dataset.py
```
Outputs `data/ca_month_dataset.csv` — a community-area-by-month dataset with crime counts, arrest counts, stop counts, lag variables, and ACS demographic controls.

**Step 2: Run analysis**
```bash
python code/analysis.py
```
Outputs figures to `figures/` and prints regression results to the console.

**Step 3: Render the paper**
```bash
cd docs
quarto render index.qmd
```
Renders to HTML (and PDF/docx if configured). Python chunks in the paper run automatically via Jupyter.

