"""통일화 모음집의 네 캐릭터·실제 자원 픽셀·원래 재생표를 오프라인 검사한다."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from playwright.sync_api import sync_playwright
from scripts.build_sprite_style_album import extracted, zero_image, zero_palettes, selection_image
from scripts.c01_audio_build import read_disc, require
from scripts.export_x_consistency import Archive
from scripts.export_sprite_playback import parse_sequence, TABLES
from src.psx_disc import file_hash


def main(directory):
    directory = directory.resolve()
    require(directory.is_relative_to(ROOT / 'out'), 'Album must be inside outputs')
    manifest = json.loads((directory / 'manifest.json').read_text('utf8'))
    html = ROOT / manifest['HTML']
    require(file_hash(html) == manifest['sha256'], 'Album hash mismatch')
    text = html.read_text('utf8')
    data = extracted(text, 'const DATA=')
    playback = extracted(text, 'PLAYBACK=')
    actual = {}
    for mode, source in manifest['sources'].items():
        path = ROOT / source['bin']
        require(file_hash(path) == source['sha256'], 'Current BIN differs')
        actual[mode] = read_disc(path, ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC', 'SLUS_005.61', 'ST0E_U1.ARC', 'COL0E_U1.ARC'))[0]
        require(playback['sources'][mode]['bin_sha256'] == source['sha256'], 'Stale animation source')
    table_checks = 0
    for name, char in playback['characters'].items():
        mode = 'ver_buki_riko' if name in ('riko', 'shibuki') else 'ver_rin_nana'
        family = 'zero' if name in ('riko', 'rin') else 'x'
        for form, animations in char['forms'].items():
            if form.startswith('capsule'):
                continue
            for animation in animations['animations']:
                native = parse_sequence(actual[mode]['SLUS_005.61'], TABLES[family], animation['id'])
                seq = lambda obj: [(s['position'], s['duration_calls'], s['event']) for s in obj['steps']]
                require(seq(native) == seq(animation) and native['loop_to_position'] == animation['loop_to_position'], 'Animation table changed')
                table_checks += 1
    spec = importlib.util.spec_from_file_location('album_pixel_helper', ROOT / 'work/sprite_consistency_20261105/zero/album/verify_album.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    errors, requests, forms, pixels, motion = [], [], [], [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 1100}, device_scale_factor=1, offline=True)
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda r: requests.append(r.url) if not r.url.startswith(('file:', 'data:', 'blob:')) else None)
        page.goto(html.as_uri(), wait_until='load')
        helper.loaded(page)
        assert page.evaluate('DATA.reduce((n,c)=>n+c.frames.length-c.partial.length,0)') == 4510
        assert page.evaluate('DATA.reduce((n,c)=>n+c.revised_count,0)') == len(manifest['changes'])
        assert page.evaluate('Object.values(ASSETS).every(x=>x.startsWith("data:image/png;base64,"))')
        page.locator('#guides').uncheck()
        page.select_option('#zoom', '2')
        for char in data:
            name = char['id']
            mode = 'ver_buki_riko' if name in ('riko', 'shibuki') else 'ver_rin_nana'
            page.locator(f'#characters button[data-id="{name}"]').dispatch_event('click')
            for form in char['forms']:
                page.select_option('#form', form['id'])
                helper.loaded(page)
                assert page.locator('#cards .card').count() == page.evaluate('subset.length')
                page.locator('#cards .card').last.locator('button').dispatch_event('click')
                helper.loaded(page)
                forms.append([name, form['id'], page.evaluate('chosen.id')])
            archives = {n: Archive(actual[mode][n]) for n in ('PL00_U.ARC', 'PL02_U.ARC')} if name in ('shibuki', 'nana') else None
            palettes = zero_palettes(actual[mode]['PL01_U.ARC']) if name in ('riko', 'rin') else None
            for frame in char['frames']:
                if not frame.get('revised_path'):
                    continue
                form, ref = frame['form'], frame.get('ref')
                page.select_option('#form', form)
                page.evaluate('(id)=>choose(char.frames.find(f=>f.id===id))', frame['id'])
                helper.loaded(page)
                if form == 'selection':
                    expected = selection_image(actual[mode], frame)
                elif palettes:
                    expected = zero_image(actual[mode]['PL01_U.ARC'], name, frame, palettes)
                else:
                    archive = archives['PL02_U.ARC' if form.startswith('ultimate') else 'PL00_U.ARC']
                    mask = 15 if form in ('fourth', 'fourth_arm1', 'ultimate_before') or form == 'ultimate_after' and 217 <= ref <= 230 else 0
                    expected = archive.composite(ref, mask, 1 if form == 'fourth_arm1' else 2)[0]
                proof = helper.exact_image(page, '#after', expected)
                proof.update(character=name, form=form, frame_id=frame['id'])
                pixels.append(proof)
        # Exercise actual browser timers on one continuous motion per character.
        page.evaluate("""()=>{window.__steps=[];window.__oldStep=showAnimationStep;showAnimationStep=function(){__oldStep();if(animationCurrent)__steps.push(animationStep)}}""")
        for name, form in [('riko', 'normal'), ('rin', 'black'), ('shibuki', 'ultimate_before'), ('nana', 'base')]:
            page.locator(f'#characters button[data-id="{name}"]').dispatch_event('click')
            page.select_option('#form', form)
            page.select_option('#animationSelect', '8')
            helper.loaded(page)
            page.locator('#loopAnimation').check()
            page.evaluate('window.__steps=[]')
            page.locator('#playAnimation').dispatch_event('click')
            page.wait_for_function('__steps.length > animationCurrent.steps.length')
            page.locator('#playAnimation').dispatch_event('click')
            assert page.evaluate('animationTimer') is None
            trace = page.evaluate('__steps')
            count = page.evaluate('animationCurrent.steps.length')
            assert trace[:count] == list(range(count))
            page.wait_for_function("document.getElementById('animationCanvas').dataset.loaded==='true'")
            proof = helper.exact_image(page, '#animationCanvas')
            motion.append({'character': name, 'form': form, 'trace': trace, 'canvas': proof})
        assert not errors and not requests, (errors, requests)
        version = browser.version
        browser.close()
    require(file_hash(html) == manifest['sha256'], 'Album was modified')
    report = {'passed': True, 'html_sha256': manifest['sha256'], 'offline_edge_version': version,
              'forms': forms, 'modified_pixel_checks': pixels, 'native_animation_tables': table_checks,
              'full_loop_playback': motion, 'errors': errors, 'external_requests': requests,
              'gameplay_runtime_verified': False, 'no_game_input_or_save_writes': True,
              'timing_scope': 'Original duration call counts; browser uses the explicit 60 calls/sec preview assumption.'}
    (directory / 'browser_checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'passed': True, 'forms': len(forms), 'modified_pixel_checks': len(pixels), 'motion_loops': len(motion)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    main(p.parse_args().directory)
