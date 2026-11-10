"""새85..92를 고정은행에 저장하고 기존18참조는 texel 순열로만 재압축한다."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from repack_part_records_lossless import repack
from scripts.prepare_riko_ui import replace_entry
from pack_shibuki_hurt import raw,repack_fixed_global
from scripts.optimize_rin_style_tiles import permute,tile_slices
from src.psx_player import indexed_atlas,composition_frame,bank_offsets
from prepare_lowhp_final import compose
from pack_dash_complete import protected_entries
P=H/'prepared_standing_special_base01/PL00_U.ARC';PARENT='fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e'
LOCK=H/'standing_fire_locked01/LOCK.json';LOCK_SHA='ab487baf93cb62a6c73fdf2121452adcbc10dff2e33c55ef00c3e66f60b2f3e5'
REFS=tuple(range(85,93));PBS=(0,5,6,7,8)
def validate(data,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT,'부모 불일치');blob=read(LOCK);need(sha(blob)==LOCK_SHA,'잠금 변경');lock=json.loads(blob)
    need(lock['refs']==list(REFS)and lock['parent_sha256']==PARENT,'잠금 범위')
    for name,digest in lock['files'].items():
        p=(ROOT/name).resolve();need(p.is_relative_to(ROOT.resolve()),'경로 범위');need(sha(read(p))==digest,'잠긴 입력 변경 '+name)
    return lock
def build(data,read=lambda p:p.read_bytes()):
    lock=validate(data,read);a=Archive(data);new=json.loads(read(H/'standing_fire_compact01/report.json'));old=json.loads(read(H/'standing_fire_existing_tileorder01/report.json'));plan=json.loads(read(H/'standing_fire_storage_plan02/report.json'))
    targets={n:{b:np.array(Image.open(H/f'standing_fire_targets_probe01/{n:03}_bank{b}_indices.png'))for b in PBS}for n in REFS};rawchanges={};counts={};changes={b:{}for b in PBS};storage=set(lock['storage_only_refs']);storage_proofs=[]
    for n,ll in targets.items():
        for b,v in ll.items():need(sha(v.tobytes())==lock['targets'][str(n)][str(b)],'목표층 변경')
    for group in new['groups']:
        nr=bytes.fromhex(group['raw']);need(len(nr)==group['count']*128 and 0<group['count']<=32,'새 타일 정원')
        for n in group['refs']:
            need(n in REFS,'새 대상 범위');rawchanges[n]=nr;counts[n]=group['count']
            for b in PBS:changes[b][n]=b''.join(struct.pack('<BBbb',*p)for p in group['parts'][str(b)][str(n)])or struct.pack('<BBbb',0,0,-8,-8)
    need(set(rawchanges)==set(REFS),'새 대상 누락')
    for group in old['groups']:
        ns=set(group['refs'])
        if not ns&storage:continue
        need(ns<=storage,'순열 공유 범위');first=min(ns);nr=read(H/f'standing_fire_existing_tileorder01/{first:03}_trial_raw.bin');mp={int(k):v for k,v in group['mapping'].items()};source=raw(a,0,first)
        need(sha(nr)==group['optimized_raw_sha256']and sha(source)==group['source_raw_sha256'],'순열 원시입력 변경');need(permute(nr,32,[mp[t]for t in range(32)])==source,'원raw 역변환 실패');need(all(mp[t]==t for t in group['optimization']['fixed_tiles']),'공유·효과 보호타일 이동')
        storage_proofs.append({'refs':sorted(ns),'source_raw_sha256':sha(source),'permuted_raw_sha256':sha(nr),'mapping':mp,'inverse_raw_exact':True,'all32_tiles_256_nibbles_preserved':True,'saved_bytes':group['optimization']['saved'],'fixed_tiles':group['optimization']['fixed_tiles']})
        for n in ns:
            need(raw(a,0,n)==source,'공유raw 다름');rawchanges[n]=nr;counts[n]=32
            for b in PBS:changes[b][n]=b''.join(struct.pack('<BBbb',p['flags'],mp[p['tile']],p['x'],p['y'])for p in composition_frame(a.c,b,n)['parts'])
    need(set(rawchanges)==set(REFS)|storage,'변경대상 누락')
    for n in rawchanges:
        owners={f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']};need(owners<=set(rawchanges),'대상 밖 공유stream')
    nc=a.c;slacks={};methods={}
    for b,cr in changes.items():
        for rec in cr.values():need(0<len(rec)<=96 and len(rec)%4==0,'파트 기록 정원')
        try:nc,slacks[b]=repack_parts(nc,b,cr);methods[b]='existing'
        except ValueError:nc,slacks[b],methods[b]=repack(nc,b,cr)
    need(bank_offsets(nc)==bank_offsets(a.c),'조립은행 경계 변경');ng,graphics=repack_fixed_global(a,rawchanges,counts);need(ng[:56]==a.g[:56],'그래픽은행 디렉터리 변경');need(ng[a.banks[0]['end']:]==a.g[a.banks[0]['end']:],'다른 그래픽은행 바이트 변경')
    candidate=replace_entry(replace_entry(data,2,ng),3,nc);need(sha(candidate)==plan['memory_candidate_sha256'],'메모리 계획과 다른 후보');z=Archive(candidate);allraw=nonraw=0
    for gb,bank in enumerate(a.banks):
        need(len(bank['frames'])==len(z.banks[gb]['frames']),'프레임 수 변경')
        for f in bank['frames']:
            n=f['index'];selected=gb==0 and n in rawchanges;expected=rawchanges[n]if selected else raw(a,gb,n);need(raw(z,gb,n)==expected,'원시 비교 실패');need(z.banks[gb]['frames'][n]['tile_count']==(counts[n]if selected else f['tile_count']),'타일정원 변경');allraw+=1;nonraw+=not selected
    layers=nonlayers=parts=partials=storagepartials=gpu=0;unreconstructed=[]
    for n in range(len(a.banks[0]['frames'])):
        for b in PBS:
            try:oldlayer=a.layer(n,b)[0]
            except(ValueError,IndexError)as ex:
                need(n not in rawchanges,'변경대상 조립불가')
                try:z.layer(n,b)
                except(ValueError,IndexError)as ex2:need(type(ex)==type(ex2)and str(ex)==str(ex2),'기존미복원 동작 변경');unreconstructed.append([n,b,str(ex)]);continue
                raise ValueError('미복원층이 바뀜')
            need(np.array_equal(z.layer(n,b)[0],targets[n][b]if n in targets else oldlayer),'층 표시 불일치');layers+=1;nonlayers+=n not in targets
        if n in rawchanges:
            for arm in(1,2):
                for mask in range(16):
                    expected=compose(a,targets[n],mask,arm)if n in targets else a.composite(n,mask,arm)[0];need(z.composite(n,mask,arm)[0].tobytes()==expected.tobytes(),'부분 RGBA 불일치');partials+=n in targets;storagepartials+=n in storage
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in PBS and n in rawchanges:need(records(z.c,b,n)==changes[b][n],'변경기록 불일치');continue
            need(records(z.c,b,n)==records(a.c,b,n),'기타조립 기록 변경');parts+=1
    for n in rawchanges:
        cnt=counts[n];at=np.frombuffer(indexed_atlas(rawchanges[n],cnt)[0],np.uint8).reshape(-1,256)
        for b in PBS:
            for p in composition_frame(z.c,b,n)['parts']:
                t=p['tile'];need(t<cnt,'GPU 타일 정원');tile=at[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
                need(t%16!=0 or not tile[:,0].any(),'GPU U경계');need(not p['flip_y']or t//16!=0 or not tile[0].any(),'GPU V경계');gpu+=1
    effects={}
    for t in(7,8):
        oldat=np.frombuffer(indexed_atlas(raw(a,0,88),a.banks[0]['frames'][88]['tile_count'])[0],np.uint8).reshape(-1,256);newat=np.frombuffer(indexed_atlas(raw(z,0,88),counts[88])[0],np.uint8).reshape(-1,256);sl=(slice(0,16),slice(t*16,(t+1)*16));need(np.array_equal(oldat[sl],newat[sl]),'88 전체효과타일 변경');effects[str(t)]=sha(oldat[sl].tobytes())
    fx=np.array(Image.open(H/'standing_fire_targets_probe01/088_effect_indices.png'));need(int((fx>0).sum())==83,'효과83');fm=fx>0;fxrgba=np.array(a.rgba(fx))
    for arm in(1,2):
        for mask in range(16):need(np.array_equal(np.array(z.composite(88,mask,arm)[0])[fm],fxrgba[fm]),'효과가림 변경')
    gunchecks=0
    for n in(85,86,87,89,90,91,92):
        guard=np.array(Image.open(H/f'standing_fire_modules_probe02/{n:03}_gun_guard.png'))>0;gun=np.array(Image.open(H/f'standing_fire_modules_probe02/{n:03}_gun_indices.png'));rgba=np.array(a.rgba(gun))
        for arm in(1,2):
            for mask in range(16):need(np.array_equal(np.array(z.composite(n,mask,arm)[0])[guard],rgba[guard]),'총열/투명가드 불일치');gunchecks+=1
    for n in(0,141,142):
        need(raw(z,0,n)==raw(a,0,n),'대기/등장raw 변경')
        for b in PBS:need(records(z.c,b,n)==records(a.c,b,n),'대기/등장기록 변경')
    ui=json.loads((H.parent/'x_selection_audit13/shibuki/report.json').read_text('utf8'));ui_refs={r['body_ref']for r in ui['rows']};need(not ui_refs&storage,'순열만 대상에 선택사본 존재')
    return candidate,{'passed':True,'before':PARENT,'after':sha(candidate),'target_lock_sha256':LOCK_SHA,'selected_refs':list(REFS),'storage_only_refs':sorted(storage),'storage_permutation_proofs':storage_proofs,'raw_references':allraw,'non_target_raw_exact':nonraw,'storage_raw_inverse_exact':len(storage),'layers_checked':layers,'target_layers_exact':40,'non_art_layers_exact':nonlayers,'non_target_part_records_exact':parts,'unreconstructed_layers_preserved':unreconstructed,'new_partial_rgba_exact':partials,'storage_partial_rgba_exact':storagepartials,'gun_guard_rgba_cases':gunchecks,'effect88_pixels':83,'effect88_full_tile_sha256':effects,'gpu_parts':gpu,'parts_slack':slacks,'parts_methods':methods,'graphics':graphics,'protected_entries':protected_entries(data,candidate),'protected_0_141_142':True,'old_parent_preserved':sha(P.read_bytes())==PARENT,'pixel_reduction':False,'bank_directory_changed':False,'ui_mapping_evidence':{'path':'work/sprite_style_unification_20261107/x_selection_audit13/shibuki/report.json','known_body_refs':sorted(ui_refs),'storage_only_refs_have_no_selected_ui_copy':True,'new85_92_ui_copy_sync_pending':True},'native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True,'runtime_verified':False,'frozen':False,'scope':'기본/포스85..92 새40층. 기존18참조는256nibble 전체를 보존한 순열/조립tile번호만 바꿔 고정은행68B여유 확보. 별도선택1..8 동기화는 root 후속.'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='standing_fire_base_pack01');z=ap.parse_args();d=(H/z.output).resolve();need(d.is_relative_to(H.resolve())and not d.exists(),'새 소유 출력폴더');candidate,report=build(P.read_bytes());d.mkdir();(d/'PL00_U.ARC').write_bytes(candidate);a=Archive(candidate)
    for form,mask in(('base',0),('fourth',15)):
        for i,refs in enumerate(((85,86,87),(88,89,90),(91,92))):page([(f'{n} actual {form}',a.composite(n,mask)[0])for n in refs],a.composite(0,mask)[0],d/f'{form}_readback_{i:02}.png',cols=3,scale=5)
    for n in REFS:page([(f'{n} mask{m:X}',a.composite(n,m)[0])for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
    write(d/'report.json',report);print(json.dumps({k:report[k]for k in('after','raw_references','non_target_raw_exact','target_layers_exact','new_partial_rgba_exact','storage_partial_rgba_exact','gpu_parts','parts_slack')}))
if __name__=='__main__':main()
