import argparse
import logging
import os
from pathlib import Path
from typing import Any, Dict, List
import warnings

# Suppress Hugging Face, Tokenizer, and HTTP transport logs
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Mute huggingface_hub HTTP warnings
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub.utils._http").setLevel(logging.ERROR)

# Catch standard library warning outputs
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")

for logger_name in (
    "httpx",
    "sentence_transformers",
    "huggingface_hub",
    "transformers",
    "urllib3",
):
    logging.getLogger(logger_name).setLevel(logging.WARNING)

from resumatch.extractor import ProfileExtractor
from resumatch.parser import DocumentParser
from resumatch.recommender import CandidateRecommender
from resumatch.utils.job_loader import load_jobs_from_csv
from resumatch.visualizer import Visualizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("ResuMatch")


def process_resumes(
    resumes_dir: Path, parser: DocumentParser, extractor: ProfileExtractor, limit: int | None = 1
) -> List[Dict[str, Any]]:
    """Sequentially parses PDF resumes and extracts candidate metadata."""
    pdf_files = sorted(list(resumes_dir.glob("*.pdf")))
    if limit is not None:
        pdf_files = pdf_files[:limit]
    if not pdf_files:
        logger.error(f"No PDF files found in: {resumes_dir.resolve()}")
        return []

    candidates: List[Dict[str, Any]] = []

    for pdf_path in pdf_files:
        try:
            logger.info(f"Processing: {pdf_path.name}")
            raw_text = parser.parse(pdf_path)
            profile = extractor.extract(raw_text)

            cand_id = pdf_path.stem
            candidate_record = {
                "id": cand_id,
                "name": getattr(profile, "name", None) or cand_id,
                "email": profile.email or "N/A",
                "phone": profile.phone or "N/A",
                # "experience_years": getattr(profile, "experience_years", 0.0), Can be extracted if LLM used. I guess.
                "text": raw_text,
                "skills": profile.skills,
                "metadata": profile.to_dict(),
            }
            candidates.append(candidate_record)
        except Exception as e:
            logger.error(f"Failed to process {pdf_path.name}: {e}")

    return candidates


def main() -> None:
    """CLI Entrypoint executed when called via `uv run -m resumatch`."""
    parser = argparse.ArgumentParser(
        description="ResuMatch: Hybrid CV-Job Matching and Recommendation Engine"
    )
    parser.add_argument(
        "--resumes_dir",
        type=str,
        default="data/sample_data/resumes",
        help="Path to folder containing candidate PDF resumes",
    )
    parser.add_argument(
        "--max_resumes",
        type=int,
        default=3,  # how many cvs/resumes to test. 
        help="Maximum number of resumes to process (useful for testing)",
    )
    parser.add_argument(
        "--jobs_csv",
        type=str,
        default="data/sample_data/jobs/final_job_descriptions.csv",
        help="Path to CSV file containing job descriptions",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="reports",
        help="Directory to save JSON recommendations and visual charts",
    )

    args = parser.parse_args()

    resumes_path = Path(args.resumes_dir)
    jobs_csv_path = Path(args.jobs_csv)
    reports_path = Path(args.output_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    # 1. Load Job Descriptions First
    logger.info("=== Step 1: Loading Job Descriptions ===")
    jobs = load_jobs_from_csv(jobs_csv_path,"DATA-SCIENCE")
    # jobs = load_jobs_from_csv(jobs_csv_path)
    if not jobs:
        logger.error("No valid jobs found in CSV. Aborting run.")
        return
    logger.info(f"Loaded {len(jobs)} jobs successfully.")

    # 2. Instantiate Parsers & Process Candidate Resumes Sequentially
    logger.info("=== Step 2: Parsing & Extracting Candidate Resumes ===")
    doc_parser = DocumentParser()
    profile_extractor = ProfileExtractor()

    candidates = process_resumes(
        resumes_dir=resumes_path,
        parser=doc_parser,
        extractor=profile_extractor,
        limit=args.max_resumes,
    )

    if not candidates:
        logger.error("No candidate resumes were successfully processed. Aborting run.")
        return

    logger.info(
        f"Successfully extracted {len(candidates)} candidate profiles."
    )

    # 3. Match Candidates & Generate Recommendations
    logger.info("=== Step 3: Matching Candidates & Generating Recommendations ===")
    recommender = CandidateRecommender(semantic_weight=0.7, skill_weight=0.3)
    recommendations_json = recommender.recommend_batch(
        candidates=candidates,
        jobs=jobs,
        top_k=len(candidates),
    )

    json_report_path = reports_path / "batch_recommendations.json"
    with open(json_report_path, "w", encoding="utf-8") as f:
        f.write(recommendations_json)
    logger.info(f"Saved JSON recommendation report to: {json_report_path}")

    # 4. Generate Visual Analytics Charts
    logger.info("=== Step 4: Generating Visual Analytics Charts ===")
    visualizer = Visualizer(base_output_dir=reports_path / "jobs")
    results_map = recommender.matcher.evaluate_batch(
        candidates=candidates,
        jobs=jobs,
        top_k_retrieval=len(candidates),
    )
    saved_charts = visualizer.generate_batch_reports(
        candidates=candidates,
        jobs=jobs,
        results_map=results_map,
    )

    logger.info(
        f"Pipeline finished! Generated {len(saved_charts)} PNG reports under: {reports_path / 'jobs'}"
    )


if __name__ == "__main__":
    main()