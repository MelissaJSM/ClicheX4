"""새 작은머리19를 고정은행에 수납. 기존 빈678 기록·198 원시자료는 불변."""
from pathlib import Path
import sys,json,struct,io,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from prepare_vehicle_head_targets import P,PARENT,PBS,REFS,TD
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,composition_frame,indexed_atlas
from pack_shibuki_hurt import raw,repack_fixed_global
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
MANIFEST='48f29e601ea0375e09e2180e358768ed70fe9bf29eb12603853348ef24e3f3e6'
def validate(data,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT,'부모 변경');blob=read(TD/'manifest.json');need(sha(blob)==MANIFEST,'목표 목록 변경');m=json.loads(blob)
    for name,digest in m['source_files'].items():need(sha(read(ROOT/name))==digest,'출처 변경 '+name)
    for n in REFS:
        for b in PBS:
            z=np.array(Image.open(io.BytesIO(read(TD/f'{n:03}_bank{b}_indices.png'))));need(z.shape==(384,384) and z.dtype==np.uint8 and z.max()<16,'목표 색인 형식');need(sha(z.tobytes())==m['targets'][str(n)][str(b)],'목표층 변경')
    return m
def build(data):
    meta=validate(data);a=Archive(data);targets={n:{b:np.array(Image.open(TD/f'{n:03}_bank{b}_indices.png')) for b in PBS} for n in REFS};changes={0:{},5:{}};tilemap={0:1,5:4};atlas=np.zeros((16,80),np.uint8)
    # 0/2/3은 기존 빈678 파트가 읽는 타일이다. 전체256nibble을 빈칸으로 보존한다.
    for b,t in tilemap.items():atlas[:15,t*16:t*16+13]=targets[184][b][123:138,150:163]
    packed=bytes((atlas[:,::2]|atlas[:,1::2]<<4).ravel());need(len(packed)==5*128,'5타일 길이');full=np.frombuffer(indexed_atlas(packed,5)[0],np.uint8).reshape(16,256);need(not full[:,:16].any() and not full[:,32:64].any(),'빈타일 보호')
    shifts={v['ref']:v['translation_from184'] for v in meta['translations']}
    for n in REFS:
        dx,dy=shifts[n]
        for b,t in tilemap.items():changes[b][n]=struct.pack('<BBbb',0,t,-10+dx,-37+dy)
        for b in (6,7,8):
            need(not a.layer(n,b)[0].any(),'기존 비어야 함');need(all(p['tile'] in (0,2,3) for p in composition_frame(a.c,b,n)['parts']),'빈층 소비타일 변경')
    nc=a.c;slacks={}
    for b,rr in changes.items():nc,slacks[b]=repack_parts(nc,b,rr)
    raws={n:packed for n in REFS};counts={n:5 for n in REFS};ng,gfx=repack_fixed_global(a,raws,counts);out=replace_entry(replace_entry(data,2,ng),3,nc);z=Archive(out)
    need(bank_offsets(nc)==bank_offsets(a.c),'조립은행 경계');need(ng[:56]==a.g[:56] and ng[a.banks[0]['end']:]==a.g[a.banks[0]['end']:],'타그래픽은행')
    total=nonraw=layers=kept=parts=partial=gpu=0
    for gb,bank in enumerate(a.banks):
        need((bank['base'],bank['end'],len(bank['frames']))==(z.banks[gb]['base'],z.banks[gb]['end'],len(z.banks[gb]['frames'])),'그래픽 경계')
        for f in bank['frames']:
            n=f['index'];selected=gb==0 and n in REFS;need(raw(z,gb,n)==(packed if selected else raw(a,gb,n)),'원시 불일치');total+=1;nonraw+=not selected
    for n in range(237):
        if n in (105,*range(175,183)):continue
        for b in PBS:need(np.array_equal(z.layer(n,b)[0],targets[n][b] if n in targets else a.layer(n,b)[0]),f'층 불일치 {n}/{b}');layers+=1;kept+=n not in targets
        if n not in targets:continue
        for arm in (1,2):
            for mask in range(16):need(z.composite(n,mask,arm)[0].tobytes()==compose(a,targets[n],mask,arm).tobytes(),'부분 표시 불일치');partial+=1
        for b in PBS:
            for p in composition_frame(z.c,b,n)['parts']:
                t=p['tile'];tile=full[:,t%16*16:t%16*16+16];need(t%16!=0 or not tile[:,0].any(),'GPU U경계');need(not p['flip_y'] or not tile[0].any(),'GPU V경계');gpu+=1
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in changes and n in changes[b]:need(records(nc,b,n)==changes[b][n],'목표 기록');continue
            need(records(nc,b,n)==records(a.c,b,n),'비대상 기록 변경');parts+=1
    need(not z.composite(198,0)[0].getbbox() and not z.composite(198,15)[0].getbbox(),'198 빈칸');need(raw(z,0,198)==raw(a,0,198),'198 raw')
    return out,{'passed':True,'parent_sha256':PARENT,'candidate_sha256':sha(out),'target_manifest_sha256':MANIFEST,'refs':list(REFS),'counts':{'raw':total,'non_target_raw':nonraw,'target_layers':95,'changed_owner_layers':38,'selected_empty_layers_exact':57,'all_layers':layers,'non_target_layers':kept,'non_target_records':parts,'partial_RGBA':partial,'GPU_parts':gpu},'shared_new_stream':{'tile_count':5,'raw_sha256':sha(packed),'owners':list(REFS),'empty_full_tiles':[0,2,3],'base_tile':1,'overlay_tile':4},'translations':meta['translations'],'part_slack':slacks,'graphics':gfx,'all_bank_boundaries_preserved':True,'protected_entries':protected_entries(data,out),'selected_empty678_records_preserved':True,'ref198_raw_layers_records_preserved':True,'duplicate_overlay_parts_replaced_by_one_exact_part':True,'old_body_copied':False,'pixel_reduction':False,'runtime_verified':False,'native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='vehicle_head_ultimate_pack01');args=ap.parse_args();d=(H/args.output).resolve();need(d.is_relative_to(H.resolve()) and not d.exists(),'새 소유 출력');d.mkdir();out,proof=build(P.read_bytes());(d/'PL02_U.ARC').write_bytes(out);a=Archive(out)
    for form,mask in (('before',15),('after',0)):
        for i in range(2):page([(f'{n} {form}',a.composite(n,mask)[0]) for n in REFS[i*10:i*10+10]],a.composite(0,mask)[0],d/f'{form}_readback_{i:02}.png',cols=5,scale=4)
    for n in (184,196):page([(f'{n} mask{m:X}',a.composite(n,m)[0]) for m in range(16)],a.composite(0,0)[0],d/f'ownership_{n:03}.png',cols=4,scale=3)
    write(d/'report.json',proof);print(json.dumps({'candidate':sha(out),'counts':proof['counts'],'part_slack':proof['part_slack'],'gfx':proof['graphics']['remaining_slack']}))
if __name__=='__main__':main()
