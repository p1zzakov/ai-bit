from __future__ import annotations

import re
from pathlib import Path

APP = Path("/app/app.py")
IMPORT_LINE = "from discovery.api import router as discovery_router\n"
INCLUDE_LINE = "app.include_router(discovery_router)\n"


def insert_after_imports(text: str) -> str:
    if IMPORT_LINE in text:
        return text

    matches = list(
        re.finditer(
            r"^(?:from\s+[\w.]+\s+import\s+.+|import\s+.+)\n",
            text,
            flags=re.MULTILINE,
        )
    )
    if not matches:
        raise RuntimeError("Python import block not found in app.py")

    position = matches[-1].end()
    return text[:position] + IMPORT_LINE + text[position:]


def insert_router_registration(text: str) -> str:
    if INCLUDE_LINE in text:
        return text

    app_assignment = re.search(
        r"^app\s*=\s*FastAPI\([^\n]*\)\s*$",
        text,
        flags=re.MULTILINE,
    )
    if app_assignment is None:
        raise RuntimeError("FastAPI app assignment not found in app.py")

    position = app_assignment.end()
    return text[:position] + "\n" + INCLUDE_LINE.rstrip("\n") + text[position:]


def main() -> None:
    text = APP.read_text(encoding="utf-8")
    text = insert_after_imports(text)
    text = insert_router_registration(text)
    APP.write_text(text, encoding="utf-8")

    compiled = APP.read_text(encoding="utf-8")
    for marker in (IMPORT_LINE.strip(), INCLUDE_LINE.strip()):
        if marker not in compiled:
            raise RuntimeError(f"Discovery patch incomplete: {marker}")

    compile(compiled, str(APP), "exec")
    print("Applied AI-BIT Discovery ingestion router")


if __name__ == "__main__":
    main()
