from dataclasses import dataclass, field
from typing_extensions import Dict, List, Any, Union
import numpy as np
import logging
from resumatch.utils.models import MatchResult
from resumatch.matcher.retriever import SemanticRetriever
from resumatch.matcher.reranker import DeepReranker
from resumatch.matcher.heuristics import SkillOverlapHeuristics, SkillAnalysisResult


logger = logging.getLogger(__name__)


# combining neural retrieval + heuristic skill analysis
class CompositeMatcher:
    def __init__(
        self,
        semantic_weight: float = 0.7,
        skill_weight: float = 0.3,
        bi_encoder_model: str = "all-MiniLM-L6-v2",
        cross_encoder_model: str = "BAAI/bge-reranker-base",
    ) -> None:
        self.semantic_weight = semantic_weight
        self.skill_weight = skill_weight

        self.retriever = SemanticRetriever(model_name=bi_encoder_model)
        self.reranker = DeepReranker(model_name=cross_encoder_model)
        self.heuristics = SkillOverlapHeuristics()

    # for single cv
    def evaluate_single(
        self,
        cv_id: str,
        cv_text: str,
        cv_skills: set[str],
        job_id: str,
        job_text: str,
        job_skills: set[str],
    ) -> MatchResult:

        # # --- DEBUG PRINT: INPUT SKILLS ---
        # print(f"\n==========================================")
        # print(f"SINGLE EVALUATION: Job [{job_id}] vs CV [{cv_id}]")
        # print(f"Job Required Skills ({len(job_skills)}): {sorted(job_skills)}")
        # print(f"CV Extracted Skills  ({len(cv_skills)}): {sorted(cv_skills)}")

        rerank_score = self.reranker.rerank(job_text, [cv_text])[0]
        skill_res: SkillAnalysisResult = self.heuristics.evaluate_skills(
            cv_skills, job_skills
        )

        # # --- DEBUG PRINT: MATCH RESULTS ---
        # print(f"Matched Skills ({len(skill_res.matched_skills)}): {sorted(skill_res.matched_skills)}")
        # print(f"Missing Skills ({len(skill_res.missing_skills)}): {sorted(skill_res.missing_skills)}")
        # print(f"Skill Score: {skill_res.score * 100:.2f}%")
        # print(f"==========================================\n")

        # direct rerank
        rerank_score = self.reranker.rerank(job_text, [cv_text])[0]

        # heuristic Analysis
        skill_res: SkillAnalysisResult = self.heuristics.evaluate_skills(
            cv_skills, job_skills
        )

        # weighted composite calculation
        overall = (self.semantic_weight * rerank_score) + (
            self.skill_weight * skill_res.score
        )

        return MatchResult(
            cv_id=cv_id,
            job_id=job_id,
            overall_score=round(overall * 100, 2),
            semantic_score=round(rerank_score * 100, 2),
            skill_score=round(skill_res.score * 100, 2),
            matched_skills=skill_res.matched_skills,
            missing_skills=skill_res.missing_skills,
        )

    # two step retrieval and reranking across cvs and jobs
    def evaluate_batch(
        self,
        candidates: List[Dict[str, Any]],
        jobs: Union[Dict[str, Any], List[Dict[str, Any]]],
        top_k_retrieval: int = 50,
    ) -> Dict[str, List[MatchResult]]:

        if not candidates:
            return {}

        job_list = [jobs] if isinstance(jobs, dict) else jobs
        if not job_list:
            return {}

        logger.info(f"Batch Processing: Pre-encoding {len(candidates)} candidates...")

        cv_texts = [c["text"] for c in candidates]
        cv_embeddings = self.retriever.encode(cv_texts)

        results_by_job: Dict[str, List[MatchResult]] = {}

        for job in job_list:
            job_id = job["id"]
            job_text = job["text"]
            job_skills = set(job.get("skills", set()))

            # # --- DEBUG PRINT: JOB REQUIREMENTS ---
            # print(f"\n==================================================")
            # print(f"BATCH EVALUATION FOR JOB: [{job_id}]")
            # print(f"Job Skills Required ({len(job_skills)}): {sorted(job_skills)}")
            # print(f"==================================================")

            # step 1: Fast retrieval
            job_embedding = self.retriever.encode([job_text])
            effective_k = min(len(candidates), top_k_retrieval)

            retrieved_items = self.retriever.search(
                job_embedding, cv_embeddings, top_k=effective_k
            )
            retrieved_indices = [idx for idx, _ in retrieved_items]
            selected_candidates = [candidates[i] for i in retrieved_indices]

            # step 2: Deep reranking
            selected_texts = [c["text"] for c in selected_candidates]
            semantic_scores = self.reranker.rerank(job_text, selected_texts)

            # heuristic overlap and final scores
            job_matches = []
            for cand, sem_score in zip(selected_candidates, semantic_scores):
                cand_skills = set(cand.get("skills", set()))
                skill_res = self.heuristics.evaluate_skills(cand_skills, job_skills)

                overall = (self.semantic_weight * sem_score) + (
                    self.skill_weight * skill_res.score
                )
                # --- DEBUG PRINT: CANDIDATE MATCH DETAILS ---

                # print(f"  ├─ CV Skills ({len(cand_skills)}): {sorted(cand_skills)}")
                # print(f"  ├─ Matched   ({len(skill_res.matched_skills)}): {sorted(skill_res.matched_skills)}")
                # print(f"  ├─ Missing   ({len(skill_res.missing_skills)}): {sorted(skill_res.missing_skills)}")
                # print(f"  └─ Skill Score: {skill_res.score * 100:.2f}% | Semantic: {sem_score * 100:.2f}%")

                job_matches.append(
                    MatchResult(
                        cv_id=cand["id"],
                        job_id=job_id,
                        overall_score=round(overall * 100, 2),
                        semantic_score=round(sem_score * 100, 2),
                        skill_score=round(skill_res.score * 100, 2),
                        matched_skills=skill_res.matched_skills,
                        missing_skills=skill_res.missing_skills,
                    )
                )

            # sort candidate rankings per job
            job_matches.sort(key=lambda x: x.overall_score, reverse=True)
            results_by_job[job_id] = job_matches

        return results_by_job


if __name__ == "__main__":
    matcher = CompositeMatcher()
    # ------------------------ testing single evaluation ------------------------
    single_set = {
        "cv_id": "CV_001",
        "cv_text": "Data Scientist proficient in Python, SQL, and PyTorch.",
        "cv_skills": {"Python", "SQL", "PyTorch"},
        "job_id": "JOB_101",
        "job_text": "Looking for Data Scientist with Python, SQL, and AWS experience.",
        "job_skills": {"Python", "SQL", "AWS"},
    }

    # res = matcher.evaluate_single(
    #     cv_id="CV_001",
    #     cv_text="Data Scientist proficient in Python, SQL, and PyTorch.",
    #     cv_skills={"Python", "SQL", "PyTorch"},
    #     job_id="JOB_101",
    #     job_text="Looking for Data Scientist with Python, SQL, and AWS experience.",
    #     job_skills={"Python", "SQL", "AWS"},
    # )

    # print(f"CV: {res.cv_id} | Job: {res.job_id}")
    # print(f"Overall Fit:    {res.overall_score}%")
    # print(f"Semantic Match: {res.semantic_score}%")
    # print(f"Skill Score:    {res.skill_score}%")
    # print(f"Matched Skills: {res.matched_skills}")
    # print(f"Missing Skills: {res.missing_skills}")

    # ------------------------ testing batch evaluation ------------------------
    batch_candidates = [
        {
            "id": "CV_001",
            "text": "Data Scientist proficient in Python, SQL, and PyTorch.",
            "skills": {"Python", "SQL", "PyTorch"},
        },
        {
            "id": "CV_002",
            "text": """
                        SUJAN SHARMA
                Witten, Germany|ersujansharma@gmail.com|/g♀beWebsite|/♀nednLinkedIn|/gtbGitHub
                Education
                TU Dortmund UniversityDortmund, Germany
                M.Sc. in Data Science (Pursuing) Oct. 2025 – Present
                Nepal Engineering College, Pokhara UniversityChangunarayan, Bhaktapur
                Bachelor of Computer Engineering|GPA 3.55/4.0|Full Scholarship Nov. 2017 – Aug. 2022
                Work Experience
                Machine Learning EngineerAug. 2023 – Nov. 2025
                Fusemachines Nepal, Full-Time Kathmandu, Nepal
                • LeveragedLarge Language Models(GPT, Gemini, AWS Nova, Mistral) withLangChainandLangGraphfor
                information retrieval; enforced strictdata definitions and consistencyin prompt engineering, improving
                chatbot response accuracy by15%and reducing inference costs by20%on election campaign based project.
                • Developedclassification modelsfor action recognition and team classification in avideo analytics pipeline,
                achieving91% accuracy; conductedissue tracking and root cause analysison edge cases to reduce latency
                by 20%.
                • Designed internal knowledge-sharing sessions onAdvanced RAG architectures, emphasizing semantic chunking
                andmapping logicfor retrieval; co-led few weekly research sessions bridging industry practice with applied
                research.
                • Guided and evaluated 15 project teams at AI Fellowship Program 2025 as a Teaching Assistant; delivered 2
                technical lectures as an Instructor.
                AI EngineerSept. 2023 – Dec. 2025
                Letitu, Part-Time Remote – Korea
                • Designed, trained, and deployed an end-to-endML classification pipelinefor student-college prediction, career
                mapping, implementing rigorousdata validation and quality checks(80%+ accuracy), containerised with
                Dockerand served onAWS EC2.
                • AppliedSHAPandLIMEfor model interpretability and feature importance analysis; automated the full model
                lifecycle viaCI/CD pipelinesensuring reproducible training runs and versioned data artefacts.
                Front-end DeveloperNov. 2022 – Aug. 2023
                Treeleaf Technologies, Full-Time Lalitpur, Nepal
                • Contributed to building the data dashboard, share-web, and help-centre pages for the company’s main product.
                • Built a traffic violation management system for a public-sector client using Redux-Saga, protocol buffers, and
                WebSockets; followed Agile SDLC throughout.
                Technical Skills
                Data Governance & Quality: Data validation, Exploratory data analysis, data consistency checks, root-cause
                analysis, issue tracking, master data documentation
                Databases & Data Eng.: PostgreSQL, MySQL, Snowflake, dbt, SQL, Python (Pandas, NumPy), ETL pipelines,
                FastAPI, Flask, RESTful APIs
                ML / AI: PyTorch, TensorFlow, Scikit-Learn, MLflow, OpenCV, NLTK, Streamlit
                LLM / GenAI: LangChain, LangGraph, Hugging Face, LLMs, RAG, Prompt Engineering, pgvector
                Cloud & MLOps: Docker, AWS (EC2, SageMaker), CI/CD, MLflow, Git, GitHub Actions, Linux
                Programming Languages: Python, JavaScript, C++, Bash
                Communication: English (fluent), German (A1 - Learning)
                Publications
                Journal paper|Access
                •Ojha, Trailokya Raj, . . . ,Sujan Sharma. “Deep Learning CNN Models for Diseases Classification in
                Cauliflower Leaves.”Journal of Artificial Intelligence and Capsule Networks7, no. 1 (2025): 32–50.
                Conference paper|Ongoing
                •Sujan Sharma, Muskan Bhandari. “Cross-Modal Relational Knowledge Distillation for Efficient Rare
                Disease Patient Retrieval”
                Teaching Experience
                Visiting Faculty LecturerJan. 2025 – Sept. 2025
                St. Xavier’s College (Tribhuvan University), Part-Time Kathmandu, Nepal
                • TaughtInformation Retrieval(7th sem.) andImage Processing(5th sem.) to 50+ undergraduates, blending
                theory with industry-relevant applications.
                • Delivered a 24-hour hands-on training onGenerative AI and AI Agentsto 2nd- and 3rd-year students.
                Visiting Faculty LecturerMay 2023 – Oct. 2025
                Vedas College (Tribhuvan University), Part-Time Lalitpur, Nepal
                • Taught 250+ undergraduates acrossDiscrete Structures, Computer Architecture, Computer Graphics,
                and Artificial Intelligence; supervised 3 students on major projects.
                Training and Mentorship Experience
                Judge (online round) & MentorDecember 2025
                Evaluated 18 projects and mentored 10+ teams during the 2-day IDEAX Hackathon at Madan B. Memorial College.
                Generative AI Trainer June 2025 – July 2025
                Conducted a 45-hour training on Generative AI at Himalayan College of Engineering, covering all core concepts.
                Python & ML Upskill TrainerDec. 2024 – March 2025
                Delivered 3 months of advanced Python & ML training to 20+ undergraduates, focusing on core concepts and hands-on
                projects.
                AI/ML Mentor January 2024
                Mentored 50 students in 5 groups on ML/AI, offering career guidance at an event organised by Prime IT Club.
                Evaluator (Judge) in Tech FestDecember 2023
                Judged 15+ Web and AI/ML projects aligned with SDGs at Sagarmatha Tech Fest, Sagarmatha Engineering College.
                Projects
                Trustworthy Clinical Decision Support System|Research·Trustworthy AI for Healthcare Feb 2026 – Mar 2026
                •Built an agentic RAG system for medical QA over PubMed using Polars→PubMedBERT embeddings→Weaviate
                hybrid retrieval (BM25 + dense + filters), improving domain-specific retrieval quality.
                •Implemented a LangGraph pipeline with re-ranking (MiniLM) and NLI-based verification, producing grounded
                answers with sentence-level explainability and interpretable trust scores for clinical use.
                RAG-Based CV–Job Matching System|Python, LangChain, FastAPI, pgvector, Streamlit Oct. 2025 – Nov. 2025
                •Built an end-to-end Retrieval-Augmented Generation (RAG) pipeline for CV parsing, semantic similarity scoring,
                and explainable batch CV–job matching, served via a FastAPI backend with pgvector for efficient vector search.
                •Implemented LLM-powered summarisation and prompt engineering strategies using LangChain and LangGraph;
                system supports batch processing with explainable match scores.
                Major Project — Point Out Crops|Python, TensorFlow, Django, Flutter Feb. 2022 – Aug. 2022
                •Cauliflower disease classification on self-collected data with IoT-based real-time monitoring; achieved93.47%
                accuracy with ResNet50 after systematic model comparison.
                •Hosted the classification model on Raspberry Pi to automate motor rotation and spray controls in real time.
                Certifications & A wards
                •Micro-degree in Artificial Intelligence – Fusemachines Jan 2024
                •Generative AI with Large Language Models – DeepLearning.ai / Coursera Dec 2023
                •Data Science Fellow – Fellowship.ai Jan 2023
                •Full Scholarship, Bachelor of Computer Engineering – Nepal Engineering College (value>USD 8,000) 2017–2022
                """,
            "skills": {
                "Fellowship.ai",
                "Master Data Documentation",
                "EngineerAug",
                "Hugging Face",
                "WebSockets",
                "Deep Learning",
                "GPA",
                "Cloud & Mlops: Docker",
                "Git",
                "Exploratory Data Analysis",
                "Linux",
                "Restful Apis",
                "LeveragedLarge",
                "Mysql",
                "SUJAN",
                "SDLC",
                "Fastapi",
                "FestDecember",
                "Pgvector",
                "OpenCV",
                "DeepLearning",
                "Scikit-Learn",
                "Ci/Cd",
                "PubMed",
                "Postgresql",
                "ETL",
                "MiniLM",
                "Docker",
                "EngineerSept",
                "LecturerJan",
                "Data Governance",
                "Github Actions",
                "Analysis",
                "Issue Tracking",
                "UniversityDortmund",
                "LangChain",
                "Agile",
                "NLI",
                "Etl Pipelines",
                "C",
                "TrainerDec",
                "Numpy",
                "SageMaker",
                "CNN",
                "IDEAX",
                "Computer Graphics",
                "PubMedBERT",
                "Data Science",
                "Sql",
                "Python",
                "Data Consistency Checks",
                "Snowflake",
                "ResNet50",
                "Django",
                "Mlflow",
                "TaughtInformation",
                "Pytorch",
                "Aws",
                "Llms",
                "Dbt",
                "Rag",
                "C++",
                "MentorDecember",
                "Flask",
                "Prompt Engineering",
                "Machine Learning",
                "UniversityChangunarayan",
                "Pandas",
                "Tensorflow",
                "Opencv",
                "Javascript",
                "Nltk",
                "GPT",
                "Langgraph",
                "Data Analysis",
                "LecturerMay",
                "Numpy)",
                "LangGraph",
                "RAG",
                "GenAI",
                "Sagemaker)",
                "Bash",
                "Github",
                "AppliedSHAPandLIMEfor",
                "DeveloperNov",
                "Root-cause",
                "Python (pandas",
                "USD",
                "Artificial Intelligence",
                "Streamlit",
                "Aws (ec2",
                "LLM",
                "NLTK",
            },
        },
    ]
    batch_jobs = [
        {
            "id": "JOB_001_Python_Developer",
            "text": "Job Title: Python Developer\n        Category: INFORMATION-TECHNOLOGY\n        Experience Level: Junior (1-3 years)\n\n        Education Required: Bachelor's in CS or related\n\n        Required Skills:\n        Python, Django, Flask, REST APIs, SQL, Git\n\n        Preferred Skills:\n        Docker, AWS, PostgreSQL, Redis, Celery\n\n        Key Responsibilities:\n        Design and develop backend services. Write clean maintainable code. Collaborate with frontend developers. Participate in code reviews. Debug and fix production issues",
            "skills": {"Django", "Flask", "Git", "Python", "REST APIs", "SQL"},
        },
        {
            "id": "JOB_002_Senior_Python_Developer",
            "text": "Job Title: Senior Python Developer\n        Category: INFORMATION-TECHNOLOGY\n        Experience Level: Senior (5+ years)\n\n        Education Required: Bachelor's or Master's in CS\n\n        Required Skills:\n        Python, Django, Flask, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, CI/CD, System Design\n\n        Preferred Skills:\n        GraphQL, Kafka, Terraform, Machine Learning\n\n        Key Responsibilities:\n        Lead backend architecture decisions. Mentor junior developers. Design scalable microservices. Optimize database performance. Implement security best practices. Conduct technical interviews",
            "skills": {
                "AWS",
                "CI/CD",
                "Django",
                "Docker",
                "FastAPI",
                "Flask",
                "Kubernetes",
                "PostgreSQL",
                "Python",
                "System Design",
            },
        },
        {
            "id": "JOB_003_Java_Developer",
            "text": "Job Title: Java Developer\n        Category: INFORMATION-TECHNOLOGY\n        Experience Level: Junior (1-3 years)\n\n        Education Required: Bachelor's in CS or IT\n\n        Required Skills:\n        Java, Spring Boot, Hibernate, REST APIs, MySQL, Maven, Git\n\n        Preferred Skills:\n        Microservices, Docker, Jenkins, Kafka\n\n        Key Responsibilities:\n        Develop enterprise applications. Write unit and integration tests. Participate in agile ceremonies. Troubleshoot application issues. Document technical specifications",
            "skills": {
                "Git",
                "Hibernate",
                "Java",
                "Maven",
                "MySQL",
                "REST APIs",
                "Spring Boot",
            },
        },
    ]

    results_map = matcher.evaluate_batch(
        candidates=batch_candidates,
        jobs=batch_jobs,
        top_k_retrieval=2,
    )

    # results per job
    for job_id, matches in results_map.items():
        print(f"\n--- Rankings for {job_id} ---")
        for rank, match in enumerate(matches, start=1):
            print(
                f" Rank {rank}: {match.cv_id:<25} | "
                f"Overall: {match.overall_score:6.2f}% | "
                f"Semantic: {match.semantic_score:6.2f}% | "
                f"Skills: {match.skill_score:6.2f}%"
            )
            print(f"  Matched Skills: {match.matched_skills}")
