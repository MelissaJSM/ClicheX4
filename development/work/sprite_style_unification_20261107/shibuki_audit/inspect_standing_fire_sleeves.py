"""소매 donor를 고정셀 양자화하고 새 원화와 좌표/색인을 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
def main():
    d=H/'standing_fire_sleeves_inspection01';need(not d.exists(),'Fresh inspection')
    s=H/'standing_fire_fourth_sleeves01';p=s/'generated.png';need(sha(p.read_bytes())=='44ea9f8a71c9d4151bff8b76709b6cc30ab6029bef0f747c6405e4460c702776','Donor changed')
    a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());im=Image.open(p).convert('RGBA');need(im.size==(1254,1254),'Size')
    arr=np.array(im.resize((192,192),Image.Resampling.NEAREST));colors=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[16:32]],np.int32);rows=[];d.mkdir()
    for row,n in enumerate((85,89)):
        c=arr[row*96:(row+1)*96,96:192];v=(1+((c[:,:,:3].astype('int32')[:,:,None]-colors[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');v[c[:,:,3]<128]=0
        q=np.zeros((384,384),np.uint8);q[112:208,112:208]=v;Image.fromarray(q).save(d/f'{n:03}_donor_indices.png');a.rgba(q,16).save(d/f'{n:03}_donor.png')
        old=np.array(Image.open(H/f'standing_fire_native01/fourth_{n:03}_indices.png'));plate=Image.new('RGB',(1460,1060),(25,31,40));draw=ImageDraw.Draw(plate)
        for col,(label,idx)in enumerate((('before',old),('donor',q))):
            left=col*730+30;crop=a.rgba(idx,16).crop((136,132,171,183)).resize((700,1020),Image.Resampling.NEAREST);plate.paste(crop,(left,30),crop)
            for x in range(36):
                draw.line((left+x*20,30,left+x*20,1050),fill=(58,64,73))
                if x<35 and x%2==0:draw.text((left+x*20,15),str(x-24),fill='white')
            for y in range(52):
                draw.line((left,30+y*20,left+700,30+y*20),fill=(58,64,73))
                if y<51 and y%2==0:draw.text((left-25,30+y*20),str(y-28),fill='white')
            for y,x in zip(*np.nonzero(idx[132:183,136:171])):
                value=int(idx[y+132,x+136]);draw.text((left+x*20+4,30+y*20+4),hex(value)[2:].upper(),fill=(20,20,20)if value in(4,5,6,10,11)else(200,240,220))
            draw.text((left+300,2),f'{label} {n}',fill='white')
        plate.save(d/f'{n:03}_grid.png');rows.append({'ref':n,'whole_donor_changed_indices':int((q!=old).sum()),'new_source_alpha_lost':int(((old>0)&(q==0)).sum()),'new_donor_alpha_extra':int(((old==0)&(q>0)).sum())})
    write(d/'report.json',{'generated_sha256':sha(p.read_bytes()),'fixed_global_scale':192/1254,'alpha_cutoff':128,'rows':rows,'scope':'새원화 전체는 미채택. 실제 소매 표본만 후속 의미영역 등록할 진단.'})
    write(s/'generation_receipt.json',{'tool':'builtin imagegen','source_builtin':'<LOCAL_PATH>','generated_sha256':sha(p.read_bytes()),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'inputs_actually_viewed':['edit_target.png','accepted_style.png','region_guide.png'],'actual_size':list(im.size)})
    print(json.dumps(rows))
if __name__=='__main__':main()
