"""생성8셀부터 홍채·손발·의상경계·Y별칭까지 자체 재구성한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
reg=module('vehicle_quantizer',N/'base_run_repaint/register_page.py');sem=module('vehicle_semantics',N/'ultimate_standing_repaint/prepare_common.py')
def read(p):return json.loads(p.read_text('utf8'))
def same(z,p):need(np.array_equal(z,np.array(Image.open(p))),'출처 재구성 '+str(p.relative_to(D)))
def main():
 td=D/'targets_v1';m=read(td/'manifest.json');p=ROOT/m['parent_arc'];need(digest(p)==m['parent_arc_sha256'],'부모해시');a=Archive(p.read_bytes());source={};cells={};palettes={};proof=[]
 expected={'a':'a6d59e2e066a36bb9d16f538a6e02d3794558fc14ccf99768e1471df9f943fe3','b':'b9b344d270cd6b6c8a404e35d19b1b0876199b70aadf70a5c5a1e44604898d08'}
 for page,ns in(('a',(162,166)),('b',(170,174))):
  path=D/f'{page}_v1/generated.png';need(digest(path)==expected[page],'생성 해시');im=Image.open(path).convert('RGBA');need(im.size==(1254,1254),'고정 전체 캔버스')
  for row,form in enumerate(('before','after')):
   start=16 if row==0 else 0;pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[start:start+16]],np.float32);palettes[form]=pal
   for col,n in enumerate(ns):
    box=(col*627,row*627,(col+1)*627,(row+1)*627);cell=im.crop(box);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(cell,(96,96),pal,'area_vote');same(z,D/f'{page}_registered_v1/{form}_{n:03}_indices.png');source[form,n]=z;cells[form,n]=cell;proof.append({'ref':n,'form':form,'source_sha256':digest(path),'crop':box,'registered_sha256':sha(z.tobytes())})
 cm=read(D/'contacts_probe_v1/manifest.json');contact={};eye_count=pieces=0
 for q in cm['frames']:
  form,n=q['form'],q['ref'];z=source[form,n].copy();need(sha(z.tobytes())==q['source_sha256'],'등록 source hash')
  for e in q['iris_source_registration']:
   x,y=e['world'];need(z[y+160,x+160]==14,'겹친 홍채 출처');value,votes=sem.source_vote(cells[form,n],palettes[form],(x,y),{14,15});need(value==e['value']and votes==e['votes'],'홍채 아래 실제 원화표본');z[y+160,x+160]=value;xx,yy=e['original_iris_preserved_at'];need(z[yy+160,xx+160]==14,'원점 홍채 유지');eye_count+=1
  for r in q['rigid_pieces']:
   t=r['data'];piece=np.zeros_like(z)
   for x,y,index in t['source_cells']:need(int(z[y+160,x+160])==index,'손발 조각 원화');piece[y+160,x+160]=index;z[y+160,x+160]=0
   dx,dy=t['translation'];dst=np.roll(np.roll(piece,dy,0),dx,1);hit=dst>0;need(int((hit&(z>0)).sum())==t['overlap'],'강체 겹침');z[hit]=dst[hit];pieces+=1
  same(z,D/f'contacts_probe_v1/{form}_{n:03}_indices.png');need(sha(z.tobytes())==q['target_sha256'],'접점 hash');contact[form,n]=z
 common=read(D/'common_probe_v2/manifest.json');boundary=palette_count=0;targets=[];metrics=[]
 for q in common['frames']:
  n=q['ref'];b=contact['before',n].copy();donor=contact['after',n];v=b.copy();mask=sem.poly(q['polygon'])
  for e in q['palette15_source']:
   x,y=e['world'];value,votes=sem.source_vote(cells['before',n],palettes['after'],(x,y),{15});need(b[y+160,x+160]==15 and value==e['index']and votes==e['votes'],'후폼 팔레트15 의미 표본');v[y+160,x+160]=value;palette_count+=1
  for e in q['source_boundary_links']:
   x,y=e['world'];need(int(b[y+160,x+160])==e['before_index']and int(donor[y+160,x+160])==e['after_source_index'],'의상 경계 actual source');mask[y+160,x+160]=True;boundary+=1
  v[mask]=donor[mask]
  for x,y,index in q['shared_hand_cells']:need(int(b[y+160,x+160])==index,'손 원화 공유');v[y+160,x+160]=index
  need(not np.any((v>0)&(b==0))and not q['alpha_clipped'],'후폼 밖 알파 없음/클립 안함');same(b,D/f'common_probe_v2/before_{n:03}_indices.png');same(v,D/f'common_probe_v2/after_{n:03}_indices.png')
  for form,z in(('before',b),('after',v)):
   need(label(z>0,np.ones((3,3)))[1]==1,'전신 연결');yy,xx=np.nonzero(z);metrics.append({'ref':n,'form':form,'bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)],'opaque':int((z>0).sum())})
  pc=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[b];ls={0:v,5:np.where((b!=v)|pc,b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  for frame in m['frames']:
   if frame['source_key']!=n:continue
   dx,dy=frame['translation'];need(dx==0,'Y only')
   for pb,z in ls.items():
    zz=np.roll(z,dy,0);same(zz,td/f'layer{pb}_{frame["ref"]:03}.png');need(sha(zz.tobytes())==m['targets'][str(frame['ref'])][str(pb)],'65층 hash');targets.append([frame['ref'],pb,sha(zz.tobytes())])
 need(len(proof)==8 and eye_count==4 and boundary==18 and len(targets)==65,'검증 범위');write(td/'source_reconstruction.json',{'passed':True,'parent_sha256':digest(p),'target_manifest_sha256':digest(td/'manifest.json'),'generated_fixed_cells_requantized':proof,'registered_cell_count':8,'new_body_poses':4,'final_costume_displays':8,'iris_source_samples':eye_count,'rigid_source_pieces':pieces,'palette15_source_samples':palette_count,'costume_source_boundary_cells':boundary,'body_metrics':metrics,'targets_exact':targets,'derived_y_aliases':9,'old_after_exact_restoration_claimed':False,'runtime_verified':False,'scope':'실제 생성8고정셀 재양자화부터 표본/국소강체/의상경계와 원Y별칭65층을 자체 재구성했다. 독립 reader·원MIPS·실기는 별도.'});print(json.dumps({'passed':True,'cells':8,'layers':65,'iris':eye_count,'pieces':pieces,'boundary':boundary,'sha256':digest(td/'source_reconstruction.json')}))
if __name__=='__main__':main()
