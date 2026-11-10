"""나나 일반/사격 두 자세의 원래 파츠 수·타일 수 안에서 공동 배치를 구한다."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.solve_paired_cover import paired_cover
from scripts.prepare_nana_idle_shot import INV,write
from scripts.solve_sprite_cover import cover

def main():
    p=argparse.ArgumentParser();p.add_argument('--pairs',type=Path,required=True);p.add_argument('--timeout',type=float,default=12);p.add_argument('--frames',type=int,nargs='*');p.add_argument('--scope',choices=('run','air','dash','wall','fall_legs'),default='run');args=p.parse_args();d=args.pairs
    if not d.resolve().is_relative_to(ROOT/'work/ver_rin_nana/nana_art'):raise ValueError('Isolated Nana path required')
    inv=json.loads(INV.read_text('utf8'));plan=json.loads((ROOT/f'work/ver_rin_nana/nana_art/{args.scope}_v1/plan.json').read_text('utf8'));pairs=json.loads((d/'pairs.json').read_text('utf8'));old=json.loads((d/'layout.json').read_text('utf8')) if (d/'layout.json').exists() else [];rows=[]
    for p in pairs['frames']:
        n=p['run'];prior=next((q for q in old if q['frame']==n),None)
        if args.frames and n not in args.frames:
            if prior:rows.append(prior)
            continue
        a=np.array(Image.open(d/f'run_{n:03d}.png'));b=np.array(Image.open(d/f'shoot_{n:03d}.png'));q=next(q for q in plan['paired_frames'] if q['frames'][0]==n)
        nr=len(inv['base_frames'][n]['composition']['parts']);ns=len(inv['base_frames'][n+1]['composition']['parts']);slots=len(set(q['common_base_tiles']+q['nonshoot_only_tiles']+q['shoot_only_tiles']))
        r={'fits':False}
        plain=cover(a!=0,nr,args.timeout)
        if plain['fits']:
            for c in range(min(nr-1,ns-1,slots-2),max(0,nr+ns-slots-1),-1):
                for ur in range(1,nr-c+1):
                    us=min(ns-c,slots-c-ur)
                    if us<1:continue
                    # With no spare blank tile, both record counts must be exact.
                    if c+ur+us==slots and (c+ur<nr or c+us<ns):continue
                    r=paired_cover(a,b,[c,ur,us],timeout=args.timeout)
                    if r['fits']:break
                if r['fits']:break
        r.update(frame=n,mode='variant',native_parts=[nr,ns],native_slots=slots,body_fits=plain['fits']);rows.append(r);write(d/'layout.json',rows+[q for q in old if q['frame'] not in {r['frame'] for r in rows}]);print(json.dumps(r),flush=True)
    write(d/'layout.json',rows)
if __name__=='__main__':main()
