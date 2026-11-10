"""노바4 새아트와 기존10 저장순열을 고정은행에 재현한다."""
from pathlib import Path
import sys,json,struct,argparse,io
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from pack_nova_base import P,PARENT,PBS,REFS,TD,GROUPS,MANIFEST,need,sha,write,Archive,page,records,repack_parts,repack_global,replace_entry,raw,repack_fixed_global,bank_offsets,composition_frame,indexed_atlas,protected_entries,compose
from scripts.optimize_rin_style_tiles import permute
LOCK=H/'nova_locked01/LOCK.json';LOCK_SHA='8a3b109e29b5db1e287977260a8e1216e0acbf15087b739db1981e6243852a91'

def validate(data,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT,'부모 불일치');blob=read(LOCK);need(sha(blob)==LOCK_SHA,'잠금 변경');lock=json.loads(blob)
    need(lock['refs']==list(REFS)and lock['parent_sha256']==PARENT,'잠금 범위')
    for name,digest in lock['files'].items():
        p=(ROOT/name).resolve();need(p.is_relative_to(ROOT.resolve()),'입력 경로 범위');need(sha(read(p))==digest,'잠긴 입력 변경 '+name)
    return lock

def build(data,read=lambda p:p.read_bytes()):
    lock=validate(data,read);a=Archive(data);recipe=json.loads(read(H/'nova_storage01/recipe.json'));plan=json.loads(read(H/'nova_storage_plan01/report.json'));old=json.loads(read(H/'standing_fire_existing_tileorder01/report.json'))
    targets={n:{b:np.array(Image.open(io.BytesIO(read(TD/f'{n:03}_bank{b}_indices.png'))))for b in PBS}for n in REFS};storage=set(lock['storage_only_refs']);raws={};counts={};changes={int(b):{int(n):bytes.fromhex(v)for n,v in q.items()}for b,q in recipe['parts'].items()};proofs=[]
    for n,ll in targets.items():
        for b,z in ll.items():need(sha(z.tobytes())==lock['targets'][str(n)][str(b)],'목표층 변경')
    for g in recipe['groups']:
        for n in g['refs']:
            nr=read(H/f'nova_storage01/{n:03}.raw');need(sha(nr)==g['raw_sha256']and len(nr)==g['count']*128,'새raw 변경');raws[n]=nr;counts[n]=g['count']
    for g in old['groups']:
        ns=set(g['refs'])
        if not ns&storage:continue
        need(ns<=storage,'순열 공유 범위');n=min(ns);nr=read(H/f'standing_fire_existing_tileorder01/{n:03}_trial_raw.bin');mp={int(k):v for k,v in g['mapping'].items()};source=raw(a,0,n)
        need(sha(source)==g['source_raw_sha256']and sha(nr)==g['optimized_raw_sha256'],'순열 출처 변경');need(permute(nr,32,[mp[t]for t in range(32)])==source,'전체raw역순열 실패');need(all(mp[t]==t for t in g['optimization']['fixed_tiles']),'공유 보호tile 변경')
        proofs.append({'refs':sorted(ns),'mapping':mp,'source_raw_sha256':sha(source),'new_raw_sha256':sha(nr),'all32_tiles_256_nibbles_inverse_exact':True,'saved':g['optimization']['saved'],'fixed_tiles':g['optimization']['fixed_tiles']})
        for ref in ns:
            need(raw(a,0,ref)==source,'공유raw 불일치');raws[ref]=nr;counts[ref]=32
            for b in PBS:changes[b][ref]=b''.join(struct.pack('<BBbb',p['flags'],mp[p['tile']],p['x'],p['y'])for p in composition_frame(a.c,b,ref)['parts'])
    need(set(raws)==set(REFS)|storage,'범위 누락')
    for n in raws:need({f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']}<=set(raws),'대상 밖 공유raw')
    nc=a.c;slacks={};methods={}
    for b,q in changes.items():
        for rec in q.values():need(0<len(rec)<=96 and len(rec)%4==0,'파트 정원')
        try:nc,slacks[b]=repack_parts(nc,b,q);methods[b]='existing'
        except ValueError:nc,slacks[b],methods[b]=repack_global(nc,b,q)
    ng,gfx=repack_fixed_global(a,raws,counts);need(ng[:56]==a.g[:56]and ng[a.banks[0]['end']:]==a.g[a.banks[0]['end']:],'다른 은행 변경');need(bank_offsets(nc)==bank_offsets(a.c),'조립경계 변경')
    out=replace_entry(replace_entry(data,2,ng),3,nc);need(sha(out)==lock['candidate_sha256']==plan['memory_candidate_sha256'],'계획과 다른 후보');z=Archive(out);total=nonraw=layers=otherlayers=parts=newpartial=storagepartial=gpu=0;unreconstructed=[]
    for gb,bank in enumerate(a.banks):
        need((bank['base'],bank['end'],len(bank['frames']))==(z.banks[gb]['base'],z.banks[gb]['end'],len(z.banks[gb]['frames'])),'은행경계 변경')
        for f in bank['frames']:
            n=f['index'];selected=gb==0 and n in raws;need(raw(z,gb,n)==(raws[n]if selected else raw(a,gb,n)),'raw 불일치');need(z.banks[gb]['frames'][n]['tile_count']==(counts[n]if selected else f['tile_count']),'정원 변경');total+=1;nonraw+=not selected
    for n in range(len(a.banks[0]['frames'])):
        for b in PBS:
            try:oldlayer=a.layer(n,b)[0]
            except(ValueError,IndexError)as ex:
                need(n not in raws,'변경대상 조립불가')
                try:z.layer(n,b)
                except(ValueError,IndexError)as ex2:need(type(ex)==type(ex2)and str(ex)==str(ex2),'기존 미복원 변경');unreconstructed.append([n,b,str(ex)]);continue
                raise ValueError('미복원층 변경')
            need(np.array_equal(z.layer(n,b)[0],targets[n][b]if n in targets else oldlayer),f'층 불일치 {n}/{b}');layers+=1;otherlayers+=n not in targets
        if n not in raws:continue
        for arm in(1,2):
            for mask in range(16):
                want=compose(a,targets[n],mask,arm)if n in targets else a.composite(n,mask,arm)[0];need(z.composite(n,mask,arm)[0].tobytes()==want.tobytes(),'부분RGBA 불일치');newpartial+=n in targets;storagepartial+=n in storage
        at=np.frombuffer(indexed_atlas(raws[n],counts[n])[0],np.uint8).reshape(-1,256)
        for b in PBS:
            for p in composition_frame(z.c,b,n)['parts']:
                t=p['tile'];tile=at[t//16*16:t//16*16+16,t%16*16:t%16*16+16];need(t<counts[n],'GPU tile범위');need(t%16!=0 or not tile[:,0].any(),'GPU U');need(not p['flip_y']or t//16!=0 or not tile[0].any(),'GPU V');gpu+=1
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in PBS and n in raws:need(records(z.c,b,n)==changes[b][n],'대상기록 불일치');continue
            need(records(z.c,b,n)==records(a.c,b,n),'비대상기록 변경');parts+=1
    ui=json.loads((H.parent/'x_selection_audit13/shibuki/report.json').read_text('utf8'));ui_refs={r['body_ref']for r in ui['rows']};need(not ui_refs&set(raws),'현재 알려진 UI사본 공유')
    return out,{'passed':True,'before':PARENT,'after':sha(out),'refs':list(REFS),'storage_only_refs':sorted(storage),'storage_proofs':proofs,'target_lock_sha256':LOCK_SHA,'raw_references':total,'non_target_raw_exact':nonraw,'storage_raw_inverse_exact':len(storage),'layers_checked':layers,'target_layers_exact':20,'non_art_layers_exact':otherlayers,'non_target_records':parts,'unreconstructed_layers_preserved':unreconstructed,'new_partial_RGBA':newpartial,'storage_partial_RGBA':storagepartial,'gpu_parts':gpu,'parts_slack':slacks,'parts_methods':methods,'graphics':gfx,'protected_entries':protected_entries(data,out),'bank_directory_changed':False,'pixel_reduction':False,'known_UI_copy_refs':sorted(ui_refs),'native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True,'runtime_verified':False,'frozen':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='nova_base_pack02');args=ap.parse_args();d=(H/args.output).resolve();need(d.is_relative_to(H.resolve())and not d.exists(),'새 소유 출력');out,report=build(P.read_bytes());d.mkdir();(d/'PL00_U.ARC').write_bytes(out);a=Archive(out)
    for form,mask in(('base',0),('fourth',15)):
        for i,ns in enumerate(GROUPS):page([(f'{n} actual {form}',a.composite(n,mask)[0])for n in ns],a.composite(0,mask)[0],d/f'{form}_readback_{i:02}.png',cols=2,scale=5)
    for n in(213,215):page([(f'{n} mask{m:X}',a.composite(n,m)[0])for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
    write(d/'report.json',report);print(json.dumps({k:report[k]for k in('after','raw_references','non_target_raw_exact','layers_checked','new_partial_RGBA','storage_partial_RGBA','gpu_parts','parts_slack')}))
if __name__=='__main__':main()
