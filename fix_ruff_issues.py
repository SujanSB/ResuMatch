import re
from pathlib import Path


def refactor_file(file_path: Path):
    content = file_path.read_text(encoding="utf-8")
    original = content

    # 1. Fix C414: sorted(list(...)) -> sorted(...)
    content = re.sub(r'sorted\s*\(\s*list\s*\((.*?)\)\s*\)', r'sorted(\1)', content)

    # 2. Fix PLR0402: import matplotlib.gridspec as gridspec -> from matplotlib import gridspec
    content = re.sub(
        r'import\s+matplotlib\.gridspec\s+as\s+gridspec',
        'from matplotlib import gridspec',
        content
    )

    # 3. Fix RUF059: unused pie chart unpacks -> _wedges, _texts, autotexts
    content = re.sub(
        r'wedges\s*,\s*texts\s*,\s*autotexts\s*=\s*ax2\.pie',
        '_wedges, _texts, autotexts = ax2.pie',
        content
    )

    # 4. Fix C408: common dict(...) kwargs to dict literals in visualizer.py
    # Fix bbox=dict(...)
    content = re.sub(
        r'bbox\s*=\s*dict\s*\(\s*boxstyle\s*=\s*(["\'].*?["\'])\s*,\s*facecolor\s*=\s*(["\'].*?["\'])\s*,\s*edgecolor\s*=\s*(["\'].*?["\'])\s*\)',
        r'bbox={"boxstyle": \1, "facecolor": \2, "edgecolor": \3}',
        content
    )
    # Fix wedgeprops=dict(...)
    content = re.sub(
        r'wedgeprops\s*=\s*dict\s*\(\s*width\s*=\s*(.*?)\s*,\s*edgecolor\s*=\s*(["\'].*?["\'])\s*\)',
        r'wedgeprops={"width": \1, "edgecolor": \2}',
        content
    )

    if content != original:
        file_path.write_text(content, encoding="utf-8")
        print(f"Updated: {file_path}")

def main():
    py_files = list(Path("resumatch").rglob("*.py")) + list(Path("tests").rglob("*.py"))
    for py_file in py_files:
        refactor_file(py_file)

if __name__ == "__main__":
    main()