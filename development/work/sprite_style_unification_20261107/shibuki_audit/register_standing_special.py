"""95/97 생성 네셀을 캔버스 전체 고정비율로 원 CLUT에 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
 s=H/'standing_special_inputs01';o=H/'standing_special_native01';need(not o.exists(),'Fresh native');p=s/'generated.png';need(sha(p.read_bytes())=='d181854943171a73a803b323c3015416f5cbe4a8045ed05001cdd2cbbc1320cd','Generated changed');m=json.loads((s/'input.json').read_text('utf8'));pp=ROOT/m['parent']['path'];need(sha(pp.read_bytes())==m['parent']['sha256'],'Parent changed')
 for name,h in m['files'].items():need(sha((s/name).read_bytes())==h,'Input changed '+name)
 a=Archive(pp.read_bytes());im=Image.open(p).convert('RGBA');need(im.size==(1254,1254),'Unexpected source');sample=np.array(im.resize((192,192),Image.Resampling.NEAREST));o.mkdir();rows=[];forms={}
 for col,(form,mask,pal)in enumerate((('base',0,0),('fourth',15,16))):
  colors=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);figs=[]
  for row,n in enumerate((95,97)):
   cell=sample[row*96:(row+1)*96,col*96:(col+1)*96];q=(1+((cell[:,:,:3].astype('int32')[:,:,None]-colors[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');q[cell[:,:,3]<128]=0;need(not q[0].any()and not q[-1].any()and not q[:,0].any()and not q[:,-1].any(),'Edge occupied');v=np.zeros((384,384),np.uint8);v[112:208,112:208]=q;rgba=a.rgba(v,pal);Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');rgba.save(o/f'{form}_{n:03}.png');lab,count=label(q>0,np.ones((3,3)));old=a.composite(n,mask)[0];figs.extend([(f'{n} old',old),(f'{n} new',rgba)]);feet={}
   for side,(lo,hi)in{'left':(-20,0),'right':(0,20)}.items():
    reg=v[170:190,160+lo:160+hi];ys,xs=np.nonzero(reg);feet[side]=None if not len(xs)else{'bbox':[int(xs.min())+lo,int(ys.min())+10,int(xs.max())+lo+1,int(ys.max())+11],'opaque':len(xs)}
   rows.append({'form':form,'ref':n,'palette_offset':pal,'source_cell':[row,col],'old_metrics':metrics(old),'new_metrics':metrics(rgba),'components':sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True),'index_array_sha256':sha(v.tobytes()),'native_rgba_sha256':sha(rgba.tobytes()),'feet_split_x0_y10':feet,'alpha_below128_samples':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'wholebody_translation':[0,0],'local_rescale':False,'old_body_copied':False,'contacts_pending':True})
  page(figs,a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
 write(o/'report.json',{'source':str(p.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(p.read_bytes()),'source_size':list(im.size),'requested_size':[1536,1536],'fixed_global_scale':192/1254,'logical_cell':[96,96],'origin':[48,48],'native_crop':[112,112,208,208],'alpha_cutoff':128,'rows':rows,'arc_written':False,'visual_review_pending':True,'no_bbox_resize':True,'input_manifest_sha256':sha((s/'input.json').read_bytes())});write(s/'generation_receipt.json',{'tool':'builtin imagegen','generated_sha256':sha(p.read_bytes()),'generated_source_path':'<LOCAL_PATH>','prompt_sha256':sha((s/'prompt.txt').read_bytes()),'actual_source_size':list(im.size),'inputs_actually_viewed':['edit_target.png','accepted_style.png','coordinate_reference.png'],'files':m['files'],'original_preserved':True});print(json.dumps(rows))
if __name__=='__main__':main()
