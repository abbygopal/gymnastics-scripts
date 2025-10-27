from math import isnan
import pdfplumber
from pathlib import Path
import camelot # pip install camelot-py[cv]
import pandas as pd
import re


INPUT_PDF = "team_allaround.pdf"
APPARATUS = ["Vault", "UnevenBars", "BalanceBeam", "Floor"]
IS_FLOAT = re.compile(r"^-?\d+(?:\.\d+)?$")

TEAM_HDR = re.compile(
    r"""^\s*
        (?P<trank>\d+)\s+
        (?P<noc>[A-Z]{3})\s*-\s*.*?
        (?P<v>\d{1,3}\.\d{3})\s*\(\d+\)\s+
        (?P<ub>\d{1,3}\.\d{3})\s*\(\d+\)\s+
        (?P<bb>\d{1,3}\.\d{3})\s*\(\d+\)\s+
        (?P<fx>\d{1,3}\.\d{3})\s*\(\d+\)\s+
        (?P<ttotal>\d{2,3}\.\d{3})\s*$
    """,
    re.VERBOSE,
)

ATH_HDR = re.compile(
    r"""^\s*
        (?P<bib>\d{3,})\s+
        (?P<name>[A-Z][A-Za-z'\-]+(?:\s[A-Z][A-Za-z'\-]+)*)\s+
        D\s+E\s*
        (?P<trail>.*)$
    """,
    re.VERBOSE,
)

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip())

def collapse_row(row: pd.Series) -> str:
    parts = [str(x) for x in row.tolist() if str(x).strip() not in ("", "None", "nan")]
    return norm(" ".join(parts))

def floats_from(s: str):
    return [t for t in s.split() if IS_FLOAT.match(t)]

def parse_ds_pairs(tokens):
    """Parse D/S pairs from a flat list of floats: D1 S1 D2 S2 ..."""
    vals = list(map(float, tokens))
    pairs = []
    for i in range(0, len(vals) - 1, 2):
        d, s = vals[i], vals[i+1]
        pairs.append((d, s))
        if len(pairs) == 4:
            break
    return pairs

def parse_e_pen(tokens, max_groups):
    """Parse E (+ optional -pen) repeated. Stop at max_groups."""
    vals = []
    i = 0
    t = tokens[:]  # strings
    while len(vals) < max_groups and i < len(t):
        if not IS_FLOAT.match(t[i]):
            break
        E = float(t[i]); i += 1
        Pen = 0.0
        if i < len(t) and t[i].startswith("-") and IS_FLOAT.match(t[i]):
            Pen = float(t[i]); i += 1
        vals.append((E, Pen))
    return vals

def parse_pdf_team(pdf_path: str) -> pd.DataFrame:
    tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
    raw = pd.concat([t.df for t in tables], ignore_index=True)

    lines = [collapse_row(raw.iloc[i]) for i in range(len(raw))]
    lines = [ln for ln in lines if ln]

    rows = []
    ctx_rank, ctx_noc = None, None

    i = 0
    while i < len(lines):
        ln = lines[i]

        mt = TEAM_HDR.match(ln)
        if mt:
            ctx_rank = int(mt.group("trank"))
            ctx_noc = mt.group("noc")
            i += 1
            continue

        ma = ATH_HDR.match(ln)
        if ma and ctx_noc:
            bib = int(ma.group("bib"))
            name = ma.group("name").strip()
            trail = ma.group("trail") or ""

            # collect D/S floats from the end of this line (and spill over, if needed)
            ds_tokens = floats_from(trail)
            # NEXT: collect E/Pen floats from the following numeric lines until next athlete/team or enough tokens seen
            e_tokens = []

            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                # stop if we hit next athlete or team
                if ATH_HDR.match(nxt) or TEAM_HDR.match(nxt):
                    break
                toks = floats_from(nxt)
                if toks:
                    # heuristic: first numeric-only line after the athlete line is for E/Pen
                    e_tokens.extend(toks)
                j += 1

            ds_pairs = parse_ds_pairs(ds_tokens)            # [(D,S), ...]
            epen = parse_e_pen(e_tokens, max_groups=4)      # [(E,Pen), ...]

            # number of valid apparatus groups we can form
            k = min(len(ds_pairs), len(epen), 4)
            # build record, filling missing apparatus with NaN
            rec = {"Rank": ctx_rank, "Bib": bib, "Name": name, "NOC": ctx_noc}

            total = 0.0
            for idx, app in enumerate(APPARATUS):
                if idx < k:
                    D, S = ds_pairs[idx]
                    E, Pen = epen[idx]
                    rec[f"{app}_D"] = D
                    rec[f"{app}_E"] = E
                    rec[f"{app}_Pen"] = Pen
                    rec[f"{app}_Score"] = S
                    total += S
                else:
                    rec[f"{app}_D"] = float("nan")
                    rec[f"{app}_E"] = float("nan")
                    rec[f"{app}_Pen"] = float("nan")
                    rec[f"{app}_Score"] = float("nan")
                rec[f"{app}_Rk"] = None  # team PDF doesn't list per-athlete apparatus ranks

            rec["Total"] = round(total, 3) if k > 0 else float("nan")
            rows.append(rec)

            i = j
            continue

        i += 1

    cols = ["Rank", "Bib", "Name", "NOC"] + \
           [f"{a}_{f}" for a in APPARATUS for f in ("Score","D","E","Pen","Rk")] + \
           ["Total"]
    df = pd.DataFrame(rows)
    if len(df):
        # enforce column order and numeric types
        for c in cols:
            if c not in df.columns:
                df[c] = float("nan") if c not in ("Name","NOC") else None
        df = df[cols]
        for c in df.columns:
            if c in ("Name", "NOC"):
                continue
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Optional: quick report of partial athletes
    if len(df):
        partials = df[df[[f"{a}_Score" for a in APPARATUS]].isna().any(axis=1)][["Bib","Name","NOC"]]
        if len(partials):
            print("Athletes with <4 apparatus parsed (expected in team format):")
            print(partials.to_string(index=False))

    return df

if __name__ == "__main__":
    df = parse_pdf_team(INPUT_PDF)
    print("Parsed rows:", len(df))
    print(df.head(12))
    df.to_csv("team_allaround.csv", index=False)
    print("Saved to team_allaround.csv")