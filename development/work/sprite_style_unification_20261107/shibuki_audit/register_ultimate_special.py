"""Ultimate95/97의 네 셀을 전체 캔버스 고정비율로 등록한다."""
from pathlib import Path
import sys
import json
import numpy as np
from PIL import Image
from scipy.ndimage import label

H=Path(__file__).resolve().parent
ROOT=H.parents[2]
sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def main():
    source=H/'ultimate_special_inputs01'
    output=H/'ultimate_special_native01'
    need(not output.exists(),'Fresh native directory required')
    manifest=json.loads((source/'input.json').read_text('utf8'))
    generated=source/'generated.png'
    need(sha(generated.read_bytes())=='7e271d29881fa4907ae274e99dfbcf0c40a71da6d937dcc694cc61659ae6201c','Generated source changed')
    for name,digest in manifest['files'].items():
        need(sha((source/name).read_bytes())==digest,'Input changed '+name)
    parent=ROOT/manifest['parent']['path']
    need(sha(parent.read_bytes())==manifest['parent']['sha256'],'Parent changed')
    archive=Archive(parent.read_bytes())
    original=Image.open(generated).convert('RGBA')
    need(original.size==(1254,1254),'Unexpected generated canvas')
    samples=np.array(original.resize((192,192),Image.Resampling.NEAREST))
    output.mkdir()
    rows=[]
    for col,(form,mask,pal) in enumerate((('before',15,16),('after',0,0))):
        colors=np.array([[(int(w)>>k&31)*255//31 for k in (0,5,10)] for w in archive.words[pal:pal+16]],np.int32)
        figures=[]
        for row,ref in enumerate((95,97)):
            cell=samples[row*96:(row+1)*96,col*96:(col+1)*96]
            values=(1+((cell[:,:,:3].astype('int32')[:,:,None]-colors[None,None,1:])**2).sum(3).argmin(2)).astype('uint8')
            values[cell[:,:,3]<128]=0
            need(not values[0].any() and not values[-1].any() and not values[:,0].any() and not values[:,-1].any(),'Cell edge occupied')
            canvas=np.zeros((384,384),np.uint8)
            canvas[112:208,112:208]=values
            rgba=archive.rgba(canvas,pal)
            Image.fromarray(canvas).save(output/f'{form}_{ref:03}_indices.png')
            rgba.save(output/f'{form}_{ref:03}.png')
            Image.fromarray(cell).save(output/f'{form}_{ref:03}_sample_rgba.png')
            labels,count=label(values>0,np.ones((3,3)))
            old=archive.composite(ref,mask)[0]
            figures.extend([(f'{ref} old',old),(f'{ref} new',rgba)])
            rows.append({'form':form,'ref':ref,'palette_offset':pal,'source_cell':[row,col],
                         'old_metrics':metrics(old),'new_metrics':metrics(rgba),
                         'components':sorted(map(int,np.bincount(labels.flat)[1:]),reverse=True),
                         'index_array_sha256':sha(canvas.tobytes()),'native_rgba_sha256':sha(rgba.tobytes()),
                         'alpha_below128_samples':int(((cell[:,:,3]>0)&(cell[:,:,3]<128)).sum()),
                         'wholebody_translation':[0,0],'local_rescale':False,'old_body_copied':False,
                         'contacts_pending':True,'costume_review_pending':True})
        page(figures,archive.composite(0,mask)[0],output/f'{form}_comparison.png',cols=2,scale=5)
    write(output/'report.json',{'source':generated.relative_to(ROOT).as_posix(),'source_sha256':sha(generated.read_bytes()),
                              'source_size':list(original.size),'fixed_global_scale':192/1254,'logical_cell':[96,96],
                              'origin':[48,48],'native_crop':[112,112,208,208],'alpha_cutoff':128,'rows':rows,
                              'arc_written':False,'visual_review_pending':True,'no_bbox_resize':True,
                              'input_manifest_sha256':sha((source/'input.json').read_bytes())})
    write(source/'generation_receipt.json',{'tool':'builtin imagegen','generated_sha256':sha(generated.read_bytes()),
        'generated_source_path':'<LOCAL_PATH>',
        'prompt_sha256':sha((source/'prompt.txt').read_bytes()),'actual_source_size':list(original.size),
        'inputs_actually_viewed':['edit_target.png','accepted_style.png','old_coordinate_reference.png'],
        'files':manifest['files'],'original_preserved':True})
    print(json.dumps(rows))

if __name__=='__main__':
    main()
