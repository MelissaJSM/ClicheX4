"""새 서서 사격의 정확한 픽셀 공유만 시험한다. ARC·원화는 쓰지 않는다."""
from pathlib import Path
import sys,json,itertools,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop,lossless_pack
from probe_standing_fire_capacity import render,PBS
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import repack_parts
from repack_part_records_lossless import repack
from src.psx_compress import encode_stream

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='standing_fire_shared01');args=ap.parse_args()
    d=H/args.output;need(not d.exists(),'새 조사 폴더 필요');d.mkdir()
    s=H/'standing_fire_targets_probe01';refs=(85,86,87,90,91,92)
    targets={n:{b:np.array(Image.open(s/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in refs}
    old=json.loads((H/'standing_fire_capacity03/report.json').read_text('utf8'))
    sizes={q['refs'][-1]:q['compressed_bytes']for q in old['groups']}
    arc=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes())
    groups=list(itertools.combinations(refs,2))+[(85,86,87),(85,87,92),(86,87,92),(85,86,87,92)]
    rows=[]
    for ns in groups:
        row={'refs':list(ns),'separate_bytes':sum(sizes[n]for n in ns)}
        try:
            imgs=[crop(targets[n][b])for n in ns for b in PBS]
            raw,rr,method=lossless_pack(imgs)
            for i,im in enumerate(imgs):need(np.array_equal(render(raw,rr[i])[80:240,80:240],im),'표시 불일치')
            name='_'.join(map(str,ns));(d/f'{name}_raw.bin').write_bytes(raw)
            write(d/f'{name}_records.json',{'refs':list(ns),'pbs':list(PBS),'records':rr})
            changes={b:{}for b in PBS}
            for i,n in enumerate(ns):
                for j,b in enumerate(PBS):changes[b][n]=b''.join(struct.pack('<BBbb',f,t,x-80,y-80)for t,x,y,f in rr[i*5+j])or struct.pack('<BBbb',0,0,-8,-8)
            # 그룹 자체가 부모보다 요구하는 기록 공간. 최종 전체 교체는 별도.
            part={}
            for b,cr in changes.items():
                try:
                    try:_,slack=repack_parts(arc.c,b,cr);mode='existing'
                    except ValueError:_,slack,mode=repack(arc.c,b,cr)
                    part[str(b)]={'fits':True,'slack':slack,'method':mode}
                except Exception as ex:part[str(b)]={'fits':False,'error':str(ex)}
            size=len(encode_stream(raw));row.update(packed=True,method=method,compressed_bytes=size,saved_bytes=row['separate_bytes']-size,raw_sha256=sha(raw),parts=part,part_counts=[len(r)for r in rr],planes_exact=len(imgs))
        except ValueError as ex:row.update(packed=False,error=str(ex))
        rows.append(row);write(d/'report.json',{'parent_sha256':sha(arc.data),'target_manifest_sha256':sha((s/'manifest.json').read_bytes()),'groups':rows,'arc_written':False,'art_changed':False,'scope':'동일 원화 모든 층을 정확히 유지하는 공동 32타일 atlas 용량 조사. 최종 ARC/부분조합/GPU 검증은 별도.'})
        print(json.dumps(row),flush=True)
if __name__=='__main__':main()
