"""국소 원화 고정셀 등록과 좌표판. 최종 합성 전 검사 전용."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
s=H/'ultimate_standing_fire_sleeves01';d=H/'ultimate_standing_fire_sleeves_inspection01';need(not d.exists(),'새 검사 폴더 필요')
g=s/'generated.png';need(sha(g.read_bytes())=='b0a9db946680af5aad23daf6f57b3ec08bf114488448081b968ed5b34af5beb3','원화 변경')
a=Archive((H/'prepared_standing_special_ultimate01/PL02_U.ARC').read_bytes());im=Image.open(g).convert('RGBA');need(im.size==(1254,1254),'전체캔버스 크기');samples=np.array(im.resize((192,192),Image.Resampling.NEAREST));rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.int32);rows=[];pics=[];d.mkdir()
for row,n in enumerate((85,89)):
    cell=samples[row*96:(row+1)*96,96:192];ind=(1+((cell[:,:,:3].astype('int32')[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');ind[cell[:,:,3]<128]=0
    full=np.zeros((384,384),np.uint8);full[112:208,112:208]=ind;rgba=a.rgba(full);Image.fromarray(full).save(d/f'{n:03}_donor_indices.png');rgba.save(d/f'{n:03}_donor.png');Image.fromarray(cell).save(d/f'{n:03}_source_rgba.png')
    old=Image.open(H/f'ultimate_standing_fire_native01/after_{n:03}.png').convert('RGBA');pics.extend([(f'{n} first source',old),(f'{n} sleeve edit',rgba)])
    world=(-21,-25,2,4);x0,y0,x1,y1=world;scale=18;w=(x1-x0)*scale;h=(y1-y0)*scale;grid=Image.new('RGB',(2*w+80,h+60),(30,34,44));draw=ImageDraw.Draw(grid)
    for col,src in enumerate((old,rgba)):
        cut=src.crop(tuple(v+160 for v in world)).resize((w,h),Image.Resampling.NEAREST);grid.paste(cut,(40+col*(w+40),40),cut)
        for x in range(x1-x0):draw.text((40+col*(w+40)+x*scale,20),str(x+x0),fill='white')
        for y in range(y1-y0):draw.text((col*(w+40),40+y*scale),str(y+y0),fill='white')
        for x in range(x1-x0+1):draw.line((40+col*(w+40)+x*scale,40,40+col*(w+40)+x*scale,40+h),fill=(65,67,74))
        for y in range(y1-y0+1):draw.line((40+col*(w+40),40+y*scale,40+col*(w+40)+w,40+y*scale),fill=(65,67,74))
    grid.save(d/f'{n:03}_grid.png');rows.append({'ref':n,'indices_sha256':sha(full.tobytes()),'samples_alpha_below128':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum())})
page(pics,a.composite(0,0)[0],d/'comparison.png',cols=2,scale=6)
write(d/'report.json',{'source_sha256':sha(g.read_bytes()),'source_size':list(im.size),'whole_canvas_scale':192/1254,'alpha_cutoff':128,'rows':rows,'final_arm_semantic_mask_pending':True,'arc_written':False})
