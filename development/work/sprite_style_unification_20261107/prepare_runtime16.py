"""Freeze ordinary-input observers to RN16 and copy an existing Fourth save."""
from pathlib import Path
import json,hashlib,shutil
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(W/'staging_rn_v16.json');out=ROOT/plan['output'];m=read(out/'manifest.json')
assert m['resources']['PL00_U.ARC']['after']=='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42'
game=out/'rin_nana.bin';bh=sha(game);assert bh==m['modified_bin']['sha256']
assert m['disc_readback_verified'] and m['changed_EDC_ECC_valid']
scripts=[]
for name in ('read_menu','observe','record','play_watch','open_continue'):
    source=R/f'{name}_rn15.py';dest=R/f'{name}_rn16.py';assert not dest.exists()
    txt=source.read_text('utf8').replace('66b808fc2f37a93eefd915ab7199934bbed62dcef4500ee087b75daa80324989',bh)
    txt=txt.replace('rn15','rn16').replace('checkpoint15','checkpoint16')
    dest.write_text(txt,'utf8');scripts.append(dest)
source=R/'load_fourth13.py';dest=R/'load_fourth_rn16.py';assert not dest.exists()
dest.write_text(source.read_text('utf8').replace('read_menu_br13','read_menu_rn16').replace('ver_buki_riko','ver_rin_nana'),'utf8');scripts.append(dest)
cards=ROOT/'work/ver_rin_nana/sprite_style_checkpoint16/cards';cards.mkdir(parents=True,exist_ok=False)
source=ROOT/'work/ver_buki_riko/sprite_style_checkpoint13/cards/fourth_source_copy.mcr'
assert sha(source)=='ab68aa740dd7a93b8b01b4b4b9cf1a57dab11c9900052879bfbc665499bf120f'
dest=cards/'fourth_source_copy.mcr';shutil.copyfile(source,dest);assert sha(dest)==sha(source)
copies=[{'source':source.relative_to(ROOT).as_posix(),'copy':dest.relative_to(ROOT).as_posix(),'sha256':sha(source)}]
(cards/'copies.json').write_text(json.dumps(copies,indent=2)+'\n','utf8')
p=R/'nana_rising16_plan.json';assert not p.exists();p.write_bytes((R/'shibuki_rising11_plan.json').read_bytes())
p=R/'tools_binding_rn16.json';assert not p.exists()
p.write_text(json.dumps({'disc_sha256':bh,'helpers':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)} for q in scripts],
    'test_card_copies':copies,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8')
print(json.dumps({'disc_sha256':bh,'helpers':len(scripts),'fourth_card_sha256':sha(dest)}))
