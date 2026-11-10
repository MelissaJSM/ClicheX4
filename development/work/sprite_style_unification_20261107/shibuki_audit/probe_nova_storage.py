"""노바 새4참조만 타일 순서를 바꿔 고정은행 수납량을 조사한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from pack_nova_base import *
from probe_chaser_storage import optimize
def main():
    d=H/'nova_storage01';need(not d.exists(),'새 조사');d.mkdir();a=Archive(P.read_bytes());validate(a.data);raws={};counts={};rr={b:{}for b in PBS};groups=[]
    for ns in GROUPS:
        n=ns[0];nr,pp=pack_planes(bytes(4096),32,[crop(np.array(Image.open(TD/f'{n:03}_bank{b}_indices.png')))for b in PBS],set(range(1,32))-{16},[24]*5)
        count=max(t for ps in pp for t,x,y,fl in ps)+1;nr=resize_tile_storage(nr,32,count);source=nr
        fixed=set(range(0,count,16))|{t for t,x,y,fl in pp[1]}|{t for ps in pp for t,x,y,fl in ps if fl&128}
        nr,mp,opt=optimize(nr,count,sorted(fixed),steps=8);pp=[[(mp[t],x,y,fl)for t,x,y,fl in ps]for ps in pp]
        for ref in ns:
            raws[ref]=nr;counts[ref]=count;(d/f'{ref:03}.raw').write_bytes(nr)
            for b,ps in zip(PBS,pp):rr[b][ref]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in ps)or struct.pack('<BBbb',0,0,-8,-8)
        groups.append({'refs':list(ns),'count':count,'source_raw_sha256':sha(source),'raw_sha256':sha(nr),'mapping':mp,'optimization':opt});print(json.dumps(groups[-1]),flush=True)
    nc=a.c;slacks={};methods={}
    for b,rs in rr.items():
        try:nc,slacks[b]=repack_parts(nc,b,rs);methods[b]='existing'
        except ValueError:nc,slacks[b],methods[b]=repack_global(nc,b,rs)
    try:ng,gfx=repack_fixed_global(a,raws,counts)
    except ValueError as ex:gfx={'error':str(ex)}
    write(d/'recipe.json',{'parent_sha256':PARENT,'manifest_sha256':MANIFEST,'groups':groups,'parts':{str(b):{str(n):v.hex()for n,v in rs.items()}for b,rs in rr.items()},'parts_slack':slacks,'parts_methods':methods,'graphics':gfx,'arc_written':False,'no_pixels_deleted':True});print(json.dumps({'parts_slack':slacks,'graphics':gfx}))
if __name__=='__main__':main()
