"""새 Ultimate 피격의 공통부/국소 팔을 정하는 좌표판. ARC 미수정."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive

def shift(v,dx,dy):
 out=np.zeros_like(v);xs=max(0,-dx);xe=min(v.shape[1],v.shape[1]-dx);ys=max(0,-dy);ye=min(v.shape[0],v.shape[0]-dy)
 out[ys+dy:ye+dy,xs+dx:xe+dx]=v[ys:ye,xs:xe];return out

def grid(images,path,names):
 out=Image.new('RGB',(680*len(images),790),(30,36,47));dr=ImageDraw.Draw(out)
 for col,(im,name)in enumerate(zip(images,names)):
  cut=im.crop((136,136,184,188)).resize((576,624),Image.Resampling.NEAREST);x=col*680+64;y=64;out.paste(cut,(x,y),cut);dr.text((x,y-36),name,fill='white')
  for v in range(-24,25,4):
   px=x+(v+24)*12;dr.line((px,y,px,y+624),fill=(65,72,82),width=1);dr.text((px-4,y-16),str(v),fill='white')
  for v in range(-24,29,4):
   py=y+(v+24)*12;dr.line((x,py,x+576,py),fill=(65,72,82),width=1);dr.text((x-25,py-5),str(v),fill='white')
 out.save(path)

def main():
 d=H/'ultimate_hurt_common_inspection01';need(not d.exists(),'Fresh inspection');d.mkdir()
 a=Archive((H/'prepared_ultimate_ladder01/PL02_U.ARC').read_bytes())
 for n in(106,110,233,234):
  folder=H/('ultimate_hurt_native01'if n<200 else'ultimate_hurt_native02')
  grid([Image.open(folder/f'{f}_{n:03}.png').convert('RGBA')for f in('before','after')],d/f'{n:03}_grid.png',[f'{n} before',f'{n} after'])
 src=H/'ultimate_hurt234_arm01';need(sha((src/'generated.png').read_bytes())=='4417737feba5f7333f76701be161babbbbcc82640e54175132070b8552c4d6df','New arm changed')
 im=Image.open(src/'generated.png').convert('RGBA');need(im.size==(1536,1024),'Fixed page changed');s=np.array(im.resize((192,128),Image.Resampling.NEAREST))[64:128,96:192]
 rgb=np.array([[(int(w)>>ss&31)*255//31 for ss in(0,5,10)]for w in a.words[:16]],np.int32);q=(1+((s[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);q[s[:,:,3]<128]=0;v=np.zeros((384,384),np.uint8);v[128:192,112:208]=q
 old=np.array(Image.open(H/'ultimate_hurt_native02/after_234_indices.png'));yy,xx=np.indices(v.shape);head=(yy>=136)&(yy<153)&(xx>=136)&(xx<180)
 search=[]
 for dy in range(-3,4):
  for dx in range(-6,7):
   w=shift(v,dx,dy);bad=int(((old!=w)&head).sum());search.append({'dx':dx,'dy':dy,'head_mismatch_pixels':bad})
 search.sort(key=lambda z:(z['head_mismatch_pixels'],abs(z['dx'])+abs(z['dy'])));best=search[0];v=shift(v,best['dx'],best['dy']);Image.fromarray(v).save(d/'after_234_arm_donor_indices.png');a.rgba(v).save(d/'after_234_arm_donor.png')
 grid([a.rgba(old),a.rgba(v)],d/'234_arm_donor_grid.png',['after234 previous','local donor aligned; old body NOT replaced'])
 write(d/'report.json',{'grid_only':True,'refs':[106,110,233,234],'new_arm_source_sha256':sha((src/'generated.png').read_bytes()),'donor_alignment_by_unchanged_head':best,'search_top10':search[:10],'donor_crop_origin':[112,128],'palette_row':0,'scale':0.125,'alpha_cutoff':128,'wholebody_replacement':False,'arc_changed':False})
 write(src/'generation_receipt.json',{'tool':'builtin imagegen','generated_sha256':sha((src/'generated.png').read_bytes()),'prompt_sha256':sha((src/'prompt.txt').read_bytes()),'input_images':{'edit_target.png':sha((src/'edit_target.png').read_bytes())},'original_preserved':True,'project_copy':(src/'generated.png').relative_to(ROOT).as_posix()})
 print(json.dumps(best))
if __name__=='__main__':main()
