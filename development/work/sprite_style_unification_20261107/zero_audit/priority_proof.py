"""Read-only comparison crops and current-to-authored provenance checks."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
OUT=Path(__file__).parent
def load(p):return json.loads(p.read_text('utf8'))
def pic(char,key):
 revp=ROOT/'out/sprite_consistency_20261105/revised'/char/'mapping.json'
 rev=load(revp)['frames'] if revp.exists() else {}
 return Image.open(ROOT/rev['normal:'+key] if 'normal:'+key in rev else ROOT/'out/sprite_consistency_20261105'/char/'normal/native'/(key+'.png')).convert('RGBA')
def board(char,keys,name):
 keys=['b0_147']+keys
 boxes=[pic(char,k).getbbox()for k in keys];box=(min(126,min(b[0]for b in boxes))-3,min(119,min(b[1]for b in boxes))-3,max(199,max(b[2]for b in boxes))+3,max(190,max(b[3]for b in boxes))+3);scale=6;cw=(box[2]-box[0])*scale;ch=(box[3]-box[1])*scale+28
 out=Image.new('RGB',(cw*3,ch*((len(keys)+2)//3)), '#68747c');d=ImageDraw.Draw(out);f=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
 for i,key in enumerate(keys):
  x=i%3*cw;y=i//3*ch;d.text((x+5,y+4),char+' '+key,font=f,fill='white');p=pic(char,key).crop(box).resize((cw,ch-28),Image.Resampling.NEAREST);out.paste(p,(x,y+28),p)
 out.save(OUT/name)
def main():
 board('riko',['b0_111','b0_113','b0_117','b0_121','b0_125'],'riko_third_saber_6x.png')
 board('rin',['b0_008','b0_095','b0_049','b0_229','b1_183'],'rin_face_cuff_6x.png')
 records=[]
 for group,n,source_n in [('run',8,8),('ground',95,95),('ground',95,97)]:
  folder=ROOT/'work/ver_rin_nana/style_revision/v3'/group;rec=load(folder/'registered.json')['frames'][str(source_n)];p=folder/rec['file'];im=Image.open(p).convert('RGBA');bb=rec['bounds'];world=Image.new('RGBA',(384,384));world.paste(im,(160+bb[0],160+bb[1]));a=np.array(world);b=np.array(pic('rin',f'b0_{n:03d}'))
  # PNG writers expand RGB555 differently by at most one level. Compare native 5-bit values.
  qa=np.concatenate((a[:,:,:3]>>3,a[:,:,3:]),2);qb=np.concatenate((b[:,:,:3]>>3,b[:,:,3:]),2);qa[a[:,:,3]==0]=0;qb[b[:,:,3]==0]=0
  records.append({'character':'rin','frame':n,'registered_frame':source_n,'registered_png':str(p.relative_to(ROOT)),'registered_sha256_actual':hashlib.sha256(p.read_bytes()).hexdigest(),'metadata_sha256':rec['sha256'],'current_RGB555_alpha_exact':bool(np.array_equal(qa,qb)),'different_pixels':int(np.any(qa!=qb,axis=2).sum()),'normalization':{k:rec[k]for k in ('scale','source_sha256','alpha_noise_removed')if k in rec}})
 (OUT/'source_lineage_checks.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
if __name__=='__main__':main()
