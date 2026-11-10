"""고정된 사랑이 모듈을 새 Ultimate 손에 등록하는 비교 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
REFS=(100,101,102,103,104,231)
GX={100:-12,101:-9,102:-9,103:9,104:7,231:-9}
TOP={100:-19,101:-38,102:-32,103:-27,104:-35,231:-28}

def source(form,n):
    page='charge_registered_v3'if n in(100,101)else'air_registered_v1'if n in(103,104)else'recovery_registered_v1'
    return D/f'ultimate_{page}/{form}_{n:03}_registered_indices.png'

def main():
    out=D/'ultimate_weapon_probe_v1';out.mkdir(exist_ok=False)
    up=N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC'
    need(digest(up)=='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9','부모 보호')
    u=Archive(up.read_bytes());meta=json.loads((D/'canonical_weapon_probe_v2/manifest.json').read_text('utf8'))
    z=u.layer(85)[0]
    for x,y,v in meta['canonical_source_texels']:need(int(z[y+160,x+160])==v,'정본85 출처')
    rows=[];records=[]
    for n in REFS:
        panels=[]
        case=np.array(Image.open(D/f'canonical_weapon_probe_v2/base_{n:03}_case.png'))
        need(int((case>0).sum())==20,'정본20셀')
        for form in('before','after'):
            p=source(form,n);s=np.array(Image.open(p));gx,top=GX[n],TOP[n]
            handzone=(X>=gx-4)&(X<=gx+3)&(Y>=top+4)&(Y<=top+11)
            hand=handzone&np.isin(s,[10,11,12,13]);yy,xx=np.nonzero(hand)
            need(len(yy)>0,'신규 손 표본')
            hand_top=int(yy.min()-160)
            remove=(X>=gx-4)&(X<=gx+3)&(Y>=top-3)&(Y<=hand_top)&(s>0)&~hand
            target=s.copy();target[remove]=0
            visible=(case>0)&~hand;target[visible]=case[visible]
            need(np.array_equal(target[hand],s[hand]),'원화 손 보호')
            allowed=remove|(case>0)
            need(np.array_equal(target[~allowed],s[~allowed]),'몸체 보호')
            start=16 if form=='before'else 0
            Image.fromarray(target).save(out/f'{form}_{n:03}_indices.png')
            Image.fromarray(case).save(out/f'{form}_{n:03}_case.png')
            Image.fromarray(remove.astype(np.uint8)*255).save(out/f'{form}_{n:03}_removed_mask.png')
            Image.fromarray(hand.astype(np.uint8)*255).save(out/f'{form}_{n:03}_hand_mask.png')
            records.append({'ref':n,'form':form,'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),
                'canonical_source85_texels':20,'case_bbox':list((GX[n],TOP[n])),'case_sha256':sha(case.tobytes()),
                'hand_top':hand_top,'hand_preserved':int(hand.sum()),'case_visible':int(visible.sum()),
                'removed':[(int(x-160),int(y-160),int(s[y,x]))for y,x in np.argwhere(remove)],
                'components_8':int(label(target>0,np.ones((3,3)))[1]),'target_sha256':sha(target.tobytes())})
            panels.extend([('new '+form,u.rgba(s,start)),('8px case '+form,u.rgba(target,start))])
        rows.append((f'Ultimate Rising {n}',panels))
    for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
    write(out/'manifest.json',{'parent_sha256':digest(up),'case_metadata':(D/'canonical_weapon_probe_v2/manifest.json').relative_to(ROOT).as_posix(),
        'case_metadata_sha256':digest(D/'canonical_weapon_probe_v2/manifest.json'),'frames':records,
        'method':'수용85의20셀을 기본/포스동결과 동일하게90도회전한8px 정본을 신규 손가림 아래에 배치. 신규 팔/머리/다리는 모듈영역 밖 exact.',
        'body_commonization_pending':True,'native_packed':False,'runtime_verified':False})
    print(json.dumps([{k:r[k]for k in('ref','form','hand_top','case_visible','components_8')}for r in records]))

if __name__=='__main__':main()
