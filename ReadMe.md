# ResuMatch

**ResuMatch** is an automated resume matching and candidate recommendation system. It leverages a hybrid pipeline combining dense semantic retrieval, cross-encoder re-ranking, and heuristic skill extraction to evaluate and rank candidate resumes against job descriptions across multiple industry categories.

---


## Repository Structure

```text
RESUMATCH/
├── data/
│   ├── data_preparation/       # Notebooks & processing scripts for raw datasets
│   └── sample_data/            # Sample resumes and job description CSV files
|       └── jobs
        └── resumes
├── reports/
│   ├── jobs/                   # Generated visual analytics and candidate reports
│       └── Job_101/
|   └──batch_recommendations.json
├── resumatch/                  # Core ResuMatch Application Package
│   ├── extractor/
│   │   ├── constants.py        # Regex definitions, skill taxonomies, and keywords
│   │   └── resume_extractor.py # Candidate profile feature extraction
│   ├── matcher/
│   │   ├── heuristics.py       # Skill overlap and string matching logic
│   │   ├── reranker.py         # Stage 2 Cross-Encoder re-ranking module
│   │   ├── resume_matcher.py   # Hybrid matching orchestration engine
│   │   └── retriever.py        # Stage 1 Bi-Encoder vector retrieval
│   ├── parser/                 # Document parsing drivers (PDF/DOCX/TXT)
|   |   └── resume_parser.py
│   ├── utils/
│   │   └── job_loader.py       # CSV job description loader and category filter
|   |   └── models.py           # Data models and schema definitions
│   ├── __main__.py             # Main CLI execution entry point
|   ├── app.py                  # Main file of functions controlling overall pipeline             
│   └── recommender.py          # Batch recommendation orchestrator
|   └── visualizer.py           # Report and chart generation script
├── tests/                      # Unit and integration tests
├── pyproject.toml              # Dependency definitions and package configuration
└── README.md

```

---   

## System Architecture

![ResuMatch System Architecture](assets/architecture.png)

The processing pipeline is organized into five modular layers:

1. **Input Layer**
   * **PDF Resume Directory:** Ingests candidate resumes in multiple formats (`.pdf`, `.docx`, `.txt`).
   * **Job Descriptions CSV:** Loads structured job description datasets.

2. **Data Loading & Parsing Layer**
   * **Resume Parser (`resumatch.parser`):** Extracts raw text from candidate document files.
   * **Information Extractor (`resumatch.extractor`):** Parses unstructured resume text into structured candidate profile entities.
   * **Job Loader (`resumatch.utils.job_loader`):** Standardizes CSV job records into normalized job dictionary objects.

3. **Hybrid Matching Engine (`resumatch.matcher`)**
   * **Fast Semantic Retrieval (`retriever.py`):** Employs dense vector embeddings (`all-MiniLM-L6-v2`) for initial candidate selection.
   * **Deep Re-ranking (`reranker.py`):** Uses Cross-Encoder models (`BAAI/bge-reranker-base`) to score semantic affinity.
   * **Heuristic Skills Overlay (`heuristics.py`):** Performs exact and fuzzy skill matching to identify matched vs. missing skill sets.
   * **Weighted Composite Score:** Synthesizes semantic relevancy and skill overlap into a unified candidate match score.

4. **Recommendation & Reporting Layer (`resumatch.recommender`)**
   * **Candidate Ranking:** Ranks candidates per target job position.
   * **Recommendation Tiers:** Classifies candidates into *Strongly Recommended*, *Consider*, or *Not Recommended*.
   * **Structured JSON Export:** Aggregates profile metrics and match diagnostics into standard JSON outputs.

5. **Visualization & Analytics Layer (`resumatch.visualizer`)**
   * **Job Directory Generation:** Automatically organizes output directories under `reports/` for each Job ID.
   * **Candidate Visual Reports:** Renders visual match summaries, analytics charts, and individual candidate reports.

---   


## Sample Visual Report

ResuMatch automatically generates individual candidate intelligence reports featuring match telemetry, skill gap ratios, profile word clouds, and recruiter decision summary cards.

![Sample Candidate Report](assets/Sujan_Sharma_report.png)

---
