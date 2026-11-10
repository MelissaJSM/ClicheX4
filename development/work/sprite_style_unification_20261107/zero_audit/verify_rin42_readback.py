"""Read-only cumulative42 audit; no art registration or packing producer calls."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'rin_extension'
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
sha=lambda x:hashlib.sha256(x).hexdigest()
source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin'
assert sha(source.read_bytes())=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720'
before=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC'];assert sha(before)=='e6dbffce1b3f3fa4842c4092c6a4de09109db1bd5569864d4959cb7ec92849e2'
path=OUT/'prepared_air_continuation2_v2/PL01_U.ARC';after=path.read_bytes();assert sha(after)=='ffca3087c17c883e6383b0ff38417b003138d1614c8add8edb1b99199bf322df'
targets={}
run=json.loads((OUT/'run_art_sources_v1.json').read_text('utf8'))
for f in run['frames']:
    p=ROOT/f['path'];assert sha(p.read_bytes())==f['sha256'];targets[f['ref']]=p
for n in [21,27,35,39,40]:targets[n]=OUT/f'air_wall_head_candidate_v4/b0_{39 if n==40 else n:03d}_indices.png'
for n in [22,23,24,25,26]:targets[n]=OUT/f'air_continuation_registered_v2/b0_{22 if n==23 else n:03d}_indices.png'
for n,s in {44:44,46:46,47:46,48:46,50:50,51:51,52:51}.items():targets[n]=OUT/f'dash_continuation01/native/b0_{s:03d}_indices.png'
for n,s in {28:28,29:29,30:29,31:31,32:31,33:33}.items():targets[n]=OUT/f'air_continuation02/native/b0_{s:03d}_indices.png'
assert len(targets)==42
manifest_checks=[]
for name in ['run_art_sources_v1','air_wall_sources_v3','air_continuation_sources_v1','dash_sources_v1','air_continuation2_sources_v1']:
    mp=OUT/(name+'.json');m=json.loads(mp.read_text('utf8'));items=m.get('inputs',[])+m.get('frames',[])
    for f in items:
        p=ROOT/f['path'];assert sha(p.read_bytes())==f['sha256'],str(p)
    manifest_checks.append({'path':str(mp.relative_to(ROOT)),'sha256':sha(mp.read_bytes()),'files':len(items)})
g,c=entry(before,2),entry(before,3);ng,nc=entry(after,2),entry(after,3)
assert replace_entry(replace_entry(after,2,g),3,c)==before
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
assert bank_offsets(c)==bank_offsets(nc)
counts={'raw':0,'display':0,'non_target_raw_exact':0,'non_target_display_exact':0,'non_target_parts_exact':0,'selected_target_exact':0};rows=[]
def rec(c,bank,n):
    parts=composition_frame(c,bank,n)['parts'];return b''.join(c[p['record_offset']:p['record_offset']+4]for p in parts)
for bi in (0,1):
    ob=graphics_bank(g,bi);nb=graphics_bank(ng,bi);assert len(ob['frames'])==len(nb['frames'])
    for of,nf in zip(ob['frames'],nb['frames']):
        n=of['index'];selected=bi==0 and n in targets
        ar=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data
        br=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
        counts['raw']+=1;assert nf['tile_count']<=32
        if not selected:
            assert ar==br and of['tile_count']==nf['tile_count'];counts['non_target_raw_exact']+=1
            assert rec(c,bi*5,n)==rec(nc,bi*5,n);counts['non_target_parts_exact']+=1
        else:
            aa=np.frombuffer(indexed_atlas(ar,of['tile_count'])[0],np.uint8).reshape(-1,256);bb=np.frombuffer(indexed_atlas(br,nf['tile_count'])[0],np.uint8).reshape(-1,256)
            for p in composition_frame(nc,0,n)['parts']:
                t=p['tile'];y,x=t//16*16,t%16*16
                if t%16==0:assert not np.any((aa[y:y+16,x]==0)&(bb[y:y+16,x]>0))
                if p['flip_y']and t//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(bb[y,x:x+16]>0))
        if bi==1 and 42<=n<=49:continue
        old=render(before,bi,bi*5,n)[0];new=render(after,bi,bi*5,n)[0];counts['display']+=1
        if not selected:assert np.array_equal(old,new);counts['non_target_display_exact']+=1
        else:
            wanted=np.array(Image.open(targets[n]));assert np.array_equal(wanted,new);counts['selected_target_exact']+=1
            rows.append({'ref':n,'target':str(targets[n].relative_to(ROOT)),'target_sha256':sha(targets[n].read_bytes()),'changed_world_pixels':int(np.count_nonzero(old!=new)),'tiles_before_after':[of['tile_count'],nf['tile_count']]})
assert counts=={'raw':444,'display':436,'non_target_raw_exact':402,'non_target_display_exact':394,'non_target_parts_exact':402,'selected_target_exact':42}
for n in (0,1,2,146,147,148):assert np.array_equal(render(before,0,0,n)[0],render(after,0,0,n)[0])
report={'passed':True,'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':sha(source.read_bytes()),'source_arc_sha256':sha(before),'candidate':str(path.relative_to(ROOT)),'candidate_sha256':sha(after),'counts':counts,'rows':rows,'producer_functions_called':False,'all_other_entries_palette_audio_exact':True,'native_bank_boundaries_exact':True,'idle6_exact':True,'partial8_raw_and_parts_exact':True,'new_gpu_boundary_alpha':0,'timing_exe_or_game_mutation':False,'runtime_verified':False,'scope':'별도 읽기 검증기로 실제 부모 BIN과 최종29 ARC/등록PNG를 직접 대조했다. 미술 수용과 실제 실행 검증을 대체하지 않는다.'}
report['scope']='제작·패킹 함수 없이 실제 부모 BIN, 누적 42참조 ARC, 원화 입력과 등록 PNG를 직접 대조했다. 미술 수용 및 실제 플레이 검증을 대신하지 않는다.'
report['art_manifest_checks']=manifest_checks
plan={'project':'ver_rin_nana','source_bin':str(source.relative_to(ROOT)),'source_sha256':sha(source.read_bytes()),'resources':{'PL01_U.ARC':{'path':str(path.relative_to(ROOT)),'before':sha(before),'after':sha(after)}},'checkpoint_only':True,'full_art_unification_complete':False}
(OUT/'rin42_components.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
(OUT/'final42_readback_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'candidate_sha256':sha(after),'counts':counts}))
