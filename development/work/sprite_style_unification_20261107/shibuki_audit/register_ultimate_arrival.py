"""Ultimate 등장 의상 편집의 고정96셀 등록. 몸체 확대/구형머리 덮기 없음."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='ultimate_hurt_inputs01/page01');ap.add_argument('--sha',default='b6b8209011257ad7b959c087149f89e79cf032ee52bbfb7bc1d68a7aa8605b52');ap.add_argument('--refs',default='106,110');ap.add_argument('--output',default='ultimate_hurt_native01');z=ap.parse_args()
    s=H/z.source;p=s/'generated.png';need(sha(p.read_bytes())==z.sha,'Art changed');o=H/z.output;need(o.resolve().is_relative_to(H.resolve())and not o.exists(),'Fresh native');meta=json.loads((s/'input.json').read_text('utf8'));parent=ROOT/meta['ultimate_parent']['path'];need(sha(parent.read_bytes())==meta['ultimate_parent']['sha256'],'Parent changed');a=Archive(parent.read_bytes());refs=list(map(int,z.refs.split(',')));need(len(refs)==2,'Two fixed columns')
    im=Image.open(p).convert('RGBA');need(im.size==(1536,1024),'Wrong fixed page');sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));o.mkdir();rows=[]
    for row,(form,pal,mask)in enumerate((('before',16,15),('after',0,0))):
        rgb=np.array([[(int(w)>>ss&31)*255//31 for ss in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for col,n in enumerate(refs):
            cell=sample[row*64:(row+1)*64,col*96:(col+1)*96];q=(1+((cell[:,:,:3].astype('int32')[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');q[cell[:,:,3]<128]=0;v=np.zeros((384,384),np.uint8);v[128:192,112:208]=q;new=a.rgba(v,pal);Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');new.save(o/f'{form}_{n:03}.png');lab,count=label(q>0,np.ones((3,3)));sizes=np.bincount(lab.flat)[1:];old=a.composite(n,mask)[0]
            rows.append({'form':form,'ref':n,'old_metrics':metrics(old),'new_metrics':metrics(new),'native_components_8way':int(count),'component_sizes':sorted(map(int,sizes),reverse=True),'semi_alpha_samples_below128':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'native_opaque_samples':int((q>0).sum()),'index_array_sha256':sha(v.tobytes()),'component_or_art_pixels_deleted':False,'wholebody_translation':[0,0],'wholebody_rescale':False,'old_body_overlay':False,'common_head_limbs_contacts_pending':True});pics.extend([(f'{n} old {form}',old),(f'{n} new {form}',new)])
        page(pics,a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
    write(o/'report.json',{'source_sha256':z.sha,'input_manifest_sha256':sha((s/'input.json').read_bytes()),'parent_sha256':sha(a.data),'source_scale':0.125,'alpha_cutoff':128,'rows':rows,'palette_changed':False,'fixed_page_registration':True,'arc_written':False,'visual_review_pending':True,'joint_alignment_pending':True})
    input_names=['edit_target.png','accepted_ultimate_style.png','old_coordinate_reference.png']
    if(s/'previous_page_reference.png').exists():input_names.append('previous_page_reference.png')
    write(s/'generation_receipt.json',{'tool':'builtin imagegen','generated_sha256':z.sha,'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'input_images':{n:sha((s/n).read_bytes())for n in input_names},'original_preserved':True,'project_copy':p.relative_to(ROOT).as_posix()})
    print(json.dumps([{'form':r['form'],'ref':r['ref'],'bbox':r['new_metrics']['bbox'],'components':r['component_sizes']}for r in rows]))
if __name__=='__main__':main()
