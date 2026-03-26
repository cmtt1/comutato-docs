# comutato-docs

Corporate document generator — Markdown to beautifully typeset PDF.

Supports contracts, invoices, proposals, and reports with consistent branding, multi-language support (EN/RU/RO), and professional typography (EB Garamond).

## Install

```bash
git clone https://github.com/cmtt1/comutato-docs.git
cd comutato-docs
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/company.sample.yaml config/company.yaml
# Edit config/company.yaml with your company details
```

## Usage

```bash
source .venv/bin/activate

# Generate a contract
python -m docs contract input.md --lang ro --output output.pdf

# Generate an invoice
python -m docs invoice input.md --lang en

# Check version
python -m docs version

# Check for updates
python -m docs update
```

## Input format

Markdown with YAML front matter:

```yaml
---
type: contract
lang: ro
title: "Contract de prestare a serviciilor"
number: "2026/03-001"
date: "27 martie 2026"
parties:
  - name: "Company A SRL"
    role: "Prestator"
    represented_by: "Name, Title"
  - name: "Company B SRL"
    role: "Beneficiar"
    represented_by: "Name, Title"
---

## 1. Section title

Content here...
```

## Claude Code skill

This repo ships as a Claude Code skill. To use it, add the skill path to your Claude Code config:

```
~/.claude/skills/docs/SKILL.md → points to this repo's SKILL.md
```

Then use `/docs` in Claude Code to generate documents.

## Update

```bash
python -m docs update
```

This checks for new versions, pulls updates, and reinstalls dependencies if `requirements.txt` changed.

## Typography

- **Font:** EB Garamond (serif, bundled)
- **Body:** 12pt, justified, hyphenation enabled
- **Tables:** never break across pages
- **Section breaks:** new section moves to next page only if less than 1/5 page remains

## License

Proprietary — Comutato Solutions S.R.L.
