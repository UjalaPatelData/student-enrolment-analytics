"""
Generates a synthetic college admissions and enrolment dataset.

Each row is one application, followed through the funnel:
applied -> offered -> accepted -> enrolled -> retained into the next term.
Realistic patterns are built in (program capacity limits, lower international
yield, a fall in international applications from 2024, GPA-driven retention),
along with deliberate data quality problems for the cleaning step to find.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
rng = np.random.default_rng(42)

TERMS = pd.DataFrame({
    "term": ["2023F", "2024W", "2024F", "2025W", "2025F", "2026W"],
    "intake": ["Fall", "Winter", "Fall", "Winter", "Fall", "Winter"],
    "start_date": ["2023-09-05", "2024-01-08", "2024-09-03", "2025-01-06", "2025-09-02", "2026-01-05"],
})

PROGRAMS = pd.DataFrame({
    "program_code": ["BUS", "CPG", "DAT", "NUR", "ECE", "MET", "GRD", "HOS"],
    "program_name": ["Business Administration", "Computer Programming", "Data Analytics",
                     "Practical Nursing", "Early Childhood Education",
                     "Mechanical Engineering Technician", "Graphic Design", "Hospitality Management"],
    "faculty": ["Business", "Technology", "Technology", "Health", "Community Services",
                "Technology", "Creative Arts", "Business"],
    "tuition_domestic": [2150, 2400, 2450, 2300, 1950, 2350, 2200, 2100],
    "tuition_international": [8200, 8900, 9100, 9400, 7800, 8800, 8300, 8100],
})

OFFER_RATE = {"BUS": 0.86, "CPG": 0.78, "DAT": 0.74, "NUR": 0.34, "ECE": 0.88,
              "MET": 0.82, "GRD": 0.70, "HOS": 0.90}
GPA_SHIFT = {"BUS": 0.0, "CPG": -0.22, "DAT": -0.05, "NUR": 0.18, "ECE": 0.10,
             "MET": -0.08, "GRD": 0.05, "HOS": -0.02}
# International applications fall after 2024, consistent with study-permit caps.
INTL_FACTOR = {"2023F": 1.00, "2024W": 0.97, "2024F": 0.72, "2025W": 0.60, "2025F": 0.50, "2026W": 0.46}
DOM_FACTOR = {"2023F": 1.00, "2024W": 1.00, "2024F": 1.03, "2025W": 1.04, "2025F": 1.06, "2026W": 1.07}

PROG_WEIGHTS = {
    "Domestic":      [0.15, 0.12, 0.08, 0.20, 0.14, 0.12, 0.11, 0.08],
    "International": [0.24, 0.20, 0.18, 0.05, 0.04, 0.07, 0.05, 0.17],
}
CHANNELS = {
    "Domestic":      (["Website", "High School Visit", "Social Media", "Referral", "Agent"],
                      [0.44, 0.25, 0.15, 0.14, 0.02]),
    "International": (["Agent", "Website", "Social Media", "Referral", "High School Visit"],
                      [0.55, 0.28, 0.10, 0.06, 0.01]),
}
AGES = {
    "Domestic":      (["17-19", "20-24", "25+"], [0.55, 0.25, 0.20]),
    "International": (["17-19", "20-24", "25+"], [0.12, 0.58, 0.30]),
}


def simulate():
    rows = []
    for t in TERMS.itertuples():
        base = 3000 if t.intake == "Fall" else 1250
        n_dom = int(base * 0.56 * DOM_FACTOR[t.term])
        n_int = int(base * 0.44 * INTL_FACTOR[t.term])
        start = pd.Timestamp(t.start_date)
        for stype, n in (("Domestic", n_dom), ("International", n_int)):
            prog = rng.choice(PROGRAMS["program_code"], size=n, p=PROG_WEIGHTS[stype])
            chan = rng.choice(CHANNELS[stype][0], size=n, p=CHANNELS[stype][1])
            age = rng.choice(AGES[stype][0], size=n, p=AGES[stype][1])
            lead = rng.integers(14, 330, size=n)
            for p, c, a, d in zip(prog, chan, age, lead):
                offered = rng.random() < OFFER_RATE[p] + (0.05 if d > 180 else 0)
                acc_p = (0.72 if stype == "Domestic" else 0.58) \
                    + {"Referral": 0.10, "Agent": -0.08, "High School Visit": 0.05}.get(c, 0) \
                    + (0.04 if d > 180 else -0.04 if d < 60 else 0)
                accepted = offered and rng.random() < acc_p
                enr_p = 0.92 if stype == "Domestic" else (0.74 if t.term in ("2023F", "2024W") else 0.61)
                enrolled = accepted and rng.random() < enr_p
                gpa, retained = np.nan, np.nan
                if enrolled:
                    gpa = float(np.clip(rng.normal(2.85 + GPA_SHIFT[p] + (0.12 if a == "25+" else 0), 0.65), 0, 4))
                    if t.term != "2026W":  # next-term outcome not known yet
                        logit = -1.6 + 1.25 * gpa - (0.35 if t.intake == "Winter" else 0) \
                            + (0.25 if a == "25+" else 0)
                        retained = float(rng.random() < 1 / (1 + np.exp(-logit)))
                rows.append({
                    "term": t.term, "applied_date": (start - pd.Timedelta(days=int(d))).date(),
                    "program_code": p, "student_type": stype, "age_group": a, "channel": c,
                    "offered": int(offered), "accepted": int(accepted), "enrolled": int(enrolled),
                    "first_term_gpa": round(gpa, 2) if enrolled else np.nan,
                    "retained_next_term": retained,
                })
    df = pd.DataFrame(rows).sample(frac=1, random_state=7).reset_index(drop=True)
    df.insert(0, "application_id", [f"APP{100000 + i}" for i in range(len(df))])
    return df


def inject_quality_issues(df):
    df = df.copy()
    dup = df.sample(85, random_state=1)
    df = pd.concat([df, dup], ignore_index=True)
    idx = df.sample(45, random_state=2).index
    df.loc[idx, "program_code"] = " " + df.loc[idx, "program_code"].str.lower() + " "
    df.loc[df.sample(70, random_state=3).index, "channel"] = np.nan
    enr = df[df["enrolled"] == 1].sample(28, random_state=4).index
    df.loc[enr, "first_term_gpa"] = rng.choice([4.5, 5.0, -1.0, 9.9], size=len(enr))
    no_offer = df[df["enrolled"] == 1].sample(22, random_state=5).index
    df.loc[no_offer, "offered"] = 0
    starts = dict(zip(TERMS["term"], pd.to_datetime(TERMS["start_date"])))
    late = df.sample(18, random_state=6).index
    df.loc[late, "applied_date"] = [(starts[t] + pd.Timedelta(days=40)).date() for t in df.loc[late, "term"]]
    return df.sample(frac=1, random_state=8).reset_index(drop=True)


def main():
    DATA.mkdir(exist_ok=True)
    PROGRAMS.to_csv(DATA / "programs.csv", index=False)
    TERMS.to_csv(DATA / "terms.csv", index=False)
    raw = inject_quality_issues(simulate())
    raw.to_csv(DATA / "raw_applications.csv", index=False)
    print(f"Wrote {len(raw):,} raw application rows to data/raw_applications.csv")


if __name__ == "__main__":
    main()
