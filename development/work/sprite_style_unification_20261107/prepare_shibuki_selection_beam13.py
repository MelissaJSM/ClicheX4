"""Prepare an isolated exact-copy correction for the leftover orange UI beam."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_nana_ui_small import register,target_frame
from scripts.prepare_rin_ui_small import protected_repack,world
from scripts.build_sprite_style_album import selection_image
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
sha=lambda b:hashlib.sha256(b).hexdigest()
game=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v13/shibuki_riko.bin'
assert sha(game.read_bytes())=='b78509ca2a8bc2c67bb2997cba927174df1fcf8cd672a347552bcc25e96c656d'
assets=read_disc(game,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0]
old=assets['ST0E_U1.ARC'];parts=entry(old,10);texture=entry(old,0x10102)
target=target_frame(assets['PL00_U.ARC'],23)
rp,targets,positions=register(parts,2,{23:target},texture[90112:])
nt,np_,packed=protected_repack(texture[90112:],parts,rp,2,targets)
new=replace_entry(replace_entry(old,0x10102,texture[:90112]+nt),10,np_)
assert len(new)==len(old)
assert world(compose_static(nt,local_composition(composition_frame(np_,2,23))))==world(target)
other=0;allowed=set()
for bank,lo,hi in [(0,0,40960),(1,40960,90112),(2,90112,len(texture))]:
    for ref in range(composition_frame(parts,bank,0)['bank_frame_count']):
        p,q=composition_frame(parts,bank,ref),composition_frame(np_,bank,ref)
        if (bank,ref)==(2,23):
            assert len(p['parts'])==len(q['parts'])
            for a,b in zip(p['parts'],q['parts']):
                assert all(a[k]==b[k] for k in ['flip_x','flip_y','clut','unknown_flags','record_offset'])
                allowed.update(range(a['record_offset'],a['record_offset']+4))
        else:
            assert p==q,(bank,ref)
            before=compose_static(texture[lo:hi],local_composition(p))
            after=compose_static((texture[:90112]+nt)[lo:hi],local_composition(q))
            assert before==after,(bank,ref)
            other+=1
assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(parts,np_)))
assert replace_entry(replace_entry(old,0x10102,entry(new,0x10102)),10,entry(new,10))==new
out=W/'selection_shibuki_beam13';assert not out.exists();out.mkdir()
(out/'ST0E_U1.ARC').write_bytes(new)
selection_image(assets,{'bank':2,'ref':23}).save(out/'before.png')
selection_image({**assets,'ST0E_U1.ARC':new},{'bank':2,'ref':23}).save(out/'after.png')
report={'parent_bin_sha256':sha(game.read_bytes()),'parent_sha256':sha(old),'candidate_sha256':sha(new),
    'player_sha256':sha(assets['PL00_U.ARC']),'mapping':{'ui_bank':2,'ui_ref':23,'player_ref':160,'dx':0,'dy':-1},
    'pixels_and_origin_exact':True,'non_target_frames_preserved':other,'packing':packed,
    'scope':'새 원화 없이 현재 플레이용 보라색 복귀 빛기둥을 원 UI 원점에 복사. 별도 임시 ARC만 작성.',
    'other_entries_preserved':True,'palette_changed':False,'game_bin_written':False,
    'root_review_pending':True,'integration_guard_pending':True,'runtime_verified':False}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'candidate':sha(new),'protected_frames':other,'packing':packed}))
