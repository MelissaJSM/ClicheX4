from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_br_v28.json');p['output']='out/ver_buki_riko/sprite_style_unification_20261107_v29';p['checkpoint_label']='four_character_style_checkpoint_29_shibuki_nova_strike'
for name,folder,want,freeze in [('PL00_U.ARC','prepared_nova_strike_base01','36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e','8b7c984af002507dc58cb0bc53abf68498db110d2c3efdb1d70414b9730a054a'),('PL02_U.ARC','prepared_nova_strike_ultimate01','01997c949968d5a1a12d89e09c5eb46448bbcf245009feb9953e3d9e9356efd7','e9a11963e1fc19a0018f553c5a33e3ad2ca13fcb459e6f8e090606f2fb0237e1')]:
    d=H/folder;f=d/name;lock=d/'FROZEN.json';assert sha(f)==want and sha(lock)==freeze
    for n,s in read(lock)['files'].items():assert sha(d/n)==s,(folder,n)
    p['resources'][name].update(path=f.relative_to(ROOT).as_posix(),after=want);p['candidate_freeze_bindings'][name]={'path':lock.relative_to(ROOT).as_posix(),'sha256':freeze}
for n in(152,155):
    f=W/f'root_review_checkpoint{n}.json';p['root_visual_review_records'].append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f)})
out=W/'staging_br_v29.json';assert not out.exists();out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
