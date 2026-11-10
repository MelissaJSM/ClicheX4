"""233/234 새 원화를 고정1/8 셀·원팔레트로 등록한다. ARC/기존그림 불변."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def main():
    s=H/'hurt_inputs01/page02';p=s/'generated.png';expected=sha(p.read_bytes())
    original=Path('<LOCAL_PATH>')
    need(sha(original.read_bytes())==expected,'Project copy mismatch')
    o=H/'hurt_native02';need(not o.exists(),'Fresh native');o.mkdir();im=Image.open(p).convert('RGBA');need(im.size==(1536,1024),'Wrong fixed page')
    sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));a=Archive((H/'prepared_base_run01/PL00_U.ARC').read_bytes());rows=[]
    need(sha(a.data)=='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce','Parent mismatch')
    for row,(form,pal,mask) in enumerate([('base',0,0),('fourth',16,15)]):
        rgb=np.array([[(int(w)>>ss&31)*255//31 for ss in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for col,n in enumerate((233,234)):
            cell=sample[row*64:(row+1)*64,col*96:(col+1)*96];q=(1+((cell[:,:,:3].astype('int32')[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');q[cell[:,:,3]<128]=0
            v=np.zeros((384,384),np.uint8);v[128:192,112:208]=q;new=a.rgba(v,pal);Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');new.save(o/f'{form}_{n:03}.png')
            l,count=label(q>0,np.ones((3,3)));sizes=np.bincount(l.flat)[1:];old=a.composite(n,mask)[0]
            rows.append({'form':form,'ref':n,'old_metrics':metrics(old),'new_metrics':metrics(new),'source_scale':0.125,'alpha_cutoff':128,'native_components_8way':int(count),'component_sizes':sorted(map(int,sizes),reverse=True),'semi_alpha_samples_below128':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'native_opaque_samples':int((q>0).sum()),'component_or_art_pixels_deleted':False,'wholebody_translation':[0,0],'wholebody_rescale':False,'old_body_overlay':False,'coordinate_alignment_pending':True});pics.extend([(f'{n} old {form}',old),(f'{n} new {form}',new)])
        page(pics,a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
    write(o/'report.json',{'source_sha256':expected,'input_manifest_sha256':sha((s/'input.json').read_bytes()),'parent_sha256':sha(a.data),'rows':rows,'palette_changed':False,'fixed_page_registration':True,'arc_written':False,'visual_review_pending':True,'joint_alignment_pending':True})
    write(s/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':original.name,'generated_sha256':expected,'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'input_images':{n:sha((s/n).read_bytes())for n in('pose_reference.png','accepted_style_reference.png')},'original_preserved':True,'project_copy':p.relative_to(ROOT).as_posix()})
    print(json.dumps(rows))
if __name__=='__main__':main()
