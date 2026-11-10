from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old='769929d3ed42663897afd1e6afc42c74fd4f5d2885efa4a8d2340d4b948b3e6c';new='cd21411a1b44322e9c2dd93d09d0f7f42e0a54ddd3957b39364b7cb35373c6ba'
assert sha(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v26/rin_nana.bin')==new
assert sha(ROOT/'work/ver_rin_nana/sprite_style_checkpoint16/cards/fourth_source_copy.mcr')=='ab68aa740dd7a93b8b01b4b4b9cf1a57dab11c9900052879bfbc665499bf120f'
files=[]
for name in ('read_menu','observe','record','play_watch','open_continue','load_fourth','load_base','advance_hq'):
 src=R/f'{name}_rn22.py';dest=R/f'{name}_rn26.py';assert src.exists() and not dest.exists()
 t=src.read_text('utf8').replace(old,new).replace('rn22','rn26').replace('checkpoint22','checkpoint26');dest.write_text(t,'utf8');files.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
p=R/'tools_binding_rn26.json';assert not p.exists();p.write_text(json.dumps({'disc_sha256':new,'helpers':files,'no_f1_f3_or_memory_writes':True},indent=2)+'\n','utf8');print(new)
