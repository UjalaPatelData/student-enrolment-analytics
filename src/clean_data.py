"""
Data quality checks and cleaning.
Every issue found is counted and written to reports/data_quality_report.md
so the cleaning is transparent and repeatable.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw_applications.csv"
CLEAN = ROOT / "data" / "clean_applications.csv"
REPORT = ROOT / "reports" / "data_quality_report.md"


def main():
    df = pd.read_csv(RAW, parse_dates=["applied_date"])
    programs = set(pd.read_csv(ROOT / "data" / "programs.csv")["program_code"])
    terms = pd.read_csv(ROOT / "data" / "terms.csv", parse_dates=["start_date"])
    log = [("Rows received", len(df))]

    dups = df.duplicated(subset="application_id", keep="first")
    log.append(("Duplicate application IDs removed", int(dups.sum())))
    df = df[~dups].copy()

    messy = df["program_code"] != df["program_code"].str.strip().str.upper()
    log.append(("Program codes with stray spaces or lowercase fixed", int(messy.sum())))
    df["program_code"] = df["program_code"].str.strip().str.upper()
    unknown_prog = ~df["program_code"].isin(programs)
    log.append(("Rows with unknown program code removed", int(unknown_prog.sum())))
    df = df[~unknown_prog]

    missing_chan = df["channel"].isna()
    log.append(("Rows with missing channel (labelled 'Unknown')", int(missing_chan.sum())))
    df.loc[missing_chan, "channel"] = "Unknown"

    bad_gpa = df["first_term_gpa"].notna() & ~df["first_term_gpa"].between(0, 4)
    log.append(("GPA values outside 0-4.0 set to missing", int(bad_gpa.sum())))
    df.loc[bad_gpa, "first_term_gpa"] = np.nan

    no_offer = (df["enrolled"] == 1) & (df["offered"] == 0)
    log.append(("Enrolled without an offer flag (offer flag corrected)", int(no_offer.sum())))
    df.loc[no_offer, ["offered", "accepted"]] = 1

    df = df.merge(terms[["term", "start_date"]], on="term", how="left")
    late = df["applied_date"] > df["start_date"]
    log.append(("Applications dated after term start removed", int(late.sum())))
    df = df[~late].drop(columns="start_date")

    log.append(("Rows after cleaning", len(df)))
    df.to_csv(CLEAN, index=False, date_format="%Y-%m-%d")

    lines = ["# Data Quality Report", "", "| Check | Result |", "|---|---|"]
    lines += [f"| {k} | {v:,} |" for k, v in log]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for k, v in log:
        print(f"{k}: {v:,}")


if __name__ == "__main__":
    main()
