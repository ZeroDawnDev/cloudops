"""
yaml_parser.py
--------------
Parses Kubernetes manifests and Docker Compose files (both are YAML,
but have different shapes) into the normalized ParsedInfra schema.
"""

import logging
from typing import Any, Dict, List

import yaml

from models import ParsedInfra, InfraKind

logger = logging.getLogger("cloudops.parser.yaml")


def _looks_like_compose(doc: Dict[str, Any]) -> bool:
    return isinstance(doc, dict) and ("services" in doc or "version" in doc and "services" in doc)


def parse_kubernetes(filename: str, raw_text: str) -> ParsedInfra:
    """
    Kubernetes manifests can contain multiple `---`-separated documents
    (e.g. a Deployment + a Service in one file). Each becomes one resource.
    """
    resources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

    try:
        docs = [d for d in yaml.safe_load_all(raw_text) if d]
    except yaml.YAMLError as exc:
        logger.warning("YAML parse error in %s: %s", filename, exc)
        metadata["parse_error"] = str(exc)
        return ParsedInfra(kind=InfraKind.KUBERNETES, filename=filename, raw_text=raw_text, metadata=metadata)

    for doc in docs:
        resources.append(
            {
                "type": doc.get("kind", "Unknown"),
                "name": doc.get("metadata", {}).get("name", "unnamed"),
                "config": doc,
            }
        )

    metadata["resource_count"] = len(resources)
    return ParsedInfra(
        kind=InfraKind.KUBERNETES,
        filename=filename,
        raw_text=raw_text,
        resources=resources,
        metadata=metadata,
    )


def parse_docker_compose(filename: str, raw_text: str) -> ParsedInfra:
    """Each service in a docker-compose.yml becomes one resource."""
    resources: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

    try:
        doc = yaml.safe_load(raw_text) or {}
    except yaml.YAMLError as exc:
        logger.warning("YAML parse error in %s: %s", filename, exc)
        metadata["parse_error"] = str(exc)
        return ParsedInfra(kind=InfraKind.DOCKER_COMPOSE, filename=filename, raw_text=raw_text, metadata=metadata)

    for service_name, config in (doc.get("services") or {}).items():
        resources.append({"type": "docker_service", "name": service_name, "config": config})

    metadata["compose_version"] = doc.get("version")
    metadata["resource_count"] = len(resources)
    return ParsedInfra(
        kind=InfraKind.DOCKER_COMPOSE,
        filename=filename,
        raw_text=raw_text,
        resources=resources,
        metadata=metadata,
    )


def parse_yaml_auto(filename: str, raw_text: str) -> ParsedInfra:
    """Detects whether a .yml/.yaml file is Kubernetes or Docker Compose."""
    try:
        first_doc = next(yaml.safe_load_all(raw_text))
    except (yaml.YAMLError, StopIteration):
        first_doc = {}

    if _looks_like_compose(first_doc or {}):
        return parse_docker_compose(filename, raw_text)
    return parse_kubernetes(filename, raw_text)
