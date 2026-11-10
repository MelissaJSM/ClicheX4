"""217/220 새몸과18개 원효과 타일을 삭제 없이 저장하는 읽기/메모리 조사."""
from pathlib import Path
import sys,json,struct,io
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from prepare_nova_strike_base_targets import P,PARENT,PBS,REFS,TD
from scripts.export_x_consistency import Archive
from scripts.overhaul_sprites_costume_pack import pack_planes,resize_tile_storage
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from repack_part_records_lossless import repack as repack_global
from probe_chaser_storage import optimize
from pack_shibuki_hurt import raw,repack_fixed_global
from src.psx_player import composition_frame,indexed_atlas,bank_offsets
from src.psx_compress import encode_stream
from scripts.optimize_rin_style_tiles import permute
from scripts.prepare_riko_ui import replace_entry
from prepare_lowhp_final import compose
from pack_dash_complete import protected_entries
MANIFEST='784559d663dc9caa09de1a15eae01c439eecee3d4b4d354bee90d397e576e076'

def main():
    d=H/'nova_strike_storage02';need(not d.exists(),'새 조사폴더');d.mkdir()
    a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모 불일치')
    need(sha((TD/'manifest.json').read_bytes())==MANIFEST,'목표 목록 불일치');m=json.loads((TD/'manifest.json').read_text('utf8'))
    for name,digest in m['source_files'].items():need(sha((ROOT/name).read_bytes())==digest,'출처 변경 '+name)
    targets={n:{b:np.array(Image.open(TD/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in REFS}
    for n,ls in targets.items():
        for b,z in ls.items():need(sha(z.tobytes())==m['targets'][str(n)][str(b)],'목표 화소 변경')
    planes=[crop(targets[217][b])for b in PBS];rr={b:{}for b in PBS};raws={};counts={};groups=[]
    for n in REFS:
        seed=(TD/'effect220_seed32.raw').read_bytes()if n==220 else bytes(4096)
        free=set(range(18,32))if n==220 else set(range(1,32))-{16}
        nr,pp=pack_planes(seed,32,planes,free,[8,24,24,24,24]);source=nr
        count=32 if n==220 else max(t for ps in pp for t,x,y,fl in ps)+1
        nr=resize_tile_storage(nr,32,count)
        fixed=set(range(18))if n==220 else set(range(0,count,16))
        fixed|={t for ps in pp for t,x,y,fl in ps if fl&128}
        nr,mp,opt=optimize(nr,count,sorted(fixed),steps=12)
        pp=[[(mp[t],x,y,fl)for t,x,y,fl in ps]for ps in pp]
        for b,ps in zip(PBS,pp):
            rec=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in ps)
            if n==220 and b==0:rec=(TD/'effect220_prefix.bin').read_bytes()+rec
            rr[b][n]=rec or struct.pack('<BBbb',0,0,-8,-8)
        raws[n]=nr;counts[n]=count;(d/f'{n:03}.raw').write_bytes(nr)
        groups.append({'refs':[n],'count':count,'raw_sha256':sha(nr),'source_raw_sha256':sha(source),'optimization':opt,'mapping':mp,'parts':{str(b):len(rr[b][n])//4 for b in PBS}})
        write(d/'progress.json',groups);print(json.dumps(groups[-1]),flush=True)
    old=json.loads((H/'standing_fire_existing_tileorder01/report.json').read_text('utf8'));perms=[]
    for g in old['groups']:
        if g['refs'][0]not in(45,71):continue
        ns=g['refs'];n=ns[0];source=raw(a,0,n);new=(H/f'standing_fire_existing_tileorder01/{n:03}_trial_raw.bin').read_bytes();mp={int(k):v for k,v in g['mapping'].items()}
        need(sha(source)==g['source_raw_sha256'],'이전 저장탐색 부모와현재다름');need(permute(new,32,[mp[t]for t in range(32)])==source,'전체 역순열 불일치')
        for ref in ns:
            need(raw(a,0,ref)==source,'공유raw 불일치');raws[ref]=new;counts[ref]=32
            for b in PBS:rr[b][ref]=b''.join(struct.pack('<BBbb',p['flags'],mp[p['tile']],p['x'],p['y'])for p in composition_frame(a.c,b,ref)['parts'])
        perms.append({'refs':ns,'saved':g['optimization']['saved'],'source_raw_sha256':sha(source),'new_raw_sha256':sha(new),'mapping':mp,'inverse_all256_nibble_exact':True,'source_probe':f'standing_fire_existing_tileorder01/{n:03}_trial_raw.bin'})
    nc=a.c;parts={}
    for b,q in rr.items():
        try:
            try:nc,slack=repack_parts(nc,b,q);mode='existing'
            except ValueError:nc,slack,mode=repack_global(nc,b,q)
            parts[str(b)]={'slack':slack,'method':mode,'passed':True}
        except ValueError as ex:parts[str(b)]={'passed':False,'error':str(ex)}
    report={'parent_sha256':PARENT,'target_manifest_sha256':MANIFEST,'groups':groups,'parts':{str(b):{str(n):v.hex()for n,v in q.items()}for b,q in rr.items()},'part_storage':parts,'storage_only_groups':perms,'saved_existing':sum(g['saved']for g in perms),'arc_written':False,'new_base220_part_count':len(rr[0][220])//4,'native_part_limit_verified':False,'no_pixel_deletion':True,'no_bank_move':True}
    try:
        ng,gfx=repack_fixed_global(a,raws,counts);report['graphics']=gfx;need(all(v['passed']for v in parts.values()),'조립 공간 부족')
        data=replace_entry(replace_entry(a.data,2,ng),3,nc);z=Archive(data);checks={'raw':0,'layers':0,'partial_RGBA':0,'GPU_parts':0,'other_records':0}
        for gb,bank in enumerate(a.banks):
            need((bank['base'],bank['end'])==(z.banks[gb]['base'],z.banks[gb]['end']),'은행경계 변경')
            for f in bank['frames']:
                n=f['index'];need(raw(z,gb,n)==(raws[n]if gb==0 and n in raws else raw(a,gb,n)),'raw 불일치');checks['raw']+=1
        for n in range(237):
            if n in(105,*range(175,183)):continue
            for b in PBS:need(np.array_equal(z.layer(n,b)[0],targets[n][b]if n in REFS else a.layer(n,b)[0]),f'층 불일치{n}/{b}');checks['layers']+=1
            if n not in raws:continue
            for arm in(1,2):
                for mask in range(16):need(z.composite(n,mask,arm)[0].tobytes()==(compose(a,targets[n],mask,arm)if n in REFS else a.composite(n,mask,arm)[0]).tobytes(),'부분RGBA 불일치');checks['partial_RGBA']+=1
            at=np.frombuffer(indexed_atlas(raws[n],counts[n])[0],np.uint8).reshape(-1,256)
            for b in PBS:
                for p in composition_frame(z.c,b,n)['parts']:
                    t=p['tile'];tile=at[t//16*16:t//16*16+16,t%16*16:t%16*16+16];need(t<counts[n],'타일범위');need(t%16!=0 or not tile[:,0].any(),'GPU U');need(not p['flip_y']or t//16!=0 or not tile[0].any(),'GPU V');checks['GPU_parts']+=1
        for b in range(len(bank_offsets(a.c))):
            for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
                if b in PBS and n in raws:continue
                need(records(z.c,b,n)==records(a.c,b,n),'다른파트 변경');checks['other_records']+=1
        need(bank_offsets(a.c)==bank_offsets(z.c),'조립경계 변경');protected_entries(a.data,data)
        report.update(memory_candidate_passed=True,memory_candidate_sha256=sha(data),checks=checks)
    except Exception as ex:report.update(memory_candidate_passed=False,error=str(ex))
    write(d/'recipe.json',report);print(json.dumps({k:report.get(k)for k in('saved_existing','part_storage','graphics','memory_candidate_passed','error','memory_candidate_sha256','checks')}))
if __name__=='__main__':main()
