"""새 사격 소매를 새 몸체 및 원래 권총/손 접점과 정합하는 미술 후보."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper
from review_all_bodies import source as body_source
def move(ar,dx,dy):
    out=np.zeros_like(ar);y,x=np.nonzero(ar);out[y+dy,x+dx]=ar[y,x];return out
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',choices=['a','b','c'],default='a');ap.add_argument('--out');args=ap.parse_args()
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/(args.out or f'firing_{args.page}_joint_probe_v1');need(not out.exists(),'Fresh output');out.mkdir();Y,X=np.indices((384,384));xx=X-160;yy=Y-160;rows=[];report=[]
    shifts={'a':{34:(-2,-1),36:(-3,0),38:(-1,0),40:(0,1)},'b':{42:(2,2),44:(4,0),46:(2,0),48:(1,0)},'c':{50:(-3,-3),52:(-3,0),54:(-2,1)}}[args.page]
    for n in shifts:
        ref=n-1;body=np.array(Image.open(body_source(ref)/f'base_{ref:03}.png'));source=np.array(Image.open(D/f'basic_firing_{args.page}_registered_v1'/f'base_{n:03}.png'))
        q=next(f for f in p['frames']if f['ref']==n);ex,ey=[int(np.floor(v))for v in q['eye']];oldgun=np.array(Image.open(D/'fire_constraints'/f'barrel_{n:03}.png'));gy,gx=np.nonzero(oldgun);mx=int(gx.min()-160)
        # The native gun's last skin column is the wrist anchor. Register the
        # newly drawn sleeve as a rigid module; never stretch it horizontally.
        skin=np.isin(source,[10,11,12,13])&(xx<ex-6)&(yy>=ey-6)&(yy<ey+12);sy,sx=np.nonzero(skin);wrist=int(sx.max()-160)
        arm_region=(xx>wrist)&(xx<=ex+6)&(yy>=ey+2)&(yy<=ey+11)
        if args.page=='c':arm_region=(xx>wrist)&(xx<=ex+6)&(yy>=ey-5)&(yy<=ey+11)
        head=(xx>=ex-2)&(yy<=ey+5);arm_region&=~head
        arm=np.where(arm_region,source,0).astype(np.uint8);dx,dy=shifts[n];arm=move(arm,dx,dy);arm[xx<=mx+7]=0;arm[head]=0
        if args.page=='b':arm[xx>ex+4]=0
        rest=body.copy();end=16 if args.page=='b' else 14;remove=(xx<=ex+1)&(yy>=ey+4)&(yy<ey+end)&~head;rest[remove]=0
        merged=np.where(arm,arm,rest).astype(np.uint8)
        # Protect the complete gun/hand window including transparent texels.
        miny,maxy=int(gy.min()),int(gy.max());window=(X>=gx.min())&(X<=gx.min()+7)&(Y>=miny)&(Y<=maxy)
        merged[window]=oldgun[window];need(np.array_equal(merged[window],oldgun[window]),'Gun window')
        comp,count=label(merged>0,np.ones((3,3)));contacts=int(np.count_nonzero(binary_dilation(arm>0,np.ones((3,3)))&(rest>0)))
        for name,idx in [('new_body',body),('source_firing',source),('new_sleeve',arm),('merged',merged)]:Image.fromarray(idx).save(out/f'{name}_{n:03}.png');a.rgba(idx).save(out/f'{name}_{n:03}_rgba.png')
        rows.append((f'air shot {n}',[('기존',a.composite(n)[0]),('새 비사격 몸',a.rgba(body)),('새 소매 원화 전체',a.rgba(source)),('새 몸/소매 + 원 총',a.rgba(merged))]))
        report.append({'ref':n,'body_ref':ref,'source_wrist_x':wrist,'rigid_shift':[dx,dy],'gun_window_exact':True,'new_sleeve_horizontal_stretch':False,'new_sleeve_body_contact_pixels':contacts,'alpha_components_8':count,'native_packed':False})
    helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':report,'scope':'4사격팔 원화 의미영역+원 총 접점의 정적 미술 후보. 몸체/총구 연결을 직접 검토하며 패킹 또는 전체완료를 뜻하지 않음.','runtime_verified':False});print(json.dumps(report))
if __name__=='__main__':main()
