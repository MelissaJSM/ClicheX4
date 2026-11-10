"""새 사다리 원화를 고정1/8·원CLUT로 등록. 원화세부/몸체 평행크기 유지."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--sha',required=True);ap.add_argument('--out',required=True);ap.add_argument('--refs',default='143,144,146');args=ap.parse_args();refs=list(map(int,args.refs.split(',')));need(1<=len(refs)<=3,'Wrong column count')
    src=H/args.source;out=H/args.out;need(out.resolve().is_relative_to(H.resolve())and not out.exists(),'Fresh own output');need(sha(src.read_bytes())==args.sha,'Source changed')
    meta=json.loads((H/'ultimate_ladder_inputs01/manifest.json').read_text('utf8'));paths=list(meta['source_archives']); bp,up=[ROOT/p for p in paths]
    for p in(bp,up):need(sha(p.read_bytes())==meta['source_archives'][p.relative_to(ROOT).as_posix()],'Reference changed')
    base=Archive(bp.read_bytes());ult=Archive(up.read_bytes());im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Wrong fixed canvas');raw=np.array(im);sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));out.mkdir();rows=[]
    for row,(form,mask,pal)in enumerate((('before',15,16),('after',0,0))):
        rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in ult.words[pal:pal+16]],np.int32);pics=[]
        for col,n in enumerate(refs):
            c=sample[row*64:(row+1)*64,col*64:(col+1)*64]
            q=(1+((c[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[c[:,:,3]<128]=0
            v=np.zeros((384,384),np.uint8);v[128:192,128:192]=q
            rgba=ult.rgba(v,pal);Image.fromarray(v).save(out/f'{form}_{n:03}_indices.png');rgba.save(out/f'{form}_{n:03}.png')
            lab,_=label(q>0,np.ones((3,3)));sizes=sorted(np.bincount(lab.ravel())[1:].tolist(),reverse=True)
            old=ult.composite(n,mask)[0];pose=base.composite(n,0)[0];pics.extend([(f'{n} old',old),(f'{n} new fixed64',rgba)])
            rows.append({'form':form,'ref':n,'palette_start':pal,'old':metrics(old),'pose_reference':metrics(pose),'new':metrics(rgba),'components':sizes,'index_array_sha256':sha(v.tobytes()),'old_pixels_reused':0,'translation':[0,0],'scaling_after_fixed_1_over_8':False})
        page(pics,ult.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
    write(out/'report.json',{'source':src.relative_to(ROOT).as_posix(),'source_sha256':args.sha,'sources':meta['source_archives'],'scale':0.125,'alpha_threshold':128,'origin_in_cell':[32,32],'rows':rows,'source_alpha_preserved':True,'whole_image_scaling_to_bbox':False,'old_head_copy':False,'packed':False,'back_head_sunglasses_review_required':True,'common_head_limbs_contacts_pending':True,'runtime_verified':False})
    print(json.dumps({'out':str(out),'rows':[{'form':r['form'],'ref':r['ref'],'bbox':r['new']['bbox'],'components':r['components']}for r in rows]}))
if __name__=='__main__':main()
