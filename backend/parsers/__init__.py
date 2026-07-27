"""
parsers package
----------------
Exposes `parse_file`, which routes an uploaded file to the correct
specialized parser based on its extension/name, returning a ParsedInfra.
"""

from models import ParsedInfra, InfraKind
from parsers.terraform_parser import parse_terraform
from parsers.yaml_parser import parse_yaml_auto
from parsers.log_parser import parse_logs


class UnsupportedFileError(ValueError):
    pass


def parse_file(filename: str, raw_text: str) -> ParsedInfra:
    lower = filename.lower()

    if lower.endswith(".tf") or lower.endswith(".tfvars"):
        return parse_terraform(filename, raw_text)

    if lower.endswith(".yml") or lower.endswith(".yaml"):
        return parse_yaml_auto(filename, raw_text)

    if lower.endswith(".log") or lower.endswith(".txt"):
        return parse_logs(filename, raw_text)

    if lower.endswith(".json"):
        # Could be a structured log export or a raw CloudFormation-ish file;
        # treat as logs by default since agents just read raw_text either way.
        return parse_logs(filename, raw_text)

    raise UnsupportedFileError(
        f"Unsupported file type for '{filename}'. "
        "Supported: .tf, .tfvars, .yml, .yaml, .log, .txt, .json"
    )
