"""생성 12셀과 실제 채택한 국소·공통부 출처를 다시 읽어 20층을 재구성한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
reg=module('source_quantizer',N/'base_run_repaint/register_page.py')
sem=module('source_semantics',N/'ultimate_standing_repaint/prepare_common.py')
def read(p):return json.loads(p.read_text('utf8'))
def pix(p):return np.array(Image.open(p))
def same(z,p):need(np.array_equal(z,pix(p)),'재구성 불일치 '+str(p.relative_to(D)))
def main():
 td=D/'targets_v1';meta=read(td/'manifest.json');parent=ROOT/meta['parent_arc'];need(digest(parent)==meta['parent_arc_sha256'],'부모해시');a=Archive(parent.read_bytes());source={};proof=[]
 pages=[('a_v1','first_registered_v1','c37ac7f6b726f023de0a9f02d963f409983fa58b48c09dfe01e8bd744dd87d29',True),('geometry_v1','geometry_registered_v1','93cbcfe2a60713b77e65742bab4b5a7e460218c229e12a58a4abbc15c4a25b9b',True),('torso98_v1','torso98_registered_v1','96e71c32fa50eaea12a3c9b90c2fa52223364548bd4f858583c7728ba069905a',False),('hand98_v1','hand98_registered_v1','4576b0c9235db167a647732687c74d9642e76bb3a5ac0ae8edfb54c121968e64',False)]
 for name,folder,expected,square in pages:
  path=D/name/'generated.png';need(digest(path)==expected,'생성해시');im=Image.open(path).convert('RGBA');need(im.size==((1254,1254)if square else(1536,1024)),'캔버스 크기')
  for fi,form in enumerate(('before','after')):
   start=16 if form=='before'else 0;pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
   for col,n in enumerate((95,98)if square else(98,)):
    crop=(col*627,fi*627,(col+1)*627,(fi+1)*627)if square else(fi*768,0,(fi+1)*768,1024);z=np.zeros((384,384),np.uint8);y0,y1=(112,208)if square else(96,224);z[y0:y1,112:208]=reg.register(im.crop(crop),(96,y1-y0),pal,'area_vote');same(z,D/f'{folder}/{form}_{n:03}_indices.png');source[name,form,n]=z;proof.append({'page':name,'form':form,'ref':n,'crop':crop,'registered_sha256':sha(z.tobytes())})
 Y,X=np.indices((384,384));Y-=160;X-=160
 gun=a.layer(85)[0];gun=np.where((X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(gun,range(1,10)),gun,0);need(int((gun>0).sum())==20,'정본20');case=np.roll(np.roll(gun,-3,1),1,0)
 contacts=read(D/'contacts_probe_v1/manifest.json');hands=read(D/'hand98_local_probe_v1/manifest.json');registered={};piece_count=0;hand_checks=[]
 for n in(95,98):
  for form in('before','after'):
   if n==95:
    z=np.roll(source['geometry_v1',form,n],-4,0);head=np.roll(source['a_v1',form,n],-1 if form=='before'else 0,0);z[Y<=-15]=head[Y<=-15];same(z,D/f'head_body95_probe_v1/{form}_095_indices.png')
   else:z=source['torso98_v1',form,n].copy()
   q=next(q for q in contacts['records']if q['ref']==n and q['form']==form)
   for piece in q['pieces']:
    original=z.copy();p=np.zeros_like(z);dx,dy=piece['translation']
    for x,y,index in piece['source_cells']:need(int(z[y+160,x+160])==index,'강체조각 출처');p[y+160,x+160]=index;z[y+160,x+160]=0
    dest=np.roll(np.roll(p,dy,0),dx,1);occupied=dest>0;need(int((occupied&(z>0)).sum())==piece['destination_overlap_existing'],'조각겹침');z[occupied]=dest[occupied];piece_count+=1
   if n==98:
    w=q['weapon'];need(w['translation']==[-3,1]and w['canonical_texels']==20,'98 모듈 정책');original=z.copy();skin=np.zeros_like(z,bool)
    for x,y,index in w['gun_removed']:need(int(original[y+160,x+160])==index,'제거 총 표본');z[y+160,x+160]=0
    for x,y,index in w['skin']:need(int(original[y+160,x+160])==index,'손 표본');skin[y+160,x+160]=True
    vis=(case>0)&~skin;z[vis]=case[vis];z[skin]=original[skin]
   same(z,D/f'contacts_probe_v1/{form}_{n:03}_indices.png')
   if n==98:
    h=next(h for h in hands['frames']if h['form']==form);src=source['hand98_v1',form,n];box=(X>=-23)&(X<=-12)&(Y>=-7)&(Y<=2);need(len(h['source_cells'])==int(box.sum()),'손박스 범위')
    for x,y,index in h['source_cells']:need(int(src[y+160,x+160])==index,'새손 원화셀')
    original=z.copy();z[box]=src[box];skin=box&np.isin(src,(10,11,12,13));vis=(case>0)&~skin;z[vis]=case[vis];need(np.array_equal(z[~(box|(case>0))],original[~(box|(case>0))]),'손 밖 원화 보존');need(int(vis.sum())==18 and int(((case>0)&skin).sum())==2,'가림 분리');same(z,D/f'hand98_local_probe_v1/{form}_098_indices.png');hand_checks.append({'form':form,'visible':18,'skin_occluded':2,'outside_exact':True})
   registered[form,n]=z
 cm=read(D/'common_probe_v2/manifest.json');checked=[];boundaries=outline=0;metrics=[]
 for n in(95,98):
  q=next(q for q in cm['frames']if q['ref']==n);b=registered['before',n].copy();v=b.copy();donor=registered['after',n];mask=sem.poly(q['costume_polygon'])
  if n==95:
   cell=Image.open(D/'a_v1/generated.png').convert('RGBA').crop((0,0,627,627));pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
   for e in q['palette15_source']:
    x,y=e['world'];value,votes=sem.source_vote(cell,pal,tuple(e['source_world']),{15});need(value==e['index']and votes==e['votes']and b[y+160,x+160]==15,'팔레트15 실제표본');v[y+160,x+160]=value
  for e in q['source_boundary_links']:
   x,y=e['world'];need(int(b[y+160,x+160])==e['before_index']and int(donor[y+160,x+160])==e['source_after_index'],'의상 경계 출처');mask[y+160,x+160]=True;boundaries+=1
  for e in q['shared_hand_outline_links']:
   x,y=e['world'];need(b[y+160,x+160]==0 and int(donor[y+160,x+160])==e['source_after_index'],'공통손 외곽 출처');b[y+160,x+160]=donor[y+160,x+160];v[y+160,x+160]=donor[y+160,x+160];outline+=1
  v[mask]=donor[mask]
  for x,y,index in q['shared_source_cells']:need(int(b[y+160,x+160])==index,'공통 손/총 표본');v[y+160,x+160]=index
  need(not np.any((v>0)&(b==0)),'재킷 밖 맨팔');same(b,D/f'common_probe_v2/before_{n:03}_indices.png');same(v,D/f'common_probe_v2/after_{n:03}_indices.png')
  for form,z in(('before',b),('after',v)):
   need(label(z>0,np.ones((3,3)))[1]==1,'전신연결');yy,xx=np.nonzero(z);metrics.append({'ref':n,'form':form,'bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-160),int(yy.max()-160)],'opaque':int((z>0).sum())})
  pc=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[b];ls={0:v,5:np.where((b!=v)|pc,b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  for dx in(0,1):
   for pb,z in ls.items():
    value=np.roll(z,dx,1);same(value,td/f'layer{pb}_{n+dx:03}.png');need(sha(value.tobytes())==meta['targets'][str(n+dx)][str(pb)],'20목표해시');checked.append([n+dx,pb,sha(value.tobytes())])
 need(boundaries==53 and outline==1,'의미경계 합계');write(td/'source_reconstruction.json',{'passed':True,'parent_sha256':digest(parent),'target_manifest_sha256':digest(td/'manifest.json'),'generated_fixed_cells_requantized':proof,'registered_cell_count':12,'new_final_body_poses':2,'final_costume_displays':4,'diagnostic_cell_count_is_not_completed_art_count':True,'source_piece_transforms':piece_count,'hand98':hand_checks,'costume_source_boundary_cells':boundaries,'shared_hand_outline_source_cells':outline,'canonical_module_sha256':sha(gun.tobytes()),'canonical98_translation':[-3,1],'body_metrics':metrics,'targets_exact':checked,'x_plus1_all_five_layers':True,'runtime_verified':False,'scope':'12고정셀 재양자화와 채택한 국소 출처의 자체 재구성. 미채택 초기 전체그림은 완료로 세지 않는다. 95는 실제 새 사선권총,98만 정본20표본/피부가림. 최종 독립 reader·원MIPS·원순서·실기는 별도.'});print(json.dumps({'passed':True,'cells':12,'layers':len(checked),'boundary':boundaries,'sha256':digest(td/'source_reconstruction.json')}))
if __name__=='__main__':main()
