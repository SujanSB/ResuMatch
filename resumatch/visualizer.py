"""Visualizer Module.

Generates executive HR analytics dashboards (2x2 grid + 1 full-width text row) saved into:
reports/jobs/<JOB_ID>/<CANDIDATE_ID>_report.png
"""

import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Union

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import warnings
from resumatch.matcher.resume_matcher import MatchResult
from wordcloud import WordCloud, STOPWORDS

logger = logging.getLogger(__name__)
# to handle warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)

class Visualizer:

    def __init__(self, base_output_dir: Union[str, Path] = "reports_jobs") -> None:
        self.base_output_dir = Path(base_output_dir)
        sns.set_theme(style="whitegrid", palette="muted")

    def _ensure_job_folder(self, job_id: str) -> Path:
        clean_job_id = "".join(
            c if c.isalnum() or c in ("_", "-") else "_" for c in job_id
        )
        job_dir = self.base_output_dir / clean_job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def _draw_chart_3_wordcloud(self, ax: plt.Axes, raw_text: str) -> None:
        """Renders a WordCloud of profile text, excluding the explicit skills section."""
        # 1. Strip out the dedicated skills section to focus on experience & domain keywords
        skills_pattern = (
            r"(?:TECHNICAL\s+SKILLS|SKILLS|COMPETENCIES|TOOLS)\s*:?\n?"
            r"(.*?)(?=\n\n|\n[A-Z\s]{4,}:|\Z)"
        )
        cleaned_text = re.sub(
            skills_pattern, "", raw_text, flags=re.IGNORECASE | re.DOTALL
        )

        # 2. Filter out resume boilerplate, contact tokens, and common verbs/dates
        custom_stopwords = set(STOPWORDS).union({
            "email", "phone", "github", "linkedin", "experience", "education", 
            "summary", "projects", "profile", "work", "history", "university", 
            "college", "present", "jan", "feb", "mar", "apr", "may", "jun", 
            "jul", "aug", "sep", "oct", "nov", "dec", "year", "years", "using", 
            "built", "developed", "led", "managed", "worked", "germany", "nepal"
        })
        if cleaned_text.strip():
                    wordcloud = WordCloud(
                        width=800,
                        height=400,
                        background_color="white",
                        colormap="Blues",
                        stopwords=custom_stopwords,
                        max_words=60,
                        min_font_size=8,
                        random_state=42,
                    ).generate(cleaned_text)

                    ax.imshow(wordcloud, interpolation="bilinear")
                    ax.axis("off")
        else:
            ax.text(
                0.5, 0.5, "Insufficient text for WordCloud", 
                ha="center", va="center", fontsize=10, color="gray"
            )
            ax.axis("off")

        ax.set_title("Profile Narrative & Domain Keywords", fontweight="bold", fontsize=12, pad=15)

    def generate_candidate_report(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        match: MatchResult,
    ) -> Path:

        job_id = job.get("id", match.job_id)
        cand_id = candidate.get("id", match.cv_id)
        job_dir = self._ensure_job_folder(job_id)

        clean_cand_id = "".join(
            c if c.isalnum() or c in ("_", "-") else "_" for c in cand_id
        )
        output_file = job_dir / f"{clean_cand_id}_report.png"

        # GridSpec Layout: 3 Rows x 2 Columns (Last row spans both columns)
        fig = plt.figure(figsize=(15, 12))
        gs = gridspec.GridSpec(3, 2, height_ratios=[1, 1, 0.75], hspace=0.35, wspace=0.25)

        fig.suptitle(
            f"Candidate Intelligence & Profile Alignment Report\nJob: {job.get('title', job_id)} | Candidate: {cand_id}",
            fontsize=16,
            fontweight="bold",
            y=0.99
        )

        # -------------------------------------------------------------
        # PANEL 1 (Top Left): Match Telemetry (Horizontal Bar)
        # -------------------------------------------------------------
        ax1 = fig.add_subplot(gs[0, 0])
        scores_df = pd.DataFrame({
            "Metric": ["Overall Fit", "Semantic Match", "Skill Coverage"],
            "Score": [match.overall_score, match.semantic_score, match.skill_score],
        })

        sns.barplot(
            data=scores_df,
            x="Score",
            y="Metric",
            hue="Metric",
            ax=ax1,
            palette="Blues_r",
            legend=False,
        )
        ax1.set_xlim(0, 100)
        ax1.set_title("Match Telemetry (%)", fontweight="bold", fontsize=12, pad=15)
        ax1.set_xlabel("Score (%)")

        for p in ax1.patches:
            width = p.get_width()
            ax1.annotate(
                f"{width:.1f}%",
                (width - 8 if width > 15 else width + 2, p.get_y() + p.get_height() / 2.0),
                ha="center",
                va="center",
                color="white" if width > 15 else "black",
                fontweight="bold",
            )

        # -------------------------------------------------------------
        # PANEL 2 (Top Right): Required Skill Alignment (Donut Chart)
        # -------------------------------------------------------------
        ax2 = fig.add_subplot(gs[0, 1])
        n_matched = len(match.matched_skills)
        n_missing = len(match.missing_skills)

        if n_matched == 0 and n_missing == 0:
            n_matched, n_missing = 1, 0

        wedges, texts, autotexts = ax2.pie(
            [n_matched, n_missing],
            labels=[f"Matched ({n_matched})", f"Missing ({n_missing})"],
            autopct="%1.1f%%",
            startangle=140,
            colors=["#2ecc71", "#e74c3c"],
            wedgeprops=dict(width=0.4, edgecolor="w"),
        )
        plt.setp(autotexts, size=10, weight="bold")
        ax2.set_title("Required Skill Gap Ratio", fontweight="bold", fontsize=12,pad = 15)

        # -------------------------------------------------------------
        # PANEL 3 (Middle Left): Impact & Action Keyword Density
        # -------------------------------------------------------------
        ax3 = fig.add_subplot(gs[1, 0])
        cand_text = candidate.get("text", candidate.get("raw_text", ""))
        self._draw_chart_3_wordcloud(ax3, cand_text)

        # -------------------------------------------------------------
        # PANEL 4 (Middle Right): Candidate Profile Card
        # -------------------------------------------------------------
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis("off")

        cand_name = candidate.get("name", candidate.get("id", match.cv_id))
        # exp_years = candidate.get("experience_years", "N/A")
        tier = (
            "Strongly Recommended"
            if match.overall_score >= 75
            else ("Consider" if match.overall_score >= 50 else "Not Recommended")
        )

        matched_str = ", ".join(sorted(list(match.matched_skills))[:5]) or "None"
        missing_str = ", ".join(sorted(list(match.missing_skills))[:5]) or "None"

        summary_text = (
            f"RECRUITER DECISION CARD\n"
            f"----------------------------------------\n"
            f"Name:               {cand_name}\n"
            # f"Experience:         {exp_years} Years\n"
            f"Recommendation:     {tier}\n"
            f"Overall Score:      {match.overall_score}%\n\n"
            f"Top Matched Skills ({len(match.matched_skills)}):\n"
            f"  {matched_str}\n\n"
            f"Key Missing Skills ({len(match.missing_skills)}):\n"
            f"  {missing_str}\n"
        )

        ax4.text(
            0.05,
            0.95,
            summary_text,
            transform=ax4.transAxes,
            fontsize=10,
            verticalalignment="top",
            fontfamily="monospace",
            bbox=dict(
                boxstyle="round,pad=0.8", facecolor="#f8f9fa", edgecolor="#cbd5e1"
            ),
        )

        # -------------------------------------------------------------
        # PANEL 5 (Bottom Row - Full Width): Narrative & Achievements Summary
        # -------------------------------------------------------------
        ax5 = fig.add_subplot(gs[2, :])
        ax5.axis("off")

        metadata = candidate.get("metadata", {})
        achievements = metadata.get("achievements", [])
        volunteering = metadata.get("volunteering", [])

        # Extract textual highlights from raw text if metadata lists are empty
        if not achievements:
            raw = candidate.get("text", "")
            achievements = [
                s.strip()
                for s in re.split(r"[\n\.]+", raw)
                if any(w in s.lower() for w in ["award", "honor", "first", "lead", "built", "increased", "published"])
            ][:2]

        ach_str = "\n  • ".join(achievements) if achievements else "None explicit in profile."
        vol_str = "\n  • ".join(volunteering) if volunteering else "None listed."

        narrative_text = (
            f"EXECUTIVE PROFILE HIGHLIGHTS & ADDITIONAL CONTEXT\n"
            f"====================================================================================================\n"
            f"Key Achievements & Metric Highlights:\n"
            f"  • {ach_str}\n\n"
            f"Volunteering & Leadership:\n"
            f"  • {vol_str}\n"
        )

        ax5.text(
            0.02,
            0.90,
            narrative_text,
            transform=ax5.transAxes,
            fontsize=10,
            verticalalignment="top",
            fontfamily="monospace",
            bbox=dict(
                boxstyle="round,pad=0.8", facecolor="#f0fdf4", edgecolor="#86efac"
            ),
        )

        plt.subplots_adjust(top=0.88, bottom=0.08, left=0.08, right=0.92, hspace=0.35, wspace=0.3)
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
                cand_dict = cand_map.get(
                    match.cv_id,
                    {"id": match.cv_id, "skills": match.matched_skills},
                )
                chart_path = self.generate_candidate_report(cand_dict, job, match)
                saved_paths.append(chart_path)

        return saved_paths