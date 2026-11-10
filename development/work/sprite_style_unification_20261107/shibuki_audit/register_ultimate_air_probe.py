"""새 얼티밋 공중 원화를 고정 1/8과 원래 두 CLUT로 등록한다."""
from pathlib import Path
import sys,json,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scipy.ndimage import label
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,required=True);ap.add_argument('--source-sha',required=True);ap.add_argument('--out',required=True);args=ap.parse_args();d=H/'ultimate_air_inputs01';metadata=json.loads((d/'manifest.json').read_text('utf8'));refs=metadata['page_keys'][args.page-1];src=d/f'page{args.page:02}/generated.png';need(sha(src.read_bytes())==args.source_sha,'Wrong generated input');p=ROOT/metadata['ultimate_parent'];data=p.read_bytes();need(sha(data)==metadata['ultimate_parent_sha256'],'Wrong parent');a=Archive(data);out=(H/args.out).resolve();need(out.is_relative_to(H.resolve())and out!=H.resolve()and not out.exists(),'Fresh owned output required');im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Wrong generated layout');full=np.array(im);sm=np.array(im.resize((192,128),Image.Resampling.NEAREST));out.mkdir();rows=[]
    for row,(form,mask,pal)in enumerate([('before',15,16),('after',0,0)]):
        rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for col,n in enumerate(refs):
            cell=sm[row*64:row*64+64,col*64:col*64+64];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0;v=np.zeros((384,384),np.uint8);v[124:188,128:192]=q;native=a.rgba(v,pal);Image.fromarray(v).save(out/f'{form}_{n:03}_indices.png');native.save(out/f'{form}_{n:03}.png');old=a.composite(n,mask)[0];lab,_=label(q>0,np.ones((3,3)));sizes=sorted(np.bincount(lab.ravel())[1:].tolist(),reverse=True);part=full[row*512:(row+1)*512,col*512:(col+1)*512];pics.extend([(f'{n} old',old),(f'{n} new fixed scale',native)])
            rows.append({'form':form,'ref':n,'native_index_sha256':sha(v.tobytes()),'palette_start':pal,'old':metrics(old),'new':metrics(native),'idle':metrics(a.composite(0,mask)[0]),'connected_components':sizes,'alpha_threshold':128,'source_low_alpha_discarded':int(((part[:,:,3]>0)&(part[:,:,3]<128)).sum()),'old_pixels_pasted':0,'native_registration_shift':[0,0],'local_or_bbox_scaling':False})
        page(pics,a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
    write(out/'report.json',{'source':src.relative_to(ROOT).as_posix(),'source_sha256':args.source_sha,'source_size':list(im.size),'parent_sha256':metadata['ultimate_parent_sha256'],'native_scale':0.125,'native_origin':[160,160],'world_crop':[-32,-36,32,28],'rows':rows,'joint_contact_and_common_source_pending':True,'artifact':'native_registration_probe','arc_or_game_written':False,'user_accepted':False});print(json.dumps([{'form':r['form'],'ref':r['ref'],'old':r['old']['bbox'],'new':r['new']['bbox'],'connected':r['connected_components']}for r in rows]))
if __name__=='__main__':main()
