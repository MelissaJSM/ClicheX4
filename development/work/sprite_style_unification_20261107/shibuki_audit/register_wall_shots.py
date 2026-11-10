"""새 사격팔만 등록하고 원 총구/새 머리/새 몸/벽손을 지키는 후보."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_run_cycle import quantize
from native_pose_pack import SOURCE,SOURCE_SHA,need,sha,write
from register_wall_costumes import polygon

def arm_area(n,mx,my):
 sx,sy={55:(-6,-2),57:(-6,-1),59:(-6,-2),61:(-2,-2),63:(0,-1),65:(-2,-1)}[n]
 shift=sx+6
 old=polygon([(x+shift,y)for x,y in[(-20,-8),(-11,-9),(-5,-4),(-5,2),(-10,8),(-18,8)]])
 new=polygon([(mx-2,my-5),(sx-4,my-5),(sx+4,sy-4),(sx+5,sy+5),(sx-3,sy+9),(mx-2,my+8)])
 return old|new

def head_guard(n,body):
 d=H/('wall_head_edit01/native01'if n<61 else'wall_head_edit02/native01');m=np.array(Image.open(d/f'base_{n:03}_head_mask.png'))>0;yy,xx=np.indices(body.shape);x=xx-160;y=yy-160
 eye={55:(-5,-9),57:(-5,-9),59:(-5,-9),61:(-2,-9),63:(0,-8),65:(-2,-8)}[n]
 face=(x>=eye[0]-3)&(x<=eye[0]+4)&(y>=eye[1]-2)&(y<=eye[1]+5)
 hair=np.isin(body,[2,5,7,8,14,15])
 return m&(body>0)&(y<=-5)&(hair|face)

def main():
 a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);inputs=H/'wall_shot_edits01';bodydir=H/'wall_costumes04';guards=json.loads((H/'wall_barrel_guard01/guard.json').read_text('utf8'))['rows'];out=H/'wall_shots_registered03';need(not out.exists(),'Output exists');out.mkdir();rows=[];sheets={0:[],15:[]}
 hashes={1:'82799c2260d4217189b61e91387edc2fc0698b472db552e3879c1300167e0220',2:'d136bab5d843c9319b622f681ed50785dc9fca0d2082578fa3a57e55dd8bbbb5'}
 for pn,refs in((1,(55,57,59)),(2,(61,63,65))):
  path=inputs/f'generated_page{pn:02}.png';need(sha(path.read_bytes())==hashes[pn],'Shot source changed');im=Image.open(path).convert('RGBA');need(im.size==(1536,1024),'Wrong source dimensions')
  for col,n in enumerate(refs):
   body={b:np.array(Image.open(bodydir/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};guard=next(q for q in guards if q['body_ref']==n);mx,my=guard['muzzle_world'];edit=arm_area(n,mx,my);head=head_guard(n,body[0]);edit&=~head
   barrel=np.array(Image.open(H/'wall_barrel_guard01'/f'{n+1:03}_indices.png'));x0,y0,x1,y1=guard['barrel_rectangle_world_exclusive'];barrel_rect=np.zeros_like(edit);barrel_rect[y0+160:y1+160,x0+160:x1+160]=True
   generated={}
   for row,start in((0,0),(1,16)):
    rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in struct.unpack_from('<16H',a.p,start*2)],np.int32);v=quantize(im.crop((col*512,row*512,(col+1)*512,(row+1)*512)),(64,64),rgb,128);new=np.zeros((384,384),np.uint8);new[120:184,128:192]=v;generated[start]=new
   target={b:v.copy()for b,v in body.items()};target[0][edit]=generated[0][edit];target[0][barrel_rect]=barrel[barrel_rect]
   for b in(5,6,7,8):target[b][edit|barrel_rect]=0
   target[7][edit&~barrel_rect]=generated[16][edit&~barrel_rect]
   # The new base arm is the maximum arm silhouette. At only its uncovered
   # edge, register those SAME new source texels in the matching Fourth cloth
   # material. Internal Fourth arm detail remains untouched.
   outside=edit&~barrel_rect&(target[0]>0)&(target[7]==0);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:32]],np.int32);mapping={i:int(np.argmin(((rgb[17:32]-rgb[i])**2).sum(1)))+1 for i in range(1,16)};mapping.update({1:2,4:11,10:10,11:11,12:9,13:9,15:1})
   for y,x in zip(*np.nonzero(outside)):target[7][y,x]=mapping[int(target[0][y,x])]
   need(np.array_equal(target[0][~(edit|barrel_rect)],body[0][~(edit|barrel_rect)]),'New nonarm body changed')
   for b in(5,6,7,8):need(np.array_equal(target[b][~(edit|barrel_rect)],body[b][~(edit|barrel_rect)]),'New nonarm part changed')
   for b,v in target.items():Image.fromarray(v).save(out/f'{n+1:03}_bank{b}_indices.png')
   Image.fromarray(edit.astype(np.uint8)*255).save(out/f'{n+1:03}_arm_mask.png');Image.fromarray(head.astype(np.uint8)*255).save(out/f'{n+1:03}_head_protection.png')
   for mask,label in((0,'base'),(15,'fourth')):
    pic=a.rgba(target[0]);before=a.rgba(body[0])
    if mask:
     for b in(8,5,7,6):pic.alpha_composite(a.rgba(target[b],16));before.alpha_composite(a.rgba(body[b],16))
    need(np.array_equal(np.array(pic)[barrel_rect],np.array(a.rgba(barrel))[barrel_rect]),'Gun RGBA or alpha changed');pic.save(out/f'{n+1:03}_{label}.png');sheets[mask].extend([(f'{label} body{n}',before),(f'{label} shot{n+1}',pic)])
   rows.append({'ref':n+1,'body_ref':n,'generated_sha256':hashes[pn],'barrel_rectangle_rgba_exact_both_forms':True,'non_arm_new_body_exact':True,'head_opaque_pixels_protected':int(head.sum()),'arm_only_source_edge_material_pixels':int(outside.sum()),'not_packed':True})
 for mask,label in((0,'base'),(15,'fourth')):page(sheets[mask],a.composite(0,mask)[0],out/f'{label}_comparison.png',cols=2,scale=4)
 write(out/'registration.json',{'source_bin_sha256':SOURCE_SHA,'rows':rows,'no_arm_stretch':True,'old_head_body_sleeve_used':False,'arc_not_written':True,'visual_review_pending':True});print(rows)

if __name__=='__main__':main()
