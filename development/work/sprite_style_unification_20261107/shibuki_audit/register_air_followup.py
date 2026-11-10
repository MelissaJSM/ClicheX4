"""공중 후속 시트를 동일 셀배율·팔레트로 읽는다. 자동 몸체 리사이즈 없음."""
from pathlib import Path
import argparse,sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,choices=(2,3,4),required=True);args=ap.parse_args()
    D=H/f'air_detail_inputs{args.page:02}';O=H/f'air_detail_native{args.page:02}';need(not O.exists(),'Fresh output required')
    info=json.loads((D/'manifest.json').read_text('utf8'));data=(ROOT/info['parent']).read_bytes();need(sha(data)==info['parent_sha256'],'Wrong parent');a=Archive(data)
    src=D/'generated.png';im=Image.open(src).convert('RGBA');cols=info['layout']['cols'];width=cols*64;scale=im.width/width;nh=round(im.height/scale)
    need(nh==128,'Generated image aspect ratio changed');sample=np.array(im.resize((width,nh),Image.Resampling.NEAREST));O.mkdir();rows=[]
    for row,(form,mask,pal) in enumerate([('base',0,0),('fourth',15,16)]):
        colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);items=[]
        for col,n in enumerate(info['refs']):
            cell=sample[row*64:(row+1)*64,col*64:(col+1)*64];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
            arr=np.zeros((384,384),np.uint8);arr[124:188,128:192]=q;name=f'{form}_{n:03}'
            Image.fromarray(arr).save(O/f'{name}_indices.png');rgba=a.rgba(arr,pal);rgba.save(O/f'{name}.png')
            yy,xx=np.nonzero(arr);old=a.composite(n,mask)[0];oy,ox=np.nonzero(np.array(old)[:,:,3])
            rows.append({'form':form,'ref':n,'native_png':str((O/f'{name}_indices.png').relative_to(ROOT)),
                         'sha256':sha((O/f'{name}_indices.png').read_bytes()),'translation':[0,0],
                         'before_bbox_world':[int(ox.min()-160),int(oy.min()-160),int(ox.max()+1-160),int(oy.max()+1-160)],
                         'after_bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],
                         'original_foot_y':int(oy.max()-160),'new_foot_y':int(yy.max()-160),'old_head_or_body_copied':False})
            items.extend([(f'{n} old air',old),(f'{n} new fixed-scale source',rgba)])
        page(items,a.composite(0,mask)[0],O/f'{form}_comparison.png',cols=2,scale=4)
    write(O/'registration.json',{'parent_sha256':sha(data),'source_sha256':sha(src.read_bytes()),'source_scale':1/scale,
                                'source_size':list(im.size),'native_layout':[width,nh],'alpha_threshold':128,
                                'source_palette_bytes_unchanged':True,'rows':rows,'no_old_body_overwrite':True,
                                'contact_alignment_pending':True,'art_review_pending':True,'no_resource_written':True})
    print(json.dumps({'output':str(O),'rows':rows}))
if __name__=='__main__':main()
