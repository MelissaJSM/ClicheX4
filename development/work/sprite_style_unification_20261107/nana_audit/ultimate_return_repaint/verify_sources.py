"""귀환 생성2장3셀·의상40셀·원화경계1셀·효과파생의 제작자 재구성."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,need
from pack_native import PARENT,BEFORE,REFS,PBS
spec=importlib.util.spec_from_file_location('source_quantizer',N/'base_run_repaint/register_page.py');reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
read=lambda p:json.loads(p.read_text('utf8'))
def check(z,p):need(np.array_equal(z,np.array(Image.open(p))),str(p));return z
def poly(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
def shift(z,dy):
 t=np.zeros_like(z);y,x=np.nonzero(z);t[y+dy,x]=z[y,x];return t

def main():
 out=D/'packed_return_candidate_v1';lock=read(out/'INPUT_FROZEN.json')
 for q in lock['files']:need(digest(ROOT/q['path'])==q['sha256'],'고정입력 '+q['path'])
 a=Archive(PARENT.read_bytes());bodies={};cells=[]
 art=D/'body_v1/generated.png';im=Image.open(art).convert('RGBA')
 for q in read(D/'body_registered_v1/registration.json')['frames']:
  form=q['form'];start=16 if form=='before'else 0;pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
  z=np.zeros((384,384),np.uint8);z[96:224,112:208]=reg.register(im.crop(q['source_crop']),(96,128),pal,'area_vote');bodies[form]=check(z,D/f'body_registered_v1/{form}_156_indices.png');cells.append({'form':form,'art_sha256':digest(art),'crop':q['source_crop'],'native_sha256':sha(z.tobytes())})
 m=read(D/'costume_pair_probe_v2/manifest.json');local=ROOT/m['local_art'];li=Image.open(local).convert('RGBA');pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
 z=np.zeros((384,384),np.uint8);z[96:224,112:208]=reg.register(li.crop(m['local_fixed_source_crop']),(96,128),pal,'area_vote');donor=np.zeros_like(z);donor[:,4:]=z[:,:-4];check(donor,D/'costume_pair_probe_v2/waist_donor_156.png')
 b=bodies['before'].copy();initial=bodies['after'];boundary=m['original_source_boundary'];need(len(boundary)==1,'국소경계1')
 for q in boundary:
  x0,y0,x1,y1=q['source_native_sample_rect'];cell=np.array(im)[y0:y1,x0:x1];opaque=cell[:,:,3]>=128;need(int(opaque.sum())==q['opaque_samples']==30,'실제30표본');rgb=np.median(cell[:,:,:3][opaque],axis=0);idx=int(np.argmin(np.sum((pal[1:]-rgb)**2,axis=1)))+1;need(idx==q['index']==1,'표본색1');x,y=q['world'];need(b[y+160,x+160]==0,'전경경계');b[y+160,x+160]=idx
 wm=poly(m['waist_polygon']);cm=poly(m['costume_polygon']);after_source=np.where(wm,donor,initial).astype(np.uint8);need(np.count_nonzero(after_source!=initial)==40,'국소의상40');af=np.where(cm,after_source,np.where(b==15,13,b)).astype(np.uint8)
 check(b,D/'costume_pair_probe_v2/before_156.png');check(af,D/'costume_pair_probe_v2/after_156.png')
 tm=read(D/'final_targets_v1/manifest.json');hp=ROOT/tm['historical_arc'];need(digest(hp)==tm['historical_arc_sha256'],'역사ARC');h=Archive(hp.read_bytes());energy=h.layer(159)[0];need(int((energy>0).sum())==1875,'역사빛');check(energy,D/'final_targets_v1/original_energy159_indices.png')
 energy_map=np.array([0,5,6,7,8,5,6,7,8,9,8,9,13,13,9,9],np.uint8);targets={}
 for f,z in(('before',b),('after',af)):
  targets[f,156]=z;t=shift(z,-1);mask=t>0;inner=binary_dilation(mask,np.ones((3,3)),iterations=1);outer=binary_dilation(mask,np.ones((3,3)),iterations=2);targets[f,157]=np.where(mask,t,np.where(inner,7,np.where(outer,13,0))).astype(np.uint8)
  t=shift(z,-10);targets[f,158]=np.where(t>0,energy_map[t%16],energy).astype(np.uint8)
 count=0
 for n in REFS:
  b,af=targets['before',n],targets['after',n];need(not np.any((af>0)&(b==0)),'알파포함');ls={0:af,5:np.where((b!=af)|(b==15),b,0).astype(np.uint8),6:np.zeros_like(b),7:np.zeros_like(b),8:np.zeros_like(b)}
  for pb,z in ls.items():check(z,D/f'final_targets_v1/layer{pb}_{n:03}.png');count+=1
 write(out/'source_reconstruction.json',{'passed':True,'candidate_sha256':digest(out/'PL02_U.ARC'),'parent_sha256':BEFORE,'input_files_verified':len(lock['files']),'generated_pages':2,'fixed_body_cells':cells,'fixed_local_costume_cells':1,'local_art_sha256':digest(local),'local_costume_replaced_indices':40,'actual_source_boundary_cells':1,'target_layers_reconstructed':count,'original_energy_pixels':1875,'old_body_alpha_clipped':False,'old_guard_cell_reapplied':False,'scope':'제작자 원화RGB→고정셀·의상/실제경계→15층 재구성. 독립reader/원MIPS/실기와별도.','runtime_verified':False});print(json.dumps({'passed':True,'fixed_cells':3,'layers':count}))
if __name__=='__main__':main()
