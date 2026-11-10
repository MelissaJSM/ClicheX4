"""새 벽 사격팔만 원점 등록하고 새 몸/머리와 기존 총구를 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from register_ultimate_lowhp_pilot import move

O=H/'ultimate_wall_shots_native04';P=H/'prepared_ultimate_lowhp01/PL02_U.ARC'
HASHES={1:'ee58257b69f507ca21ce13040d74d02d026e209d4bbf8157cab07eff09e4ef16',2:'e8cc55354b31a63ab555d3c6d2626c0b3c879b3c2aaad418ce173fbbe7950e69'}
HEADS={55:[(-15,-25),(12,-25),(12,-5),(6,-4),(-1,-4),(-4,-5),(-8,-5),(-11,-7),(-14,-11)],57:[(-13,-25),(12,-25),(12,-5),(5,-4),(-4,-4),(-7,-6),(-10,-8),(-12,-12)],59:[(-12,-25),(12,-25),(12,-6),(7,-4),(-3,-4),(-8,-7),(-12,-10)]}
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def exact_indices(a,im,start):
    palette=np.array(a.rgba(np.arange(16,dtype=np.uint8).reshape(1,16),start)).reshape(16,4)
    pixels=np.array(im);result=np.zeros(pixels.shape[:2],np.uint8);ok=np.zeros(result.shape,bool)
    for i,c in enumerate(palette):m=np.all(pixels==c,axis=2);result[m]=i;ok|=m
    need(ok.all(),'Original barrel has colors outside this form palette');return result
def main():
    need(not O.exists(),'Fresh registration required');O.mkdir();(O/'before').mkdir();(O/'after').mkdir()
    a=Archive(P.read_bytes());rows=[];poses={};sources={}
    info=json.loads((H/'ultimate_wall_inputs01/manifest.json').read_text('utf8'))
    for page_number,refs in((1,(55,57,59)),(2,(61,63,65))):
        D=H/f'ultimate_wall_shot_inputs{page_number:02}';ip=D/'generated.png';need(sha(ip.read_bytes())==HASHES[page_number],'Source changed')
        im=Image.open(ip).convert('RGBA');need(im.size==(1536,1024),'Unexpected sheet size');pix=np.array(im.resize((192,128),Image.Resampling.NEAREST));sources[page_number]={'sha256':sha(ip.read_bytes()),'size':im.size,'alpha_threshold':128,'background_corner_alpha':int(np.array(im)[0,0,3])}
        for row,(form,start,mask)in enumerate((('before',16,15),('after',0,0))):
            rgb=np.array([[(int(v)>>s&31)*255//31 for s in(0,5,10)]for v in a.words[start:start+16]],np.int32)
            for col,n in enumerate(refs):
                bp=H/('ultimate_wall_contacts_probe01'if n<61 else'ultimate_wall_page02_contacts01')/form/f'{n:03}_indices.png';body=np.array(Image.open(bp))
                px=pix[row*64:(row+1)*64,col*64:(col+1)*64];idx=(1+((px[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);idx[px[:,:,3]<128]=0
                source=np.zeros_like(body);source[120:184,128:192]=idx;unshifted=source.copy()
                dy=-2 if n in(57,59)else 0
                source=move(source,0,dy)
                r=next(v for v in info['refs']if v['body_ref']==n);mx,my=r['original_muzzle_world'];x0,y0,x1,y1=r['barrel_rect_world']
                sx=-4 if n<61 else 3
                oldarm=poly([(-16,-10),(-8,-10),(sx,-4),(sx,1),(sx-4,3),(-12,3),(-16,0)])
                newarm=poly([(mx+7,my-3),(sx-2,my-3),(sx+2,-5),(sx+2,0),(sx-3,1),(mx+7,my+6)])
                head=poly(HEADS[n])if n<61 else(np.array(Image.open(H/'ultimate_wall_raised_native01'/f'{n:03}_head_mask.png'))>0)
                oldarm&=~head;newarm&=~head;edit=oldarm|newarm
                br=np.zeros_like(edit);br[y0+160:y1+160,x0+160:x1+160]=True
                cleanup=np.zeros_like(edit);cleanup[y0+158:y1+163,x0+158:x1+160]=True;cleanup&=~head
                barrel=np.zeros_like(body);barrel[y0+160:y1+160,x0+160:x1+160]=exact_indices(a,a.composite(n+1,mask)[0].crop((x0+160,y0+160,x1+160,y1+160)),start)
                target=body.copy();target[oldarm]=unshifted[oldarm];target[newarm]=source[newarm];target[cleanup]=0;target[br]=barrel[br]
                need(np.array_equal(target[~(edit|br|cleanup)],body[~(edit|br|cleanup)]),'Nonarm new body changed')
                need(np.array_equal(np.array(a.rgba(target,start))[br],np.array(a.composite(n+1,mask)[0])[br]),'Original barrel RGBA changed')
                need(np.array_equal(target[head&~br],body[head&~br]),'New head changed')
                for label,q in [('indices',target),('authored',source),('unshifted_source',unshifted),('arm_mask',edit.astype(np.uint8)*255),('old_bent_arm_mask',oldarm.astype(np.uint8)*255),('new_arm_mask',newarm.astype(np.uint8)*255),('head_guard',head.astype(np.uint8)*255),('barrel_mask',br.astype(np.uint8)*255),('gun_cleanup_mask',cleanup.astype(np.uint8)*255)]:Image.fromarray(q).save(O/form/f'{n+1:03}_{label}.png')
                a.rgba(target,start).save(O/form/f'{n+1:03}.png');poses[form,n+1]=target
                rows.append({'body_ref':n,'shot_ref':n+1,'form':form,'source_art_sha256':HASHES[page_number],'body_sha256':sha(bp.read_bytes()),'source_translation':[0,dy],'original_muzzle_world':[mx,my],'barrel_rect_world':r['barrel_rect_world'],'barrel_rgba_exact':True,'new_source_duplicate_barrel_removed':True,'nonarm_body_exact':True,'head_guard_exact':True,'arm_stretched':False,'candidate_only':True})
    outside={}
    for n in range(56,67,2):
        diff=(poses['after',n]>0)&(poses['before',n]==0);outside[n]=int(diff.sum());Image.fromarray(diff.astype(np.uint8)*255).save(O/f'{n:03}_outside.png')
    for form,start,mask in(('before',16,15),('after',0,0)):
        items=[]
        for n in range(55,66,2):
            bp=H/('ultimate_wall_contacts_probe01'if n<61 else'ultimate_wall_page02_contacts01')/form/f'{n:03}.png'
            items.extend([(f'{n} new body',Image.open(bp)),(f'{n+1} arm candidate',a.rgba(poses[form,n+1],start))])
        page(items,a.composite(0,mask)[0],O/f'{form}_comparison.png',cols=4,scale=5)
    write(O/'registration.json',{'sources':sources,'rows':rows,'after_outside_before':outside,'old_head_body_used':False,'packed':False,'candidate_only':True,'limitations':['앞팔 정합 초안이다. 어깨/손목 접합 및 양폼 알파를 실제 열람한 뒤 확정한다.','원래 총구 사각형은 투명 픽셀까지 RGBA 동일하게 보호했다.']})
    print({'outside':outside,'out':str(O)})
if __name__=='__main__':main()
