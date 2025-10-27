from math import isnan
import pdfplumber
from pathlib import Path
import camelot # pip install camelot-py[cv]
import pandas as pd
import re

INPUT_PDF = "events.pdf"
OUT_CSV   = "events.csv"

EVENT_PATTERNS = [
    ("Women's Vault", "Vault"),
    ("Women's Uneven Bars", "Uneven Bars"),
    ("Women's Balance Beam", "Balance Beam"),
    ("Women's Floor Exercise", "Floor"),
]

def detect_event_name(page_text: str) -> str:
    for pat, name in EVENT_PATTERNS:
        if pat in page_text:
            return name
    if re.search(r"Women's\s+Vault", page_text, re.I): return "Vault"
    if re.search(r"Women's\s+Uneven\s+Bars", page_text, re.I): return "Uneven Bars"
    if re.search(r"Women's\s+Balance\s+Beam", page_text, re.I): return "Balance Beam"
    if re.search(r"Women's\s+Floor", page_text, re.I): return "Floor"
    return "Unknown"

def find_header_row(df: pd.DataFrame) -> int:
    for i in range(min(len(df), 25)):
        row = df.iloc[i].astype(str).str.strip()
        if row.str.contains(r"\bRank\b").any() and row.str.contains(r"\bName\b").any():
            return i
    return 0

def make_unique_columns(cols):
    seen = {}
    out = []
    for c in cols:
        c = str(c).strip()
        if c == "":
            c = "Unnamed"
        if c not in seen:
            seen[c] = 1
            out.append(c)
        else:
            seen[c] += 1
            out.append(f"{c}_{seen[c]}")
    return out

def clean_table_keep_all_cols(t):
    df = t.df.copy()

    # Drop fully-empty columns Camelot sometimes creates
    df = df.loc[:, ~(df.replace("", pd.NA).isna().all(axis=0))].copy()

    hdr_idx = find_header_row(df)
    headers = df.iloc[hdr_idx].astype(str).str.strip().tolist()
    headers = make_unique_columns(headers)            # <<< ensure uniqueness
    df = df.drop(index=list(range(0, hdr_idx + 1))).reset_index(drop=True)
    df.columns = headers

    # Strip whitespace
    df = df.applymap(lambda x: str(x).strip())

    # Drop fully-empty rows
    df = df[~(df.replace("", pd.NA).isna().all(axis=1))].reset_index(drop=True)

    # Also ensure columns are unique after any later ops
    df.columns = make_unique_columns(df.columns)
    return df

def parse_events_pdf(pdf_path: str, out_csv: str):
    # 1) detect event names per page
    page_events = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            txt = p.extract_text() or ""
            page_events.append(detect_event_name(txt))

    # 2) extract tables page-by-page
    all_rows = []
    for pageno, event_name in enumerate(page_events, start=1):
        tables = camelot.read_pdf(pdf_path, pages=str(pageno), flavor="stream")
        if not tables:
            continue

        # pick the largest table (by rows×cols) if multiple
        main = max(tables, key=lambda tt: tt.df.shape[0] * tt.df.shape[1])

        df = clean_table_keep_all_cols(main)
        if df.empty:
            continue

        # Add Event column (first)
        df.insert(0, "Event", event_name)

        # Optional: normalize a few obvious header variants
        df = df.rename(columns=lambda c: c.replace("Pen.", "Pen"))

        all_rows.append(df)

    if not all_rows:
        print("No tables extracted.")
        return

    # 3) align columns across pages (outer join) and concat
    #    (helps when different events have different columns)
    master_cols = []
    for d in all_rows:
        for c in d.columns:
            if c not in master_cols:
                master_cols.append(c)

    # reindex each df to the union of columns, preserving values
    normed = [d.reindex(columns=master_cols) for d in all_rows]

    out_df = pd.concat(normed, ignore_index=True)

    # 4) numeric pass (best-effort)
    for c in out_df.columns:
        if c in ("Event", "Name"):
            continue
        out_df[c] = pd.to_numeric(out_df[c], errors="ignore")

    out_df.to_csv(out_csv, index=False)
    print(f"Saved {len(out_df)} rows to {out_csv}")

if __name__ == "__main__":
    parse_events_pdf(INPUT_PDF, OUT_CSV)