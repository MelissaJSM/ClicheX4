from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(W/'staging_rn_v19.json');out=ROOT/plan['output'];m=read(out/'manifest.json');bh=sha(out/'rin_nana.bin')
assert bh==m['modified_bin']['sha256']=='383cd66528a25abf1bef08b4791824d52d3ae676b8e09af567fcae36447cea7c'
assert m['disc_readback_verified'] and m['changed_EDC_ECC_valid'];scripts=[]
for name in ('read_menu','observe','record','play_watch','open_continue'):
 source=R/f'{name}_rn18.py';dest=R/f'{name}_rn19.py';assert not dest.exists()
 txt=source.read_text('utf8').replace('0f40463b883e00a7e3acf268fd45052b905d0454440d8c5436ce24fe80f58c95',bh).replace('rn18','rn19').replace('checkpoint18','checkpoint19');dest.write_text(txt,'utf8');scripts.append(dest)
source=R/'load_ultimate_rn17.py';dest=R/'load_ultimate_rn19.py';assert not dest.exists();txt=source.read_text('utf8').replace('read_menu_rn17','read_menu_rn19')
old="assert tuple(slot[i] for i in (0,1,2,3,4,41))==(0,48,2,15,255,1),'Unexpected acquired-Ultimate record'";assert old in txt
txt=txt.replace(old,"selected=tuple(slot[i] for i in (0,1,2,3,4,41))\n                    if selected!=(0,48,2,15,255,1):\n                        trace.append({'seconds':now,'record_not_ready':selected,'cursor':t[7]})\n                        last=now;time.sleep(.05);continue")
dest.write_text(txt,'utf8');scripts.append(dest)
source=R/'advance_hq_rn18.py';dest=R/'advance_hq_rn19.py';assert not dest.exists();dest.write_text(source.read_text('utf8').replace('read_menu_rn18','read_menu_rn19'),'utf8');scripts.append(dest)
cards=ROOT/'work/ver_rin_nana/sprite_style_checkpoint13/cards';bindings=[]
for n,h in {'nana_allboss.mcr':'bfeacc6f59f0731581af8e8d77709fea04211775a2b66acf4478ff01ff5c9c6e','rin_allboss.mcr':'b0a596dba2e0e6ba6cdaaf87a894990365f0a33ee2b8d6536f6a5eb2298d77f9'}.items():
 p=cards/n;assert sha(p)==h;bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':h})
p=R/'tools_binding_rn19.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':bh,'helpers':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in scripts],'existing_test_card_copies':bindings,'save_record_guard':'25초 안에 정확한 DATA3 Ultimate 레코드 확인시 결정','no_f1_f3_or_memory_writes':True},ensure_ascii=False,indent=2)+'\n','utf8');print(bh)
