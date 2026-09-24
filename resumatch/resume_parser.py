from pathlib import Path
from pypdf import PdfReader
from docx import Document
import argparse


# Document Reader for parsing text from Pdf/docs/md/txt files
class DocumentParser:
    """Parses text content from local document files."""

    def parse(self, file_path: str | Path) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if path.suffix.lower() == ".pdf":
            return self._parse_pdf(path)
        elif path.suffix.lower() in [".doc", ".docx",".txt", ".md"]:
            if path.suffix.lower() in [".doc", ".docx"]:
                try:
                    doc = Document(path)
                    return "\n".join([para.text for para in doc.paragraphs])
                except ImportError:
                    raise ImportError("python-docx is required to parse .doc/.docx files")
            else:
                return path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    # use pypdf for pdf files
    def _parse_pdf(self, path: Path) -> str:
        reader = PdfReader(path)
        text_content = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_content.append(extracted)
        return "\n".join(text_content)


# CLI for the parsing only
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse text from document files.")
    parser.add_argument("file_path", type=str, help="Path to the document file")
    args = parser.parse_args()

    document_parser = DocumentParser()
    try:
        result = document_parser.parse(args.file_path)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
