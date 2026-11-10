"""원EXE bank/ref와 모음집 스텝 연결을 독립 대조하고 변경 동작을 모두 순회한다."""
from pathlib import Path
import sys,json,importlib.util,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.build_sprite_style_album import extracted
from scripts.c01_audio_build import read_disc
from scripts.export_sprite_playback import parse_sequence,TABLES,at,ZERO_SELECTOR
from src.psx_disc import file_hash
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser();parser.add_argument('album_directory',type=Path,nargs='?',default=Path('out/sprite_style_unification_20261107/review_v4'));args=parser.parse_args()
D=(ROOT/args.album_directory).resolve();manifest=json.loads((D/'manifest.json').read_text('utf8'));html=ROOT/manifest['HTML'];assert file_hash(html)==manifest['sha256']
text=html.read_text('utf8');data=extracted(text,'const DATA=');playback=extracted(text,'PLAYBACK=');empty=extracted(text,'const EMPTY=')
exe={}
for mode,v in manifest['sources'].items():
    p=ROOT/v['bin'];assert file_hash(p)==v['sha256'];exe[mode]=read_disc(p,('SLUS_005.61',))[0]['SLUS_005.61']
checks=0;queue=[]
for char in data:
    name=char['id'];mode='ver_buki_riko'if name in('riko','shibuki')else'ver_rin_nana';family='zero'if name in('riko','rin')else'x';revised={f['id']for f in char['frames']if f.get('revised_path')}
    for form,group in playback['characters'][name]['forms'].items():
        if form.startswith('capsule'):continue
        for animation in group['animations']:
            original=parse_sequence(exe[mode],TABLES[family],animation['id']);assert len(original['steps'])==len(animation['steps'])
            bank=at(exe[mode],ZERO_SELECTOR+animation['id'],1)[0]if family=='zero'else None
            for source,s in zip(original['steps'],animation['steps']):
                expected=f'{form}:b{bank}_{source["frame_ref"]:03}'if family=='zero'else f'{form}_{source["frame_ref"]:03}'
                assert s['position']==source['position']and s['duration_calls']==source['duration_calls']and s['event']==source['event']
                assert s['frame_id']==expected if s['frame_id'] else bool(s['reason'])
                checks+=1
            if any(s['frame_id']in revised for s in animation['steps']):queue.append((name,form,animation))
spec=importlib.util.spec_from_file_location('pixel_helper',ROOT/'work/sprite_consistency_20261105/zero/album/verify_album.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
report=[];errors=[];requests=[]
with sync_playwright()as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True);context=browser.new_context(viewport={'width':1600,'height':1100},device_scale_factor=1,offline=True);page=context.new_page()
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url)if not r.url.startswith(('file:','data:','blob:'))else None)
    page.goto(html.as_uri(),wait_until='load');helper.loaded(page);page.locator('#guides').uncheck();page.select_option('#zoom','1');page.locator('#showRevised').check();previous=None
    for name,form,anim in queue:
        if previous!=(name,form):
            page.locator(f'#characters button[data-id="{name}"]').dispatch_event('click');page.select_option('#form',form);helper.loaded(page);previous=(name,form)
        page.select_option('#animationSelect',str(anim['id']));frames=[]
        for i,step in enumerate(anim['steps']):
            expected=page.evaluate('(id)=>{const f=char.frames.find(v=>v.id===id);return f?selectedPath(f):EMPTY}',step['frame_id'])
            page.evaluate('(i)=>{stopAnimation();animationStep=i;showAnimationStep()}',i)
            page.wait_for_function('(p)=>{const c=document.getElementById("animationCanvas");return c.dataset.loaded==="true"&&c.dataset.path===p}',arg=expected)
            helper.exact_image(page,'#animationCanvas')
            frames.append(dict(position=step['position'],frame_id=step['frame_id'],duration_calls=step['duration_calls'],asset=expected,canvas_pixels_exact=True))
        report.append(dict(character=name,form=form,animation_id=anim['id'],steps=frames,loop_to_position=anim['loop_to_position']))
        if len(report)%30==0:print(json.dumps({'checked_sequences':len(report),'of':len(queue)}),flush=True)
    assert not errors and not requests
    version=browser.version;browser.close()
result=dict(passed=True,html_sha256=manifest['sha256'],native_bank_frame_mappings=checks,affected_sequences=report,step_count=sum(len(r['steps'])for r in report),edge_version=version,
    stepwise_canvas_validation=True,real_time_timer_test='browser_checks.json has four continuous loops',gameplay_runtime_verified=False,no_game_input_or_save_writes=True,errors=errors,external_requests=requests)
(D/'affected_animation_steps.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'sequences':len(report),'steps':result['step_count'],'native_mappings':checks}))
