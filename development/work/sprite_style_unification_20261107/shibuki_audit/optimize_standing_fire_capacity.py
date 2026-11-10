"""고정 원화/효과 타일의 순서만 바꾸는 압축 조사."""
from pathlib import Path
import sys,json,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,write,sha
from optimize_hurt_tile_storage import optimize

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='standing_fire_tileorder01');ap.add_argument('--steps',type=int,default=4);args=ap.parse_args()
    d=H/args.output;need(not d.exists(),'새 폴더 필요');d.mkdir();rows=[]
    jobs=[(H/'standing_fire_capacity03'/f'group_{n:03}_raw.bin',[7,8]if n==89 else [])for n in(85,86,87,89,90,91,92)]
    jobs += [(H/'standing_fire_shared01'/f'{name}_raw.bin',[])for name in('85_86','87_92')]
    for p,fixed in jobs:
        raw=p.read_bytes();nr,mp,r=optimize(raw,fixed,args.steps);name=p.stem
        (d/f'{name}.bin').write_bytes(nr);r.update(source_path=p.relative_to(ROOT).as_posix(),mapping={str(k):v for k,v in mp.items()})
        write(d/f'{name}.json',r);rows.append(r);write(d/'report.json',{'groups':rows,'arc_written':False,'scope':'모든 타일의 256개 원색인 보존 및 0/16·효과7/8 위치 고정. 실제 조립 재바인딩·전체 검증은 후속.'});print(json.dumps({'source':name,'before':r['before'],'after':r['after'],'saved':r['saved']}),flush=True)
if __name__=='__main__':main()
