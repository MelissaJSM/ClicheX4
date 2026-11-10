"""231의 새 신발 모듈을 원 접지 행에 1px 강체 정합한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,need,write,helper
Y,X=np.indices((384,384));Y-=160;X-=160

def main():
    out=D/'ultimate_ground_feet_probe_v1';out.mkdir(exist_ok=False)
    u=Archive((N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC').read_bytes())
    records=[];rows=[]
    for form in('before','after'):
        p=D/f'ultimate_costume_pair_probe_v4/{form}_231.png';s=np.array(Image.open(p));t=s.copy();allow=np.zeros_like(s,dtype=bool);maps=[]
        for x0,x1 in[(-18,-9),(7,15)]:
            # 새 원화 발목의 연결 행19는 몸에 남긴다. 같은 원화의 신발과
            # 아래 발목 모듈19..21 전체를 +1y 평행이동해20..22에 등록한다.
            clear=(X>=x0)&(X<x1)&(Y>=20)&(Y<=23);t[clear]=0;allow|=clear
            for sy in range(19,22):
                for sx in range(x0,x1):
                    t[sy+161,sx+160]=s[sy+160,sx+160]
                    maps.append([sx,sy,sx,sy+1,int(s[sy+160,sx+160])])
        need(np.array_equal(t[~allow],s[~allow]),'발 모듈 밖 보호')
        need(int(label(t>0,np.ones((3,3)))[1])==1,'발목 단절')
        yy,xx=np.nonzero(t);need(int(yy.max())-160==22,'원 접지22')
        Image.fromarray(t).save(out/f'{form}_231.png');Image.fromarray(t).save(out/f'{form}_232.png')
        records.append({'form':form,'refs':[231,232],'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),
            'source_to_target':maps,'translation':[0,1],'upper_ankle_row19_retained_from_same_new_source':True,
            'new_floor':22,'old_candidate_floor':21,'body_gun_and_upper_legs_unchanged':True,
            'shoe_pixels_resized':False,'plain_color_fill':False,'native_sha256':sha(t.tobytes())})
        mask=15 if form=='before'else 0;off=16 if mask else 0
        rows.append((f'grounded {form}',[('idle / ground22',u.composite(0,mask)[0]),('old 231 / ground22',u.composite(231,mask)[0]),('new / ground21',u.rgba(s,off)),('new foot module / ground22',u.rgba(t,off))]))
    helper.grid(rows,out/'comparison.png',7)
    write(out/'registration.json',{'frames':records,'scope':'새 신발 모듈의 위치만1px 아래로 맞추고 상부 발목 경계행은 동일 새원화에서 유지한 연결 비교. 전체 다리/몸 축척·단색채움 없음. 최종 미술 검토 전 후보.','native_packed':False,'runtime_verified':False})
    print(json.dumps({'refs':[231,232],'forms':2,'floor':22,'connected':True}))

if __name__=='__main__':main()
