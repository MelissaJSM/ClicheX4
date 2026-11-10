import json, shutil, subprocess, sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[4]
d=Path(__file__).parent
art=json.loads((d/'production09/art.json').read_text())
rows=[]
trial=d/'negative_inputs'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
def run(name, edit, message, parent='out/ver_buki_riko/shibuki_special_style_20261026T230854606760Z', scope='base_arrival_victory_style_11'):
    target=trial/name
    shutil.copytree(d/'production09',target)
    manifest=json.loads(json.dumps(art));edit(manifest)
    (target/'art.json').write_text(json.dumps(manifest),encoding='utf-8')
    before=set((ROOT/'work/ver_buki_riko/shibuki_arrival_victory_style').iterdir())
    p=subprocess.run([sys.executable,'scripts/prepare_shibuki_remaining.py','--art',str(target),'--parent',parent,'--scope',scope,'--repack-bank'],cwd=ROOT,capture_output=True,text=True)
    row={'name':name,'rejected':p.returncode!=0,'reason':p.stderr.strip().splitlines()[-1],'expected_reason':message,'no_output_written':before==set((ROOT/'work/ver_buki_riko/shibuki_arrival_victory_style').iterdir())}
    if not row['rejected'] or message not in row['reason'] or not row['no_output_written']:raise ValueError(row)
    rows.append(row)
run('wrong_palette',lambda a:a['palette_words'].__setitem__(1,a['palette_words'][1]^1),'Palette mismatch')
run('missing_frame',lambda a:a['remaining_frames'].pop(),'Incomplete or overlapping groups')
run('armor_tile',lambda a:a['groups'][0]['writable'].append(16),'Writable/armor/effect conflict')
run('wrong_parent',lambda a:None,'Repack parent differs',parent='out/ver_buki_riko/shibuki_weapon_palette_20261026T170706783998Z')
run('wrong_scope',lambda a:None,'Bank repack is approved only',scope='base_remaining_105')
(d/'negative_inputs.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows))
