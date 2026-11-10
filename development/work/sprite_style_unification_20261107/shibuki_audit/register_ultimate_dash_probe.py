"""얼티밋 대시 새 의상 페이지를 원래 CLUT/고정64셀로만 등록한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,required=True);ap.add_argument('--source-sha',required=True);ap.add_argument('--out',required=True);ap.add_argument('--original-filename',required=True);z=ap.parse_args();d=H/'ultimate_dash_inputs01';metadata=json.loads((d/'manifest.json').read_text('utf8'));refs=metadata['pages'][z.page-1];src=d/f'page{z.page:02}/generated.png';need(sha(src.read_bytes())==z.source_sha,'Source changed');u=ROOT/metadata['ultimate_parent']['path'];need(sha(u.read_bytes())==metadata['ultimate_parent']['sha256'],'Parent changed');a=Archive(u.read_bytes());b=Archive((ROOT/metadata['base_pose']['path']).read_bytes());out=(H/z.out).resolve();need(out.is_relative_to(H.resolve())and out!=H.resolve()and not out.exists(),'Fresh own output');im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Wrong fixed-cell layout');full=np.array(im);sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));out.mkdir();rows=[]
    for row,(form,mask,pal)in enumerate((('before',15,16),('after',0,0))):
        rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for col,n in enumerate(refs):
            cell=sample[row*64:(row+1)*64,col*64:(col+1)*64];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0;v=np.zeros((384,384),np.uint8);v[124:188,128:192]=q;rgba=a.rgba(v,pal);Image.fromarray(v).save(out/f'{form}_{n:03}_indices.png');rgba.save(out/f'{form}_{n:03}.png');lab,cnt=label(q>0,np.ones((3,3)));sizes=sorted(np.bincount(lab.ravel())[1:].tolist(),reverse=True);part=full[row*512:(row+1)*512,col*512:(col+1)*512];old=a.composite(n,mask)[0];pose=b.composite(n,0)[0];pics.extend([(f'{n} old',old),(f'{n} new fixed64',rgba)]);rows.append({'form':form,'ref':n,'palette_start':pal,'old':metrics(old),'pose_reference':metrics(pose),'new':metrics(rgba),'components':sizes,'low_alpha_excluded':int(((part[:,:,3]>0)&(part[:,:,3]<128)).sum()),'old_pixels_reused':0,'translation':[0,0],'scaling_after_fixed_1_over_8':False})
        page(pics,a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
    prompt=(src.parent/'prompt.txt').read_text('utf8').strip();(src.parent/'prompt_used.txt').write_text(prompt,encoding='utf8');write(src.parent/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':z.original_filename,'source_sha256':z.source_sha,'prompt_sha256':sha(prompt.encode()),'inputs':{str(p.relative_to(H)):sha(p.read_bytes())for p in(src.parent/'new_pose_reference.png',d/'accepted_ultimate_style.png',src.parent/'current_ultimate_reference.png')},'source_alpha_retained':True})
    write(out/'report.json',{'source':src.relative_to(ROOT).as_posix(),'source_sha256':z.source_sha,'parent_sha256':metadata['ultimate_parent']['sha256'],'native_scale':0.125,'alpha_threshold':128,'rows':rows,'common_head_limbs_and_costume_registration_pending':True,'artifact':'native registration probe','arc_written':False,'gameplay_verified':False});print(json.dumps({'out':str(out),'rows':[{'ref':r['ref'],'form':r['form'],'bbox':r['new']['bbox'],'components':r['components']}for r in rows]}))
if __name__=='__main__':main()
