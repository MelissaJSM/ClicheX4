"""새 기본/포스 이동 첫6표시 고정1/8·원팔레트 등록 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
def main():
    d=H/'base_run_followup02';o=H/'base_run_native01';need(not o.exists(),'Fresh output');meta=json.loads((d/'manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent']).read_bytes());need(sha(a.data)==meta['parent_sha256'],'Parent changed');p=d/'generated.png';s='4937d67682025bb9a2b940e9b6fa009e0c816666bffce654e7d93cfc6bc12b30';need(sha(p.read_bytes())==s,'Source changed');im=Image.open(p).convert('RGBA');need(im.size==(1536,1024),'Fixed cell mismatch');sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));o.mkdir();rows=[]
    for row,(form,mask,pal)in enumerate((('base',0,0),('fourth',15,16))):
        rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for col,n in enumerate(meta['first_new_keys']):
            cell=sample[row*64:(row+1)*64,col*64:(col+1)*64];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0;v=np.zeros((384,384),np.uint8);v[124:188,128:192]=q;Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');new=a.rgba(v,pal);new.save(o/f'{form}_{n:03}.png');old=a.composite(n,mask)[0];yy,xx=np.nonzero(v);oy,ox=np.nonzero(np.array(old)[:,:,3]);ll,count=label(v>0,np.ones((3,3),int));sizes=sorted([int(np.count_nonzero(ll==i))for i in range(1,count+1)],reverse=True);rows.append({'form':form,'ref':n,'palette_start':pal,'bbox_before':[int(ox.min()-160),int(oy.min()-160),int(ox.max()+1-160),int(oy.max()+1-160)],'bbox_new':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'foot_before':int(oy.max()-160),'foot_new':int(yy.max()-160),'components8':sizes,'old_body_pixels_overwritten':0});pics.extend([(f'{n} current',old),(f'{n} new fixed1/8',new)])
        page(pics,a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
    prompt=(d/'prompt.txt').read_text('utf8').strip();(d/'prompt_used.txt').write_text(prompt,'utf8');write(d/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':'exec-902d4b7e-e047-407e-86c6-acfc616cd84e.png','source_sha256':s,'source_size':list(im.size),'prompt_sha256':sha(prompt.encode()),'inputs':{n:sha((d/n).read_bytes())for n in('edit_target.png','accepted_style.png')}});write(o/'report.json',{'source_sha256':s,'parent_sha256':sha(a.data),'scale':.125,'alpha_threshold':128,'rows':rows,'old_art_overwrite':False,'palette_changed':False,'contact_alignment_pending':True,'partial_layers_pending':True,'art_review_pending':True,'gameplay_verified':False});print(json.dumps(rows))
if __name__=='__main__':main()
