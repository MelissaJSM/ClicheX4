"""실제 COL 팔레트 연결을 사용해 린 잔기 색상과 전송 빛을 수정한다."""
import json,struct,sys,shutil
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_hud_emblems import require,all_compositions,composed,render_pixels
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from src.psx_personal_effects import apply_warp,WARP_FRAMES
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

PARENT=ROOT/'out/ver_rin_nana/rin_life_item_20261029T041200538927Z'
PARENT_SHA='9606c288ac85d2d4256f31c5d2b376daf6ef90e23bd6c082af01c22b78359924'
WORK=ROOT/'work/ver_rin_nana/effect_color_audit_v1'
OLD_STAGE_LIFE=bytes.fromhex('0000b9a89fde6c84bdb55e803388dffb7ff7dfee7eeafcc57ac5fee53dd53dc0')
WARP_TONE=bytes((0,1,2,3,4,6,6,7,9,9,10,11,12,13,14,10))

def prepare():
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent BIN differs')
    m=json.loads((PARENT/'manifest.json').read_text('utf8'));old=(PARENT/'modified.arc').read_bytes()
    require(sha256(old)==m['modified_archive_sha256'],'Player ARC differs')
    new,warp=apply_warp(old,lut=WARP_TONE)
    require(entry(old,3)==entry(new,3) and entry(old,0x10206)==entry(new,0x10206),'Static art or parts changed')
    bodypal=entry(old,9)[:32];life=bytearray(entry(old,9)[11*32:12*32])
    # The existing face conversion uses indices3,8..13. Give remaining entries
    # a matching cool ramp for the life-related EX tank, another CLUT0x780B user.
    for dst,src in {1:5,2:10,4:10,5:6,6:4,7:11,14:3,15:9}.items():life[dst*2:dst*2+2]=bodypal[src*2:src*2+2]
    life=bytes(life);require(life[:2]==b'\0\0' and len(life)==32,'Invalid life CLUT')
    changes=[];reports=[]
    with (PARENT/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size);records=d.inspect()['files']
        player=next(r for r in records if r['path']=='/ARC/PL01_U.ARC;1');require(d.read(player['lba'],player['size'])==old,'Player readback differs')
        changes.append(({**player,'sha256':sha256(old)},new))
        for r in records:
            n=r['path'].split('/')[-1]
            if not (n.startswith('COL') and n.endswith('Z.ARC;1') and n[3:5] not in ('0D','0E','0F')):continue
            a=d.read(r['lba'],r['size']);pal=entry(a,5)
            require(pal[352:384]==OLD_STAGE_LIFE,'Unexpected stage life palette '+n)
            changed=replace_entry(a,5,pal[:352]+life+pal[384:]);e=next(e for e in psx_arc(a) if e['type']=='0x5');lo=e['offset']+352
            require(a[:lo]==changed[:lo] and a[lo+32:]==changed[lo+32:] and len(a)==len(changed),'Stage patch escaped row11')
            changes.append(({**r,'sha256':sha256(a)},changed));reports.append({'path':r['path'],'old_sha256':sha256(a),'new_sha256':sha256(changed),'palette_row':11})
    require(len(reports)==24,'Unexpected Zero stage palette copy count')
    checked=0;changed_frames=[];shared_protected=[];g,ng=entry(old,2),entry(new,2);parts=entry(old,3)
    selected_offsets={f['offset'] for bank in (0,1) for f in graphics_bank(g,bank)['frames'] if f['index'] in WARP_FRAMES[bank]}
    for bank in (0,1):
        a,b=graphics_bank(g,bank),graphics_bank(ng,bank)
        for f,z in zip(a['frames'],b['frames']):
            before=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;after=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
            selected=f['index'] in WARP_FRAMES[bank]
            if not selected and before==after:
                checked+=1;continue
            comp=composition_frame(parts,0 if bank==0 else 5,f['index']);bp,sz,bb,_=compose_launch(before,f['tile_count'],comp);ap,ns,nb,_=compose_launch(after,z['tile_count'],comp)
            require(ns==sz and nb==bb and ap==(bytes(WARP_TONE[v] for v in bp) if selected else bp),'Beam/body display mismatch')
            if not selected and f['offset'] not in selected_offsets:require(before==after,'Nonbeam compressed stream changed')
            elif not selected and before!=after:shared_protected.append([bank,f['index']])
            if selected:changed_frames.append([bank,f['index']])
            checked+=1
    return m,old,new,life,changes,{'stage_life_palettes':reports,'actual_life_clut':'0x780B','palette_source':'COL entry5 row11, not PL01 entry9 row11',
        'known_palette_consumers':['normal life pickup type4','EX life tank type18','pickup-related visual consumer at US0x800CA540'],
        'warp_tone_indices':list(WARP_TONE),'warp_frames':changed_frames,'compressed_references_checked':checked,'warp_stream_checks':warp,'shared_stream_body_display_preserved':shared_protected,
        'player_body_static_parts_palette_animation_bytes_preserved':True,'all_other_stage_bytes_preserved':True,'x_stage_palettes_preserved':True,
        'exe_unchanged':True,'runtime_verified':False}

def build():
    m,old,new,life,changes,v=prepare();_,_,again,again_life,again_changes,_=prepare()
    require(new==again and life==again_life and changes==again_changes,'Independent preparation differs')
    protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        for q in protection['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed '+q['path'])
    protect();out=ROOT/'out/ver_rin_nana'/('rin_effect_colors_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',changes,PARENT_SHA);(out/'modified.arc').write_bytes(new);shutil.copyfile(PARENT/'rin_nana.cue',out/'rin_nana.cue')
    for folder in ('ui','portrait','hunter','dialogue','pause','weapon_get','hud_theme','life_item'):shutil.copytree(PARENT/folder,out/folder)
    effect=out/'effect_colors';effect.mkdir();(effect/'life_palette.bin').write_bytes(life);(effect/'old_stage_life_palette.bin').write_bytes(OLD_STAGE_LIFE)
    comps=all_compositions(entry(new,3))
    for n in range(89,99):
        a,sz,bb,_=composed(entry(new,0x10206),comps[3,n]);render_pixels(a,life).save(effect/f'pickup_{n}.png')
    changed={q['lba'] for q in result['changed_sectors']};count=0
    with (PARENT/'rin_nana.bin').open('rb') as f,(out/'rin_nana.bin').open('rb') as g:
        while True:
            a,b=f.read(2352),g.read(2352)
            if not a:require(not b,'Output grew');break
            require(len(a)==len(b) and (a!=b)==(count in changed),'Unexpected sector difference')
            if count in changed:validate_checks(b)
            count+=1
    with (out/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,result['size'])
        for r,a in changes:require(d.read(r['lba'],r['size'])==a,'Modified ARC readback differs')
    protect();v.update(all_disc_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,readback_equal=True,
        reproduced_archives=len(changes),protected_files=len(protection['files']),embedded_static_bodies=m['verification']['embedded_static_bodies'])
    manifest={**m,'kind':'rin_actual_effect_colors','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'modified_bin':result,
        'modified_archive_sha256':sha256(new),'verification':v,'inherited_verification':m['verification'],'runtime_verified':False}
    for name,data in [('manifest.json',manifest),('verification.json',v),('preservation.json',protection)]:(out/name).write_text(json.dumps(data,indent=2)+'\n','utf8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),
        'sha256':result['sha256'],'frames':m['cumulative_frames'],'bank1_frames':m['cumulative_bank1_frames'],'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'sha256':result['sha256'],'sectors':len(changed)}))

if __name__=='__main__':build()
