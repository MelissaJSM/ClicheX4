"""Bind existing bounded controls to one verified checkpoint13 image."""
import argparse, hashlib, json, shutil
from pathlib import Path
W=Path(__file__).resolve().parent
ROOT=W.parents[1]
R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('mode',choices=['br','rn']);a=p.parse_args()
mode={'br':'ver_buki_riko','rn':'ver_rin_nana'}[a.mode]
old=read(ROOT/'out'/mode/'sprite_style_unification_20261107_v12/manifest.json')['modified_bin']['sha256']
new=read(ROOT/'out'/mode/'sprite_style_unification_20261107_v13/manifest.json')['modified_bin']['sha256']
stem={'br':'shibuki_riko','rn':'rin_nana'}[a.mode]
assert sha(ROOT/'out'/mode/'sprite_style_unification_20261107_v13'/f'{stem}.bin')==new
tools=[]
for name in ['observe','record','read_menu','open_continue','play_watch']:
    src=R/f'{name}_{a.mode}12.py';dst=R/f'{name}_{a.mode}13.py'
    s=src.read_text('utf8').replace(old,new).replace(f'_{a.mode}12',f'_{a.mode}13').replace('checkpoint11','checkpoint13').replace('checkpoint12','checkpoint13')
    assert old not in s
    if dst.exists():assert dst.read_text('utf8')==s
    else:dst.write_text(s,'utf8')
    tools.append({'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'output':dst.relative_to(ROOT).as_posix(),'sha256':sha(dst)})
src=R/'open_selection_br12.py';dst=R/f'open_selection_{a.mode}13.py'
s=src.read_text('utf8').replace('read_menu_br12',f'read_menu_{a.mode}13')
if dst.exists():assert dst.read_text('utf8')==s
else:dst.write_text(s,'utf8')
tools.append({'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'output':dst.relative_to(ROOT).as_posix(),'sha256':sha(dst)})
cards=[]
target=ROOT/'work'/mode/'sprite_style_checkpoint13/cards';target.mkdir(parents=True,exist_ok=True)
for c in read(ROOT/'work'/mode/'sprite_style_checkpoint12/cards/copies.json'):
    source=ROOT/c['copy'];assert sha(source)==c['sha256']
    dest=target/source.name
    if not dest.exists():shutil.copy2(source,dest)
    assert sha(dest)==c['sha256']
    cards.append({'source':source.relative_to(ROOT).as_posix(),'copy':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
for dest,obj in [(target/'copies.json',cards),(R/f'tools_binding_{a.mode}13.json',{'project':mode,'disc_sha256':new,'opposite_mode_rejected':True,'tools':tools})]:
    s=json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    if dest.exists():assert dest.read_text('utf8')==s
    else:dest.write_text(s,'utf8')
print(json.dumps({'project':mode,'disc_sha256':new,'tools':len(tools),'cards':cards}))
