"""CLI argument parsing and dispatch."""
import argparse
import os
import subprocess
import sys

from docs.config import load_company_config
from docs.render import render_document

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION_FILE = os.path.join(ROOT_DIR, "VERSION")
REPO_URL = "https://github.com/cmtt1/comutato-docs.git"


def get_version():
    """Read the current local version from VERSION file."""
    if os.path.isfile(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return "unknown"


def cmd_update():
    """Check for updates and pull if available."""
    print(f"comutato-docs v{get_version()}")
    print(f"Install dir: {ROOT_DIR}")
    print()

    # Check if this is a git repo
    if not os.path.isdir(os.path.join(ROOT_DIR, ".git")):
        print("Not a git checkout — cannot auto-update.")
        print(f"To enable updates, clone from: {REPO_URL}")
        sys.exit(1)

    # Fetch latest
    print("Checking for updates...")
    result = subprocess.run(
        ["git", "fetch", "origin"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error fetching: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    # Compare local vs remote
    local = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT_DIR, capture_output=True, text=True,
    ).stdout.strip()

    remote = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        cwd=ROOT_DIR, capture_output=True, text=True,
    ).stdout.strip()

    if local == remote:
        print(f"✓ Already up to date (v{get_version()})")
        return

    # Show what's new
    print("Updates available:")
    subprocess.run(
        ["git", "log", "--oneline", f"{local}..{remote}"],
        cwd=ROOT_DIR,
    )
    print()

    # Pull
    print("Pulling updates...")
    result = subprocess.run(
        ["git", "pull", "origin", "main"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error pulling: {result.stderr.strip()}", file=sys.stderr)
        print("Try: git stash && git pull origin main && git stash pop")
        sys.exit(1)

    # Reinstall dependencies if requirements changed
    diff_files = subprocess.run(
        ["git", "diff", "--name-only", local, "HEAD"],
        cwd=ROOT_DIR, capture_output=True, text=True,
    ).stdout
    if "requirements.txt" in diff_files:
        print("requirements.txt changed — reinstalling dependencies...")
        venv_pip = os.path.join(ROOT_DIR, ".venv", "bin", "pip")
        if os.path.isfile(venv_pip):
            subprocess.run(
                [venv_pip, "install", "-r", os.path.join(ROOT_DIR, "requirements.txt")],
                cwd=ROOT_DIR,
            )

    print(f"✓ Updated to v{get_version()}")


def cmd_version():
    """Print version and exit."""
    print(f"comutato-docs v{get_version()}")


def main():
    parser = argparse.ArgumentParser(
        prog="docs",
        description="Generate branded Comutato documents from Markdown to PDF.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # update subcommand
    subparsers.add_parser("update", help="Check for and install updates")

    # version subcommand
    subparsers.add_parser("version", help="Print current version")

    # document generation (positional: type + input)
    gen_parser = subparsers.add_parser(
        "contract", help="Generate a contract PDF"
    )
    gen_parser.add_argument("input", help="Input Markdown file path")
    gen_parser.add_argument(
        "--lang", default="en", choices=["en", "ru", "ro"],
        help="Language for company requisites and hyphenation (default: en)",
    )
    gen_parser.add_argument(
        "--output", default=None,
        help="Output PDF path (default: {input_basename}.pdf)",
    )

    inv_parser = subparsers.add_parser(
        "invoice", help="Generate an invoice PDF"
    )
    inv_parser.add_argument("input", help="Input Markdown file path")
    inv_parser.add_argument(
        "--lang", default="en", choices=["en", "ru", "ro"],
        help="Language for company requisites and hyphenation (default: en)",
    )
    inv_parser.add_argument(
        "--output", default=None,
        help="Output PDF path (default: {input_basename}.pdf)",
    )

    args = parser.parse_args()

    if args.command == "update":
        cmd_update()
        return

    if args.command == "version":
        cmd_version()
        return

    if args.command not in ("contract", "invoice"):
        parser.print_help()
        sys.exit(1)

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output
    if output_path is None:
        output_path = os.path.splitext(args.input)[0] + ".pdf"

    config = load_company_config()

    render_document(
        doc_type=args.command,
        input_path=args.input,
        output_path=output_path,
        lang=args.lang,
        config=config,
    )

    size_kb = os.path.getsize(output_path) / 1024
    print(f"✓ {output_path} ({size_kb:.0f} KB)")
