"""시부키 등록10몸체를 읽기만 하여 머리/손 좌표와 비교판을 저장한다."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1];H=W/'root_shibuki_hover'
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def box(z):
 y,x=np.nonzero(z)
 return [int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]if len(x)else None
def main():
 out=D/'readback_v2';assert not out.exists();out.mkdir();p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';assert sha(p)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e';a=Archive(p.read_bytes());files=[p];metrics=[];rows=[];pal={}
 for start in(0,16):pal[str(start)]=[[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]]
 for n in(221,223,225,227,229):
  row=[];allnew=[]
  for form,mask,start in(('base_legs',8,0),('fourth',15,16)):
   f=(H/f'registered_neutral{1 if n<225 else 2:02}'/f'{form}_{n:03}_nearest_indices.png')if n<229 else(H/'reach229_registered01'/f'{form}_local_indices.png');files.append(f);z=np.array(Image.open(f));assert z.shape==(384,384)and z.max()<16;im=a.rgba(z,start);old=a.composite(n,mask)[0];allnew.append(np.array(im));row.extend([(f'old {form}',old),(f'new {form}',im)])
   # 동일RGB255/222/189는기본13/포스9다.좌표후보만분리하며의미는실제판열람으로판정한다.
   skin_index=13 if start==0 else 9;assert pal[str(start)][skin_index]==[255,222,189]
   skin=z==skin_index;skin[159:]=False;cc,num=label(skin,np.ones((3,3)));components=[]
   for k in range(1,num+1):
    v=cc==k;coords=[[int(x-160),int(y-160)]for y,x in np.argwhere(v)];components.append({'pixels':len(coords),'bbox':box(v),'coordinates':coords})
   metrics.append({'ref':n,'form':form,'indices_path':f.relative_to(ROOT).as_posix(),'sha256':sha(f),'whole_bbox':box(z>0),'old_whole_bbox':[v-160 for v in old.getbbox()],'skin_index':skin_index,'skin_upper_components_not_automatic_semantic_masks':components})
  crop=(136,123,183,165);sheet=Image.new('RGB',(47*10*4,42*10+44),'#bcc5ca');dr=ImageDraw.Draw(sheet)
  for j,(title,im)in enumerate(row):
   tile=im.crop(crop).resize((470,420),Image.Resampling.NEAREST);sheet.paste(tile,(j*470,44),tile);dr.text((j*470+5,3),f'{n} {title}; world x -24..22 / y -37..4',fill='black')
   for x in range(-20,23,5):dr.text((j*470+(x+24)*10,23),str(x),fill='black')
   for y in range(-35,5,5):dr.text((j*470+2,44+(y+37)*10),str(y),fill='black')
  sheet.save(out/f'upper_{n:03}.png')
  same=np.all(allnew[0]==allnew[1],axis=2);active=(allnew[0][:,:,3]>0)|(allnew[1][:,:,3]>0);metrics.append({'ref':n,'new_forms_full_RGBA_difference_pixels':int((~same&active).sum()),'already_common_pixel_policy_verified':False})
 data={'read_only':True,'producer_functions_called':False,'art_or_ARC_modified':False,'source':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)},'palette_rgb':pal,'metrics':metrics,'inputs':[{'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f)}for f in files],'actual_review_pending':True,'excluded_diagnostic':'measurements.json의양폼index9동일피부가정은잘못이며해당성분측정을제외.이v2는실제동일RGB의기본13/포스9로정정.본래RGBA비교판은정확한팔레트였다.','scope':'기존source와10등록색인에서실제RGBA/피부후보좌표를읽는다.피부후보성분은자동손/얼굴의미마스크가아니며분리판을눈으로판정해야한다.새레이어/패킹/실기검사없음.'};(D/'measurements_v2.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'metrics':[{k:v for k,v in q.items()if k!='skin_upper_components_not_automatic_semantic_masks'}for q in metrics]},ensure_ascii=False))
if __name__=='__main__':main()
