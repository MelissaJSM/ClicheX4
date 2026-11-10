"""첫3의 고정 원화9셀부터15목표층을 다시 읽어 출처를 검증한다. 자원 쓰기 없음."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def poly(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
def read(p):return np.array(Image.open(p))
def main():
 parent=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';a=Archive(parent.read_bytes())
 path=N/'base_run_repaint/register_page.py';spec=importlib.util.spec_from_file_location('source_quantizer',path);reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
 meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));arms=json.loads((D/'a_arm_registered_v1/manifest.json').read_text('utf8'));commons=json.loads((D/'a_common_probe_v1/manifest.json').read_text('utf8'));grips=json.loads((D/'a_grip_probe_v1/manifest.json').read_text('utf8'))
 fullart=D/'a_v1/generated.png';armart=D/'a_arm_v1/generated.png';fullim=Image.open(fullart).convert('RGBA');armim=Image.open(armart).convert('RGBA');need(fullim.size==armim.size==(1536,1024),'고정 전체캔버스')
 need(digest(fullart)=='4052c6ab0ca0555234ee44f2258f92c7c29d05f69734b54ddc1dbe26fa1888ce','첫원화');need(digest(armart)=='63e74beea1bccb9ba4714a455f9c36284c6770125da980b269c86d4d4de2e8ed','허용된 팔원화')
 fixed={};cells=[];checks=[]
 def quant(im,cell,palette):
  col,row=cell%3,cell//3;crop=(col*512,row*512,(col+1)*512,(row+1)*512)
  pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[palette:palette+16]],np.float32)
  z=np.zeros((384,384),np.uint8);z[124:188,128:192]=reg.register(im.crop(crop),(64,64),pal,'area_vote');return z,crop
 for q in meta['frames']:
  form,n=q['form'],q['ref'];z,crop=quant(fullim,q['cell'],16 if form=='before' else 0);need(np.array_equal(z,read(D/f'a_registered_v1/{form}_{n:03}_indices.png')),'첫원화 고정셀 재현');fixed[form,n]=z
  cells.append({'source':'a_v1/generated.png','cell':q['cell'],'crop':crop,'form':form,'ref':n,'indexed_sha256':sha(z.tobytes())})
 for col,n in enumerate(meta['refs']):
  arm=next(q for q in arms['frames']if q['ref']==n);common=next(q for q in commons['frames']if q['ref']==n);grip=next(q for q in grips['frames']if q['ref']==n)
  donor,crop=quant(armim,col+3,0);need(np.array_equal(donor,read(D/f'a_arm_registered_v1/after_donor_{n:03}_indices.png')),'팔원화 고정셀 재현');cells.append({'source':'a_arm_v1/generated.png','cell':col+3,'crop':crop,'form':'after_arm_donor','ref':n,'indexed_sha256':sha(donor.tobytes())})
  arm_mask=poly(arm['native_polygon']);v=np.where(arm_mask,donor,fixed['after',n]).astype(np.uint8);b=fixed['before',n].copy();need(np.array_equal(v,read(D/f'a_arm_registered_v1/after_{n:03}_indices.png')),'팔국소출처')
  cm=np.zeros_like(v,bool)
  for points in common['polygons']:cm|=poly(points)
  v=np.where(cm,v,b).astype(np.uint8);fringe=(v>0)&(b==0)
  expected_links={(int(x-160),int(y-160),int(v[y,x]))for y,x in np.argwhere(fringe)}
  actual_links={(q['world'][0],q['world'][1],q['index'])for q in common['new_before_boundary_links']};need(expected_links==actual_links,'실제 원화 경계 표본 목록');b[fringe]=v[fringe]
  need(np.array_equal(b,read(D/f'a_common_probe_v1/before_{n:03}_indices.png'))and np.array_equal(v,read(D/f'a_common_probe_v1/after_{n:03}_indices.png')),'공통사지 출처')
  x0,y0,x1,y1=grip['source_box_world'];window=(slice(y0+160,y1+160),slice(x0+160,x1+160));old=v.copy();v[window]=b[window]
  need(not np.isin(b[window],(5,6,7,8,9,15)).any(),'손창은 피부/어두운 커프만')
  need(np.array_equal(b,read(D/f'a_grip_probe_v1/before_{n:03}_indices.png'))and np.array_equal(v,read(D/f'a_grip_probe_v1/after_{n:03}_indices.png')),'실제손 공유 재현')
  ls={0:v,5:np.where((b!=v)|(b==15),b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  for pb,z in ls.items():need(np.array_equal(z,read(D/f'a_layers_probe_v1/layer{pb}_{n:03}.png')),'최종15목표층 출처')
  checks.append({'ref':n,'source_boundary_cells':len(expected_links),'source_hand_changed_cells':int((old!=v).sum()),'target_layers_exact':5,'old_body_copied':False,'new_source_body_outside_costume_exact':True})
 files=[parent,fullart,armart,path,D/'a_inputs_v1/manifest.json',D/'a_arm_registered_v1/manifest.json',D/'a_common_probe_v1/manifest.json',D/'a_grip_probe_v1/manifest.json',D/'a_layers_probe_v1/manifest.json']
 out=D/'a_layers_probe_v1/source_reconstruction.json';write(out,{'passed':True,'scope':'허용된 첫3의9고정원화셀/공통사지/경계/손15층 자체 출처 재구성. 별도독립검사가 아니며 ARC·MIPS·실기·나머지사다리는 범위 밖. 거부된 B의상은 읽거나 수정하지 않는다.','files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in files],'source_cells':cells,'frames':checks,'old_body_copied':False,'game_asset_written':False});print(json.dumps({'passed':True,'source_cells':len(cells),'layers':15,'sha256':digest(out)}))
if __name__=='__main__':main()
