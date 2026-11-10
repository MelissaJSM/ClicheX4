"""138/139 새 팔 donor의 불변 머리를 기준으로 국소 등록좌표를 조사한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from inspect_ultimate_hurt_common import shift
from scripts.export_x_consistency import Archive

def grid(ims,path,labels):
    out=Image.new('RGB',(620*len(ims),720),(30,36,47));d=ImageDraw.Draw(out)
    for k,(im,name)in enumerate(zip(ims,labels)):
        x=620*k+48;y=42;cut=im.crop((136,124,188,188)).resize((520,640),Image.Resampling.NEAREST);out.paste(cut,(x,y),cut);d.text((x,y-25),name,fill='white')
        for n in range(-24,29,4):
            xx=x+(n+24)*10;d.line((xx,y,xx,y+640),fill=(65,72,82));d.text((xx,y-12),str(n),fill='white')
        for n in range(-36,29,4):
            yy=y+(n+36)*10;d.line((x,yy,x+520,yy),fill=(65,72,82));d.text((x-24,yy),str(n),fill='white')
    out.save(path)

def main():
    out=H/'ultimate_arrival_overhead_arm_inspection01';need(not out.exists(),'Fresh inspection');out.mkdir();a=Archive((H/'prepared_ultimate_hurt02/PL02_U.ARC').read_bytes());rows=[];yy,xx=np.indices((384,384));xx-=160;yy-=160
    for n,oldfolder in((138,'ultimate_arrival_native02'),(139,'ultimate_arrival_separate_native01')):
        old=np.array(Image.open(H/oldfolder/f'after_{n:03}_indices.png'));donor=np.array(Image.open(H/f'ultimate_arrival_overhead_arms_native01/after_{n:03}_indices.png'))
        # The face and left hair below the clasp are outside the edited sleeve.
        head=(xx>=-13)&(xx<=-3)&(yy>=-22)&(yy<=-7);search=[]
        for dy in range(-2,3):
            for dx in range(-2,3):
                w=shift(donor,dx,dy);search.append({'dx':dx,'dy':dy,'head_mismatches':int(((old!=w)&head).sum())})
        search.sort(key=lambda r:(r['head_mismatches'],abs(r['dx'])+abs(r['dy'])));best=search[0];w=shift(donor,best['dx'],best['dy']);Image.fromarray(w).save(out/f'after_{n:03}_donor_indices.png');a.rgba(w).save(out/f'after_{n:03}_donor.png')
        before=Image.open(H/oldfolder/f'before_{n:03}.png').convert('RGBA');grid([before,a.rgba(old),a.rgba(w)],out/f'{n:03}_grid.png',[f'{n} original new jacket',f'{n} rejected swimsuit sleeve',f'{n} local bare-arm donor (not full replacement)'])
        rows.append({'ref':n,'original_new_folder':oldfolder,'head_roi_world':[-13,-22,-3,-7],'best':best,'top5':search[:5],'donor_sha256':sha(donor.tobytes()),'aligned_sha256':sha(w.tobytes())})
    write(out/'report.json',{'rows':rows,'wholebody_replacement':False,'arc_changed':False,'arm_semantic_mask_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
