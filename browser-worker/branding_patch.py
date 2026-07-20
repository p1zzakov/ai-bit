from __future__ import annotations

from pathlib import Path

ADMIN_PATH = Path("/app/admin_dashboard.py")
APP_PATH = Path("/app/app.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Patch {label!r} expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    text = ADMIN_PATH.read_text(encoding="utf-8")
    text = text.replace("1.0.0-rc.6", "1.0.0-rc.9")
    text = text.replace("1.0.0-rc.7", "1.0.0-rc.9")
    text = text.replace("1.0.0-rc.8", "1.0.0-rc.9")

    system_button = '<button data-key="system"><span class="icon">S</span><span class="label">Система</span></button>'
    text = replace_once(
        text,
        system_button,
        system_button + '<button data-key="about"><span class="icon">?</span><span class="label">О системе</span></button>',
        "about navigation",
    )

    system_frame = '<iframe class="frame" data-key="system" data-src="/system"></iframe>'
    text = replace_once(
        text,
        system_frame,
        system_frame + '<iframe class="frame" data-key="about" data-src="/about"></iframe>',
        "about frame",
    )

    system_meta = "system:{title:'Система и качество данных',subtitle:'Источники, права, свежесть и диагностика',url:'/system'}"
    text = replace_once(
        text,
        system_meta,
        system_meta + ",about:{title:'О системе',subtitle:'Разработчик, версия и Brand Integrity',url:'/about'}",
        "about metadata",
    )

    # Explicitly mark every module URL loaded inside Unified Admin. This is more
    # reliable than depending only on browser Sec-Fetch-Dest headers.
    for path in (
        "/executive",
        "/dashboard",
        "/operations",
        "/processes",
        "/business-architecture",
        "/reports-ui",
        "/automation",
        "/system",
        "/about",
    ):
        text = text.replace(f'data-src="{path}"', f'data-src="{path}?embedded=1"')

    ADMIN_PATH.write_text(text, encoding="utf-8")

    app_text = APP_PATH.read_text(encoding="utf-8")
    app_text = app_text.replace("1.0.0-rc.7", "1.0.0-rc.9")
    app_text = app_text.replace("1.0.0-rc.8", "1.0.0-rc.9")
    APP_PATH.write_text(app_text, encoding="utf-8")
    print("Applied AI-BIT developer info icon patch 1.0.0-rc.9")


if __name__ == "__main__":
    main()
