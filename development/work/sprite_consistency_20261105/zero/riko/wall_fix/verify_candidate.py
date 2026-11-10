"""리코 벽 머리 후보의 재현·보존·입력 거부 증거. 원본/게임 실행 상태는 쓰지 않는다."""
from pathlib import Path
import json
import sys
import struct
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_consistency_wall import WORK, TARGETS, prepare, inputs, bindings
from scripts.export_zero_consistency import write
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from src.psx_disc import file_hash
from src.psx_player import graphics_bank, decode_stream

HEAD=WORK/'art/head_v2_registered.png'
HEAD_SHA='13c9fe97eb6e6a4d5801da60ff5dd8759b0680da4efffb81c1a7e217e066ea9e'
CANDIDATE=WORK/'prepared_v1/PL01_U.ARC'
CANDIDATE_SHA='36e231a882be87d71d603667a26909025003b88908f939f115d328b0dd4d53dc'


def main():
    folder=WORK/'negative_inputs'
    if folder.exists():
        raise ValueError('Fresh negative test directory required')
    folder.mkdir()
    original=Image.open(HEAD)
    wrongpal=original.copy();pal=wrongpal.getpalette();pal[12]^=1;wrongpal.putpalette(pal)
    wrongpal.save(folder/'palette_changed.png',transparency=0)
    noalpha=original.copy();noalpha.info.pop('transparency',None);noalpha.save(folder/'opaque_zero.png')
    badindex=original.copy();badindex.putpixel((0,0),16);badindex.save(folder/'index16.png',transparency=0)
    huge=Image.new('P',(33,20),0);huge.putpalette(original.getpalette());huge.paste(original,(0,0))
    huge.save(folder/'too_wide.png',transparency=0)
    cases=[
        ('hash',HEAD,'0'*64,0,-3,'Head SHA mismatch'),
        ('palette',folder/'palette_changed.png',None,0,-3,'Palette changes require'),
        ('opaque_zero',folder/'opaque_zero.png',None,0,-3,'Expected transparent index 0'),
        ('index16',folder/'index16.png',None,0,-3,'pixel indices above 15'),
        ('size',folder/'too_wide.png',None,0,-3,'Unexpected head geometry'),
        ('coverage',HEAD,HEAD_SHA,80,-3,'New head escapes original parts'),
    ]
    rejected=[]
    for name,path,expected,dx,dy,message in cases:
        out=folder/('must_not_exist_'+name)
        try:
            prepare(path,expected or file_hash(path),dx,dy,out)
        except ValueError as error:
            assert message in str(error),(name,str(error))
            assert not out.exists(),name
            rejected.append({'case':name,'rejected':True,'reason':str(error),'output_created':False})
        else:
            raise AssertionError('Invalid input accepted: '+name)
    try:
        prepare(HEAD,HEAD_SHA,0,-3,WORK/'prepared_v1')
    except ValueError as error:
        assert 'Fresh wall_fix output required' in str(error)
        rejected.append({'case':'existing_output','rejected':True,'reason':str(error),'candidate_sha_preserved':file_hash(CANDIDATE)==CANDIDATE_SHA})
    else:
        raise AssertionError('Existing output accepted')
    assert file_hash(HEAD)==HEAD_SHA
    assert file_hash(CANDIDATE)==CANDIDATE_SHA
    replay=WORK/'reproduced_v1'
    prepare(HEAD,HEAD_SHA,0,-3,replay)
    assert file_hash(replay/'PL01_U.ARC')==CANDIDATE_SHA
    source,source_sha,before,head,mask=inputs();after=CANDIDATE.read_bytes()
    rows=bindings(before,head,mask)
    records=[];same_full=0;same_partial=0;targets=0
    for bank in (0,1):
        old=graphics_bank(entry(before,2),bank);new=graphics_bank(entry(after,2),bank)
        for of,nf in zip(old['frames'],new['frames']):
            frame=of['index'];assert of['tile_count']==nf['tile_count']<=32
            if bank==1 and 42<=frame<=49:
                assert decode_stream(entry(before,2),of['offset'],of['limit'],128).data==decode_stream(entry(after,2),nf['offset'],nf['limit'],128).data
                same_partial+=1
                continue
            ob,_=render(before,bank,0 if bank==0 else 5,frame)
            nb,_=render(after,bank,0 if bank==0 else 5,frame)
            if frame not in TARGETS[bank]:
                assert np.array_equal(ob,nb),(bank,frame)
                same_full+=1
            else:
                row=next(r for r in rows if r['bank']==bank and r['frame']==frame)
                assert np.array_equal(ob[row['protected_mask']],nb[row['protected_mask']])
                targets+=1
    # All named non-graphics resources, in addition to helper's whole-ARC check.
    from scripts.prepare_riko_ui import replace_entry
    assert replace_entry(after,2,entry(before,2))==before
    assert entry(before,3)==entry(after,3)
    assert entry(before,9)==entry(after,9)
    idle_a,_=render(before,0,0,147);idle_b,_=render(after,0,0,147)
    assert np.array_equal(idle_a,idle_b)
    source_after=file_hash(source);assert source_after==source_sha
    report={'passed':True,'source_bin_sha256':source_sha,'source_unchanged':True,
      'candidate_arc_sha256':CANDIDATE_SHA,'reproduction_byte_identical':True,
      'head_file_sha256':HEAD_SHA,'identity_roundtrip_arc_sha256':file_hash(WORK/'roundtrip_identity/PL01_U.ARC'),
      'checks':{'target_frames':targets,'unchanged_standalone_non_targets':same_full,
                'unchanged_partial_raw_non_targets':same_partial,'total_non_targets':same_full+same_partial,
                'idle147_identical':True,'composition_palette_sound_static_timing_identical':True,
                'protected_hand_body_weapon_feet_identical':True,'tile_counts_unchanged_max32':True,
                'shared_effect_refs_preserved':True},
      'negative_tests':rejected,'game_bin_written':False,'runtime_verified':False,
      'scope':'파일 재현·정적 보존 검사이며 별도 구현에 의한 독립 검증 또는 실기 검증은 아님'}
    write(WORK/'verification.json',report)
    print(json.dumps({'passed':True,'negative_cases':len(rejected),'non_target':same_full+same_partial,'evidence':str(WORK/'verification.json')}))


if __name__=='__main__':
    main()
