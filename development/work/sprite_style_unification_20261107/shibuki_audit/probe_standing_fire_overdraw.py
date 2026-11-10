"""두 자세 공통 알파와 실제 후그리기를 이용한 정확표시 공동 atlas 조사."""
from pathlib import Path
import sys,json,itertools,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import repack_parts
from repack_part_records_lossless import repack
from probe_standing_fire_capacity import render,PBS
from src.psx_compress import encode_stream

def main():
    d=H/'standing_fire_overdraw01';need(not d.exists(),'새 폴더 필요');d.mkdir();s=H/'standing_fire_targets_probe01'
    a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());report=[]
    target={n:{b:np.array(Image.open(s/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in(85,86,87,90,91,92)}
    for refs in((85,86),(87,92),(90,91)):
        rows=[];valid=[]
        for combo in itertools.chain.from_iterable(itertools.combinations(PBS,k)for k in range(6)):
            for alpha in(False,True):
                imgs=[];keys=[]
                for b in PBS:
                    l,r=(target[n][b]for n in refs)
                    pieces=[(str(refs[0]),l),(str(refs[1]),r)]
                    if b in combo:
                        m=((l>0)&(r>0))if alpha else((l==r)&(l>0))
                        pieces=[('common',np.where(m,l,0)),(str(refs[0]),np.where(m,0,l)),(str(refs[1]),np.where(m&(l==r),0,r))]
                    for name,v in pieces:
                        if v.any():imgs.append(crop(v.astype('uint8')));keys.append((b,name))
                row={'refs':list(refs),'common_banks':list(combo),'alpha_common':alpha}
                try:
                    nr,rs=pack_many_patterns(bytes(4096),32,imgs,set(range(1,32)),[24]*len(imgs));pr=dict(zip(keys,rs));parts={n:{b:pr.get((b,'common'),[])+pr.get((b,str(n)),[])for b in PBS}for n in refs}
                    need(all(len(rr)<=24 for ll in parts.values()for rr in ll.values()),'24parts 초과')
                    for n in refs:
                        for b in PBS:need(np.array_equal(render(nr,parts[n][b]),target[n][b]),'후그리기 exact 실패')
                    row.update(passed=True,bytes=len(encode_stream(nr)),raw=nr.hex(),parts=parts);valid.append(row)
                except ValueError as ex:row.update(passed=False,error=str(ex))
                rows.append({k:v for k,v in row.items()if k not in('raw','parts')})
        best=sorted(valid,key=lambda r:(r['bytes'],sum(len(x)for ll in r['parts'].values()for x in ll.values())))[:5]
        for row in best:
            fit={}
            for b in PBS:
                cr={n:b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in row['parts'][n][b])or struct.pack('<BBbb',0,0,-8,-8)for n in refs}
                try:
                    try:_,slack=repack_parts(a.c,b,cr);mode='existing'
                    except ValueError:_,slack,mode=repack(a.c,b,cr)
                    fit[str(b)]={'fits':True,'slack':slack,'method':mode}
                except Exception as ex:fit[str(b)]={'fits':False,'error':str(ex)}
            row['part_fit']=fit
        write(d/('_'.join(map(str,refs))+'.json'),{'rows':rows,'best':best});summary={'refs':list(refs),'options':len(rows),'fits':len(valid),'best_bytes':best[0]['bytes']if best else None};report.append(summary);write(d/'report.json',{'groups':report,'art_changed':False,'arc_written':False,'scope':'공통본의 다른 색도 후그리기로 덮인 뒤 모든 원화층 exact인 경우만 조사. 최종부분/GPU 검사는 별도.'});print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
