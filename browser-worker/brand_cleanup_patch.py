from __future__ import annotations

from pathlib import Path

APP_PATH = Path("/app/app.py")
ADMIN_PATH = Path("/app/admin_dashboard.py")
REPORT_PATH = Path("/app/report_engine.py")


def replace_all(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected {old!r} in {path}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> None:
    replace_all(APP_PATH, "1.0.0-rc.7", "1.0.0-rc.8")
    replace_all(ADMIN_PATH, "1.0.0-rc.7", "1.0.0-rc.8")
    replace_all(REPORT_PATH, "1.0.0-rc.7", "1.0.0-rc.8")
    print("Applied AI-BIT Brand Cleanup patch 1.0.0-rc.8")


if __name__ == "__main__":
    main()
