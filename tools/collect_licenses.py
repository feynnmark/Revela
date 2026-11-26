"""Collect license documents only, never package code or Python caches."""
from importlib.metadata import distributions
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]


def is_license_document(path: Path) -> bool:
    if '__pycache__' in path.parts or path.suffix.lower() in {'.py', '.pyc', '.pyo', '.pyd', '.dll', '.so'}:
        return False
    if path.name.lower().startswith(('license', 'copying', 'notice', 'copyright', 'authors')):
        return True
    return 'licenses' in (p.lower() for p in path.parts) and path.suffix.lower() in {'', '.txt', '.md', '.rst', '.html', '.bsd', '.license'}


def collect() -> None:
    destination = (ROOT / 'build' / 'licenses').resolve()
    if not destination.is_relative_to(ROOT) or destination.parent != ROOT / 'build':
        raise RuntimeError('Invalid generated license directory.')
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    if python_license.is_file():
        (destination / 'Python').mkdir()
        shutil.copy2(python_license, destination / 'Python' / 'LICENSE.txt')
    for distribution in distributions():
        name = distribution.metadata['Name']
        for file in distribution.files or []:
            if not is_license_document(file):
                continue
            source = Path(distribution.locate_file(file))
            if source.is_file():
                relative = Path(*file.parts[1:]) if len(file.parts) > 1 else Path(file.name)
                target = destination / name / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)


if __name__ == '__main__':
    collect()
