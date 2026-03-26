"""Tests for CLI argument parsing and dispatch."""
import os
import subprocess
import sys

import pytest

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
PYTHON = os.path.join(REPO_DIR, ".venv", "bin", "python")


def run_cli(*args):
    """Run docs CLI and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [PYTHON, "-m", "docs", *args],
        capture_output=True,
        text=True,
        cwd=REPO_DIR,
    )
    return result.returncode, result.stdout, result.stderr


class TestCLI:
    def test_no_args_shows_usage(self):
        rc, stdout, stderr = run_cli()
        assert rc != 0
        assert "usage" in stderr.lower()

    def test_missing_input_file(self, tmp_path):
        rc, stdout, stderr = run_cli("contract", "/nonexistent/file.md")
        assert rc != 0
        assert "not found" in stderr.lower()

    def test_unimplemented_type(self, tmp_path):
        input_path = os.path.join(FIXTURES, "sample_contract_en.md")
        rc, stdout, stderr = run_cli("invoice", input_path)
        assert rc != 0
        assert "not yet implemented" in stderr.lower()

    def test_invalid_type(self):
        rc, stdout, stderr = run_cli("unknown_type", "file.md")
        assert rc != 0

    def test_contract_success(self, tmp_path):
        input_path = os.path.join(FIXTURES, "sample_contract_en.md")
        output_path = str(tmp_path / "cli_test.pdf")
        rc, stdout, stderr = run_cli("contract", input_path, "--output", output_path)
        assert rc == 0
        assert os.path.isfile(output_path)
        assert "✓" in stdout

    def test_lang_flag(self, tmp_path):
        input_path = os.path.join(FIXTURES, "sample_contract_ru.md")
        output_path = str(tmp_path / "cli_ru.pdf")
        rc, stdout, stderr = run_cli("contract", input_path, "--lang", "ru", "--output", output_path)
        assert rc == 0
        assert os.path.isfile(output_path)

    def test_invalid_lang(self):
        input_path = os.path.join(FIXTURES, "sample_contract_en.md")
        rc, stdout, stderr = run_cli("contract", input_path, "--lang", "jp")
        assert rc != 0

    def test_default_output_path(self, tmp_path):
        """Without --output, PDF goes next to input file."""
        import shutil
        # Copy fixture to tmp to avoid polluting fixtures dir
        src = os.path.join(FIXTURES, "sample_contract_en.md")
        dst = str(tmp_path / "my_contract.md")
        shutil.copy(src, dst)

        rc, stdout, stderr = run_cli("contract", dst)
        assert rc == 0
        expected_pdf = str(tmp_path / "my_contract.pdf")
        assert os.path.isfile(expected_pdf)
