"""체이서13과 기존16참조 역순열을 메모리에서만 결합하는 저장 계획."""
from pathlib import Path
import sys,json,struct,copy
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from pack_chaser_base import *
from scripts.optimize_rin_style_tiles import permute

def main():
    d=H/'chaser_storage_plan01';need(not d.exists(),'새 계획 폴더');d.mkdir();a=Archive(P.read_bytes());recipe=json.loads((H/'chaser_storage01/recipe.json').read_text('utf8'))
    old=json.loads((H/'standing_fire_existing_tileorder01/report.json').read_text('utf8'));chosen=(33,39,55,57,59,63,65,75)
    rr={int(b):{int(n):bytes.fromhex(v)for n,v in q.items()}for b,q in recipe['parts'].items()};raws={};counts={};perms=[]
    for g in recipe['groups']:
        for n in g['refs']:raws[n]=(H/f'chaser_storage01/{n:03}.raw').read_bytes();counts[n]=g['count'];need(sha(raws[n])==g['raw_sha256'],'새 stream 변경')
    for g in old['groups']:
        if g['refs'][0]not in chosen:continue
        ns=g['refs'];n=ns[0];source=raw(a,0,n);new=(H/f'standing_fire_existing_tileorder01/{n:03}_trial_raw.bin').read_bytes();mp={int(k):v for k,v in g['mapping'].items()}
        need(sha(source)==g['source_raw_sha256'],'이전탐색 source가 현재와다름');need(permute(new,32,[mp[t]for t in range(32)])==source,'전체raw역순열 불일치')
        for ref in ns:
            need(raw(a,0,ref)==source,'공유source 불일치');raws[ref]=new;counts[ref]=32
            for b in PBS:rr[b][ref]=b''.join(struct.pack('<BBbb',p['flags'],mp[p['tile']],p['x'],p['y'])for p in composition_frame(a.c,b,ref)['parts'])
        perms.append({'refs':ns,'saved':g['optimization']['saved'],'source_raw_sha256':sha(source),'new_raw_sha256':sha(new),'mapping':mp,'inverse_all256_nibble_exact':True,'source_probe':f'standing_fire_existing_tileorder01/{n:03}_trial_raw.bin'})
    nc=a.c;parts={}
    for b,q in rr.items():
        try:
            try:nc,slack=repack_parts(nc,b,q);mode='existing'
            except ValueError:nc,slack,mode=repack_global(nc,b,q)
            parts[str(b)]={'slack':slack,'method':mode,'passed':True}
        except ValueError as ex:parts[str(b)]={'passed':False,'error':str(ex)}
    report={'parent_sha256':PARENT,'source_recipe_sha256':sha((H/'chaser_storage01/recipe.json').read_bytes()),'source_manifest_sha256':MANIFEST,'new_art_refs':list(REFS),'storage_only_refs':sorted(n for g in perms for n in g['refs']),'storage_only_groups':perms,'saved':sum(g['saved']for g in perms),'parts':parts,'arc_written':False,'bank_directory_changed':False,'scope':'현재 고정은행 안의 새13표시와 기존16참조 타일저장순열을 메모리로만 대조. 기존그림은 전체raw 역순열/각5층 및32부분에서 보존 확인.','all_source_inputs_unchanged':True}
    try:
        ng,gfx=repack_fixed_global(a,raws,counts);report['graphics']=gfx;need(all(v['passed']for v in parts.values()),'조립 미수납')
        data=replace_entry(replace_entry(a.data,2,ng),3,nc);z=Archive(data);raw_checks=layer_checks=partial=gpu=other_records=0
        for gb,bank in enumerate(a.banks):
            need((bank['base'],bank['end'])==(z.banks[gb]['base'],z.banks[gb]['end']),'은행경계 변경')
            for f in bank['frames']:
                n=f['index'];need(raw(z,gb,n)==(raws[n]if gb==0 and n in raws else raw(a,gb,n)),'raw 불일치');raw_checks+=1
        for n in range(237):
            if n in(105,*range(175,183)):continue
            targets={b:np.array(Image.open(TD/f'{n:03}_bank{b}_indices.png'))for b in PBS}if n in REFS else None
            for b in PBS:need(np.array_equal(z.layer(n,b)[0],targets[b]if targets else a.layer(n,b)[0]),f'층 불일치 {n}/{b}');layer_checks+=1
            if n not in raws:continue
            for arm in(1,2):
                for mask in range(16):need(z.composite(n,mask,arm)[0].tobytes()==(compose(a,targets,mask,arm)if targets else a.composite(n,mask,arm)[0]).tobytes(),'부분RGBA 불일치');partial+=1
            at=np.frombuffer(indexed_atlas(raws[n],counts[n])[0],np.uint8).reshape(-1,256)
            for b in PBS:
                for p in composition_frame(z.c,b,n)['parts']:
                    t=p['tile'];tile=at[t//16*16:t//16*16+16,t%16*16:t%16*16+16];need(t<counts[n],'tile범위');need(t%16!=0 or not tile[:,0].any(),'GPU U');need(not p['flip_y']or t//16!=0 or not tile[0].any(),'GPU V');gpu+=1
        for b in range(len(bank_offsets(a.c))):
            for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
                if b in PBS and n in raws:continue
                need(records(z.c,b,n)==records(a.c,b,n),'비대상기록변경');other_records+=1
        need(bank_offsets(a.c)==bank_offsets(z.c),'조립경계 변경');protected_entries(a.data,data)
        report.update(memory_candidate_passed=True,memory_candidate_sha256=sha(data),raw_checks=raw_checks,layer_checks=layer_checks,partial_RGBA=partial,GPU_parts=gpu,other_records=other_records,limits=['새508원MIPS/directory/큐 및독립reader는 후속','실제게임/차량 손잡이 접점은 미확인','별도UI/저장사본은 이번표시와 관계읽기만으로없다고확대하지않음'])
    except Exception as ex:report.update(memory_candidate_passed=False,error=str(ex))
    write(d/'report.json',report);print(json.dumps({k:report.get(k)for k in('saved','parts','graphics','memory_candidate_passed','error','memory_candidate_sha256','raw_checks','layer_checks','partial_RGBA','GPU_parts')}))
if __name__=='__main__':main()
