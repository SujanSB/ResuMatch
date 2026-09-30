from pathlib import Path
import json
import pandas as pd
import pytest
from fpdf import FPDF

from resumatch.app import main


def create_dummy_pdf(filepath: Path, content: str):
    # creating basic pdf for testing
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in content.strip().split("\n"):
        pdf.cell(200, 10, txt=line.strip(), ln=1)
    pdf.output(str(filepath))


@pytest.fixture
def test_pipeline_environment():
    # setting up test input output directories
    test_dir = Path(__file__).parent / "test_data"
    resume_dir = test_dir / "resumes"
    jobs_dir = test_dir / "jobs"
    output_dir = Path(__file__).parent / "output"  # Saved under tests/output/

    resume_dir.mkdir(parents=True, exist_ok=True)
    jobs_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # create a dummy PDF resume
    resume_pdf = resume_dir / "Cand_01_SoftwareEngineer.pdf"
    sample_text = """
    Sujan Sharma
    Software and Data Engineer
    Email: candidate@example.com
    Skills: Python, PyTorch, SQL, Docker, Matplotlib, Linux, Pandas
    Experience: Data Engineer proficient in Python, SQL, PyTorch, and Docker.
    """
    create_dummy_pdf(resume_pdf, sample_text)

    # 2. Create sample jobs CSV
    jobs_df = pd.DataFrame(
        [
            {
                "id": "JOB_001",
                "title": "Data Engineer",
                "description": "Looking for a Data Engineer experienced in Python, SQL, and Docker.",
                "category": "Data Science",
                "skills": "Python, SQL, Docker, PyTorch",
            }
        ]
    )
    jobs_file = jobs_dir / "sample_jobs.csv"
    jobs_df.to_csv(jobs_file, index=False)

    return {
        "resume_dir": str(resume_dir),
        "jobs_file": str(jobs_file),
        "output_dir": str(output_dir),
    }


def test_overall_pipeline_execution(test_pipeline_environment, monkeypatch):
    resume_dir = test_pipeline_environment["resume_dir"]
    jobs_file = test_pipeline_environment["jobs_file"]
    output_dir = test_pipeline_environment["output_dir"]

    test_args = [
        "resumatch",
        "--resumes",
        resume_dir,
        "--jobs",
        jobs_file,
        "--output",
        output_dir,
    ]
    monkeypatch.setattr("sys.argv", test_args)

    # running application pipeline
    main()

    out_path = Path(output_dir)
    assert out_path.exists(), "Output directory inside tests/ should exist."

    png_files = list(out_path.glob("**/*.png"))
    assert len(png_files) > 0, f"Expected PNG report files in {out_path}, found none."

    json_files = list(out_path.glob("**/*.json"))
    assert len(json_files) > 0, f"Expected JSON result files in {out_path}, found none."

    print(
        f"\n[SUCCESS] Generated {len(png_files)} PNG(s) and {len(json_files)} JSON(s) in {out_path}"
    )
