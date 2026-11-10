"""90 후폼 국소팔 donor의 고정96셀 검토판."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
s=H/'ultimate_standing90_arm01';d=H/'ultimate_standing90_arm_inspection01';need(not d.exists(),'새 폴더 필요');d.mkdir()
g=s/'generated.png';r=json.loads((s/'generation_receipt.json').read_text('utf8'));need(sha(g.read_bytes())==r['generated_sha256'],'원화 변경')
a=Archive((H/'prepared_standing_special_ultimate01/PL02_U.ARC').read_bytes());im=Image.open(g).convert('RGBA');need(im.width==im.height,'정사각');cell=np.array(im.resize((96,96),Image.Resampling.NEAREST));rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.int32);ind=(1+((cell[:,:,:3].astype('int32')[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');ind[cell[:,:,3]<128]=0
full=np.zeros((384,384),np.uint8);full[112:208,112:208]=ind;rgba=a.rgba(full);Image.fromarray(full).save(d/'donor_indices.png');rgba.save(d/'donor.png');Image.fromarray(cell).save(d/'sample_rgba.png')
old=Image.open(H/'ultimate_standing_followthrough_native01/after_090.png').convert('RGBA');world=(-24,-24,0,3);x0,y0,x1,y1=world;scale=20;w=(x1-x0)*scale;h=(y1-y0)*scale;grid=Image.new('RGB',(2*w+80,h+60),(30,34,44));dr=ImageDraw.Draw(grid)
for col,src in enumerate((old,rgba)):
    cut=src.crop(tuple(v+160 for v in world)).resize((w,h),Image.Resampling.NEAREST);grid.paste(cut,(40+col*(w+40),40),cut)
    for x in range(x1-x0):dr.text((40+col*(w+40)+x*scale,20),str(x+x0),fill='white')
    for y in range(y1-y0):dr.text((col*(w+40),40+y*scale),str(y+y0),fill='white')
    for x in range(x1-x0+1):dr.line((40+col*(w+40)+x*scale,40,40+col*(w+40)+x*scale,40+h),fill=(65,67,74))
    for y in range(y1-y0+1):dr.line((40+col*(w+40),40+y*scale,40+col*(w+40)+w,40+y*scale),fill=(65,67,74))
grid.save(d/'grid.png');page([('90 first',old),('90 local donor',rgba)],a.composite(0,0)[0],d/'comparison.png',cols=2,scale=6)
write(d/'report.json',{'source_sha256':sha(g.read_bytes()),'source_size':list(im.size),'whole_canvas_scale':96/im.width,'alpha_cutoff':128,'native_metrics':metrics(rgba),'donor_indices_sha256':sha(full.tobytes()),'source_crop_or_body_scale':False,'semantic_patch_pending':True})
