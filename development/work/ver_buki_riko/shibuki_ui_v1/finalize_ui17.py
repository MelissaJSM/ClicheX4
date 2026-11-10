import json,shutil,sys,struct
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.inventory_shibuki_ui import D
from scripts.project import digest
p=D/'candidate17';out=ROOT/'out/ver_buki_riko/shibuki_ui_20261027T052213672376Z'
m=json.loads((out/'manifest.json').read_text('utf8'))
assert digest(out/'shibuki_riko.bin')==m['modified_bin']['sha256']
board=Image.new('RGBA',(1200,1050),(40,43,57,255));dr=ImageDraw.Draw(board)
dr.text((15,12),'OFFLINE NATIVE ASSET PREVIEW - Shibuki UI candidate17',fill='white')
def add(name,x,y,scale=2):
    im=Image.open(p/(name+'.png')).convert('RGBA');im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
    board.alpha_composite(im,(x,y+20));dr.text((x,y),name,fill='white')
add('selection_portrait',15,40);add('selection_name_5',435,42);add('weapon_title',820,140,1)
for n in range(4):add(f'dialogue_{n}',15+n*280,400)
for n,x in [(0,15),(3,170),(6,355),(9,550)]:add(f'hq_{n:02}',x,660)
add('pause_portrait',780,660);add('hud_69',960,660,3)
board.convert('RGB').save(p/'final_review.png')
shutil.copyfile(D/'candidate16/hq_idle_offline.gif',p/'hq_idle_offline.gif')
for name in ('final_review.png','backgrounds.png','save_combinations.png','hq_idle_offline.gif'):shutil.copyfile(p/name,out/name)
for name in ('STATUS.md','DECISIONS.md','COMMANDS.md','TEST_RESULTS.md','SHIBUKI_UI.md'):
    path=ROOT/'docs'/name;s=path.read_text('utf8')
    s=s.replace('shibuki_ui_20261027T051207173188Z',out.name).replace('c1ae648174decd35539b9bae6e2750308b4000fdf89f2b1bb5d2b75705cb7a07',m['modified_bin']['sha256']).replace('c1ae6481…','f51d27a7…')
    for a,b in [('candidate16','candidate17'),('repro16','repro17'),('text_review16','text_review17')]:s=s.replace(a,b)
    path.write_text(s,encoding='utf8')
path=D/'art_prompts.md';path.write_text(path.read_text('utf8').replace('candidate16','candidate17'),encoding='utf8')
path=ROOT/'projects/ver_buki_riko/shibuki_ui_candidate.json';pointer=json.loads(path.read_text('utf8'))
pointer.update(build=str(out.relative_to(ROOT)).replace('\\','/'),cue=str((out/'shibuki_riko.cue').relative_to(ROOT)).replace('\\','/'),bin_sha256=m['modified_bin']['sha256'],arc_sha256=m['modified_archive_sha256'],review=str((p/'final_review.png').relative_to(ROOT)).replace('\\','/'),text_proposal=str((D/'text_review17/proposal.json').relative_to(ROOT)).replace('\\','/'))
path.write_text(json.dumps(pointer,indent=2),encoding='utf8')
for path in (ROOT/'out/ver_buki_riko').glob('shibuki_ui_*/manifest.json'):
    if path.parent==out:continue
    value=json.loads(path.read_text('utf8'));value.update(superseded=True,superseded_by=str(out.relative_to(ROOT)).replace('\\','/'));path.write_text(json.dumps(value,indent=2),encoding='utf8')
log=(D/'unit_tests.log').read_bytes();log=log.decode('utf16' if log.startswith(b'\xff\xfe') else 'utf8')
assert 'Ran 199 tests' in log and log.rstrip().endswith('OK')
(D/'test_summary.json').write_text(json.dumps({'python':sys.version,'unit_tests':199,'passed':True,'log':'unit_tests.log'},indent=2),encoding='utf8')
files=['scripts/inventory_shibuki_ui.py','scripts/prepare_shibuki_ui.py','scripts/verify_shibuki_ui.py','scripts/build_shibuki_ui.py','scripts/prepare_shibuki_dialogue.py','src/psx_shibuki_text.py','src/psx_ui_text_space.py','tests/test_shibuki_ui_text.py']
(D/'source_hashes.json').write_text(json.dumps({n:digest(ROOT/n) for n in files},indent=2),encoding='utf8')
print(json.dumps({'final_build':str(out),'bin_sha256':m['modified_bin']['sha256'],'arc_sha256':m['modified_archive_sha256'],'unit_tests':199,'game_control_used':False,'dialogue_approval_pending':True}))
