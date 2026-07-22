from __future__ import annotations

import re
from pathlib import Path

ADMIN = Path('/app/admin_dashboard.py')
VERSION = '6.0.0'
KEY = 'projectIntelligence'
URL = '/project-intelligence'


def log(status: str, message: str) -> None:
    print(f'[{status}] {message}')


def insert_navigation(text: str) -> str:
    if re.search(r'data-key=["\']projectIntelligence["\']', text):
        log('SKIP', 'Project Intelligence navigation already exists')
        return text

    button = (
        '<button data-key="projectIntelligence">'
        '<span class="icon">ТЗ</span>'
        '<span class="label">Формирование ТЗ</span>'
        '</button>'
    )

    anchors = (
        r'(<button\b[^>]*data-key=["\']onecRequirements["\'][^>]*>.*?</button>)',
        r'(<button\b[^>]*data-key=["\']system["\'][^>]*>.*?</button>)',
        r'(</nav>)',
    )
    for index, pattern in enumerate(anchors):
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        # After the old 5.1 item, otherwise before System/closing nav.
        if index == 0:
            pos = match.end(1)
        else:
            pos = match.start(1)
        text = text[:pos] + button + text[pos:]
        log('APPLY' if index < 2 else 'FALLBACK', 'Project Intelligence navigation inserted')
        return text

    raise RuntimeError('6.0.0 navigation container not found')


def insert_frame(text: str) -> str:
    if re.search(
        r'data-key=["\']projectIntelligence["\'][^>]*data-src=["\']/project-intelligence["\']',
        text,
        flags=re.IGNORECASE,
    ):
        log('SKIP', 'Project Intelligence iframe already exists')
        return text

    frame = '<iframe class="frame" data-key="projectIntelligence" data-src="/project-intelligence"></iframe>'
    anchors = (
        r'(<iframe\b[^>]*data-key=["\']onecRequirements["\'][^>]*>\s*</iframe>)',
        r'(<iframe\b[^>]*data-key=["\']system["\'][^>]*>\s*</iframe>)',
        r'(</div>\s*</main>)',
    )
    for index, pattern in enumerate(anchors):
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        if index == 0:
            pos = match.end(1)
        else:
            pos = match.start(1)
        text = text[:pos] + frame + text[pos:]
        log('APPLY' if index < 2 else 'FALLBACK', 'Project Intelligence iframe inserted')
        return text

    raise RuntimeError('6.0.0 iframe container not found')


def insert_meta(text: str) -> str:
    if re.search(r'projectIntelligence\s*:\s*\{', text):
        log('SKIP', 'Project Intelligence metadata already exists')
        return text

    item = (
        "projectIntelligence:{title:'Формирование ТЗ',"
        "subtitle:'AI Project Analyst: материалы, интервью, MCP-проверка и комплект ТЗ',"
        "url:'/project-intelligence'},"
    )

    anchors = (
        r'(onecRequirements\s*:\s*\{[^{}]*?url\s*:\s*["\']/onec-requirements["\'][^{}]*?\})',
        r'(system\s*:\s*\{[^{}]*?url\s*:\s*["\']/system["\'][^{}]*?\})',
    )
    for index, pattern in enumerate(anchors):
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        if index == 0:
            pos = match.end(1)
            prefix = ',' if not text[:pos].rstrip().endswith(',') else ''
            text = text[:pos] + prefix + item + text[pos:]
        else:
            pos = match.start(1)
            text = text[:pos] + item + text[pos:]
        log('APPLY', 'Project Intelligence metadata inserted')
        return text

    raise RuntimeError('6.0.0 page metadata map not found')


def validate(text: str) -> None:
    required = (
        'data-key="projectIntelligence"',
        'data-src="/project-intelligence"',
        'projectIntelligence:{title:',
        "url:'/project-intelligence'",
        'Формирование ТЗ',
    )
    missing = [marker for marker in required if marker not in text]
    if missing:
        raise RuntimeError(f'6.0.0 navigation patch incomplete: {missing}')
    log('OK', 'Project Intelligence navigation validation passed')


def main() -> None:
    text = ADMIN.read_text(encoding='utf-8')
    text = insert_navigation(text)
    text = insert_frame(text)
    text = insert_meta(text)
    validate(text)
    ADMIN.write_text(text, encoding='utf-8')
    print('Applied AI-BIT Enterprise 6.0.0 — Project Intelligence Navigation Fix')


if __name__ == '__main__':
    main()
