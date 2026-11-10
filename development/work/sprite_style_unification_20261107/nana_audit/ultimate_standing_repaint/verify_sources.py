"""네 생성셀을 다시 양자화하고 명시된 의미영역·원효과에서15층을 재구성한다."""
from pathlib import Path
import json,sys,importlib.util
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,need
from prepare_common import source_vote,poly
from prepare_targets import shift
def read(p):return json.loads(p.read_text('utf8'))
def pix(p):return np.array(Image.open(p))
def main():
 td=D/'targets_probe_v2';m=read(td/'manifest.json');parent=ROOT/m['parent_arc'];need(digest(parent)==m['parent_arc_sha256'],'부모')
 a=Archive(parent.read_bytes());art=D/'a_v1/generated.png';need(digest(art)=='d4cf2d3b4059ff0189898c9283f71d336ff356c5f7f48d27bd10edfe7e6f6afd','새원화')
 im=Image.open(art).convert('RGBA');need(im.size==(1254,1254),'전체캔버스');spec=importlib.util.spec_from_file_location('source_quantizer',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
 cm=read(D/'common_probe_v3/manifest.json');original={};cells=[]
 for row,form,start in((0,'before',16),(1,'after',0)):
  pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  for col,n in enumerate((89,97)):
   crop=(col*627,row*627,(col+1)*627,(row+1)*627);cell=im.crop(crop);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(cell,(96,96),pal,'area_vote');need(np.array_equal(z,pix(D/f'first_registered_v1/{form}_{n:03}_indices.png')),'4고정셀')
   q=next(q for q in cm['frames']if q['ref']==n);e=next(e for e in q['eye_registration']if e['form']==form);x,y=e['world'];v,votes=source_vote(cell,pal,(x,y),{14,15});need(v==e['source_vote']and votes==e['votes'],'홍채윗경계실제표본');need(z[y+160,x+160]==14 and z[y+161,x+160]==14,'홍채위치');z[y+160,x+160]=v;original[form,n]=z
   cells.append({'ref':n,'form':form,'crop':crop,'registered_source_sha256':sha(pix(D/f'first_registered_v1/{form}_{n:03}_indices.png').tobytes()),'eye_requantized_cell':e})
 common={}
 for col,n in enumerate((89,97)):
  q=next(q for q in cm['frames']if q['ref']==n);b=original['before',n];v=b.copy();pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);cell=im.crop((col*627,0,(col+1)*627,627))
  for r in q['palette15_face_semantic']:
   x,y=r['world'];value,votes=source_vote(cell,pal,(x,y),{15});need(value==r['after_index']and votes==r['votes']and b[y+160,x+160]==15,'팔레트15 의미표본');v[y+160,x+160]=value
  mask=poly(q['costume_polygon'])
  for link in q['source_boundary_links']:
   x,y=link['world'];need(int(b[y+160,x+160])==link['before_index']and int(original['after',n][y+160,x+160])==link['source_after_index'],'커프출처');mask[y+160,x+160]=True
  v[mask]=original['after',n][mask]
  hm=poly(q['shared_hand_polygon']);need(np.array_equal(hm,pix(D/f'common_probe_v3/shared_hand_mask_{n:03}.png')>0),'실제새손마스크');v[hm]=b[hm]
  need(np.array_equal(b,pix(D/f'common_probe_v3/before_{n:03}_indices.png'))and np.array_equal(v,pix(D/f'common_probe_v3/after_{n:03}_indices.png')),'공통몸재구성');common[n]=(b,v)
 fxinfo=m['original_effect_source'];fxpath=ROOT/fxinfo['npy'];need(digest(fxpath)==fxinfo['npy_sha256'],'원효과파일');fx=np.load(fxpath);need(int((fx>0).sum())==83,'효과83');checked=[]
 for n in(88,89,97):
  sn=89 if n==88 else n;dx=-1 if n==88 else 0;b,v=[shift(z,dx)for z in common[sn]]
  if n==88:b[fx>0]=fx[fx>0];v[fx>0]=fx[fx>0]
  pc=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[b];ls={0:v,5:np.where((b!=v)|pc,b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  for pb,z in ls.items():need(np.array_equal(z,pix(td/f'layer{pb}_{n:03}.png'))and sha(z.tobytes())==m['targets'][str(n)][str(pb)],'15최종층');checked.append([n,pb,sha(z.tobytes())])
 out=td/'source_reconstruction.json';need(not out.exists(),'새보고만');write(out,{'passed':True,'source_art_sha256':digest(art),'parent_arc_sha256':digest(parent),'source_cells':cells,'target_manifest_sha256':digest(td/'manifest.json'),'layers_exact':checked,'original_effect83_source':fxinfo,'no_old_body_copied':True,'scope':'자체 원화4셀 재양자화와 명시된 눈/팔레트15·의상·공통손에서15층 재구성. 원효과의 원게임타일 독립검사는 별도 HUD 관계보고에 결속. 새MIPS/독립/실기 아님.'});print(json.dumps({'passed':True,'source_cells':4,'layers':15,'sha256':digest(out)}))
if __name__=='__main__':main()
