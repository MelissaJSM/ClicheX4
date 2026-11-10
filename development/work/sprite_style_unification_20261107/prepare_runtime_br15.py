"""Bind ordinary-input helpers to BR15 and existing protected test copies."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(W/'staging_br_v15.json');out=ROOT/plan['output'];m=read(out/'manifest.json')
assert m['resources']['PL00_U.ARC']['after']=='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce'
bh=sha(out/'shibuki_riko.bin');assert bh==m['modified_bin']['sha256']=='dfd1b9d09e8fad846aebfd51a89aecc46bff98bc6281619bb21abf1c8dbf27fc'
assert m['disc_readback_verified'] and m['changed_EDC_ECC_valid']
scripts=[]
for name in ('read_menu','observe','record','play_watch','open_continue'):
    source=R/f'{name}_br14.py';dest=R/f'{name}_br15.py';assert not dest.exists()
    txt=source.read_text('utf8').replace('b1e00232f8a62bea766e7b40dded110b0c2e66a2fbd2795725347510a0af581d',bh)
    txt=txt.replace('br14','br15').replace('checkpoint14','checkpoint15')
    dest.write_text(txt,'utf8');scripts.append(dest)
for source,dest in [('load_fourth13.py','load_fourth_br15.py'),('load_base_rn16.py','load_base_br15.py')]:
    dest=R/dest;assert not dest.exists()
    txt=(R/source).read_text('utf8').replace('read_menu_br13','read_menu_br15').replace('read_menu_rn16','read_menu_br15').replace('ver_rin_nana','ver_buki_riko')
    dest.write_text(txt,'utf8');scripts.append(dest)
p=R/'shibuki_run15_plan.json';assert not p.exists();p.write_bytes((R/'nana_ultimate_run14_plan.json').read_bytes())
cards=ROOT/'work/ver_buki_riko/sprite_style_checkpoint13/cards'
expected={'x_allboss.mcr':'bfeacc6f59f0731581af8e8d77709fea04211775a2b66acf4478ff01ff5c9c6e',
          'zero_allboss.mcr':'b0a596dba2e0e6ba6cdaaf87a894990365f0a33ee2b8d6536f6a5eb2298d77f9',
          'fourth_source_copy.mcr':'ab68aa740dd7a93b8b01b4b4b9cf1a57dab11c9900052879bfbc665499bf120f'}
for name,digest in expected.items():assert sha(cards/name)==digest,name
p=R/'tools_binding_br15.json';assert not p.exists()
p.write_text(json.dumps({'disc_sha256':bh,'helpers':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)} for q in scripts],
 'existing_test_card_copies':[{'path':(cards/n).relative_to(ROOT).as_posix(),'sha256':h} for n,h in expected.items()],
 'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8')
print(json.dumps({'disc_sha256':bh,'helpers':len(scripts)}))
