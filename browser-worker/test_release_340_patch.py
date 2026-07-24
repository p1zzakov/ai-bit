from __future__ import annotations

from release_340_patch import ensure_integrator_workspace


def test_repairs_partial_integrator_workspace() -> None:
    source = '''
    <button data-key="integrator"><span>Интегратору</span></button>
    <button data-key="automation"><span>Автоматизация</span></button>
    <iframe class="frame" data-key="automation" data-src="/automation"></iframe>
    <script>
    const meta={automation:{title:'Scheduling & Automation'}};
    button.classList.add('active');frame.classList.add('active');$('#title').textContent=meta[key].title;$('#subtitle').textContent=meta[key].subtitle;if(!frame.src)
    </script>
    '''

    result = ensure_integrator_workspace(source)

    assert result.count('data-key="integrator"') == 2
    assert '<iframe class="frame" data-key="integrator" data-src="/integrator"></iframe>' in result
    assert "integrator:{title:'Интегратору'" in result
    assert "if(!button||!frame)" in result


def test_patch_is_idempotent() -> None:
    source = '''
    <button data-key="integrator"></button>
    <iframe class="frame" data-key="integrator" data-src="/integrator"></iframe>
    const meta={integrator:{title:'Интегратору',subtitle:'x',url:'/integrator'},automation:{title:'Scheduling & Automation'}};
    '''

    once = ensure_integrator_workspace(source)
    twice = ensure_integrator_workspace(once)

    assert twice == once
