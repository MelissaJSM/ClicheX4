"""90/91 새 네 표시를 고정 전체 캔버스 배율로 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def main():
    source=H/'standing_fire_inputs02';out=H/'standing_fire_followthrough_native01'
    need(not out.exists(),'Fresh registration')
    m=json.loads((source/'input.json').read_text('utf8'));g=source/'generated.png'
    need(sha(g.read_bytes())=='bb22eb089d41f7a8154241dd6619612e375bdc55943797d473d479e5c1f034f4','Source changed')
    for n,d in m['files'].items():need(sha((source/n).read_bytes())==d,'Input changed '+n)
    p=ROOT/m['parent']['path'];need(sha(p.read_bytes())==m['parent']['sha256'],'Parent changed');a=Archive(p.read_bytes())
    original=Image.open(g).convert('RGBA');need(original.size==(1254,1254),'Unexpected canvas')
    samples=np.array(original.resize((192,192),Image.Resampling.NEAREST));rows=[];out.mkdir()
    for col,(form,mask,pal) in enumerate((('base',0,0),('fourth',15,16))):
        colors=np.array([[(int(w)>>k&31)*255//31 for k in (0,5,10)]for w in a.words[pal:pal+16]],np.int32);fig=[]
        for row,n in enumerate((90,91)):
            cell=samples[row*96:(row+1)*96,col*96:(col+1)*96]
            ind=(1+((cell[:,:,:3].astype('int32')[:,:,None]-colors[None,None,1:])**2).sum(3).argmin(2)).astype('uint8');ind[cell[:,:,3]<128]=0
            need(not(ind[0].any()or ind[-1].any()or ind[:,0].any()or ind[:,-1].any()),'Cell clipped')
            canvas=np.zeros((384,384),np.uint8);canvas[112:208,112:208]=ind;im=a.rgba(canvas,pal)
            Image.fromarray(canvas).save(out/f'{form}_{n:03}_indices.png');im.save(out/f'{form}_{n:03}.png');Image.fromarray(cell).save(out/f'{form}_{n:03}_sample_rgba.png')
            labs,count=label(ind>0,np.ones((3,3)));old=a.composite(n,mask)[0]
            rows.append({'form':form,'ref':n,'palette_offset':pal,'source_cell':[row,col],'old_metrics':metrics(old),'new_metrics':metrics(im),'components':sorted(map(int,np.bincount(labs.flat)[1:]),reverse=True),'index_array_sha256':sha(canvas.tobytes()),'native_rgba_sha256':sha(im.tobytes()),'alpha_below128_samples':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),'wholebody_translation':[0,0],'local_rescale':False,'old_body_copied':False,'contacts_pending':True,'costume_review_pending':True})
            fig.extend([(f'{n} old',old),(f'{n} new',im)])
        page(fig,a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
    write(out/'report.json',{'source':g.relative_to(ROOT).as_posix(),'source_sha256':sha(g.read_bytes()),'source_size':list(original.size),'fixed_global_scale':192/1254,'logical_cell':[96,96],'origin':[48,48],'native_crop':[112,112,208,208],'alpha_cutoff':128,'rows':rows,'arc_written':False,'visual_review_pending':True,'no_bbox_resize':True,'input_manifest_sha256':sha((source/'input.json').read_bytes())})
    write(source/'generation_receipt.json',{'tool':'builtin imagegen','generated_sha256':sha(g.read_bytes()),'generated_source_path':'<LOCAL_PATH>','prompt_sha256':sha((source/'prompt.txt').read_bytes()),'actual_source_size':list(original.size),'inputs_actually_viewed':['edit_target.png','new_style_reference.png','coordinate_reference.png'],'files':m['files'],'original_preserved':True})
    print(json.dumps(rows))
if __name__=='__main__':main()
