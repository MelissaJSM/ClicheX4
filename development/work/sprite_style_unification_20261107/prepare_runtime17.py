"""Bind ordinary-input observers to RN17; reuse only unchanged test card copies."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(W/'staging_rn_v17.json');out=ROOT/plan['output'];m=read(out/'manifest.json')
assert m['resources']['PL02_U.ARC']['after']=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
game=out/'rin_nana.bin';bh=sha(game);assert bh==m['modified_bin']['sha256']
assert m['disc_readback_verified'] and m['changed_EDC_ECC_valid']
scripts=[]
for name in ('read_menu','observe','record','play_watch','open_continue'):
    source=R/f'{name}_rn16.py';dest=R/f'{name}_rn17.py';assert not dest.exists()
    txt=source.read_text('utf8').replace('c2972d3552214336316f0e2d85d96f8f66ac50b470a423dbba47cda994258e78',bh)
    txt=txt.replace('rn16','rn17').replace('checkpoint16','checkpoint17')
    dest.write_text(txt,'utf8');scripts.append(dest)
source=R/'load_ultimate_rn14.py';dest=R/'load_ultimate_rn17.py';assert not dest.exists()
dest.write_text(source.read_text('utf8').replace('read_menu_rn14','read_menu_rn17'),'utf8');scripts.append(dest)
p=R/'nana_ultimate_rising17_plan.json';assert not p.exists();p.write_bytes((R/'nana_rising16_plan.json').read_bytes())
cards=ROOT/'work/ver_rin_nana/sprite_style_checkpoint13/cards'
expected={'nana_allboss.mcr':'bfeacc6f59f0731581af8e8d77709fea04211775a2b66acf4478ff01ff5c9c6e',
          'rin_allboss.mcr':'b0a596dba2e0e6ba6cdaaf87a894990365f0a33ee2b8d6536f6a5eb2298d77f9'}
for name,digest in expected.items():assert sha(cards/name)==digest,name
p=R/'tools_binding_rn17.json';assert not p.exists()
p.write_text(json.dumps({'disc_sha256':bh,'helpers':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)} for q in scripts],
    'existing_test_card_copies':[{'path':(cards/n).relative_to(ROOT).as_posix(),'sha256':h} for n,h in expected.items()],
    'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8')
print(json.dumps({'disc_sha256':bh,'helpers':len(scripts)}))
