"""새 대시 소매의 강체 정합 및 원 권총 창 합성 진단."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper
from prepare_next_guides import body_path
def move(ar,dx,dy):
    out=np.zeros_like(ar);y,x=np.nonzero(ar);out[y+dy,x+dx]=ar[y,x];return out
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent');out=D/'firing_b_joint_probe_v2';need(not out.exists(),'Fresh output');out.mkdir();Y,X=np.indices((384,384));x=X-160;y=Y-160;rows=[];proof=[]
    shifts={78:(-8,-3),80:(-4,-2),82:(-6,2),84:(-6,2)}
    for n,(dx,dy)in shifts.items():
        b=np.array(Image.open(body_path(n-1)));s=np.array(Image.open(D/'basic_firing_b_registered_v1'/f'base_{n:03}.png'));gun=np.array(Image.open(D/'fire_constraints'/f'barrel_{n:03}.png'));q=next(q for q in plan['frames']if q['ref']==n);ex,ey=map(lambda v:int(np.floor(v)),q['eye']);gy,gx=np.nonzero(gun);mx=int(gx.min()-160)
        skin=np.isin(s,[10,11,12,13])&(x<ex-8)&(y>=ey-4)&(y<ey+11);sy,sx=np.nonzero(skin);wrist=int(sx.max()-160)
        source_head=(x>=ex-2)&((y<=ey+2)|((y<=ey+5)&np.isin(s,[5,6,7,8,9,10,11,12,13,14])));region=(x>wrist)&(x<=ex+8)&(y>=ey-2)&(y<=ey+10)&~source_head
        region&=(np.isin(s,[1,2,3,4])|((s==5)&(x<=wrist+4)))
        selected=np.where(region,s,0).astype(np.uint8);labs,count=label(selected>0,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;chosen=int(sizes.argmax());excluded_head_fragments=int(np.count_nonzero(selected[labs!=chosen]));selected[labs!=chosen]=0
        arm=move(selected,dx,dy);head=(x>=ex-2)&((y<=ey+2)|((y<=ey+5)&np.isin(b,[5,6,7,8,9,10,11,12,13,14])));arm[head]=0;arm[x<=mx+7]=0
        rest=b.copy();remove=(x<=ex+2)&(y>=ey+3)&(y<ey+15)&~head;rest[remove]=0;merged=np.where(arm,arm,rest).astype(np.uint8)
        window=(X>=gx.min())&(X<=gx.min()+7)&(Y>=gy.min())&(Y<=gy.max());merged[window]=gun[window];need(np.array_equal(merged[window],gun[window]),'Gun exact')
        for name,ar in [('new_body',b),('source_firing',s),('new_sleeve',arm),('rest_body',rest),('merged',merged)]:Image.fromarray(ar).save(out/f'{name}_{n:03}.png');a.rgba(ar).save(out/f'{name}_{n:03}_rgba.png')
        count=int(label(merged>0,np.ones((3,3)))[1]);contacts=int(np.count_nonzero(binary_dilation(arm>0,np.ones((3,3)))&(rest>0)));proof.append({'ref':n,'source_wrist_x':wrist,'rigid_shift':[dx,dy],'gun_window_exact':True,'components_8':count,'arm_body_contacts':contacts,'excluded_separate_source_head_texels':excluded_head_fragments,'arm_stretch':False,'candidate_only':True});rows.append((f'dash fire{n}',[('원래',a.composite(n)[0]),('새 몸체',a.rgba(b)),('새 사격 원화',a.rgba(s)),('새 팔 강체 정합',a.rgba(merged))]))
    helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':proof,'native_packed':False,'runtime_verified':False,'scope':'연결·팔 길이 검토 후보. 컴포넌트 연결 수치만으로 자연스러운 어깨를 보장하지 않음.'});print(json.dumps(proof))
if __name__=='__main__':main()
