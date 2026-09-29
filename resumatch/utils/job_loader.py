import pandas as pd


def load_jobs_from_csv(csv_path: str) -> list[dict]:
    df = pd.read_csv(csv_path)
    jobs = []

    for _, row in df.iloc[0:5].iterrows():
        raw_skills = f"{row.get('Skills', '')};{row.get('PreferredSkills', '')}"

        skills_set = {
            s.replace("*", "").strip().lower()
            for s in raw_skills.split(";")
            if s.strip()
        }

        full_text = row.get('FullProcessedDescription', '')

        jobs.append({
            "id": f"JOB_{row['JobID']}_{row.get('Title', '').replace(' ', '_')}",
            "text": full_text,
            "skills": skills_set,
        })

    return jobs

if __name__ == "__main__":
    csv_path = "/Users/sujansharma/Documents/0Study_Files/2nd/Python-Programming/ResuMatch/data/data_preparation/processed/final_job_descriptions.csv"  
    jobs = load_jobs_from_csv(csv_path)
    print(f'Loaded {len(jobs)} jobs')
    print(jobs)
