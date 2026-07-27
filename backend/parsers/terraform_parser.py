"""
terraform_parser.py
--------------------
Parses .tf files (HCL2) into the normalized ParsedInfra schema so
downstream agents never need to know HCL syntax.
"""

import io
import logging
from typing import Any, Dict, List

import hcl2

from models import ParsedInfra, InfraKind

logger = logging.getLogger("cloudops.parser.terraform")


def _strip_quotes(value):
    """
    Some python-hcl2 versions leave literal surrounding double-quotes on
    string keys/values (e.g. '"aws_s3_bucket"' instead of 'aws_s3_bucket').
    Normalize recursively so downstream agents see clean identifiers.
    """
    if isinstance(value, str) and len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    if isinstance(value, dict):
        return {_strip_quotes(k): _strip_quotes(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_strip_quotes(v) for v in value]
    return value


def parse_terraform(filename: str, raw_text: str) -> ParsedInfra:
    """
    Parses raw Terraform HCL text into a flat list of resource dicts:
    [{"type": "aws_s3_bucket", "name": "data", "config": {...}}, ...]

    Falls back gracefully (empty resource list + error note in metadata)
    on malformed HCL instead of crashing the whole pipeline.
    """
    resources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

    try:
        parsed = hcl2.load(io.StringIO(raw_text))
    except Exception as exc:  # noqa: BLE001
        logger.warning("HCL parse error in %s: %s", filename, exc)
        metadata["parse_error"] = str(exc)
        return ParsedInfra(
            kind=InfraKind.TERRAFORM,
            filename=filename,
            raw_text=raw_text,
            resources=[],
            metadata=metadata,
        )

    # hcl2 returns top-level blocks as lists: resource, provider, variable, module...
    for resource_block in parsed.get("resource", []):
        for resource_type, instances in resource_block.items():
            resource_type = _strip_quotes(resource_type)
            for resource_name, config in instances.items():
                resources.append(
                    {
                        "type": resource_type,
                        "name": _strip_quotes(resource_name),
                        "config": _strip_quotes(config),
                    }
                )

    metadata["providers"] = parsed.get("provider", [])
    metadata["variables"] = parsed.get("variable", [])
    metadata["resource_count"] = len(resources)

    return ParsedInfra(
        kind=InfraKind.TERRAFORM,
        filename=filename,
        raw_text=raw_text,
        resources=resources,
        metadata=metadata,
    )
