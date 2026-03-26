---
name: docs
description: Generate branded Comutato documents (contracts, invoices, proposals) from Markdown to PDF
argument-hint: "[contract|invoice|proposal] input.md [--lang ru|en|ro] [--output path.pdf]"
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, AskUserQuestion
---

# /docs — Comutato Corporate Document Generator

Generate beautifully typeset, brand-consistent PDF documents from Markdown input.

## Setup

**IMPORTANT:** Before running any command, resolve the install directory. The SKILL.md you are reading is symlinked from the repo. To find the repo root:

```bash
DOCS_DIR="$(dirname "$(readlink -f ~/.claude/skills/docs/SKILL.md)")"
```

Use `$DOCS_DIR` in all commands below instead of a hardcoded path.

- Venv: `$DOCS_DIR/.venv`
- Dependencies: weasyprint, jinja2, python-frontmatter, markdown, pyphen

## Document Types

| Type | Status | Description |
|------|--------|-------------|
| `contract` | Ready | Legal contracts with title page, parties, signatures |
| `invoice` | Phase 2 | One-page invoices |
| `proposal` | Phase 2 | One-page commercial proposals |
| `report` | Phase 2 | Multi-page reports with TOC |
| `presentation` | Phase 3 | YC-style minimalist slides |

## How to Use

### Step 1: Prepare the input

The user provides content as Markdown. If the input has no YAML front matter, generate it by asking the user for:
- Contract number
- Date
- Party names, roles, and representatives

**Expected front matter for contracts:**
```yaml
---
type: contract
lang: ru          # or en, ro
title: "Договор оказания услуг"
number: "2026/03-001"
date: "26 марта 2026 г."
parties:
  - name: "Comutato SRL"
    role: "Исполнитель"
    represented_by: "Юрий Леванов, Директор"
  - name: "ООО «Клиент»"
    role: "Заказчик"
    represented_by: "Имя Фамилия, Должность"
---
```

### Step 2: Validate the input

Before rendering, check:
1. Front matter has required fields: `type`, `number`, `date`, `parties` (list with at least 2 entries, each with `name`)
2. `--lang` matches the content language. If the body is in Russian but `--lang en`, warn the user.
3. If front matter is missing entirely, ask the user for the required fields and generate it.

### Step 3: Render

```bash
DOCS_DIR="$(dirname "$(readlink -f ~/.claude/skills/docs/SKILL.md)")" && cd "$DOCS_DIR" && source .venv/bin/activate && python -m docs contract {{input_file}} --lang {{lang}} --output ~/Downloads/{{input_basename}}.pdf
```

If the user provides an explicit `--output` path, use that instead of `~/Downloads/`.

Default output: `~/Downloads/{input_basename}.pdf` — always export to Downloads unless `--output` is explicitly provided by the user.

### Step 4: Present result

- Report the output file path and size
- Open the PDF: `open {{output_path}}`

## Typography

- **Font:** EB Garamond (serif, bundled locally)
- **Body:** 12pt, justified, line-height 1.6, hyphenation enabled
- **Headings:** EB Garamond SemiBold, 14-20pt
- **Tables:** 10pt, thin borders, alternating row shading, never break across pages
- **Headers:** "comutato" (lowercase, gray) left, "Page X of Y" right
- **Footer:** Company legal name, address, email (gray, 8pt)
- **Colors:** Dark text (#1a1a1a) on white (#ffffff), no accent colors in contracts

## Languages

Supports Russian (ru), English (en), and Romanian (ro). The `--lang` flag controls:
- Company requisites language in headers/footers
- `<html lang>` attribute for proper hyphenation
- Signature block labels (Подписи сторон / Signatures / Semnăturile părților)

Content must be written in the target language — the skill does NOT translate.

## Examples

```bash
DOCS_DIR="$(dirname "$(readlink -f ~/.claude/skills/docs/SKILL.md)")" && cd "$DOCS_DIR" && source .venv/bin/activate

# Russian contract
python -m docs contract contract.md --lang ru

# English contract with custom output path
python -m docs contract contract_en.md --lang en --output ~/Documents/contract_final.pdf
```

## Update

To check for and install updates:
```bash
DOCS_DIR="$(dirname "$(readlink -f ~/.claude/skills/docs/SKILL.md)")" && cd "$DOCS_DIR" && source .venv/bin/activate && python -m docs update
```

This fetches the latest version from GitHub, shows what changed, pulls updates, and reinstalls dependencies if needed.

## Company Config

Requisites are stored in `$DOCS_DIR/config/company.yaml`. This file is gitignored. To set up for a new installation, copy `company.sample.yaml` and fill in real details.
