"""단독 재검토판을 오프라인 Edge에서 열고 최신 BIN 픽셀과 표시를 대조한다."""
import importlib.util
import json
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_disc import file_hash

spec = importlib.util.spec_from_file_location('prior_album_checks', ROOT / 'work/sprite_consistency_20261105/zero/album/verify_album.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
OUT = ROOT / 'out/sprite_reaudit_20261106'


def main():
    manifest = json.loads((OUT / 'manifest.json').read_text('utf8'))
    html = ROOT / manifest['HTML']
    assert file_hash(html) == manifest['sha256']
    forms, pixels, errors, external = [], [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 1100}, device_scale_factor=1, offline=True)
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('request', lambda r: external.append(r.url) if not r.url.startswith(('file:', 'data:', 'blob:')) else None)
        page.goto(html.as_uri(), wait_until='load')
        checks.loaded(page)
        assert page.evaluate('DATA.reduce((n,c)=>n+c.frames.length-c.partial.length,0)') == 4510
        assert page.evaluate('DATA.reduce((n,c)=>n+c.revised_count,0)') == len(manifest['changes'])
        chars = page.evaluate('DATA.map(c=>({id:c.id,forms:c.forms.map(f=>f.id)}))')
        page.locator('#guides').uncheck()
        for char in chars:
            page.locator(f'#characters button[data-id="{char["id"]}"]').click()
            for form in char['forms']:
                page.select_option('#form', form)
                checks.loaded(page)
                assert page.locator('#cards .card').count() == page.evaluate('subset.length')
                last = page.locator('#cards .card').last
                last.locator('button').click()
                checks.loaded(page)
                forms.append({'character': char['id'], 'form': form, 'last_frame': page.evaluate('chosen.id')})
                if form != 'partial_fourth':
                    pixels.append(checks.exact_image(page, '#after'))
        for name, mode, ref, group in (
                ('shibuki', 'ver_buki_riko', 79, 'dash'),
                ('shibuki', 'ver_buki_riko', 37, 'air'),
                ('nana', 'ver_rin_nana', 120, 'hurt_lowhp'),
                ('nana', 'ver_rin_nana', 141, 'arrival')):
            source = manifest['sources'][mode]
            assert file_hash(ROOT / source['bin']) == source['sha256']
            resource = 'PL02_U.ARC' if name == 'shibuki' else 'PL00_U.ARC'
            arc = Archive(read_disc(ROOT / source['bin'], (resource,))[0][resource])
            page.locator(f'#characters button[data-id="{name}"]').click()
            if name == 'shibuki':
                for form, mask in (('ultimate_before', 15), ('ultimate_after', 0)):
                    page.select_option('#form', form)
                    page.select_option('#group', group)
                    page.locator(f'.card[data-id="{form}_{ref:03}"] button').click()
                    checks.loaded(page)
                    pixels.append(checks.exact_image(page, '#after', arc.composite(ref, mask, 2)[0]))
            else:
                page.select_option('#form', 'partial_fourth')
                page.select_option('#group', group)
                page.locator(f'.card[data-id="partial_fourth_{ref:03}"] button').click()
                for arm in (1, 2):
                    page.select_option('#armorArm', str(arm))
                    for mask in range(16):
                        page.select_option('#armorMask', str(mask))
                        checks.loaded(page)
                        pixels.append(checks.exact_image(page, '#after', arc.composite(ref, mask, arm)[0]))
        assert not errors and not external, (errors, external)
        browser.close()
    report = {'passed': True, 'html_sha256': file_hash(html), 'forms': forms,
              'pixel_checks': pixels, 'external_requests': external, 'browser_errors': errors,
              'gameplay_runtime_verified': False}
    (Path(__file__).parent / 'album_browser_checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf8')
    print(json.dumps({'passed': True, 'forms': len(forms), 'pixel_checks': len(pixels)}))


if __name__ == '__main__':
    main()
