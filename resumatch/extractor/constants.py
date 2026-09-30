# Taxonomies, regex patterns, and constant used for profile extraction

# predefined skills for tech related jobs( not mendatory, but can be used for better accuracy)

HEADER_STOPWORDS = {
    "experience",
    "education",
    "skills",
    "projects",
    "summary",
    "profile",
    "work history",
}


DEFAULT_SKILL_TAXONOMY: set[str] = {
    # Programming Languages
    "python",
    "java",
    "c++",
    "c#",
    "c",
    "r",
    "go",
    "golang",
    "rust",
    "swift",
    "kotlin",
    "javascript",
    "typescript",
    "php",
    "ruby",
    "sql",
    "html",
    "css",
    "scala",
    "elixir",
    "haskell",
    "matlab",
    "sas",
    "d3.js",
    # Data Science, AI & ML
    "pandas",
    "numpy",
    "scipy",
    "scikit-learn",
    "pytorch",
    "tensorflow",
    "keras",
    "matplotlib",
    "seaborn",
    "machine learning",
    "deep learning",
    "data science",
    "natural language processing",
    "nlp",
    "computer vision",
    "bayesflow",
    "data engineering",
    "data architecture",
    "data governance",
    "data modeling",
    "data quality",
    "data analytics",
    "big data",
    "artificial intelligence",
    "reinforcement learning",
    "lenstronomy",
    "rag",
    "langchain",
    "langgraph",
    # Web Frameworks & Backend
    "react",
    "angular",
    "vue",
    "django",
    "flask",
    "fastapi",
    "spring",
    "express",
    "node.js",
    "svelte",
    "tailwind",
    "next.js",
    "nuxt.js",
    "laravel",
    "symfony",
    "spring boot",
    "ruby on rails",
    "asp.net",
    "rest api",
    "graphql",
    "microservices",
    # Cloud, DevOps & Tools
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "git",
    "github",
    "gitlab",
    "ci/cd",
    "jenkins",
    "terraform",
    "ansible",
    "linux",
    "bash",
    "prometheus",
    "grafana",
    "datadog",
    "helm",
    # Databases & Storage
    "postgresql",
    "mysql",
    "mongodb",
    "sqlite",
    "redis",
    "elasticsearch",
    "neo4j",
    "pgvector",
    "snowflake",
    "dbt",
    # Methodologies & General
    "agile",
    "scrum",
    "unit testing",
    "pytest",
    "data analysis",
    "system design",
    "object-oriented programming",
}

# academic Degree with regex
DEGREE_PATTERNS: dict[str, str] = {
    "Bachelor": r"(?:\bB\.?S\.?|\bB\.?A\.?|\bBachelor\b|\bBSc\b|\bB\.?Tech\b)(?![a-zA-Z0-9])",
    "Master": r"(?:\bM\.?S\.?|\bM\.?A\.?|\bMaster\b|\bMSc\b|\bM\.?Tech\b)(?![a-zA-Z0-9])",
    "PhD": r"(?:\bPh\.?D\.?|\bDoctorate\b|\bDoctor of Philosophy\b)(?![a-zA-Z0-9])",
}

# contact Information regex
CONTACT_PATTERNS: dict[str, str] = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "phone": r"\(?\+?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}",
    "github": r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+",
    "linkedin": r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+",
}

# section Header extraction
SKILLS_SECTION_PATTERN = (
    r"(?:TECHNICAL\s+SKILLS|SKILLS|COMPETENCIES|TOOLS)\s*:?\n?"  # As of now
    r"(.*?)(?=\n\n|\n[A-Z\s]{4,}:|\Z)"
)

# technical entity pattern
TECH_ENTITY_PATTERN = (
    r"\b([A-Z][a-z0-9]+[A-Z][a-zA-Z0-9]+)\b|"  # camelCase (OpenCV, HuggingFace)
    r"\b([A-Z]{3,5})\b|"  # acronyms (CUDA, FPGA, LLM, NLP)
    r"\b([a-zA-Z0-9\-_]+\.(?:js|py|io|ai|db))\b"  # code extensions (Next.js, Node.js)
)

# non-skill words to ignore during dynamic discovery
STOPWORD_EXCLUSIONS: set[str] = {
    "email",
    "phone",
    "github",
    "linkedin",
    "education",
    "experience",
    "summary",
    "projects",
    "profile",
}
