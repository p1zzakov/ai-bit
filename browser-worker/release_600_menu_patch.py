from __future__ import annotations

import re
from pathlib import Path

ADMIN = Path('/app/admin_dashboard.py')


def log(status: str, message: str) -> None:
    print(f'[{status}] {message}')


def insert_navigation(text: str) -> str:
    if re.search(r'data-key=["\']projectIntelligence["\']', text):
        log('SKIP', 'Project Intelligence navigation already exists')
        return text

    button = '<button data-key="projectIntelligence"><span class="icon">ТЗ</span><span class="label">Формирование ТЗ</span></button>'
    anchors = (
        (r'(<button\b[^>]*data-key=["\']onecRequirements["\'][^>]*>.*?</button>)', True),
        (r'(<button\b[^>]*data-key=["\']system["\'][^>]*>.*?</button>)', False),
        (r'(</nav>)', False),
    )
    for pattern, after in anchors:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        pos = match.end(1) if after else match.start(1)
        log('APPLY', 'Project Intelligence navigation inserted')
        return text[:pos] + button + text[pos:]
    raise RuntimeError('6.0.0 navigation container not found')


def insert_frame(text: str) -> str:
    if re.search(r'data-key=["\']projectIntelligence["\'][^>]*data-src=["\']/project-intelligence["\']', text):
        log('SKIP', 'Project Intelligence iframe already exists')
        return text

    frame = '<iframe class="frame" data-key="projectIntelligence" data-src="/project-intelligence"></iframe>'
    anchors = (
        (r'(<iframe\b[^>]*data-key=["\']onecRequirements["\'][^>]*>\s*</iframe>)', True),
        (r'(<iframe\b[^>]*data-key=["\']system["\'][^>]*>\s*</iframe>)', False),
        (r'(</div>\s*</main>)', False),
    )
    for pattern, after in anchors:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        pos = match.end(1) if after else match.start(1)
        log('APPLY', 'Project Intelligence iframe inserted')
        return text[:pos] + frame + text[pos:]
    raise RuntimeError('6.0.0 iframe container not found')


def insert_meta(text: str) -> str:
    if re.search(r'projectIntelligence\s*:\s*\{', text):
        log('SKIP', 'Project Intelligence metadata already exists')
        return text

    item = "projectIntelligence:{title:'Формирование ТЗ',subtitle:'AI Project Analyst: материалы, интервью, MCP-проверка и комплект ТЗ',url:'/project-intelligence'},"
    anchors = (
        (r'(onecRequirements\s*:\s*\{[^{}]*?url\s*:\s*["\']/onec-requirements["\'][^{}]*?\})', True),
        (r'(system\s*:\s*\{[^{}]*?url\s*:\s*["\']/system["\'][^{}]*?\})', False),
    )
    for pattern, after in anchors:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        pos = match.end(1) if after else match.start(1)
        prefix = ',' if after and not text[:pos].rstrip().endswith(',') else ''
        log('APPLY', 'Project Intelligence metadata inserted')
        return text[:pos] + prefix + item + text[pos:]
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
