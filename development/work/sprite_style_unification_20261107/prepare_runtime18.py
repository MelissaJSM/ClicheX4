"""Bind fresh-boot observation and guarded card-load helpers to RN18."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(W/'staging_rn_v18.json');out=ROOT/plan['output'];m=read(out/'manifest.json')
assert m['resources']['PL00_U.ARC']['after']=='978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f'
bh=sha(out/'rin_nana.bin');assert bh==m['modified_bin']['sha256'] and m['disc_readback_verified'] and m['changed_EDC_ECC_valid']
scripts=[]
for name in ('read_menu','observe','record','play_watch','open_continue'):
 source=R/f'{name}_rn17.py';dest=R/f'{name}_rn18.py';assert not dest.exists()
 txt=source.read_text('utf8').replace('13da8bfc9cb6968028300ff362975826c1d6f08f3a009b623fa26fe529e5b124',bh).replace('rn17','rn18').replace('checkpoint17','checkpoint18')
 dest.write_text(txt,'utf8');scripts.append(dest)
for name,expected,description in [('base',(0,48,0,0,255,0),'basic'),('fourth',(0,48,2,15,255,0),'full-armor')]:
 source=R/f'load_{name}_rn16.py';dest=R/f'load_{name}_rn18.py';assert not dest.exists()
 txt=source.read_text('utf8').replace('read_menu_rn16','read_menu_rn18')
 old=f"assert tuple(slot[i] for i in (0,1,2,3,4,41))=={str(expected).replace(' ','')},'Unexpected {description} record'"
 assert old in txt
 # DATA list can become visible before its selected record buffer is stable.
 # A different record never authorizes confirmation; wait within existing 25s bound.
 new="selected=tuple(slot[i] for i in (0,1,2,3,4,41))\n                    if selected!="+str(expected)+":\n                        trace.append({'seconds':now,'record_not_ready':selected,'cursor':t[7]})\n                        last=now;time.sleep(.05);continue"
 txt=txt.replace(old,new)
 dest.write_text(txt,'utf8');scripts.append(dest)
source=R/'advance_hq_rn16.py';dest=R/'advance_hq_rn18.py';assert not dest.exists();dest.write_text(source.read_text('utf8').replace('read_menu_rn16','read_menu_rn18'),'utf8');scripts.append(dest)
cards=ROOT/'work/ver_rin_nana/sprite_style_checkpoint13/cards'
expected={'nana_allboss.mcr':'bfeacc6f59f0731581af8e8d77709fea04211775a2b66acf4478ff01ff5c9c6e','rin_allboss.mcr':'b0a596dba2e0e6ba6cdaaf87a894990365f0a33ee2b8d6536f6a5eb2298d77f9'}
bindings=[]
for name,digest in expected.items():
 p=cards/name;assert sha(p)==digest;bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest})
p=ROOT/'work/ver_rin_nana/sprite_style_checkpoint16/cards/fourth_source_copy.mcr'
assert sha(p)=='ab68aa740dd7a93b8b01b4b4b9cf1a57dab11c9900052879bfbc665499bf120f';bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
p=R/'tools_binding_rn18.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':bh,'helpers':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)} for q in scripts],
 'existing_test_card_copies':bindings,'save_record_guard':'25초 한도 내 정확한 대상 레코드가 확인될 때만 결정 입력','no_f1_f3_or_memory_writes':True},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'disc_sha256':bh,'helpers':len(scripts)}))
