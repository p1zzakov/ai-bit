from __future__ import annotations

from pathlib import Path

APP = Path("/app/app.py")


def main() -> None:
    text = APP.read_text(encoding="utf-8")
    import_line = "from discovery.api import router as discovery_router\n"
    if import_line not in text:
        anchor = "from pydantic_settings import BaseSettings, SettingsConfigDict\n"
        if anchor not in text:
            raise RuntimeError("Discovery import anchor not found in app.py")
        text = text.replace(anchor, anchor + import_line, 1)

    include_line = "app.include_router(discovery_router)\n"
    if include_line not in text:
        anchor = 'app = FastAPI(title="AI-BIT Browser Worker", version="0.2.0")\n'
        if anchor not in text:
            raise RuntimeError("FastAPI app anchor not found in app.py")
        text = text.replace(anchor, anchor + include_line, 1)

    APP.write_text(text, encoding="utf-8")
    compiled = APP.read_text(encoding="utf-8")
    for marker in (import_line.strip(), include_line.strip()):
        if marker not in compiled:
            raise RuntimeError(f"Discovery patch incomplete: {marker}")
    print("Applied AI-BIT Discovery ingestion router")


if __name__ == "__main__":
    main()
