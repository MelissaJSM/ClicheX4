"""새 나나 기본/포스 전체쌍의 의미 파츠 검토. 승인용 중간 결과만 생성."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from scipy.ndimage import binary_dilation,label
from PIL import Image
import numpy as np
D=Path(__file__).parent
def main():
    out=D/'fourth_layers_probe_v1';out.mkdir(exist_ok=True)
    a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'))
    yy,xx=np.indices((384,384));xx=xx-160;yy=yy-160;reports=[];fulls={}
    for n in range(1,33,2):
        p=next(q for q in plan['frames']if q['ref']==n);ex,ey=p['eye_world_original_registration'];hip=ey+18
        authored=np.array(Image.open(D/'fourth_geometry_probe_v1'/f'run_{n:03}.png'))
        front=(xx<=ex+1)&(yy>=np.where(xx<ex-3,ey+1,ey+4))&(yy<ey+15)
        for f in(n,n+1):
            base=np.array(Image.open(D/'cycle_registered_v1'/f'{"run"if f%2 else"shoot"}_{f:03}.png'))
            costume=authored.copy()
            if f%2==0:
                costume[front]=0
                arm=np.array(Image.open(D/'cycle_registered_v1'/f'arm_{f:03}.png'))
                costume[arm>0]=arm[arm>0]
            full=np.where(costume,costume,base).astype(np.uint8)
            # The arm was drawn afresh for the basic costume and remains the
            # same charcoal sleeve/pistol material in Fourth. No old sleeve is used.
            hand_seed=np.isin(full,(10,11,12,13))&(xx>=ex+5)&(yy>=ey+7)&(yy<ey+15)
            rear_hand=binary_dilation(hand_seed,iterations=2)&(yy>=ey+5)&(yy<hip)
            head=(yy<ey+4)&((xx>=ex-3)|(yy<ey))
            rear_split={13:12,27:17,31:12}.get(n,4)
            leg=(yy>=hip)|((xx>=ex+14)&(yy>=ey+rear_split))
            forearm=(xx<ex+3)&(yy>=ey)&(yy<hip)&~head
            armmask=(forearm|rear_hand)&~head
            owner=np.full((384,384),6,np.uint8);owner[leg]=8;owner[armmask]=7;owner[head]=5
            # Every changed opaque pixel has precisely one semantic owner.
            diff=(full!=base)&(full>0);layers={pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}
            merged=base.copy()
            for pb in(8,5,7,6):merged=np.where(layers[pb],layers[pb],merged)
            need(np.array_equal(merged,full),'Layer split differs')
            need(not np.any((base>0)&(full==0)),'Base uncovered')
            for pb,v in layers.items():Image.fromarray(v).save(out/f'layer{pb}_{f:03}.png')
            Image.fromarray(full).save(out/f'full_{f:03}.png');fulls[f]=full
            reports.append({'ref':f,'full_sha256':sha(full.tobytes()),'base_sha256':sha(base.tobytes()),'layers':{str(pb):sha(v.tobytes())for pb,v in layers.items()},'changed_by_owner':{str(pb):int(np.count_nonzero(v))for pb,v in layers.items()},'gun_from_new_shoot_source':f%2==0})
    for start in range(1,33,8):
        helper.grid([(f'ref {n}',[('포스 대기',a.composite(0,15)[0]),('새 포스 run',a.rgba(fulls[n],16)),('새 포스 사격',a.rgba(fulls[n+1],16))])for n in range(start,start+8,2)],out/f'comparison_{(start-1)//8+1}.png',6)
    write(out/'manifest.json',{'ready_to_apply':False,'frames':reports,'method':'검토용 새 원화+기본 공통부분. 기존 대기/아머배분에 맞춘 의미 파츠. 큰 뒤베일 leg8 유지. 실제 새 팔/총만 사격에 사용.','runtime_verified':False})
    print(json.dumps({'frames':len(reports),'out':str(out)}))
if __name__=='__main__':main()
