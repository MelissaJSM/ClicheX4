"""156 두셀 원화 전체 고정1/8 등록. 원그림/비율을 덮거나 변형하지 않는다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',default='ultimate_return_inputs01');ap.add_argument('--output',default='ultimate_return_native01');ap.add_argument('--sha',required=True);z=ap.parse_args();s=H/z.source;o=H/z.output;need(not o.exists(),'Fresh native output');p=s/'generated.png';need(sha(p.read_bytes())==z.sha,'Generated source changed');m=json.loads((s/'input.json').read_text('utf8'));pp=ROOT/m['ultimate_parent']['path'];need(sha(pp.read_bytes())==m['ultimate_parent']['sha256'],'Parent changed')
 for name,h in m['files'].items():need(sha((s/name).read_bytes())==h,'Input changed '+name)
 layout=m['source_layout'];need(layout['size']==[1536,1024]and layout['native_cell']==[96,128]and layout['native_origin']==[48,64]and layout['crop']==[112,96,208,224],'Layout mismatch');a=Archive(pp.read_bytes());im=Image.open(p).convert('RGBA');need(im.size==(1536,1024),'Wrong generated dimensions');samples=np.array(im.resize((192,128),Image.Resampling.NEAREST));o.mkdir();rows=[]
 for col,(form,pal,mask)in enumerate((('before',16,15),('after',0,0))):
  rgb=np.array([[(int(w)>>ss&31)*255//31 for ss in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);cell=samples[:,col*96:(col+1)*96];q=(1+((cell[:,:,:3].astype('int32')[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');q[cell[:,:,3]<128]=0;need(not q[0].any()and not q[-1].any()and not q[:,0].any()and not q[:,-1].any(),'Cell edge occupied');v=np.zeros((384,384),np.uint8);v[96:224,112:208]=q;rgba=a.rgba(v,pal);Image.fromarray(v).save(o/f'{form}_156_indices.png');rgba.save(o/f'{form}_156.png');lab,count=label(q>0,np.ones((3,3)));old=a.composite(156,mask)[0];page([('156 old '+form,old),('156 new '+form,rgba)],a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
  feet={}
  for side,(x0,x1)in{'left':(-18,0),'right':(0,18)}.items():
   region=v[170:190,160+x0:160+x1];ys,xs=np.nonzero(region);feet[side]={'bbox':[int(xs.min())+x0,int(ys.min())+10,int(xs.max())+x0+1,int(ys.max())+11],'opaque':len(xs)}if len(xs)else None
  rows.append({'form':form,'ref':156,'old_metrics':metrics(old),'new_metrics':metrics(rgba),'native_components_8way':int(count),'component_sizes':sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True),'feet_split_x0_y10':feet,'semi_alpha_samples_below128':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'native_opaque_samples':int((q>0).sum()),'index_array_sha256':sha(v.tobytes()),'wholebody_translation':[0,0],'wholebody_rescale':False,'old_body_overlay':False,'common_contacts_pending':True})
 write(o/'report.json',{'source_sha256':z.sha,'input_manifest_sha256':sha((s/'input.json').read_bytes()),'parent_sha256':sha(a.data),'source_scale':.125,'alpha_cutoff':128,'fixed_crop':layout['crop'],'native_origin':layout['native_origin'],'rows':rows,'palette_changed':False,'arc_written':False,'visual_review_pending':True});write(s/'generation_receipt.json',{'tool':'builtin imagegen','generated_sha256':z.sha,'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'input_images':{n:sha((s/n).read_bytes())for n in m['files']if n.endswith('.png')},'original_preserved':True,'project_copy':p.relative_to(ROOT).as_posix()});print(json.dumps(rows))
if __name__=='__main__':main()
