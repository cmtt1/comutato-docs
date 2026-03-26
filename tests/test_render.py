"""Tests for the rendering pipeline."""
import os
import tempfile

import frontmatter
import pytest

from docs.config import load_company_config
from docs.render import (
    render_document,
    validate_contract_frontmatter,
    load_css,
    FONTS_DIR,
    STYLES_DIR,
    TEMPLATES_DIR,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestValidateContractFrontmatter:
    def test_valid_frontmatter(self):
        meta = {
            "type": "contract",
            "number": "2026/01-001",
            "date": "Jan 1, 2026",
            "parties": [
                {"name": "Company A", "role": "Provider"},
                {"name": "Company B", "role": "Client"},
            ],
        }
        assert validate_contract_frontmatter(meta) == []

    def test_missing_type(self):
        meta = {"number": "001", "date": "Jan 1", "parties": [{"name": "A"}, {"name": "B"}]}
        errors = validate_contract_frontmatter(meta)
        assert any("type" in e for e in errors)

    def test_missing_number(self):
        meta = {"type": "contract", "date": "Jan 1", "parties": [{"name": "A"}, {"name": "B"}]}
        errors = validate_contract_frontmatter(meta)
        assert any("number" in e for e in errors)

    def test_missing_parties(self):
        meta = {"type": "contract", "number": "001", "date": "Jan 1"}
        errors = validate_contract_frontmatter(meta)
        assert any("parties" in e for e in errors)

    def test_parties_not_list(self):
        meta = {"type": "contract", "number": "001", "date": "Jan 1", "parties": "not a list"}
        errors = validate_contract_frontmatter(meta)
        assert any("list" in e for e in errors)

    def test_parties_too_few(self):
        meta = {"type": "contract", "number": "001", "date": "Jan 1", "parties": [{"name": "A"}]}
        errors = validate_contract_frontmatter(meta)
        assert any("at least 2" in e for e in errors)

    def test_party_missing_name(self):
        meta = {
            "type": "contract",
            "number": "001",
            "date": "Jan 1",
            "parties": [{"name": "A", "role": "X"}, {"role": "Y"}],
        }
        errors = validate_contract_frontmatter(meta)
        assert any("missing 'name'" in e for e in errors)

    def test_empty_metadata(self):
        errors = validate_contract_frontmatter({})
        assert len(errors) >= 4  # All required fields missing


class TestLoadCSS:
    def test_loads_base_css(self):
        css = load_css("contract")
        assert "EB Garamond" in css
        assert "@page" in css

    def test_loads_contract_css(self):
        css = load_css("contract")
        assert "contract-title-page" in css
        assert "contract-signatures" in css

    def test_includes_font_face(self):
        css = load_css("contract")
        assert "@font-face" in css
        assert "EBGaramond-Variable.ttf" in css

    def test_nonexistent_type_warns(self, capsys):
        css = load_css("nonexistent")
        captured = capsys.readouterr()
        assert "Warning" in captured.err


class TestRenderDocument:
    @pytest.fixture
    def config(self):
        return load_company_config()

    def test_render_russian_contract(self, config, tmp_path):
        input_path = os.path.join(FIXTURES, "sample_contract_ru.md")
        output_path = str(tmp_path / "output_ru.pdf")
        render_document("contract", input_path, output_path, "ru", config)
        assert os.path.isfile(output_path)
        assert os.path.getsize(output_path) > 1000  # Not empty

    def test_render_english_contract(self, config, tmp_path):
        input_path = os.path.join(FIXTURES, "sample_contract_en.md")
        output_path = str(tmp_path / "output_en.pdf")
        render_document("contract", input_path, output_path, "en", config)
        assert os.path.isfile(output_path)
        assert os.path.getsize(output_path) > 1000

    def test_render_deterministic(self, config, tmp_path):
        """Same input produces structurally identical PDF output.
        Note: WeasyPrint embeds creation timestamps, so byte-for-byte
        comparison fails. We compare page count, text content, and file
        size instead.
        """
        import fitz

        input_path = os.path.join(FIXTURES, "sample_contract_en.md")
        output1 = str(tmp_path / "run1.pdf")
        output2 = str(tmp_path / "run2.pdf")
        render_document("contract", input_path, output1, "en", config)
        render_document("contract", input_path, output2, "en", config)

        doc1 = fitz.open(output1)
        doc2 = fitz.open(output2)
        assert len(doc1) == len(doc2)
        for i in range(len(doc1)):
            assert doc1[i].get_text() == doc2[i].get_text()
        # File sizes should be within 1% (timestamps differ slightly)
        size1 = os.path.getsize(output1)
        size2 = os.path.getsize(output2)
        assert abs(size1 - size2) / max(size1, size2) < 0.01
        doc1.close()
        doc2.close()

    def test_render_creates_output_directory(self, config, tmp_path):
        input_path = os.path.join(FIXTURES, "sample_contract_en.md")
        output_path = str(tmp_path / "nested" / "dir" / "output.pdf")
        render_document("contract", input_path, output_path, "en", config)
        assert os.path.isfile(output_path)

    def test_invalid_frontmatter_exits(self, config, tmp_path):
        """Contract with missing required fields should fail validation."""
        input_path = os.path.join(FIXTURES, "no_frontmatter.md")
        output_path = str(tmp_path / "should_fail.pdf")
        with pytest.raises(SystemExit):
            render_document("contract", input_path, output_path, "en", config)

    def test_pdf_has_multiple_pages(self, config, tmp_path):
        """Russian contract fixture should produce multi-page PDF."""
        input_path = os.path.join(FIXTURES, "sample_contract_ru.md")
        output_path = str(tmp_path / "multipage.pdf")
        render_document("contract", input_path, output_path, "ru", config)

        import fitz
        doc = fitz.open(output_path)
        assert len(doc) >= 3  # Title page + body + signatures
        doc.close()

    def test_pdf_contains_cyrillic_text(self, config, tmp_path):
        """Russian contract should have Cyrillic text extractable."""
        input_path = os.path.join(FIXTURES, "sample_contract_ru.md")
        output_path = str(tmp_path / "cyrillic.pdf")
        render_document("contract", input_path, output_path, "ru", config)

        import fitz
        doc = fitz.open(output_path)
        full_text = "".join(page.get_text() for page in doc)
        doc.close()
        assert "Договор" in full_text
        assert "Исполнитель" in full_text
        assert "Comutato SRL" in full_text

    def test_pdf_has_header_footer(self, config, tmp_path):
        """Pages 2+ should have comutato header and company footer."""
        input_path = os.path.join(FIXTURES, "sample_contract_ru.md")
        output_path = str(tmp_path / "headers.pdf")
        render_document("contract", input_path, output_path, "ru", config)

        import fitz
        doc = fitz.open(output_path)
        # Page 2 (index 1) should have header
        page2_text = doc[1].get_text()
        assert "comutato" in page2_text.lower()
        assert "Page 2" in page2_text or "page 2" in page2_text.lower()
        doc.close()

    def test_pdf_table_not_split(self, config, tmp_path):
        """Payment table should stay on one page."""
        input_path = os.path.join(FIXTURES, "sample_contract_ru.md")
        output_path = str(tmp_path / "table.pdf")
        render_document("contract", input_path, output_path, "ru", config)

        import fitz
        doc = fitz.open(output_path)
        # The payment table has "15 000 EUR" — find which page
        for i, page in enumerate(doc):
            text = page.get_text()
            if "15 000 EUR" in text and "20 000 EUR" in text:
                # Both amounts on same page = table not split
                break
        else:
            pytest.fail("Payment table amounts not found on any single page")
        doc.close()


class TestResourcePaths:
    def test_fonts_dir_exists(self):
        assert os.path.isdir(FONTS_DIR)

    def test_font_files_exist(self):
        assert os.path.isfile(os.path.join(FONTS_DIR, "EBGaramond-Variable.ttf"))
        assert os.path.isfile(os.path.join(FONTS_DIR, "EBGaramond-Italic-Variable.ttf"))

    def test_templates_dir_exists(self):
        assert os.path.isdir(TEMPLATES_DIR)
        assert os.path.isfile(os.path.join(TEMPLATES_DIR, "contract.html"))

    def test_styles_dir_exists(self):
        assert os.path.isdir(STYLES_DIR)
        assert os.path.isfile(os.path.join(STYLES_DIR, "base.css"))
        assert os.path.isfile(os.path.join(STYLES_DIR, "contract.css"))
