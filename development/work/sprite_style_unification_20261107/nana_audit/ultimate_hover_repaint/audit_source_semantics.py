"""홍채·다리 음영의 실제 생성 표본을 읽는다. 등록 이미지는 바꾸지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
def main():
 out=D/'source_semantics_audit_v1';out.mkdir(exist_ok=False);meta=json.loads((D/'first_registered_v1/manifest.json').read_text('utf8'));inp=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/inp['parent_arc']).read_bytes());im=Image.open(D/'a_v1/generated.png').convert('RGBA');pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);proof=[]
 for q in meta['frames']:
  n=q['ref'];cell=im.crop(q['crop']);ar=np.array(cell);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255;labs=np.zeros(ar.shape[:2],np.uint8)
  for y in range(len(labs)):labs[y]=1+((rgb[y,:,None]-pal[None,1:])**2).sum(2).argmin(1)
  box=lambda v:np.array(Image.fromarray(v.astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))
  votes=np.stack([box((labs==i)*alpha)for i in range(16)]);mass=box(alpha);mean=np.stack([box(rgb[:,:,c]*alpha)/np.maximum(mass,.001)for c in range(3)],2);z=np.array(Image.open(D/f'first_registered_v1/body_{n:03}_indices.png'));eye=q['old_eye'];eye_samples=[]
  for dy in range(-1,2):
   for dx in range(-1,2):
    x,y=eye[0]+dx,eye[1]+dy;eye_samples.append({'world':[x,y],'current_index':int(z[y+160,x+160]),'green_fraction':float(votes[14,y+48,x+48]),'votes':{str(i):float(votes[i,y+48,x+48])for i in range(1,16)}})
  legs=[]
  for yy,xx in np.argwhere(np.isin(z,[5,6,7,8,9])):
   x,y=int(xx-160),int(yy-160)
   if y<8:continue
   meanrgb=mean[y+48,x+48];allowed=np.array([1,2,3,4,10,11,12,13]);nearest=int(allowed[((meanrgb-pal[allowed])**2).sum(1).argmin()]);legs.append({'world':[x,y],'current_index':int(z[yy,xx]),'source_alpha_weighted_mean_rgb':meanrgb.tolist(),'nearest_nonpink_index':nearest,'votes':{str(i):float(votes[i,y+48,x+48])for i in range(1,16)}})
  # Coordinate sheet exposes native indices without editing them.
  bounds=(-17,-33,24,29);scale=18;board=Image.new('RGB',((bounds[2]-bounds[0])*scale+42,(bounds[3]-bounds[1])*scale+26),'#b9c1c7');draw=ImageDraw.Draw(board)
  for y in range(bounds[1],bounds[3]):
   draw.text((0,(y-bounds[1])*scale+26),str(y),fill='black')
   for x in range(bounds[0],bounds[2]):
    i=int(z[y+160,x+160]);px=(x-bounds[0])*scale+42;py=(y-bounds[1])*scale+26
    if y==bounds[1]:draw.text((px,0),str(x),fill='black')
    if i:draw.rectangle((px,py,px+scale-1,py+scale-1),fill=tuple(int(v)for v in pal[i]));draw.text((px+4,py+2),hex(i)[2:].upper(),fill='white'if i<7 else'black')
  board.save(out/f'grid_{n}.png');proof.append({'ref':n,'eye_original':eye,'eye_samples':eye_samples,'lower_pink_candidates':legs})
 write(out/'report.json',{'source_sha256':digest(D/'a_v1/generated.png'),'frames':proof,'scope':'현재 홍채9주변셀과 y>=8 다리 영역 분홍 인덱스의 실제 생성RGB/표본을 읽었다. 의미영역 채택은 아직 하지 않았고 원화/등록 PNG를 변경하지 않았다.'});print(json.dumps({q['ref']:{'old_eye_green':next(v['green_fraction']for v in q['eye_samples']if v['world']==q['eye_original']),'leg_candidates':[(v['world'],v['current_index'],v['nearest_nonpink_index'])for v in q['lower_pink_candidates']]}for q in proof}))
if __name__=='__main__':main()
