# Extractor for information extraction from resumes
import re
from typing import Literal
from typing import Literal, Dict, List
from resumatch.extractor.constants import (
    CONTACT_PATTERNS,
    DEFAULT_SKILL_TAXONOMY,
    DEGREE_PATTERNS,
    SKILLS_SECTION_PATTERN,
    STOPWORD_EXCLUSIONS,
    TECH_ENTITY_PATTERN,
    HEADER_STOPWORDS 
)
from resumatch.utils.models import ExtractedProfile

# extracts candidate metadata, contact info, degrees, and skills.
class ProfileExtractor:
    def __init__(
        self,
        taxonomy: set[str] | None = None,
        mode: Literal["all", "taxonomy", "dynamic"] = "all",
    ) -> None:
        self.taxonomy = taxonomy or DEFAULT_SKILL_TAXONOMY
        self.mode = mode

    def extract(self, text: str) -> ExtractedProfile:
        """Extracts contact info, degrees, and skills from the given text."""
        email = self._extract_regex(text, CONTACT_PATTERNS["email"])
        phone = self._extract_regex(text, CONTACT_PATTERNS["phone"])
        github = self._extract_regex(text, CONTACT_PATTERNS["github"])
        linkedin = self._extract_regex(text, CONTACT_PATTERNS["linkedin"])

        degrees = self._extract_degrees(text)

        section_texts = self._extract_sections(text)
        achievements = self._extract_achievements(text, section_texts)
        volunteering = self._extract_volunteering(text, section_texts)
        
        # extract taxonomy skills
        taxonomy_skills = (
            self._extract_taxonomy_skills(text)
            if self.mode in ("all", "taxonomy")
            else set()
        )

        # extract dynamically discovered skills
        dynamic_skills = (
            self._extract_dynamic_skills(text, exclude=taxonomy_skills)
            if self.mode in ("all", "dynamic")
            else set()
        )

        # combine with source flags
        skills_with_sources: dict[str, str] = {
            skill: "default_taxonomy" for skill in taxonomy_skills
        }
        for skill in dynamic_skills:
            skills_with_sources[skill] = "dynamic_discovered"

        all_skills = taxonomy_skills.union(dynamic_skills)

        return ExtractedProfile(
raw_text=text,
            email=email,
            phone=phone,
            github=github,
            linkedin=linkedin,
            degrees=degrees,
            skills=all_skills,
            taxonomy_skills=taxonomy_skills,
            dynamic_skills=dynamic_skills,
            skills_with_sources=skills_with_sources,
            achievements=achievements,
            volunteering=volunteering,
            section_texts=section_texts,
        )

    def _extract_regex(self, text: str, pattern: str) -> str | None:
        # regex pattern match 
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return match.group(0) if match else None

    def _extract_degrees(self, text: str) -> list[str]:
        # get academic degrees with regex
        found_degrees: list[str] = []
        for degree_name, pattern in DEGREE_PATTERNS.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                found_degrees.append(degree_name)
        return found_degrees

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Splits raw text into key sections for downstream visualizer context."""
        sections = {
            "Experience": "",
            "Projects": "",
            "Education": "",
            "Awards": "",
            "Volunteering": "",
        }

        # Header detection regex
        exp_match = re.search(
            r"(?i)(work experience|experience|employment history)(.*?)(?=education|projects|skills|certifications|volunteering|awards|\Z)",
            text,
            re.DOTALL,
        )
        proj_match = re.search(
            r"(?i)(projects|key projects)(.*?)(?=experience|education|skills|certifications|volunteering|awards|\Z)",
            text,
            re.DOTALL,
        )
        award_match = re.search(
            r"(?i)(certifications & awards|awards|honors|achievements)(.*?)(?=experience|projects|education|skills|volunteering|\Z)",
            text,
            re.DOTALL,
        )
        vol_match = re.search(
            r"(?i)(volunteering|volunteer|teaching experience|training and mentorship)(.*?)(?=experience|projects|education|skills|awards|\Z)",
            text,
            re.DOTALL,
        )

        if exp_match:
            sections["Experience"] = exp_match.group(2).strip()
        if proj_match:
            sections["Projects"] = proj_match.group(2).strip()
        if award_match:
            sections["Awards"] = award_match.group(2).strip()
        if vol_match:
            sections["Volunteering"] = vol_match.group(2).strip()

        return sections

    def _extract_achievements(
        self, text: str, sections: Dict[str, str]
    ) -> List[str]:
        """Extracts bullet points containing metrics, awards, or key impact phrases."""
        highlights: List[str] = []
        target_text = sections.get("Awards") or text

        lines = [line.strip() for line in target_text.split("\n") if line.strip()]
        metric_pattern = r"(?i)(\baward\b|\bhonors?\b|\bscholarship\b|\bfirst\b|\b%\b|\$\d+|\breduced\b|\bincreased\b|\bachieved\b)"

        for line in lines:
            clean_line = re.sub(r"^[•\-\*\d\.\s]+", "", line).strip()
            if len(clean_line) > 15 and re.search(metric_pattern, clean_line):
                # Format long lines
                truncated = clean_line[:110] + "..." if len(clean_line) > 110 else clean_line
                if truncated not in highlights:
                    highlights.append(truncated)
            if len(highlights) >= 3:
                break

        return highlights

    def _extract_volunteering(
        self, text: str, sections: Dict[str, str]
    ) -> List[str]:
        """Extracts leadership, mentorship, or volunteering entries."""
        vol_items: List[str] = []
        target_text = sections.get("Volunteering") or ""

        if not target_text:
            vol_match = re.search(
                r"(?i)(mentor|mentored|judge|judged|trainer|trained|volunteered|community)(.*?)(?=\n\n|\Z)",
                text,
            )
            if vol_match:
                target_text = vol_match.group(0)

        lines = [line.strip() for line in target_text.split("\n") if line.strip()]
        for line in lines:
            clean_line = re.sub(r"^[•\-\*\d\.\s]+", "", line).strip()
            if len(clean_line) > 15 and not any(h in clean_line.lower() for h in HEADER_STOPWORDS):
                truncated = clean_line[:110] + "..." if len(clean_line) > 110 else clean_line
                if truncated not in vol_items:
                    vol_items.append(truncated)
            if len(vol_items) >= 3:
                break

        return vol_items

    def _extract_taxonomy_skills(self, text: str) -> set[str]:
        clean_text = text.lower()
        found_skills: set[str] = set()

        for skill in self.taxonomy:
            escaped_skill = re.escape(skill.lower())
            # prevent 'c' from matching inside 'c++' or 'c#'
            pattern = rf"(?<![a-zA-Z0-9]){escaped_skill}(?![a-zA-Z0-9+#.])"
            if re.search(pattern, clean_text):
                found_skills.add(skill)

        return found_skills
    

    def _extract_dynamic_skills(self, text: str, exclude: set[str]) -> set[str]:

        discovered: set[str] = set()
        exclude_lower = {s.lower() for s in exclude} | HEADER_STOPWORDS

        section_match = re.search(
            SKILLS_SECTION_PATTERN, text, flags=re.IGNORECASE | re.DOTALL
        )

        if section_match:
            section_text = section_match.group(1)
            # Split on colons, commas, pipes, semicolons, asterisks, newlines, and bullet points
            raw_tokens = re.split(r"[:,•|;\n\*\&]", section_text)
            
            for token in raw_tokens:
                clean_token = re.sub(r"^[\s\-\*\•\d\.]+", "", token).strip()
                clean_token = re.sub(r"[\(\)]", "", clean_token).strip()

                if 2 <= len(clean_token) <= 30 and not any(
                    c in clean_token for c in ["@", "http", "/", "\\"]
                ):
                    token_lower = clean_token.lower()
                    if token_lower not in exclude_lower:
                        discovered.add(token_lower)

        return discovered

def run_extractor(cv_text: str) -> None:
    """Run extraction demo on a sample string."""
    extractor = ProfileExtractor(mode="all")
    profile = extractor.extract(cv_text)

    print(f"Email: {profile.email}")
    print(f"Phone: {profile.phone}")
    print(f"Degrees: {profile.degrees}")
    print(f"Skills ({len(profile.skills)}): {profile.skills}")
    print("\nSkill Source Mapping:")
    for skill, source in profile.skills_with_sources.items():
        print(f"  - {skill}: [{source}]")


if __name__ == "__main__":
    cv_text1 = """
    Sujan Sharma
    Email: sujan@example.com | Phone: +49 123 456 789
    LinkedIn: linkedin.com/in/sujansharma | GitHub: github.com/SujanSB
    Education: MSc in Data Science

    Technical Skills:
    Python, PyTorch, Scikit-Learn, Docker, Git, SQL, C++, REST API,
    OpenCV, HuggingFace, Vitis_HLS, Next.js, CUDA
    """
    

    cv_text2 = """
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
        """
    cv_text3 ="""
        INFORMATION TECHNOLOGY
        Summary
        Dedicated  Information Assurance Professional  well-versed in analyzing and mitigating risk and finding cost-effective
        solutions. Excels at boosting performance and productivity by establishing realistic goals and enforcing deadlines. 
        Versatile IT professional with 37 years of Enterprise design and engineering methodology.
        Skills
        |  |  |
        | --- | --- |
        | * Enterprise platforms * Knowledge of Product Lifecycle Management (PLM) * Project tracking * Hardware and software
        upgrade planning * Product requirements documentation * Self-directed * MS Visio * Decisive * Collaborative * Domain
        Active Directory Layout * Data storage engineering | * Information Assurance * Risk Management Framework (RMF) *
        Active Directory design and deployment * Workstation build and deployment * Systems Accreditation Packages * Red
        Hat Enterprise Linux installation and hardening * Network Design & Troubleshooting * High Performance Computing |
        Experience
        Company Name    City  ,   State    Information Technology   02/2011  to   Current
        I was hired to manage accreditation
        efforts for a major department modernization project involving 3
        accreditation packages each leading to successful Authorization To
        Operate decisions. Responsibilities then increased to include all
        departmental accreditation efforts leading to another 3 successful
        ATOs. Now, working on 4 new accreditation including
        re-authorization for an existing project. Succeeded in writing and
        implementing vulnerability management for existing accredited
        systems.
        Success
        of the accreditation hinged on coordination with ONI Enterprise in
        critical design decisions and to help the program integrate smoothly
        into the Enterprise thru many meetings, analyzing the Enterprise
        business model to understand the best fit for the program.
        The
        different projects required careful management of specific STIG
        compliance and hardening for the different configurations and
        services required for the specific domain to be integrated.   Analyzed complex computer systems to assess vulnerability
        and risk.    Supervised  5 external computer consultants and vendors.    Managed application patches, data backup,
        security changes and network configuration.
        Company Name    City  ,   State    Systems Engineer   02/2006  to   02/2011
        I was Hired
        to initiate processing strategies in fulfilling department analyst requirements. Requirements were fulfilled thru i dentifying
        product problems and strengths and collected data on customer experience  and review of Enterprise compliance to
        transition to new
        technology for supporting new processing needs thru proper processing
        power.  The next challenge  came as storage requirements for better performance and more
        controlled uses. After careful study of local infrastructure design, a local storage with off the shelf solutions was
        adopted to grow local storage to over 200TB. In using this solution,
        the department saved just over a million dollars in purchasing and
        maintenance costs compared to the alternative. Next came requirements to improve processing of future big data
        formats fulfilled in a Red Hat Linux high compute cluster I designed, purchased and
        accredited for operation in the Enterprise.  Improvement on big data analytical processing reduced time from
        30 hours to 30 minutes as well as allow for more robust data thru
        higher selections of sensors, frequencies and range than allowed thru
        the traditional process.
        Company Name    City  ,   State    Senior Systems Analyst   02/1999  to   02/2006
        I was hired to improve corporate and
        client communications and processing requirements which resulted in
        the design, build and deployment of 3 Enterprise network solutions. One
        solution resulted in expanding capabilities to supporting Washington
        Navy Yard, Norfolk Virginia and Hawaii support facilities.
        Fulfilled
        requirements for detecting crucial network software/hardware
        weaknesses and developing preventive strategies and solutions for
        avoiding interruptions and increasing system security thru
        documenting system layouts, wiring diagrams and addressing schema to
        understand layouts and make informed solutions to upper management.
        Education and Training
        Associate of Science  :  Electronic Engineering   1980     Florence Darlington Technical School  ,   City  ,   State
        Electronic Engineering.
        Dean's list for high GPA.
        Class President for second year
        Skills
        - Active Directory
        - Hardware Engineering
        - Information Technology
        - Red Hat Enterprise Linux Servers
        - MS Windows Servers
        - MS Windows Desktop
        - Network Design & Troubleshooting
        - Architectural Diagrams
        - Accreditation Boundarys
        - Risk Management
        - Enterprise Strategies
        - Vendor Relations
        - Desktop Publishing Software: Photoshop, Illustrator, HTML
        - Team Work
        - Collaboration
            """
    run_extractor(cv_text1)