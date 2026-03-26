"""Core rendering pipeline: Markdown → HTML → Jinja2 → WeasyPrint → PDF."""
import os
import re
import sys

import frontmatter
import markdown as md
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
STYLES_DIR = os.path.join(ROOT_DIR, "styles")
FONTS_DIR = os.path.join(ROOT_DIR, "fonts")

MARKDOWN_EXTENSIONS = [
    "tables",
    "fenced_code",
    "toc",
    "sane_lists",
    "attr_list",
]


def validate_contract_frontmatter(metadata):
    """Validate contract front matter has required fields.
    Returns list of error messages (empty = valid).
    """
    errors = []
    required = ["type", "number", "date", "parties"]
    for field in required:
        if field not in metadata:
            errors.append(f"Missing required field: '{field}'")

    if "parties" in metadata:
        parties = metadata["parties"]
        if not isinstance(parties, list) or len(parties) < 2:
            errors.append("'parties' must be a list with at least 2 entries")
        else:
            for i, party in enumerate(parties):
                if not isinstance(party, dict):
                    errors.append(f"Party {i+1} must be a dict with 'name' and 'role'")
                elif "name" not in party:
                    errors.append(f"Party {i+1} missing 'name'")

    return errors


def validate_invoice_frontmatter(metadata):
    """Validate invoice front matter has required fields.
    Returns list of error messages (empty = valid).
    """
    errors = []
    required = ["number", "date", "parties", "items", "total"]
    for field in required:
        if field not in metadata:
            errors.append(f"Missing required field: '{field}'")

    if "parties" in metadata:
        parties = metadata["parties"]
        if not isinstance(parties, list) or len(parties) < 2:
            errors.append("'parties' must be a list with at least 2 entries")
        else:
            for i, party in enumerate(parties):
                if not isinstance(party, dict) or "name" not in party:
                    errors.append(f"Party {i+1} must be a dict with 'name'")

    if "items" in metadata:
        items = metadata["items"]
        if not isinstance(items, list) or len(items) < 1:
            errors.append("'items' must be a non-empty list")

    return errors


def load_css(doc_type):
    """Load base.css + document-type CSS, return combined string."""
    css_parts = []

    # Font-face declarations for EB Garamond
    # WeasyPrint doesn't support variable font weight ranges, so we declare
    # specific weights pointing to the same variable font file.
    fonts_uri = "file://" + FONTS_DIR.replace(" ", "%20")
    for weight, weight_name in [("400", "normal"), ("600", "bold")]:
        css_parts.append(f"""
@font-face {{
    font-family: 'EB Garamond';
    src: url('{fonts_uri}/EBGaramond-Variable.ttf') format('truetype');
    font-weight: {weight};
    font-style: normal;
}}
@font-face {{
    font-family: 'EB Garamond';
    src: url('{fonts_uri}/EBGaramond-Italic-Variable.ttf') format('truetype');
    font-weight: {weight};
    font-style: italic;
}}
""")

    for name in ["base", doc_type]:
        css_path = os.path.join(STYLES_DIR, f"{name}.css")
        if os.path.isfile(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                css_parts.append(f.read())
        else:
            print(f"Warning: CSS file not found: {css_path}", file=sys.stderr)

    return "\n".join(css_parts)


def _wrap_sections(html):
    """Wrap each heading (h2/h3) + first content block in a section-start div.

    Page-break rule: a new section should only move to the next page if it
    would start in the last 1/5 of the page (~140pt on A4).  We achieve this
    by wrapping the heading + the first following block element in a
    non-breakable container with min-height equal to 1/5 of the page body.
    The rest of the section content flows normally and can break across pages.
    """
    # Split on h2/h3 opening tags, keeping the delimiter
    parts = re.split(r'(?=<h[23][ >])', html)
    if len(parts) <= 1:
        return html

    out = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if re.match(r'<h[23][ >]', part):
            # Capture the heading + first two block elements so the
            # non-breakable chunk is naturally ~120-160pt tall (≈1/5 page).
            block_tag = r'<(?:p|table|ul|ol|blockquote|div)\b[^>]*>.*?</(?:p|table|ul|ol|blockquote|div)>'
            pattern = (
                r'(<h[23][^>]*>.*?</h[23]>\s*)'   # the heading itself
                r'(' + block_tag + r')'             # first block
                r'(\s*' + block_tag + r')?'         # optional second block
            )
            m = re.match(pattern, part, re.DOTALL)
            if m:
                head_and_blocks = m.group(0)
                rest = part[m.end():]
                out.append(
                    f'<div class="section-start">{head_and_blocks}</div>{rest}'
                )
            else:
                # Heading with no parseable blocks — wrap heading alone
                out.append(f'<div class="section-start">{part}</div>')
        else:
            # Content before the first heading (preamble)
            out.append(part)

    return "\n".join(out)


def render_document(doc_type, input_path, output_path, lang, config):
    """Full rendering pipeline."""
    # 1. Parse input with front matter
    with open(input_path, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)

    metadata = dict(post.metadata)
    body_md = post.content

    # 2. Validate front matter
    if doc_type == "contract":
        errors = validate_contract_frontmatter(metadata)
    elif doc_type == "invoice":
        errors = validate_invoice_frontmatter(metadata)
    else:
        errors = []

    if errors:
        print("Error: invalid front matter:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    # 3. Convert Markdown body to HTML
    body_html = md.markdown(body_md, extensions=MARKDOWN_EXTENSIONS)

    # 3a. Wrap heading+content groups in <section> tags for page-break control.
    # Each h2/h3 and everything until the next h2/h3 becomes a section.
    body_html = _wrap_sections(body_html)

    # 4. Load CSS
    css = load_css(doc_type)

    # 5. Load and render Jinja2 template
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template(f"{doc_type}.html")

    # Build template context
    company = config.get("company", {})
    branding = config.get("branding", {})

    context = {
        "body": body_html,
        "meta": metadata,
        "lang": lang,
        "company": company,
        "branding": branding,
        "css": css,
        # Language-specific company info
        "company_legal_name": company.get("legal_name", {}).get(lang, company.get("legal_name", {}).get("en", "")),
        "company_address": company.get("address", {}).get(lang, company.get("address", {}).get("en", "")),
        "company_tax_id": company.get("tax_id", ""),
        "company_registration": company.get("registration", ""),
        "company_email": company.get("contact", {}).get("email", ""),
        "company_phone": company.get("contact", {}).get("phone", ""),
        "company_website": company.get("contact", {}).get("website", ""),
        "bank_name": company.get("bank", {}).get("name", ""),
        "bank_iban": company.get("bank", {}).get("iban", ""),
        "bank_swift": company.get("bank", {}).get("swift", ""),
        "header_text": branding.get("header_text", "comutato"),
    }

    html_string = template.render(**context)

    # 6. Render PDF with WeasyPrint
    try:
        pdf_bytes = HTML(
            string=html_string,
            base_url=ROOT_DIR,
        ).write_pdf()
    except Exception as e:
        print(f"Error rendering PDF: {e}", file=sys.stderr)
        sys.exit(1)

    # 7. Write output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
