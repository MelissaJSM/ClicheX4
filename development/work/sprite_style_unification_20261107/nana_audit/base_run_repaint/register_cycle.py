"""새 원화 전체를 머리 크기·눈·발 기준으로 등록한다. 과거 도트 재덮기 없음."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from register_page import crop_cell,register
from preview_restore import Archive,sha,digest,write,need,helper
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).parent
PAGES=[('run_page1_v2',[1,7,15,25]),('run_page2_v1',[3,5,9,11]),('run_page3_v1',[13,17,19,21]),('run_page4_v1',[23,27,29,31])]
ORDER=[29,31,5,7,9,11,13,15,17,19,21,23,25,27]
TICKS=[2,2,2,3,2,2,3,2,2,2,3,2,2,3]

def body_register(crop,p,palette):
    a=np.array(crop);rgb=a[:,:,:3].astype(float);opaque=a[:,:,3]>=128
    green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&opaque
    green[crop.height//2:]=False
    ey,ex=np.nonzero(green);need(len(ex)>0,'Source eye missing')
    sy=float(np.median(ey));sx=float(np.median(ex))
    top=p['bbox_world'][1];bottom=p['bbox_world'][3]
    dx,dy=p['eye_world_original_registration'];split=round(sy+1)
    h1=dy-top+1;h2=bottom-dy-1
    # Head-to-eye height supplies scale without mistaking windblown hair for skull.
    # One global horizontal scale is applied to the whole newly drawn body.
    scale=h1/split
    width=round(crop.width*scale)
    head_width=None
    first=register(crop.crop((0,0,crop.width,split)),(width,h1),palette,'area_vote')
    second=register(crop.crop((0,split,crop.width,crop.height)),(width,h2),palette,'area_vote')
    # Only genuine source eye can introduce green; register()'s top-half restriction
    # is irrelevant for second crop: there are no green labels beneath the eye.
    native=np.concatenate((first,second))
    yy,xx=np.nonzero(native==14)
    if not len(xx):raise ValueError('Registered eye disappeared')
    eye_x=round(float(np.median(xx)))
    native[native==14]=12
    native[dy-top,eye_x]=14
    yy,xx=np.nonzero(native==14)
    x=dx-eye_x;y=top
    target=np.zeros((384,384),np.uint8)
    target[160+y:160+y+native.shape[0],160+x:160+x+width]=native
    fy,fx=np.nonzero(target)
    return target,{'source_eye':[sx,sy],'source_head_width':head_width,'horizontal_scale':scale,'native_width':width,'vertical_split':split,'native_split':[h1,h2],'position':[x,y],'eye_world':[float(np.median(xx)+x),float(np.median(yy)+y)],'foot_max_y':int(fy.max()-160),'bbox_world':[int(fx.min()-160),int(fy.min()-160),int(fx.max()+1-160),int(fy.max()+1-160)]}

def main():
    out=D/'cycle_registered_v1';out.mkdir(exist_ok=True)
    a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));need(sha(a.data)==plan['source_arc_sha256'],'Parent changed')
    palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
    rows=[];targets={};reports=[]
    for folder,refs in PAGES:
        im=Image.open(D/folder/'generated.png').convert('RGBA')
        for i,n in enumerate(refs):
            p=next(q for q in plan['frames']if q['ref']==n);crop,box=crop_cell(im,i);target,r=body_register(crop,p,palette)
            need(r['eye_world']==list(map(float,p['eye_world_original_registration'])),'Eye anchor drift')
            need(r['foot_max_y']==p['foot_max_y'],'Foot anchor drift')
            Image.fromarray(target).save(out/f'run_{n:03}.png');a.rgba(target).save(out/f'run_{n:03}_rgba.png');targets[n]=target
            reports.append({'ref':n,'source':str((D/folder/'generated.png').relative_to(ROOT)),'source_sha256':digest(D/folder/'generated.png'),'cell':i,'crop':box,**r,'indexed_sha256':sha(target.tobytes()),'old_art_pixels':0})
    for start in range(0,16,4):
        ids=sorted(targets)[start:start+4]
        rows=[(f'ref {n}',[('대기 기준',a.rgba(a.layer(0)[0])),('이전',a.rgba(a.layer(n)[0])),('새 원화 · 눈/발 정합',a.rgba(targets[n]))])for n in ids]
        helper.grid(rows,out/f'comparison_{start//4+1}.png',6)
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);gif=[]
    for n in ORDER:
        board=Image.new('RGB',(768,420),'#adb9c1');draw=ImageDraw.Draw(board)
        for i,(title,pixels)in enumerate([('대기',a.layer(0)[0]),('기존 달리기',a.layer(n)[0]),('새 달리기',targets[n])]):
            im=a.rgba(pixels).crop((128,128,192,192)).resize((256,256),Image.Resampling.NEAREST);board.paste(im,(i*256,50),im);draw.text((i*256+8,12),title+f' / {n}',font=font,fill='black')
        gif.append(board)
    gif[0].save(out/'run_timeline.gif',save_all=True,append_images=gif[1:],duration=[round(t*1000/60)for t in TICKS],loop=0,disposal=2)
    write(out/'registration.json',{'parent_arc_sha256':sha(a.data),'palette_sha256':sha(a.p),'scope':'새 나나 기본 달리기16참조, 원화 전체 사용. 기존 머리 꼭대기~눈 높이로 전체 가로배율을 결정하고 눈/발 앵커에 등록. 포스 합성/실기는 별도 미완료.','frames':reports,'animation_order':ORDER,'duration_ticks':TICKS,'runtime_verified':False})
    print(json.dumps({'frames':len(reports),'directory':str(out),'eye_and_foot_anchors_exact':True}))
if __name__=='__main__':main()
