"""Tests for company config loading."""
import os
import tempfile

import pytest
import yaml

from docs.config import load_company_config, CONFIG_PATH


class TestLoadCompanyConfig:
    def test_load_valid_config(self):
        config = load_company_config()
        assert "company" in config
        assert "branding" in config
        assert config["company"]["name"] == "comutato"

    def test_load_config_has_required_fields(self):
        config = load_company_config()
        company = config["company"]
        assert "legal_name" in company
        assert "address" in company
        assert "tax_id" in company
        assert "contact" in company
        assert "bank" in company

    def test_load_config_multilingual(self):
        config = load_company_config()
        for lang in ["en", "ru", "ro"]:
            assert lang in config["company"]["legal_name"]
            assert lang in config["company"]["address"]

    def test_missing_config_exits(self):
        with pytest.raises(SystemExit):
            load_company_config("/nonexistent/path/company.yaml")

    def test_malformed_yaml_exits(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: : :\n  broken")
            f.flush()
            try:
                with pytest.raises(SystemExit):
                    load_company_config(f.name)
            finally:
                os.unlink(f.name)

    def test_empty_config_exits(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            try:
                with pytest.raises(SystemExit):
                    load_company_config(f.name)
            finally:
                os.unlink(f.name)

    def test_config_without_company_key_exits(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"branding": {"color": "blue"}}, f)
            f.flush()
            try:
                with pytest.raises(SystemExit):
                    load_company_config(f.name)
            finally:
                os.unlink(f.name)

    def test_branding_defaults(self):
        config = load_company_config()
        branding = config["branding"]
        assert branding["header_text"] == "comutato"
        assert branding["primary_color"] == "#1a1a1a"
        assert branding["background"] == "#ffffff"
