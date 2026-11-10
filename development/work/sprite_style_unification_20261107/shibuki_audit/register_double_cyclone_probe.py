"""두 원화 페이지를 전역 1/8, 기존 CLUT로 읽고 체형/접점 차이를 숨기지 않는다."""
from pathlib import Path
import sys,json,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
import numpy as np
from scipy.ndimage import label
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ultimate-source',default='double_cyclone_inputs02/page02/generated.png');ap.add_argument('--out',default='double_cyclone_native01');args=ap.parse_args();o=(H/args.out).resolve();need(o.is_relative_to(H.resolve())and o!=H.resolve(),'Output outside work');need(not o.exists(),'Fresh output required');o.mkdir();rows=[]
    specs=[('base',1,0,'prepared_air01/PL00_U.ARC',0,0),('fourth',1,1,'prepared_air01/PL00_U.ARC',15,16),('ultimate_before',2,0,'prepared_ultimate_wall01/PL02_U.ARC',15,16),('ultimate_after',2,1,'prepared_ultimate_wall01/PL02_U.ARC',0,0)]
    for form,pn,col,resource,mask,pal in specs:
        src=H/args.ultimate_source if pn==2 else H/f'double_cyclone_inputs02/page{pn:02}/generated.png';im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Unexpected page resolution');small=np.array(im.resize((192,128),Image.Resampling.NEAREST));cell=small[:,col*96:(col+1)*96];a=Archive((H/resource).read_bytes());colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32)
        q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
        v=np.zeros((384,384),np.uint8);v[96:224,112:208]=q;Image.fromarray(v).save(o/f'{form}_098_indices.png');native=a.rgba(v,pal);native.save(o/f'{form}_098.png');old=a.composite(98,mask)[0];idle=a.composite(0,mask)[0]
        p=o/f'{form}_comparison.png';page([('98 old',old),('98 new 1/8',native)],idle,p,cols=2,scale=5)
        components,count=label(q>0,np.ones((3,3)));sizes=sorted(np.bincount(components.ravel())[1:].tolist(),reverse=True)
        rows.append({'form':form,'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src.read_bytes()),'source_size':list(im.size),'scale':0.125,'alpha_threshold':128,'palette_row':pal//16,'no_local_resize':True,'old_head_or_limb_copied':False,'native_rgba_sha256':sha(native.tobytes()),'source_index_sha256':sha(v.tobytes()),'idle':metrics(idle),'old98':metrics(old),'new98':metrics(native),'components':sizes,'native_review_status':'not_final','contact_guard_pending':True})
    write(o/'report.json',{'rows':rows,'game_or_arc_written':False,'whole_body_resize':False,'source_alpha_preserved':True,'visual_review_pending':True})
    print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
