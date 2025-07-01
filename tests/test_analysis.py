import os
import tempfile
import pytest

from langtools_mcp.lsp.analysis import (
    validate_file_type, run_analysis_for_language,
    BaseAnalyzer, register_analyzer, ANALYZER_REGISTRY
)

def test_python_file_success():
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tf:
        tf.write(b'# python test file')
        tf.flush()
        try:
            assert validate_file_type(tf.name) == 'python'
        finally:
            os.remove(tf.name)

def test_go_file_success():
    with tempfile.NamedTemporaryFile(suffix='.go', delete=False) as tf:
        tf.write(b'// go test file')
        tf.flush()
        try:
            assert validate_file_type(tf.name) == 'go'
        finally:
            os.remove(tf.name)

def test_unsupported_extension_raises():
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tf:
        tf.write(b'plain text')
        tf.flush()
        try:
            with pytest.raises(ValueError, match=r'Unsupported file extension'):
                validate_file_type(tf.name)
        finally:
            os.remove(tf.name)

def test_missing_file_raises():
    missing = '/tmp/this_file_does_not_exist_123456.py'
    if os.path.exists(missing):
        os.remove(missing)
    with pytest.raises(ValueError, match=r'File does not exist'):
        validate_file_type(missing)

class DummyAnalyzer(BaseAnalyzer):
    def analyze(self, file_path: str) -> dict:
        return {"result": f"dummy analysis for {file_path}"}

def test_run_analysis_for_language_success():
    # Register dummy
    register_analyzer("python", DummyAnalyzer)
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tf:
        tf.write(b'# test')
        tf.flush()
        try:
            result = run_analysis_for_language(tf.name)
            assert result["result"].startswith("dummy analysis")
        finally:
            os.remove(tf.name)

def test_run_analysis_unregistered_language_raises():
    # Save and clear registry
    old_reg = ANALYZER_REGISTRY.copy()
    ANALYZER_REGISTRY.clear()
    with tempfile.NamedTemporaryFile(suffix='.go', delete=False) as tf:
        tf.write(b'// test go')
        tf.flush()
        try:
            with pytest.raises(NotImplementedError, match=r'No analyzer registered for language'):
                run_analysis_for_language(tf.name)
        finally:
            os.remove(tf.name)
    ANALYZER_REGISTRY.clear()
    ANALYZER_REGISTRY.update(old_reg)
