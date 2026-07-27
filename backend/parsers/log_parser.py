"""
log_parser.py
-------------
Parses raw cloud error logs (CloudWatch/Stackdriver/Azure Monitor style
plaintext, or JSON-lines logs) into the normalized ParsedInfra schema.
We don't try to fully structure logs -- agents read raw_text directly --
but we do extract lightweight signals (error counts, timestamps, keywords)
into metadata to help the LLM focus.
"""

import json
import re
from collections import Counter
from typing import Any, Dict, List

from models import ParsedInfra, InfraKind

ERROR_KEYWORDS = [
    "error", "exception", "timeout", "throttl", "denied", "refused",
    "unavailable", "fatal", "critical", "fail", "5xx", "500", "503",
]


def parse_logs(filename: str, raw_text: str) -> ParsedInfra:
    lines = [ln for ln in raw_text.splitlines() if ln.strip()]
    keyword_counts: Counter = Counter()
    resources: List[Dict[str, Any]] = []

    for line in lines:
        lower = line.lower()
        for kw in ERROR_KEYWORDS:
            if kw in lower:
                keyword_counts[kw] += 1

        # Try to parse JSON-lines logs (common for CloudWatch exports)
        stripped = line.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                parsed_line = json.loads(stripped)
                resources.append({"type": "log_event", "name": None, "config": parsed_line})
                continue
            except json.JSONDecodeError:
                pass

    metadata = {
        "line_count": len(lines),
        "keyword_counts": dict(keyword_counts),
        "structured_events": len(resources),
    }

    return ParsedInfra(
        kind=InfraKind.LOGS,
        filename=filename,
        raw_text=raw_text,
        resources=resources,
        metadata=metadata,
    )
