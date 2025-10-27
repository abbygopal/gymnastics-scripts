from math import isnan
import pdfplumber
from pathlib import Path
import camelot # pip install camelot-py[cv]
import pandas as pd
import re

APPARATUS = ["Vault", "UnevenBars", "BalanceBeam", "Floor"]

IDENTITY_RE = re.compile(
    r"""
    ^\s*(?P<rank>\d+)\s+                # Rank
    (?P<bib>\d+)\s+                     # Bib
    (?P<name>(?:[A-Z][^\d]{0,40}\s?)+?) # Name (no digits)
    \s+(?P<noc>[A-Z]{3})\s+             # NOC (3 caps)
    D\s+E\s*$                           # literal trailing 'D E'
    """,
    re.VERBOSE
)

# Example: "6.400 15.766 (1)" -> D=6.400, Score=15.766, Rk=1
D_SCORE_RK = re.compile(
    r"(?P<D>\d{1,2}\.\d{3})\s+(?P<score>\d{1,2}\.\d{3})\s+\((?P<rk>\d+)\)"
)

IS_FLOAT = re.compile(r"^-?\d+(?:\.\d+)?$")

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip())

def collapse_row(row: pd.Series) -> str:
    parts = [str(x) for x in row.tolist() if str(x).strip() not in ("", "None", "nan")]
    return norm(" ".join(parts))

def parse_dscore_line(line: str):
    line = norm(line)
    # Sometimes Camelot glues floats; make sure there is spacing after D floats
    line = re.sub(r'(?<=\d\.\d{3})(?=\d)', ' ', line)

    triplets = []
    for m in D_SCORE_RK.finditer(line):
        triplets.append({
            "D": float(m.group("D")),
            "Score": float(m.group("score")),
            "Rk": int(m.group("rk")),
        })
    # Total is the last float on the line
    total = None
    floats = re.findall(r"\d{1,2}\.\d{3}", line)
    if floats:
        total = float(floats[-1])
    return triplets, total

def parse_e_pen_line(line: str):
    toks = norm(line).split()
    out = []
    i = 0
    for _ in range(4):
        if i >= len(toks) or not IS_FLOAT.match(toks[i]):
            return None
        E = float(toks[i]); i += 1
        Pen = 0.0
        if i < len(toks) and toks[i].startswith('-') and IS_FLOAT.match(toks[i]):
            Pen = float(toks[i]); i += 1
        out.append((E, Pen))
    return out

def parse_pdf(pdf_path: str) -> pd.DataFrame:
    tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
    raw = pd.concat([t.df for t in tables], ignore_index=True)

    # Build simple line list
    lines = [collapse_row(raw.iloc[i]) for i in range(len(raw))]
    lines = [ln for ln in lines if ln]

    records = []
    for i, line in enumerate(lines):
        m = IDENTITY_RE.match(line)
        if not m:
            continue

        # We need the D/Score/Rk (+Total) line just above and the E(+Pen) line just below.
        if i - 1 < 0 or i + 1 >= len(lines):
            continue
        dscore_line = lines[i - 1]
        e_line = lines[i + 1]

        # Parse the three parts
        d_trips, total = parse_dscore_line(dscore_line)
        epen = parse_e_pen_line(e_line)

        # Expect 4 apparatus triplets and 4 E/Pen pairs
        if not d_trips or len(d_trips) < 4 or not epen or len(epen) < 4:
            # Uncomment for debugging:
            # print("Skip block due to parse mismatch:", dscore_line, "|", line, "|", e_line)
            continue

        rank = int(m.group("rank"))
        bib = int(m.group("bib"))
        name = m.group("name").strip()
        noc = m.group("noc")

        rec = {"Rank": rank, "Bib": bib, "Name": name, "NOC": noc}

        for j, app in enumerate(APPARATUS):
            D = d_trips[j]["D"]
            Score = d_trips[j]["Score"]
            Rk = d_trips[j]["Rk"]
            E, Pen = epen[j]

            rec[f"{app}_Score"] = Score
            rec[f"{app}_D"] = D
            rec[f"{app}_E"] = E
            rec[f"{app}_Pen"] = Pen
            rec[f"{app}_Rk"] = Rk

        rec["Total"] = total
        records.append(rec)

    cols = ["Rank","Bib","Name","NOC"] + \
           [f"{a}_{f}" for a in APPARATUS for f in ("Score","D","E","Pen","Rk")] + \
           ["Total"]
    df = pd.DataFrame.from_records(records)
    if set(cols).issubset(df.columns):
        df = df[cols]

    # numeric cleanup
    for c in df.columns:
        if c in ("Name", "NOC"):
            continue
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

if __name__ == "__main__":
    df = parse_pdf("individual_allaround.pdf")
    print("Parsed rows:", len(df))
    print(df.head(5))
    df.to_csv("individual_allaround.csv", index=False)
    print("Saved to individual_allaround.csv")