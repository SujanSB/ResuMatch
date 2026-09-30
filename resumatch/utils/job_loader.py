import pandas as pd
import re
from typing import List, Dict, Set


def parse_skill_string(raw_skills: str | list) -> Set[str]:
    """Splits raw string representations of skills into clean, individual tokens."""
    if isinstance(raw_skills, list):
        raw_skills = ",".join(str(s) for s in raw_skills)
    if not isinstance(raw_skills, str) or not raw_skills.strip():
        return set()

    # Split by commas, semicolons, pipes, or bullets (avoiding '/' to preserve CI/CD, PL/SQL, etc.)
    tokens = re.split(r"[,;|•\n]", raw_skills)

    clean_set = set()
    for token in tokens:
        cleaned = re.sub(r"^[\s\-\*\•\d\.]+", "", token).strip().lower()
        if cleaned and len(cleaned) > 1:
            clean_set.add(cleaned)

    return clean_set


def load_jobs_from_csv(
    csv_path: str, category: str | None = None
) -> List[Dict]:
    df = pd.read_csv(csv_path)

    # Filter by category if specified
    if category is not None and "Category" in df.columns:
        target_cat = str(category).strip().upper()
        df = df[
            df["Category"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            == target_cat
        ]

    jobs: List[Dict] = []
    # only taking few rows of 
    df = df.iloc[0:5]

    # Iterate over all rows in the filtered DataFrame
    for idx, row in df.iterrows():
        # Safely extract skill fields avoiding NaN issues
        skills_val = (
            str(row.get("Skills", "")) if pd.notna(row.get("Skills")) else ""
        )
        pref_skills_val = (
            str(row.get("PreferredSkills", ""))
            if pd.notna(row.get("PreferredSkills"))
            else ""
        )
        raw_skills = f"{skills_val};{pref_skills_val}"

        full_text = (
            str(row.get("FullProcessedDescription", "")).strip()
            if pd.notna(row.get("FullProcessedDescription"))
            else ""
        )
        job_id_val = (
            str(row.get("JobID", idx)).strip()
            if pd.notna(row.get("JobID"))
            else str(idx)
        )
        title_val = (
            str(row.get("Title", "")).strip().replace(" ", "_")
            if pd.notna(row.get("Title"))
            else ""
        )

        job = {
            "id": f"JOB_{job_id_val}_{title_val}",
            "text": full_text,
            "skills": parse_skill_string(raw_skills),  # Correct variable passed
        }

        jobs.append(job)

    return jobs


if __name__ == "__main__":
    csv_path = "data/sample_data/jobs/final_job_descriptions.csv"

    jobs = load_jobs_from_csv(csv_path)

    print(f"Loaded {len(jobs)} jobs successfully.")