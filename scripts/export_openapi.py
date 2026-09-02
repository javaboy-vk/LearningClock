# =============================================================================
# File Name : export_openapi.py
# Artifact  : LearningClock - OpenAPI Schema Exporter
# Author    : javaboy-vk
# Date      : 2026-08-25
# Version   : v0.1.1
# Purpose:
#   Generates the tracked OpenAPI JSON contract from the FastAPI application.
# =============================================================================

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from learningclock.api import app  # noqa: E402

OPENAPI_PATH = ROOT / "docs" / "openapi.json"


# Source documentation:
#   What it does: Writes the FastAPI schema to the tracked OpenAPI contract file.
#   Why it exists: Runtime Swagger/ReDoc and reviewed docs must derive from one app object.
#   Designed use: Run dev openapi after route/model/metadata changes; only openapi.json changes.
def main() -> int:
    schema = json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"
    OPENAPI_PATH.write_text(schema, encoding="utf-8")
    print(f"wrote {OPENAPI_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
