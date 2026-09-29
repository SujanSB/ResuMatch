"""Visualizer Module.

Generates custom Seaborn & Matplotlib analytics dashboards saved into 
job-specific directories: reports/jobs/<JOB_ID>/<CANDIDATE_ID>_report.png
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Union

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from resumatch.matcher.resume_matcher import MatchResult

logger = logging.getLogger(__name__)

# Visual analytics dashboard/ candidate-job report
class Visualizer:

    def __init__(self, base_output_dir: Union[str, Path] = "reports_jobs") -> None:
        self.base_output_dir = Path(base_output_dir)
        sns.set_theme(style="whitegrid", palette="muted")

    def _ensure_job_folder(self, job_id: str) -> Path:
        clean_job_id = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in job_id)
        job_dir = self.base_output_dir / clean_job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def generate_candidate_report(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        match: MatchResult,
    ) -> Path:
  
        job_id = job.get("id", match.job_id)
        cand_id = candidate.get("id", match.cv_id)
        job_dir = self._ensure_job_folder(job_id)

        clean_cand_id = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in cand_id)
        output_file = job_dir / f"{clean_cand_id}_report.png"

        # Create 2x2 Subplot Figure
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(
            f"Candidate Match & Profile Report\nJob: {job.get('title', job_id)} | Candidate: {cand_id}",
            fontsize=15,
            fontweight="bold",
            y=0.98,
        )

        # PANEL 1: Match Telemetry (Horizontal Bar Chart)
        scores_df = pd.DataFrame({
            "Metric": ["Overall Fit", "Semantic Match", "Skill Coverage"],
            "Score": [match.overall_score, match.semantic_score, match.skill_score],
        })
        
        ax1 = axes[0, 0]
        sns.barplot(data=scores_df, x="Score", y="Metric", ax=ax1, palette="Blues_r")
        ax1.set_xlim(0, 100)
        ax1.set_title("Match Telemetry (%)", fontweight="bold", fontsize=12)
        ax1.set_xlabel("Score (%)")

        for p in ax1.patches:
            width = p.get_width()
            ax1.annotate(
                f"{width:.1f}%",
                (width - 9 if width > 15 else width + 2, p.get_y() + p.get_height() / 2.0),
                ha="center",
                va="center",
                color="white" if width > 15 else "black",
                fontweight="bold",
            )

        # PANEL 2: Skill Overlap Ratio (Donut Chart)
        ax2 = axes[0, 1]
        n_matched = len(match.matched_skills)
        n_missing = len(match.missing_skills)
        
        if n_matched == 0 and n_missing == 0:
            n_matched, n_missing = 1, 0  # Fallback visualization

        wedges, texts, autotexts = ax2.pie(
            [n_matched, n_missing],
            labels=[f"Matched ({n_matched})", f"Missing ({n_missing})"],
            autopct="%1.1f%%",
            startangle=140,
            colors=["#2ecc71", "#e74c3c"],
            wedgeprops=dict(width=0.4, edgecolor="w"),
        )
        plt.setp(autotexts, size=10, weight="bold")
        ax2.set_title("Required Skill Alignment Ratio", fontweight="bold", fontsize=12)

        # PANEL 3: Extracted CV Skills Word / Category Frequency
        ax3 = axes[1, 0]
        cand_skills = sorted(list(candidate.get("skills", match.matched_skills)))[:12]
        
        if cand_skills:
            # Display top extracted skills as a bar plot
            skill_lengths = [len(s) for s in cand_skills]  # Sample frequency mapping
            skill_df = pd.DataFrame({"Skill": cand_skills, "Weight": skill_lengths})
            sns.barplot(data=skill_df, x="Weight", y="Skill", ax=ax3, palette="viridis")
            ax3.set_title("Extracted Profile Skills Overview", fontweight="bold", fontsize=12)
            ax3.set_xlabel("Relevance Weight")
        else:
            ax3.text(0.5, 0.5, "No extracted skills data", ha="center", va="center")


        # PANEL 4: Candidate Profile & Experience Summary Card
        ax4 = axes[1, 1]
        ax4.axis("off")  # text-based profile summary card

        cand_name = candidate.get("name", candidate.get("id", match.cv_id))
        experience = candidate.get("experience_years", "N/A")
        tier = "Strongly Recommended" if match.overall_score >= 75 else ("Consider" if match.overall_score >= 55 else "Not Recommended")
        
        matched_str = ", ".join(sorted(list(match.matched_skills))[:6]) or "None"
        missing_str = ", ".join(sorted(list(match.missing_skills))[:6]) or "None"

        summary_text = (
            f"CANDIDATE SUMMARY CARD\n"
            f"----------------------------------------\n"
            f"Name:               {cand_name}\n"
            f"Experience:         {experience} Years\n"
            f"Recommendation:     {tier}\n"
            f"Overall Match:      {match.overall_score}%\n\n"
            f"Matched Skills ({len(match.matched_skills)}):\n"
            f"  {matched_str}\n\n"
            f"Missing Skills ({len(match.missing_skills)}):\n"
            f"  {missing_str}\n"
        )

        ax4.text(
            0.05,
            0.95,
            summary_text,
            transform=ax4.transAxes,
            fontsize=11,
            verticalalignment="top",
            fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.8", facecolor="#f8f9fa", edgecolor="#cbd5e1"),
        )

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close(fig)

        logger.info(f"Report chart saved: {output_file}")
        return output_file

    def generate_batch_reports(
        self,
        candidates: List[Dict[str, Any]],
        jobs: Union[Dict[str, Any], List[Dict[str, Any]]],
        results_map: Dict[str, List[MatchResult]],
    ) -> List[Path]:
        job_list = [jobs] if isinstance(jobs, dict) else jobs
        cand_map = {c["id"]: c for c in candidates}
        saved_paths = []

        for job in job_list:
            job_id = job["id"]
            job_matches = results_map.get(job_id, [])

            for match in job_matches:
                cand_dict = cand_map.get(match.cv_id, {"id": match.cv_id, "skills": match.matched_skills})
                chart_path = self.generate_candidate_report(cand_dict, job, match)
                saved_paths.append(chart_path)

        return saved_paths



if __name__ == "__main__":
    from resumatch.matcher.resume_matcher import MatchResult

    viz = Visualizer(base_output_dir="reports_jobs")

    sample_cand = {
        "id": "CV_002_Sujan_Sharma",
        "name": "Sujan Sharma",
        "experience_years": 3.5,
        "skills": ["Python", "PyTorch", "LangChain", "RAG", "Docker", "AWS", "SQL", "FastAPI"],
    }

    sample_job = {
        "id": "Job_101",
        "title": "Senior AI / ML Engineer",
    }

    sample_match = MatchResult(
        cv_id="CV_002_Sujan_Sharma",
        job_id="Job_101",
        overall_score=84.5,
        semantic_score=88.0,
        skill_score=76.2,
        matched_skills={"Python", "PyTorch", "RAG", "LangChain", "Docker", "AWS"},
        missing_skills={"Kubernetes"},
    )

    saved_p = viz.generate_candidate_report(sample_cand, sample_job, sample_match)
    print(f"Candidate profile dashboard is saved at: {saved_p}")