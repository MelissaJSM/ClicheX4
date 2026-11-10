"""고정4셀을 다시 양자화하고 홍채·의상·권총·손 표본에서10층을 재구성한다."""
from pathlib import Path
import json,sys,importlib.util
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def module(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
sm=module('standing_sources',N/'ultimate_standing_repaint/prepare_common.py');reg=module('recoil_quantizer',N/'base_run_repaint/register_page.py')
def read(p):return json.loads(p.read_text('utf8'))
def pix(p):return np.array(Image.open(p))
def main():
 td=D/'targets_v1';m=read(td/'manifest.json');a=Archive((ROOT/m['parent_arc']).read_bytes());cm=read(D/'common_probe_v2/manifest.json');art=D/'a_v1/generated.png';need(digest(art)==cm['source_art_sha256'],'원화');im=Image.open(art).convert('RGBA');need(im.size==(1254,1254),'전체캔버스');source={};cells=[]
 for row,form,start in((0,'before',16),(1,'after',0)):
  pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  for col,n in enumerate((90,91)):
   crop=(col*627,row*627,(col+1)*627,(row+1)*627);cell=im.crop(crop);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(cell,(96,96),pal,'area_vote');need(np.array_equal(z,pix(D/f'first_registered_v1/{form}_{n:03}_indices.png')),'4고정셀');qh=sha(z.tobytes());q=next(q for q in cm['frames']if q['ref']==n)
   for e in q['eye_source']:
    if e['form']!=form:continue
    x,y=e['world'];val,votes=sm.source_vote(cell,pal,(x,y),{14,15});need(val==e['value']and votes==e['votes']and z[y+160,x+160]==14 and z[y+161,x+160]==14,'홍채원표본');z[y+160,x+160]=val
   source[form,n]=z;cells.append({'ref':n,'form':form,'crop':crop,'registered_sha256':qh})
 Y,X=np.indices((384,384));Y-=160;X-=160;z=a.layer(85)[0];gun=np.where((X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10)),z,0).astype(np.uint8);need(int((gun>0).sum())==20,'정본20');case=np.roll(gun,-2,1);checked=[]
 for col,n in enumerate((90,91)):
  q=next(q for q in cm['frames']if q['ref']==n);b=source['before',n].copy();v=b.copy();pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);cell=im.crop((col*627,0,(col+1)*627,627))
  for r in q['face15_source']:
   x,y=r['world'];val,votes=sm.source_vote(cell,pal,(x,y),{15});need(val==r['value']and votes==r['votes']and b[y+160,x+160]==15,'얼굴15');v[y+160,x+160]=val
  mask=sm.poly(q['costume_polygon'])
  for link in q['source_boundary_links']:
   x,y=link['world'];need(int(b[y+160,x+160])==link['before_index']and int(source['after',n][y+160,x+160])==link['source_after_index'],'소매경계출처');mask[y+160,x+160]=True
  v[mask]=source['after',n][mask];weapon=q['weapon']
  if n==90:
   share=sm.poly(weapon['polygon']);v[share]=b[share]
  else:
   need(weapon['module_sha256']==sha(gun.tobytes())and weapon['translation']==[-2,0],'정본좌표정책')
   for form,arr in(('before',b),('after',v)):
    r=next(r for r in weapon['registrations']if r['form']==form);original=arr.copy();skin=np.zeros_like(arr,bool)
    for x,y,index in r['removed_source_cells']:need(int(original[y+160,x+160])==index,'제거총출처');arr[y+160,x+160]=0
    for x,y,index in r['preserved_skin_cells']:need(int(original[y+160,x+160])==index,'피부손출처');skin[y+160,x+160]=True
    vis=(case>0)&~skin;arr[vis]=case[vis];arr[skin]=original[skin]
   for x,y,index in weapon['common_cells']:need(int(b[y+160,x+160])==index,'공통총/피부손');v[y+160,x+160]=index
  need(np.array_equal(b,pix(D/f'common_probe_v2/before_{n:03}_indices.png'))and np.array_equal(v,pix(D/f'common_probe_v2/after_{n:03}_indices.png')),'공통등록재현');pc=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[b];ls={0:v,5:np.where((b!=v)|pc,b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  for pb,z in ls.items():need(np.array_equal(z,pix(td/f'layer{pb}_{n:03}.png'))and sha(z.tobytes())==m['targets'][str(n)][str(pb)],'10목표층');checked.append([n,pb,sha(z.tobytes())])
 out=td/'source_reconstruction.json';need(not out.exists(),'새출처보고');write(out,{'passed':True,'source_art_sha256':digest(art),'source_cells':cells,'parent_arc_sha256':sha(a.data),'target_manifest_sha256':digest(td/'manifest.json'),'layers_exact':checked,'canonical85_module_sha256':sha(gun.tobytes()),'canonical85_pixels':20,'source_boundary_cells':sum(len(q['source_boundary_links'])for q in cm['frames']),'scope':'자체4생성셀 재양자화와 기록된 홍채/의상/경계19셀·새권총/정본20texel·피부손을 재구성. 독립reader/새MIPS/실기는별도.91은발사후연결모션이며단독발사원점 증명아님.','runtime_verified':False});print(json.dumps({'passed':True,'cells':4,'layers':10,'sha256':digest(out)}))
if __name__=='__main__':main()
