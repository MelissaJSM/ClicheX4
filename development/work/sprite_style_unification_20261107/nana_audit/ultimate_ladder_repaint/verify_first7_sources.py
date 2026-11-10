"""첫3 출처검증을 결속하고 별개2의4원화셀/손/반전까지35층을 재구성한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
PBS=(0,5,6,7,8)
def read(p):return json.loads(p.read_text('utf8'))
def pix(p):return np.array(Image.open(p))
def main():
 parent=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';a=Archive(parent.read_bytes());prior=D/'a_layers_probe_v1/source_reconstruction.json';pr=read(prior)
 need(pr['passed']and digest(prior)=='349ef5611be843d4b4cbda39ab854ac66016d0cbc5b694e6de2e5bad39ed40d7','첫3출처 근거')
 for q in pr['files']:need(digest(ROOT/q['path'])==q['sha256'],'앞선검사입력불변')
 quant=N/'base_run_repaint/register_page.py';spec=importlib.util.spec_from_file_location('first7_quantizer',quant);reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
 cm=read(D/'c_common_probe_v2/manifest.json');fm=read(D/'first7_targets_v1/manifest.json');art=D/'c_v1/generated.png';need(digest(art)=='aa7aa49d12931998e969689317333230e75bde9acffb94db6068672a81a7cb12','C원화');im=Image.open(art).convert('RGBA');need(im.size==(1254,1254),'C캔버스');original={};cells=[];checked={}
 for row,form,start in((0,'before',16),(1,'after',0)):
  pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  for col,n in enumerate((154,183)):
   crop=(col*627,row*627,(col+1)*627,(row+1)*627);z=np.zeros((384,384),np.uint8);z[132:196,128:192]=reg.register(im.crop(crop),(64,64),pal,'area_vote');need(np.array_equal(z,pix(D/f'c_registered_v1/{form}_{n:03}_indices.png')),'C4고정셀');original[form,n]=z;cells.append({'ref':n,'form':form,'source_crop':crop,'fixed_native_sha256':sha(z.tobytes())})
 for n in (154,183):
  cq=next(q for q in cm['frames']if q['ref']==n);fq=next(q for q in fm['frames']if q['ref']==n);mask=Image.new('L',(384,384));dr=ImageDraw.Draw(mask)
  for points in cq['costume_polygons']:dr.polygon([(x+160,y+160)for x,y in points],fill=1)
  for x,y in cq['after_ear_accents_source15']:dr.point((x+160,y+160),fill=1)
  m=np.array(mask)>0;b=original['before',n].copy();v=np.where(m,original['after',n],b).astype(np.uint8);fringe=(v>0)&(b==0);need(int(fringe.sum())==len(cq['new_before_boundary_source_links']),'C원표본경계');b[fringe]=v[fringe]
  need(np.array_equal(b,pix(D/f'c_common_probe_v2/before_{n:03}_indices.png'))and np.array_equal(v,pix(D/f'c_common_probe_v2/after_{n:03}_indices.png')),'C공통영역')
  old=v.copy()
  for x0,y0,x1,y1 in fq['shared_new_hand_boxes']:v[y0+160:y1+160,x0+160:x1+160]=b[y0+160:y1+160,x0+160:x1+160]
  need(int((v!=old).sum())==len(fq['shared_new_hand_links']),'C실제 손표본');checked[n]={0:v,5:np.where((b!=v)|(b==15),b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
 for n in (143,144,146):checked[n]={pb:pix(D/f'a_layers_probe_v1/layer{pb}_{n:03}.png')for pb in PBS}
 for sn,tn,k in((144,145,-1),(146,147,0)):
  checked[tn]={}
  for pb,z in checked[sn].items():out=np.zeros_like(z);y,x=np.nonzero(z);out[y,320-x+k]=z[y,x];checked[tn][pb]=out
 for n,ls in checked.items():
  for pb,z in ls.items():need(np.array_equal(z,pix(D/f'first7_targets_v1/layer{pb}_{n:03}.png'))and sha(z.tobytes())==fm['targets'][str(n)][str(pb)],'35목표층출처')
 report={'passed':True,'prior_first3_source_proof':{'path':prior.relative_to(ROOT).as_posix(),'sha256':digest(prior),'source_cells':9},'new_c_source':{'path':art.relative_to(ROOT).as_posix(),'sha256':digest(art),'source_cells':cells},'target_manifest_sha256':digest(D/'first7_targets_v1/manifest.json'),'target_layers_exact':35,'new_body_refs':[143,144,146,154,183],'new_mirror_refs':[145,147],'new_hand_cells':{str(q['ref']):len(q['shared_new_hand_links'])for q in fm['frames']if q['ref']in(154,183)},'scope':'자체 원화출처 재구성. 첫3은불변9셀검증에결속,C4셀은다시양자화. 후보ARC/MIPS/독립/실기 검증은별도. 거부된B원화와7연결참조미처리.','game_asset_written':False}
 p=D/'first7_targets_v1/source_reconstruction.json';write(p,report);print(json.dumps({'passed':True,'layers':35,'source_cells':13,'sha256':digest(p)}))
if __name__=='__main__':main()
