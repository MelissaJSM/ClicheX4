"""새 준비4의 홍채와 다리 실제RGB 후보를 읽고 좌표판으로 남긴다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write
s=importlib.util.spec_from_file_location('nova_vote',N/'ultimate_standing_repaint/prepare_common.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def main():
 out=D/'source_semantics_audit_v2';out.mkdir(exist_ok=False);meta=json.loads((D/'a_registered_v1/manifest.json').read_text('utf8'));inp=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/inp['parent_arc']).read_bytes());im=Image.open(D/'a_v1/generated.png').convert('RGBA');proof=[]
 for q in meta['frames']:
  n,form=q['ref'],q['form'];start=16 if form=='before'else 0;pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[start:start+16]],np.float32);cell=im.crop(q['source_crop']);ar=np.array(cell);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255;res=lambda z:np.array(Image.fromarray(z.astype(np.float32),'F').resize((96,96),Image.Resampling.BOX));mass=res(alpha);mean=np.stack([res(rgb[:,:,k]*alpha)/np.maximum(mass,.001)for k in range(3)],2);z=np.array(Image.open(D/f'a_registered_v1/{form}_{n:03}_indices.png'));eye=[];legs=[]
  for yy,xx in np.argwhere((z==14)&(np.indices(z.shape)[0]<155)):
   x,y=int(xx-160),int(yy-160);value,votes=v.source_vote(cell,pal,(x,y),set());non,nvotes=v.source_vote(cell,pal,(x,y),{14,15});eye.append({'world':[x,y],'index':14,'green_fraction':votes.get('14',0),'nearest_noniris':non,'noniris_votes':nvotes})
  for yy,xx in np.argwhere(np.isin(z,[5,6,7,8,9])):
   x,y=int(xx-160),int(yy-160)
   if y<5:continue
   allowed=np.array([1,2,3,4,10,11,12,13]);c=mean[y+48,x+48];value=int(allowed[((pal[allowed]-c)**2).sum(1).argmin()]);legs.append({'world':[x,y],'old':int(z[yy,xx]),'source_alpha_weighted_rgb':c.tolist(),'nearest_skin_or_outline':value})
  b=(-17,-31,38,26);scale=16;board=Image.new('RGB',((b[2]-b[0])*scale+36,(b[3]-b[1])*scale+24),'#b9c1c7');dr=ImageDraw.Draw(board)
  for y in range(b[1],b[3]):
   dr.text((0,(y-b[1])*scale+24),str(y),fill='black')
   for x in range(b[0],b[2]):
    i=int(z[y+160,x+160]);px=(x-b[0])*scale+36;py=(y-b[1])*scale+24
    if y==b[1]:dr.text((px,0),str(x),fill='black')
    if i:dr.rectangle((px,py,px+scale-1,py+scale-1),fill=tuple(int(c)for c in pal[i]));dr.text((px+3,py+1),hex(i)[2:].upper(),fill='white'if i<7 else'black')
  p15=[]
  for yy,xx in np.argwhere(z==15):
   x,y=int(xx-160),int(yy-160);value,votes=v.source_vote(cell,pal,(x,y),{15});p15.append({'world':[x,y],'old':15,'value':value,'votes':votes})
  board.save(out/f'{form}_{n}.png');proof.append({'ref':n,'form':form,'old_eye':q['old_eye'],'iris_candidates':eye,'lower_material_candidates':legs,'palette15_candidates':p15})
 write(out/'report.json',{'source_sha256':digest(D/'a_v1/generated.png'),'frames':proof,'read_only':True,'scope':'실제표본과색인지도 읽기. 홍채 정리/피부그늘 소유 수용은 후속이다.'});print(json.dumps([{k:q[k]for k in('ref','form','iris_candidates','lower_material_candidates')}for q in proof]))
if __name__=='__main__':main()
