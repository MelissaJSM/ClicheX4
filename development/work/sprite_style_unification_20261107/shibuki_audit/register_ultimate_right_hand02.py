"""새 오른팔104 의상 편집을 고정1/12로 양 원팔레트에 등록한다."""
from pathlib import Path
import sys,json,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_fill_holes
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ref',type=int,default=104,choices=(103,104));args=ap.parse_args();ref=args.ref
    out=H/('rising_ultimate_right_native02'if ref==104 else'rising_ultimate_prepare103_native01');need(not out.exists(),'Fresh output');out.mkdir()
    a=Archive((H/'prepared_rising_fire_ultimate01/PL02_U.ARC').read_bytes());source=H/('rising_ultimate_right_retry02/generated.png'if ref==104 else'rising_ultimate_prepare103/generated.png')
    need(sha(source.read_bytes())==('74a197461566e86697e057233986214a7d2f19695bdb536cfba0584e7480b84b'if ref==104 else'99724204405fe4237a8a19a4deb9388b2526ab586f0c88b6dca7f5e755afc04f'),'Source changed')
    im=Image.open(source).convert('RGBA');need(im.size==(1536,1024),'Layout changed');rows=[]
    for col,form,mask,pal in ((0,'before',15,16),(1,'after',0,0)):
        cell=np.array(im.crop((col*768,128,(col+1)*768,896)).resize((64,64),Image.Resampling.NEAREST))
        rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32)
        q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
        v=np.zeros((384,384),np.uint8);v[124:188,128:192]=q;Image.fromarray(v).save(out/f'{form}_{ref}_indices.png');r=a.rgba(v,pal);r.save(out/f'{form}_{ref}.png')
        lab,n=label(v>0,np.ones((3,3)));sizes=np.bincount(lab.ravel())[1:];need(n==1,'Disconnected source pixels')
        page([(f'{ref} wrong side current',a.composite(ref,mask)[0]),(f'{ref} new right hand + costume',r)],a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
        rows.append({'form':form,'source_sha256':sha(source.read_bytes()),'metrics':metrics(r),'components':int(n),'fixed_native_scale':1/12,'alpha_threshold':128,'old_art_pixels_used':0})
    write(out/'report.json',{'candidate_only':True,'resource_written':False,'rows':rows,'shared_parts_and_contact_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
