"""새 얼티밋 대시 사격 팔만 등록하고 원총구/얼굴/다리 보호를 검사한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_dash_body_layers import rect
from register_dash_shot_page import REMOVED,FACE,palette
from prepare_dash_shot_inputs import GROUPS,SHOULDER
from probe_ultimate_dash_common01 import poly

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,required=True);ap.add_argument('--sha',required=True);ap.add_argument('--out',required=True);ap.add_argument('--original-filename',required=True);ap.add_argument('--preserve-palm-outline',type=int,choices=(0,1),default=0);z=ap.parse_args();src=H/f'ultimate_dash_shot_inputs01/page{z.page:02}';p=src/'generated.png';need(sha(p.read_bytes())==z.sha,'Source hash changed');o=(H/z.out).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh own output');a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes());bodydir=H/'ultimate_dash_contacts04';gdir=H/'ultimate_dash_barrel_guard01';gmeta=json.loads((gdir/'report.json').read_text('utf8'));im=Image.open(p).convert('RGBA');need(im.size==(1536,1024),'Wrong layout');full=np.array(im);sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));o.mkdir();rows=[];pairs={};palm_rows={};y,x=np.indices((384,384))
    for row,(form,pal,equip)in enumerate((('before',16,15),('after',0,0))):
        colors=palette(a,pal);pics=[]
        for col,n in enumerate(GROUPS[z.page-1]):
            cell=sample[row*64:(row+1)*64,col*96:(col+1)*96];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0;donor=np.zeros((384,384),np.uint8);donor[124:188,112:208]=q;body=np.array(Image.open(bodydir/f'{form}_{n:03}_indices.png'));gm=next(r for r in gmeta['rows']if r['body_ref']==n and r['form']==form);mx,my=gm['muzzle_world'];sx,sy=SHOULDER[n];added=[(mx+7,my-3),(sx-6,my-3),(sx+3,sy-3),(sx+3,sy+5),(sx-6,sy+8),(mx+7,my+7)];face=rect(FACE[n]);legs=np.array(Image.open(bodydir/f'{n:03}_legs_mask.png'))>0;head=np.array(Image.open(bodydir/f'{n:03}_head_mask.png'))>0;patch=(poly(REMOVED[n])|(poly(added)&(x>=160+mx+8)))&~face&~legs
            if n==77:patch&=~rect((-12,11,24,32))
            if n==81:patch|=rect((-15,-3,-5,5));patch&=~rect((-6,6,24,32))
            gun=np.array(Image.open(gdir/f'{n+1:03}_indices.png'));guard=np.array(Image.open(gdir/f'{n+1:03}_mask.png'))>0;target=body.copy();target[patch]=donor[patch];target[guard]=gun[guard]
            band=(x>=160+mx+8)&(x<160+mx+12)&(y>=160+my-4)&(y<160+my+5);skin=band&np.isin(donor,[12,13]);yy,xx=np.nonzero(skin);need(len(yy)>0,'No source palm below barrel')
            if form=='before':palm_rows[n]=int(yy.min())
            ring=band&(y<palm_rows[n]-z.preserve_palm_outline)&~guard;protected=ring&(body>0);need(np.all(head[protected]),'Ring crosses non-head body');target[protected]=body[protected];patch&=~protected;ring&=~protected;target[ring]=0;allowed=patch|guard|ring
            need(np.array_equal(target[~allowed],body[~allowed]),'Body outside arm changed');need(np.array_equal(target[face&~guard],body[face&~guard]),'Face changed');need(np.array_equal(target[legs&~guard],body[legs&~guard]),'Legs changed');need(np.array_equal(target[guard],gun[guard]),'Canonical barrel changed')
            outside=[]
            if form=='after':
                for py,px in zip(*np.nonzero((target>0)&(pairs[n]==0))):
                    block=full[(py-124)*8:(py-124)*8+8,(px-112)*8+col*768:(px-112)*8+col*768+8];opaque=block[:,:,3]>=128;outside.append({'world':[int(px-160),int(py-160)],'after_index':int(target[py,px]),'before_source_opaque_samples':int(opaque.sum())})
            else:pairs[n]=target.copy()
            for name,v in(('source',donor),('indices',target)):Image.fromarray(v).save(o/f'{form}_{n+1:03}_{name}.png')
            a.rgba(target,pal).save(o/f'{form}_{n+1:03}.png')
            for name,v in(('patch',patch),('allowed',allowed),('ring',ring),('face',face)):Image.fromarray(v.astype(np.uint8)*255).save(o/f'{form}_{n+1:03}_{name}_mask.png')
            occupied=target>0;lab,cnt=label(occupied,np.ones((3,3),int));sizes=sorted([int((lab==i).sum())for i in range(1,cnt+1)],reverse=True);contact=binary_dilation(gun>0,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&occupied&~guard
            rows.append({'form':form,'ref':n+1,'body_ref':n,'palette_start':pal,'muzzle_world':[mx,my],'components8':sizes,'barrel_adjacent_pixels':[[int(px-160),int(py-160)]for py,px in zip(*np.nonzero(contact))],'after_outside_before':outside,'changed_arm_pixels':int(np.count_nonzero(target!=body)),'head_face_protected':True,'leg_exact':True,'body_outside_arm_exact':True,'canonical_barrel_exact':True});pics.extend([(f'{n} new {form} body',a.rgba(body,pal)),(f'{n+1} fixed gun new arm',a.rgba(target,pal))])
        page(pics,a.composite(0,equip)[0],o/f'{form}_comparison.png',cols=2,scale=5)
    prompt=(src/'prompt.txt').read_text('utf8').strip();(src/'prompt_used.txt').write_text(prompt,encoding='utf8');write(src/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':z.original_filename,'source_sha256':z.sha,'prompt_sha256':sha(prompt.encode()),'inputs':{n:sha((src/n).read_bytes())for n in('edit_target.png','arm_guide.png')},'source_size':list(im.size)})
    write(o/'report.json',{'parent_sha256':sha(a.data),'source_sha256':z.sha,'page':z.page,'scale':.125,'alpha_threshold':128,'preserved_palm_source_outline_rows':z.preserve_palm_outline,'rows':rows,'candidate_only':True,'alpha_corrections_applied':False,'visual_review_pending':True,'packed':False,'gameplay_verified':False});print(json.dumps(rows))
if __name__=='__main__':main()
