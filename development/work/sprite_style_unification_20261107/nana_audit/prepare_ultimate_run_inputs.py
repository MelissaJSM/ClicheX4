"""얼티밋 이동32의 현재 실제 조립과 새 기본형 동작틀을 분리해 수집한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path[:0]=[str(ROOT),str(D/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
def merged(a,n,mask):
 z=a.layer(n,0)[0].copy()
 if mask:
  for pb in(8,5,7,6):
   p=a.layer(n,pb)[0];z[p>0]=p[p>0]
 return z
def main():
 ultimate=D/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';base=D/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';need(digest(ultimate)=='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031','Frozen Ultimate');need(digest(base)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','Frozen basic');a=Archive(ultimate.read_bytes());b=Archive(base.read_bytes());out=D/'ultimate_run_repaint/inputs_first_v1';out.mkdir(parents=True,exist_ok=False);keys=(1,7,15,25);window=(112,112,208,208);reports=[]
 for name,arc,mask,refs in(('old_before_targets',a,15,keys),('new_basic_motion_only',b,0,keys),('before_accepted_style',a,15,(0,85,39,55)),('after_accepted_style',a,0,(0,85,39,55))):
  sheet=Image.new('RGBA',(1536,1536))
  for i,n in enumerate(refs):
   im=arc.composite(n,mask)[0];outside=np.array(im)[:,:,3].copy();outside[112:208,112:208]=0;need(not outside.any(),'Input crop');sheet.alpha_composite(im.crop(window).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768));reports.append({'sheet':name,'ref':n,'mask':mask,'rgba_sha256':sha(np.array(im).tobytes())})
  sheet.save(out/f'{name}.png')
 records=[]
 for n in range(1,33):
  layers={pb:a.layer(n,pb)[0]for pb in(0,5,6,7,8)}
  for mask,form in((15,'before'),(0,'after')):
   im=a.composite(n,mask)[0];im.save(out/f'{form}_{n:03}_rgba.png');v=merged(a,n,mask);Image.fromarray(v).save(out/f'{form}_{n:03}_indices.png');yy,xx=np.nonzero(v);Y,X=np.indices(v.shape);ey,ex=np.nonzero((v==14)&(Y<170));records.append({'ref':n,'form':form,'stream_offset':a.banks[0]['frames'][n]['offset'],'tile_count':a.banks[0]['frames'][n]['tile_count'],'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'sole_y':int(yy.max()-160),'eye_world':[float(np.median(ex))-160,float(np.median(ey))-160]if len(ex)else None,'layer_index_sha256':{str(pb):sha(ar.tobytes())for pb,ar in layers.items()},'rgba_sha256':sha(np.array(im).tobytes())})
 for i,refs in enumerate(((1,7),(15,25))):helper.grid([(f'run {n}',[('Ultimate idle',a.composite(0,15)[0]),('current Ultimate',a.composite(n,15)[0]),('accepted basic motion / costume differs',b.composite(n,0)[0])])for n in refs],out/f'input_comparison_{i+1}.png',6)
 write(out/'manifest.json',{'source_arc':ultimate.relative_to(ROOT).as_posix(),'source_arc_sha256':digest(ultimate),'basic_motion_reference_arc':base.relative_to(ROOT).as_posix(),'basic_motion_reference_sha256':digest(base),'full_scope':list(range(1,33)),'first_keys':list(keys),'input_native_window_world':[-48,-48,48,48],'cell_pixels':768,'sheet_pixels':1536,'native_scale':8,'records':records,'image_references':reports,'inputs':{p.name:digest(p)for p in out.glob('*.png')},'authority':'대기는얼티밋 의상/얼굴 기준. 기본형은 동작 흐름/세밀도만 참조하며 검정의상과부츠를 복사하지 않음.','new_art_generated':False,'runtime_verified':False});print(str(out))
if __name__=='__main__':main()
