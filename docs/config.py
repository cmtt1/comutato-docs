"""Company configuration loading and validation."""
import os
import sys

import yaml

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "config", "company.yaml")
SAMPLE_CONFIG_PATH = os.path.join(ROOT_DIR, "config", "company.sample.yaml")


def load_company_config(config_path=None):
    """Load and return the company configuration dict."""
    path = config_path or CONFIG_PATH

    if not os.path.isfile(path):
        print(
            f"Error: company config not found at {path}\n"
            f"Run: cp {SAMPLE_CONFIG_PATH} {CONFIG_PATH}\n"
            "Then fill in your company details.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error: malformed company.yaml: {e}", file=sys.stderr)
            sys.exit(1)

    if not config or "company" not in config:
        print("Error: company.yaml must have a 'company' section.", file=sys.stderr)
        sys.exit(1)

    return config
