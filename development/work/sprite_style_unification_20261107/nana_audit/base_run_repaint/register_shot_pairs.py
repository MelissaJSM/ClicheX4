"""새 몸체와 새로 그린 팔을 평행이동·손목 기준 강체 회전으로 등록한다."""
from pathlib import Path
import sys,json,math
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from register_cycle import body_register,PAGES,ORDER,TICKS
from register_page import crop_cell
from preview_restore import Archive,sha,digest,write,need,helper
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).parent

def translated(a,dx,dy):
    out=np.zeros_like(a);y,x=np.nonzero(a);xx=x+dx;yy=y+dy
    need(len(x)==0 or (xx.min()>=0 and xx.max()<384 and yy.min()>=0 and yy.max()<384),'Shift clipping')
    out[yy,xx]=a[y,x];return out

def main():
    out=D/'cycle_registered_v1';a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'))
    palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
    yy,xx=np.indices((384,384));xx=xx-160;yy=yy-160
    reports=[];result={};rawshot={}
    for page,(_,refs)in enumerate(PAGES,1):
        path=D/f'shot_page{page}_v2/generated.png';im=Image.open(path).convert('RGBA')
        for cell,n in enumerate(refs):
            p=next(q for q in plan['frames']if q['ref']==n);crop,box=crop_cell(im,cell)
            full,registration=body_register(crop,p,palette)
            ex,ey=p['eye_world_original_registration'];run=np.array(Image.open(out/f'run_{n:03}.png'))
            # Forward arm semantic window avoids eye/fringe, shoulder opening,
            # rear arm, waist, skirt, legs and trailing hair.
            arm_window=(xx<=ex+3)&(yy>=np.where(xx<ex-2,ey+1,ey+4))&(yy<=ey+11)
            arm=np.where(arm_window,full,0).astype(np.uint8)
            ys,xs=np.nonzero(arm);need(len(xs)>0,'Authored arm missing')
            mx=int(xs.min()-160);my=float(np.median(ys[xs==xs.min()])-160)
            desired=p['original_muzzle'];dx=int(desired[0]-mx);dy=round(desired[1]-my)
            need(-5<=dx<=10 and abs(dy)<=5,f'Redraw required rather than arm stretching {n}: {dx},{dy}')
            arm=translated(arm,dx,dy)
            # Keep the entire pistol/hand at its native muzzle, rotate the newly
            # authored sleeve around its wrist so shoulder height remains natural.
            # This is rigid registration, never a horizontal sleeve stretch.
            wrist=np.array([desired[0]+7,desired[1]+3],float)
            ay0,ax0=np.nonzero(arm);right=int(ax0.max()-160)
            proximal_y=float(np.median(ay0[ax0>=ax0.max()-1])-160)
            vector=np.array([right,proximal_y])-wrist
            destination=np.array([ex+3,ey+6],float)-wrist
            angle=math.atan2(destination[1],destination[0])-math.atan2(vector[1],vector[0])
            need(abs(angle)<math.radians(35),'Sleeve rotation too large')
            co,si=math.cos(angle),math.sin(angle)
            vx=xx-wrist[0];vy=yy-wrist[1]
            source_x=np.rint(co*vx+si*vy+wrist[0]+160).astype(int)
            source_y=np.rint(-si*vx+co*vy+wrist[1]+160).astype(int)
            valid=(source_x>=0)&(source_x<384)&(source_y>=0)&(source_y<384)&(xx>=wrist[0])
            rotated=np.zeros_like(arm);rotated[valid]=arm[source_y[valid],source_x[valid]]
            rotated[xx<wrist[0]]=arm[xx<wrist[0]];arm=rotated
            arm[xx>ex+3]=0
            # Preserve head even if the registered upper sleeve approaches it.
            arm[(xx>=ex-2)&(yy<ey+4)]=0
            remove=(xx<=ex+1)&(yy>=np.where(xx<ex-3,ey+1,ey+4))&(yy<ey+15)
            shoot=run.copy();shoot[remove]=0;shoot[arm>0]=arm[arm>0]
            common=(~remove)&(arm==0)
            need(np.array_equal(shoot[common],run[common]),'Common body changed')
            need(np.array_equal(shoot[yy>=ey+15],run[yy>=ey+15]),'Leg/skirt boundary changed')
            need(np.array_equal(shoot[(xx>=ex-2)&(yy<ey+4)],run[(xx>=ex-2)&(yy<ey+4)]),'Eye/head changed')
            ay,ax=np.nonzero(arm);newmx=int(ax.min()-160);newmy=float(np.median(ay[ax==ax.min()])-160)
            need(newmx==desired[0]and abs(newmy-desired[1])<=.5,'Muzzle registration failed')
            Image.fromarray(shoot).save(out/f'shoot_{n+1:03}.png');a.rgba(shoot).save(out/f'shoot_{n+1:03}_rgba.png')
            Image.fromarray(arm).save(out/f'arm_{n+1:03}.png');Image.fromarray(full).save(out/f'authored_shoot_{n+1:03}.png')
            result[n+1]=shoot;rawshot[n+1]=full
            reports.append({'run':n,'shoot':n+1,'source':str(path.relative_to(ROOT)),'source_sha256':digest(path),'crop':box,'source_registration':registration,'muzzle_before':[mx,my],'muzzle_target':desired,'arm_translation':[dx,dy],'sleeve_rigid_rotation_degrees':math.degrees(angle),'muzzle_after':[newmx,newmy],'arm_horizontal_stretch':False,'common_body_source':'new run drawing','old_art_pixels':0,'indexed_sha256':sha(shoot.tobytes()),'arm_sha256':sha(arm.tobytes())})
    for start in range(0,16,4):
        ids=sorted(result)[start:start+4]
        helper.grid([(f'ref {n}',[('정지 사격 기준',a.composite(85)[0]),('이전',a.composite(n)[0]),('새 run 공통몸체 + 새 사격팔',a.rgba(result[n]))])for n in ids],out/f'shot_comparison_{start//4+1}.png',6)
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);gif=[]
    for n in ORDER:
        board=Image.new('RGB',(768,350),'#adb9c1');draw=ImageDraw.Draw(board)
        for i,(title,pix)in enumerate([('새 달리기',np.array(Image.open(out/f'run_{n:03}.png'))),('새 이동 사격',result[n+1]),('기존 이동 사격',a.layer(n+1)[0])]):
            im=a.rgba(pix).crop((128,128,192,192)).resize((256,256),Image.Resampling.NEAREST);board.paste(im,(i*256,45),im);draw.text((i*256+6,12),title+f' / {n}',font=font,fill='black')
        gif.append(board)
    gif[0].save(out/'paired_timeline.gif',save_all=True,append_images=gif[1:],duration=[round(t*1000/60)for t in TICKS],loop=0,disposal=2)
    write(out/'pairs.json',{'parent_arc_sha256':sha(a.data),'frames':reports,'all_16_muzzles_registered':True,'runtime_verified':False,'shared_body_head_legs':True,'method':'새 사격 원화 전체등록 후 앞팔을 의미 범위로 분리, 가로늘림 없이 평행이동 및 손목 기준 강체 회전. 새 run 몸체와 합성.'})
    print(json.dumps({'pairs':len(reports),'muzzles':'all exact to within half pixel median','path':str(out)}))
if __name__=='__main__':main()
