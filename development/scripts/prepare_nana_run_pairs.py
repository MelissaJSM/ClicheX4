"""나나 이동 몸체에 수용 사격 팔을 원작 총구 기준으로 등록한다."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.prepare_nana_idle_shot import INV,write,shifted
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.normalize_nana_run import quantize

def main():
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();d=args.art;out=args.output
    if not d.resolve().is_relative_to(ROOT/'work/ver_rin_nana/nana_art') or not out.resolve().is_relative_to(ROOT/'work/ver_rin_nana/nana_art') or out.exists():raise ValueError('Fresh isolated Nana output required')
    art=json.loads((d/'art.json').read_text('utf8'));inv=json.loads(INV.read_text('utf8'));words=art['palette_words'];out.mkdir(parents=True)
    source=ROOT/'work/ver_rin_nana/nana_art/run_v1/firing_generated.png';pic=Image.open(source).convert('RGBA');pic=pic.crop((0,0,pic.width//8,pic.height//2));ar=np.array(pic);sy,sx=np.nonzero(ar[:,:,3]>=192);pic=pic.crop((int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)))
    colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32);s=quantize(pic,(round(pic.width*45/pic.height*.9),45),colors)
    eyes=(s==14);eyes[22:]=False;ey0,ex0=map(lambda v:int(round(np.median(v))),np.nonzero(eyes));yy0,xx0=np.indices(s.shape)
    arm=np.where((xx0<=ex0+2)&(yy0>=ey0+1)&(yy0<ey0+9),s,0).astype(np.uint8);ys,xs=np.nonzero(arm);left=int(xs.min());top=int(ys.min());bottom=int(ys.max()+1);right=int(xs.max()+1);arm=arm[top:bottom,left:right]
    ax=np.indices(arm.shape)[1];arm[(ax>=6)&~np.isin(arm,[1,2,3,4])]=0;yy,xx=np.indices((80,96))
    def muzzle(n):
        original=np.array(Image.open(INV.parent/f'base_{n:03d}.png'));b=inv['base_frames'][n]['bounds'];mask=original!=0;mask[:5]=False;mask[28:]=False;y,x=np.nonzero(mask);left=int(x.min());ys=np.nonzero(mask[:,left])[0];return [left+b[0],float(np.median(ys))+b[1]]
    records=[];sheet=Image.new('RGB',(8*240,4*242),'#222630');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14)
    for i,r in enumerate(art['frames']):
        n=r['frame'];a=np.array(Image.open(d/r['image']));mx,my=muzzle(n+1);ex,ey=r['eye'];gx,gy=round(mx)+48,round(my)+40-1;end=ex+4;gun=np.zeros_like(a)
        # Register the authored sleeve between muzzle and shoulder. The first six
        # columns (handgun/hand) retain native size; only sleeve length is fitted.
        sleeve=np.array(Image.fromarray(arm[:,6:]).resize((end-gx-6,arm.shape[0]),Image.Resampling.NEAREST));registered=np.concatenate((arm[:,:6],sleeve),axis=1);gun[gy:gy+registered.shape[0],gx:end]=registered
        # Keep head, hair, torso center, skirt and all legs exactly common. Replace
        # only the forward arm window; authored run pistol cannot persist below it.
        ex,ey=r['eye'];mask=(xx<ex+1)&(yy>=np.where(xx<ex-3,ey+2,ey+5))&(yy<ey+15)
        gun[(xx>=ex-3)&(yy<ey+4)]=0
        b=a.copy();b[mask]=0;b[gun!=0]=gun[gun!=0]
        if np.any(b[yy>=ey+15]!=a[yy>=ey+15]):raise ValueError('Shooting arm overlaps lower body')
        for name,v in [('run',a),('shoot',b),('common',np.where(a==b,a,0).astype(np.uint8)),('shoot_body',np.where(a!=b,b,0).astype(np.uint8)),('gun',gun)]:save_image(v.tobytes(),(96,80),words,out/f'{name}_{n:03d}.png')
        records.append({'run':n,'shoot':n+1,'common_rects':[],'run_arm_rect':[0,0],'gun_rect':[0,0],'original_muzzle':[mx,my],'registered_arm_bounds':[gx,gy,end,gy+arm.shape[0]],'body_shared_except_forward_arm':True})
        for j,name in enumerate(('run','shoot')):
            pic=Image.open(out/f'{name}_{n:03d}.png').convert('RGBA').crop((16,12,76,65)).resize((240,212),Image.Resampling.NEAREST);x,y=i%8*240,(i//8*2+j)*242;sheet.paste(pic,(x,y+24),pic);draw.text((x+5,y+3),f'{name} {n+j:03d}',font=font,fill='white')
    sheet.save(out/'paired_4x.png');write(out/'pairs.json',{'task':'x_nana','frames':records,'palette_words':words,'body_art':d.as_posix(),'body_manifest_sha256':digest(d/'art.json'),'arm_source':source.relative_to(ROOT).as_posix(),'arm_source_sha256':digest(source),'runtime_verified':False});print(out)
if __name__=='__main__':main()
