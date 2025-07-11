from abc import ABC, abstractmethod
from pathlib import Path

SUPPORTED_LANGUAGES = {
    ".py": "python",
    ".go": "go",
}


class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, file_path: str) -> dict:
        """
        Analyze the file and return structured results.
        """
        pass


ANALYZER_REGISTRY = {}


def register_analyzer(language: str, analyzer_cls):
    ANALYZER_REGISTRY[language] = analyzer_cls()


def validate_file_type(file_path: str) -> str:
    """
    Checks if the provided file path exists and is a supported language file.
    Returns the detected language string (python/go).
    Raises ValueError if not supported or if file does not exist.
    """
    p = Path(file_path)
    if not p.is_file():
        raise ValueError(f"File does not exist: {file_path!r}")
    ext = p.suffix.lower()
    if ext not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported file extension: {ext!r}. Only .py and .go files are supported."
        )
    return SUPPORTED_LANGUAGES[ext]


def run_analysis_for_language(file_path: str) -> dict:
    language = validate_file_type(file_path)
    analyzer = ANALYZER_REGISTRY.get(language)
    if not analyzer:
        raise NotImplementedError(f"No analyzer registered for language: {language!r}")
    return analyzer.analyze(file_path)
