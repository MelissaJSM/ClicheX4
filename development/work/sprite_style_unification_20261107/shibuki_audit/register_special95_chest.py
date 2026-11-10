"""새 포스95 가슴 표본만 고정셀로 합성하고 그 밖의 새 원화는 보존한다."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
 s=H/'standing_special95_chest01';src=s/'generated.png';need(sha(src.read_bytes())=='d2833dcbaa9f52826c77c722347720832b25c8097b45c6ae512f99c108eac3a8','Donor changed');d=H/'standing_special_native01';o=H/'standing_special_native02';need(not o.exists(),'Fresh native');a=Archive((H/'prepared_hurt_base01/PL00_U.ARC').read_bytes());im=Image.open(src).convert('RGBA');need(im.size==(1254,1254),'Source size');cell=np.array(im.resize((192,192),Image.Resampling.NEAREST))[:96,96:192];colors=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[16:32]],np.int32);q=(1+((cell[:,:,:3].astype('int32')[:,:,None]-colors[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');q[cell[:,:,3]<128]=0;v=np.zeros((384,384),np.uint8);v[112:208,112:208]=q;old=np.array(Image.open(d/'fourth_095_indices.png'));yy,xx=np.indices(v.shape);x=xx-160;y=yy-160;roi=(x>=-10)&(x<6)&(y>=-3)&(y<10);out=old.copy();out[roi]=v[roi];need(np.array_equal(out[~roi],old[~roi]),'Protected art changed');need(not np.any((old>0)&(out==0)&roi),'Donor opened a gap');o.mkdir()
 for f in('base','fourth'):
  pics=[]
  for n in(95,97):
   idx=out if(f,n)==('fourth',95)else np.array(Image.open(d/f'{f}_{n:03}_indices.png'));Image.fromarray(idx).save(o/f'{f}_{n:03}_indices.png');rgba=a.rgba(idx,16 if f=='fourth'else 0);rgba.save(o/f'{f}_{n:03}.png');pics.extend([(f'{n} old',a.composite(n,15 if f=='fourth'else 0)[0]),(f'{n} new',rgba)])
  page(pics,a.composite(0,15 if f=='fourth'else 0)[0],o/f'{f}_comparison.png',cols=2,scale=5)
 Image.fromarray(v).save(o/'fourth95_donor_indices.png');Image.fromarray(roi.astype('uint8')*255).save(o/'donor_region.png');page([('95 first red chest',a.rgba(old,16)),('95 new chest sample',a.rgba(v,16)),('95 local result',a.rgba(out,16)),('95 protected area',a.rgba(np.where(~roi,out,0),16))],a.composite(0,15)[0],o/'chest_comparison.png',cols=2,scale=5);write(o/'report.json',{'source_sha256':sha(src.read_bytes()),'source_size':list(im.size),'global_scale':192/1254,'alpha':128,'source_native_report_sha256':sha((d/'report.json').read_bytes()),'changed_pixels':int((old!=out).sum()),'donor_roi_world':[-10,-3,6,10],'outside_roi_exact':True,'head_arms_legs_other3_preserved':True,'body_metrics':metrics(a.rgba(out,16)),'indices_sha256':sha(out.tobytes()),'contacts_and_partial_layers_pending':True,'arc_written':False});write(s/'generation_receipt.json',{'tool':'builtin imagegen','source_builtin':'<LOCAL_PATH>','generated_sha256':sha(src.read_bytes()),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'inputs_actually_viewed':['edit_target.png','accepted_style.png','region_guide.png']});print(json.dumps({'changed':int((old!=out).sum()),'report':sha((o/'report.json').read_bytes())}))
if __name__=='__main__':main()
