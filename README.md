## 2024 Women's Olympic Gymnastics Scoring Analysis
Project Overview

This project was created to analyze women’s artistic gymnastics scores from the 2024 Olympic Games.
The main goal was to investigate how Difficulty (D) scores and Execution (E) scores contribute to the final total score, and to explore which factor has a stronger influence on performance outcomes.

## Objective

I was tasked with:
- Extracting and cleaning official Olympic scoring data from PDFs published by USA Gymnastics.
- Creating a structured dataset (CSV) containing Gymnast name, Country, Apparatus, D Score, E Score, and Total Score.

Exploring research questions such as:
- Is the difficulty or execution score more important in determining the final result?
- How do scoring trends vary by apparatus?
- Are there differences between qualification and finals rounds?
  
This repository contains three specialized Python scripts for extracting and parsing gymnastics competition results from PDF documents. Each script is designed for different types of competition formats and outputs structured CSV data.

## Overview of the Scripts

The scripts in the `scripts/` folder parse gymnastics competition PDFs using advanced table extraction techniques to convert complex formatted data into structured, analyzable CSV files.

## Scripts Included

1. **`events.py`** - Parses individual event competition results
2. **`team_allaround.py`** - Parses team all-around competition results  
3. **`individual_allaround`** - Parses individual all-around competition results

These 3 scripts take in the data from the pdfs, and organize them into a clean csv file, which I then used in google sheets to organize and create graphs/make conclusions with the data.

Inside Sheets, I:

- Checked for inconsistencies — such as duplicate gymnast names, missing values, and misaligned columns.
- Standardized apparatus names (e.g., Vault → VT, Uneven Bars → UB, Balance Beam → BB, Floor → FX).
- Verified numeric accuracy of the D (Difficulty) and E (Execution) scores.

Created calculated columns, including:
- Score Difference = D_Score - E_Score
- Contribution Ratio = D_Score / Total_Score
- Used conditional formatting to highlight gymnasts with extreme scores or unusual combinations (e.g., very high difficulty but low execution).

These cleaning and preprocessing steps made it easier to visualize relationships and patterns before doing more advanced analysis.

## From Sheets to Poster Presentation

Once the dataset was fully cleaned and organized, I used the results to design my final research poster.
The visualizations and conclusions in the poster were directly based on the Sheets analysis.

## Key Poster Elements

Research Question:
“Which contributes more to a gymnast’s final Olympic score — Difficulty (D) or Execution (E)?”

Visuals & Graphs (Created in Sheets or Canva):
- Scatterplot of D vs Total Score
- Scatterplot of E vs Total Score
- Bar chart comparing average D and E scores by apparatus
- Box plot showing score spread per event

Statistical Insights:

- Calculated correlation coefficients between D and total vs E and total.
- Found that while D score increases potential, E score consistency is more strongly correlated with overall performance.
- Noted that some apparatus (e.g., Beam, Floor) showed tighter E-score clustering, implying execution is more decisive there.

This project provided an in-depth look at how Difficulty (D) and Execution (E) scores interact to determine final results in women’s artistic gymnastics at the 2024 Olympic Games.
By extracting and cleaning the official scoring data from PDFs, organizing it in Google Sheets, and analyzing key score relationships, I was able to uncover meaningful insights into competitive scoring dynamics.
The analysis revealed that while higher D scores increase a gymnast’s potential for a higher total score, E scores show a stronger overall correlation with final performance. In other words, athletes who perform with greater precision and fewer deductions tend to achieve more consistent success, even when their routines are less difficult.
