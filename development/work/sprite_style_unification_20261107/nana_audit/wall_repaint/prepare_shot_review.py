"""Measure actual muzzle reach of newly authored wall sleeves without stretching."""
from pathlib import Path
import sys,json,argparse,math
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from PIL import Image,ImageDraw
import numpy as np
from scipy.ndimage import binary_dilation,label

def translate(m,dx,dy):
    out=np.zeros_like(m);y,x=np.nonzero(m);need(np.all((x+dx>=0)&(x+dx<384)&(y+dy>=0)&(y+dy<384)),'Clipping');out[y+dy,x+dx]=m[y,x];return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',type=int,choices=[1,2,3,4],default=1);args=ap.parse_args()
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['source_arc']).read_bytes());need(sha(a.data)==plan['source_sha256'],'Parent')
    out=D/f'shot_reach_review_v{args.version}';out.mkdir(exist_ok=True);rows=[];report=[];Y,X=np.indices((384,384));xx=X-160;yy=Y-160
    for n in range(55,67,2):
        f=n+1;p=next(q for q in plan['frames']if q['ref']==n);ex,ey=map(int,p['eye_world']);bd=D/('basic_remaining_contacts_v1'if n in(59,63)else'basic_contacts_probe_v3');body=np.array(Image.open(bd/f'base_{n:03}.png'))
        sd=D/(('basic_remaining_registered_v1'if f in(64,66)else'basic_firing_registered_v1')if args.version==1 else('basic_remaining_reach_registered_v2'if f in(64,66)else'basic_firing_reach_registered_v2'));source=np.array(Image.open(sd/f'base_{f:03}.png'))
        window=(xx<=ex+4)&(yy>=np.where(xx<ex-2,ey+1,ey+4))&(yy<=ey+12)
        arm=np.where(window,source,0).astype(np.uint8)
        if args.version>=2:
            lab,cnt=label(arm>0,np.ones((3,3)));ay,ax=np.nonzero(arm);seed_x=int(ax.min());seed_y=int(ay[np.where(ax==seed_x)[0][0]]);chosen=int(lab[seed_y,seed_x]);arm[lab!=chosen]=0
        old=a.layer(f)[0];ys,xs=np.nonzero(old);mx=int(xs.min()-160);my=float(np.median(ys[xs==xs.min()])-160)
        ay,ax=np.nonzero(arm);smx=int(ax.min()-160);smy=float(np.median(ay[ax==ax.min()])-160);dx,dy=mx-smx,round(my-smy)
        if args.version>=3:
            # The source 60 has a high folded knee; the broad first diagnostic
            # window accidentally captured it through torso-connected pixels.
            # Arm-only module stops below its wrist, excluding that whole leg.
            arm[yy>int(np.floor(smy+5))]=0
        relocated=translate(arm,dx,dy)
        if args.version==4 and f==62:
            angle=math.radians(8);wx,wy=mx+8,my+3;co,si=math.cos(angle),math.sin(angle);vx,vy=xx-wx,yy-wy
            rx=np.rint(co*vx+si*vy+wx+160).astype(int);ry=np.rint(-si*vx+co*vy+wy+160).astype(int);valid=(rx>=0)&(rx<384)&(ry>=0)&(ry<384)&(xx>=wx)
            rotation=np.zeros_like(relocated);rotation[valid]=relocated[ry[valid],rx[valid]];rotation[xx<wx]=relocated[xx<wx];relocated=rotation
        remove=(xx<=ex+1)&(yy>=np.where(xx<ex-3,ey+1,ey+4))&(yy<ey+15)
        rest=body.copy();rest[remove]=0
        if args.version>=3:
            if f==62:relocated[xx>ex+5]=0
            head_guard=(yy<=ey+4)&(xx>=ex-2)
            relocated[head_guard]=0;rest[head_guard]=body[head_guard]
        merged=np.where(relocated,relocated,rest).astype(np.uint8)
        connected=binary_dilation(relocated>0,structure=np.ones((3,3)))&(rest>0);prox=np.nonzero(connected)
        nlab,count=label(merged>0,np.ones((3,3)));arm_components=set(int(v)for v in nlab[relocated>0]if v);eye_component=int(nlab[ey+160,ex+160]);joins_head_body=eye_component in arm_components
        record={'ref':f,'body_ref':n,'body_source':str(bd.relative_to(ROOT)),'source':str(sd.relative_to(ROOT)),'old_muzzle':[mx,my],'new_muzzle_before':[smx,smy],'rigid_translation':[dx,dy],'arm_horizontal_stretch':False,'arm_matches_body_component':joins_head_body,'touching_new_body_pixels':len(prox[0]),'post_translation_arm_right':int(np.where(relocated>0)[1].max()-160),'nominal_shoulder_x':ex+4,'not_final':True}
        for label_name,m in [('body',body),('source',source),('arm_only',arm),('translated_arm',relocated),('merged_probe',merged)]:Image.fromarray(m).save(out/f'{label_name}_{f:03}.png')
        display=a.rgba(merged);draw=ImageDraw.Draw(display);draw.rectangle((160+mx-1,160+int(my)-2,160+mx+1,160+int(my)+2),outline=(255,0,0,255))
        rows.append((f'fire {f} / shift {dx},{dy}',[('기존 발사점',a.composite(f)[0]),('새 원화 전체',a.rgba(source)),('새 몸 + 새 팔 / 검사 후보',display)]));report.append(record)
    helper.grid(rows[:3],out/'comparison_1.png',6);helper.grid(rows[3:],out/'comparison_2.png',6)
    write(out/'reach.json',{'scope':'Source-art reach diagnosis only. A connected mask is not proof of natural shoulder/elbow anatomy. None of these probes are packed.','source_arc_sha256':sha(a.data),'frames':report,'native_packed':False,'runtime_verified':False})
    print(json.dumps(report))
if __name__=='__main__':main()
