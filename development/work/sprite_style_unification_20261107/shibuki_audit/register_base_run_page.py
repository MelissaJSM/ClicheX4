"""연속 이동 페이지를 고정 1/8·원 팔레트로 등록한다."""
from pathlib import Path
import argparse,sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',required=True,choices=['page02','page03','page04','page05']);ap.add_argument('--sha',required=True);ap.add_argument('--original-name',required=True);args=ap.parse_args();d=H/'base_run_inputs01'/args.page;o=H/f'base_run_{args.page}_native01';need(not o.exists(),'Fresh output');meta=json.loads((d/'manifest.json').read_text('utf8'));p=ROOT/meta['parent'];need(sha(p.read_bytes())==meta['parent_sha256'],'Parent changed');a=Archive(p.read_bytes());need(sha((d/'generated.png').read_bytes())==args.sha,'Source changed');im=Image.open(d/'generated.png').convert('RGBA');need(im.size==(1536,1024),'Fixed cells differ');sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));o.mkdir();rows=[]
    for row,(form,mask,pal)in enumerate((('base',0,0),('fourth',15,16))):
        rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for col,n in enumerate(meta['refs']):
            cell=sample[row*64:(row+1)*64,col*64:(col+1)*64];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0;v=np.zeros((384,384),np.uint8);v[124:188,128:192]=q;Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');new=a.rgba(v,pal);new.save(o/f'{form}_{n:03}.png');old=a.composite(n,mask)[0];yy,xx=np.nonzero(v);oy,ox=np.nonzero(np.array(old)[:,:,3]);labels,count=label(v>0,np.ones((3,3),int));sizes=sorted([int(np.count_nonzero(labels==i))for i in range(1,count+1)],reverse=True)
            rows.append({'form':form,'ref':n,'palette_start':pal,'bbox_before':[int(ox.min()-160),int(oy.min()-160),int(ox.max()+1-160),int(oy.max()+1-160)],'bbox_new':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'sole_before':int(oy.max()-160),'sole_new':int(yy.max()-160),'components8':sizes,'all_source_pixels_above128_used':True,'old_art_pixels_copied':0});pics.extend([(f'{n} current',old),(f'{n} new fixed1/8',new)])
        page(pics,a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
    prompt=(d/'prompt.txt').read_text('utf8').strip();(d/'prompt_used.txt').write_text(prompt,'utf8');write(d/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':args.original_name,'source_sha256':args.sha,'source_size':list(im.size),'prompt_sha256':sha(prompt.encode()),'inputs':{name:sha((d/name).read_bytes())for name in('edit_target.png','accepted_style.png','new_detail_reference.png')}})
    write(o/'report.json',{'parent_sha256':sha(a.data),'source_sha256':args.sha,'rows':rows,'alpha_threshold':128,'scale':.125,'old_head_or_body_copied':False,'palette_changed':False,'whole_body_resized':False,'contact_alignment_pending':True,'partial_layers_pending':True,'runtime_verified':False});print(json.dumps(rows))
if __name__=='__main__':main()
