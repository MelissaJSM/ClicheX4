"""새 Ultimate 전후7을 원 bank0/5의 불투명 덮기 구조로 준비한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
REFS=(100,101,102,103,104,231,232);PBS=(0,5,6,7,8)
PARENT=N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC'
BEFORE='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',choices=['v1','v2'],default='v2');args=ap.parse_args()
    need(digest(PARENT)==BEFORE,'부모 보호');u=Archive(PARENT.read_bytes());out=D/f'ultimate_layers_probe_{args.version}';out.mkdir(exist_ok=False)
    rows=[];records=[]
    for n in REFS:
        source=D/('ultimate_ground_feet_probe_v1'if n in(231,232)else('ultimate_costume_pair_probe_v6'if args.version=='v2'else'ultimate_costume_pair_probe_v5'))
        bp=source/f'before_{n:03}.png';ap=source/f'after_{n:03}.png'
        before=np.array(Image.open(bp));after=np.array(Image.open(ap))
        need(not np.any((after>0)&(before==0)),'투명오버레이로 삭제불가')
        overlay=np.where((before!=after)|(before==15),before,0).astype(np.uint8)
        layers={0:after,5:overlay,6:np.zeros_like(after),7:np.zeros_like(after),8:np.zeros_like(after)}
        actual=u.rgba(after);actual.alpha_composite(u.rgba(overlay,16));need(actual.tobytes()==u.rgba(before,16).tobytes(),'전폼 합성 일치')
        for pb,z in layers.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
        Image.fromarray(before).save(out/f'before_{n:03}.png');Image.fromarray(after).save(out/f'after_{n:03}.png')
        records.append({'ref':n,'before_source':bp.relative_to(ROOT).as_posix(),'before_source_sha256':digest(bp),
            'after_source':ap.relative_to(ROOT).as_posix(),'after_source_sha256':digest(ap),
            'base_sha256':sha(after.tobytes()),'layers':{str(pb):sha(z.tobytes())for pb,z in layers.items()if pb},
            'before_native_sha256':sha(before.tobytes()),'after_native_sha256':sha(after.tobytes()),
            'before_full_RGBA_exact':True,'after_alpha_subset_before':True,'overlay_pixels':int((overlay>0).sum())})
        if n!=232:rows.append((f'Rising {n}',[('before idle',u.composite(0,15)[0]),('new before layers',actual),('after idle',u.composite(0,0)[0]),('new after bank0',u.rgba(after))]))
    for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
    write(out/'manifest.json',{'source_arc_sha256':BEFORE,'frames':records,'policy':'실제 Ultimate 표시 미획득 mask15/획득후 mask0. after bank0와 before차분 bank5, 6/7/8 빈층. 7참조만 대상.',
        'art_review_pending':True,'native_packed':False,'runtime_verified':False})
    print(json.dumps({'refs':7,'layers':35,'overlay_sizes':[r['overlay_pixels']for r in records]}))

if __name__=='__main__':main()
