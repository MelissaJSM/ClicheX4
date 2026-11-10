"""새 탑승원화의 홍채 표본과 손·신발 강체 원점을 등록한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,helper,need
s=importlib.util.spec_from_file_location('ride_vote',N/'ultimate_standing_repaint/prepare_common.py');sm=importlib.util.module_from_spec(s);s.loader.exec_module(sm)
Y,X=np.indices((384,384));Y-=160;X-=160
def move(z,mask,dx,dy):
 src=z.copy();piece=np.where(mask,src,0);z[mask]=0;dest=np.roll(np.roll(piece,dy,0),dx,1);hit=dest>0;overlap=int((hit&(z>0)).sum());z[hit]=dest[hit]
 return {'translation':[dx,dy],'source_cells':[[int(x-160),int(y-160),int(src[y,x])]for y,x in np.argwhere(mask&(src>0))],'overlap':overlap}
def main():
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/'contacts_probe_v1';out.mkdir(exist_ok=False);rows=[];proof=[]
 for n in(162,166,170,174):
  page='a'if n<170 else'b';im=Image.open(D/f'{page}_v1/generated.png').convert('RGBA');col=0 if n in(162,170)else 1
  for row,(form,start,mask)in enumerate((('before',16,15),('after',0,0))):
   z=np.array(Image.open(D/f'{page}_registered_v1/{form}_{n:03}_indices.png'));old=z.copy();eye=[];moves=[];cell=im.crop((col*627,row*627,(col+1)*627,(row+1)*627));pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[start:start+16]],np.float32)
   if n in(170,174):
    x,y=(-12,-16)if n==170 else(-8,-18);need(z[y+160,x+160]==14,'추가 홍채');v,votes=sm.source_vote(cell,pal,(x,y),{14,15});z[y+160,x+160]=v;eye.append({'world':[x,y],'value':v,'votes':votes,'original_iris_preserved_at':[-12,-15]if n==170 else[-8,-19]})
   if n==170:
    moves.append({'meaning':'손잡이 앞손과 손목','data':move(z,(X<=-11)&(Y>=-7)&(Y<=-2),-1,-1)})
    moves.append({'meaning':'발목 아래 신발','data':move(z,Y>=8,0,-1)})
   if n==174:
    moves.append({'meaning':'손잡이 앞손과 손목','data':move(z,(X<=-9)&(Y>=-12)&(Y<=-5),0,-1)})
    moves.append({'meaning':'오른쪽 아래 신발','data':move(z,(X>=-5)&(Y>=7),0,-1)})
   Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png');proof.append({'ref':n,'form':form,'source':(D/f'{page}_registered_v1/{form}_{n:03}_indices.png').relative_to(ROOT).as_posix(),'source_sha256':sha(old.tobytes()),'iris_source_registration':eye,'rigid_pieces':moves,'components8':int(label(z>0,np.ones((3,3)))[1]),'target_sha256':sha(z.tobytes())});rows.append((f'{form}{n}',[('old pose',a.composite(n,mask)[0]),('new fixed',a.rgba(old,start)),('contact candidate',a.rgba(z,start))]))
 for i in range(0,8,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'parent_sha256':m['parent_arc_sha256'],'frames':proof,'scope':'새 원화만의 국소강체 정합/실제표본 홍채정리 후보. 전체변형·임의그림채움 없음. 아직 미술/의상공통층 최종아님.','native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'form':q['form'],'eye':[(e['world'],e['value'])for e in q['iris_source_registration']],'components':q['components8']}for q in proof]))
if __name__=='__main__':main()
