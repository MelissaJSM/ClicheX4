"""새 공중 사격 원화를 고정 배율로 읽는 미리보기. 아직 자원 패킹하지 않음."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
from inspect_air_layers import P
from prepare_lowhp_final import compose

def main():
    o=H/'air_shot_native_probe02';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive(P.read_bytes());meta=[]
    sources=[(1,(33,35,37),H/'air_shot_inputs02/page01/generated.png'),(2,(39,41,43),H/'air_shot_extra_hand_retry01/generated.png'),(3,(45,47,49),H/'air_shot_inputs02/page03/generated.png'),(4,(51,53),H/'air_shot_inputs02/page04/generated.png')]
    for pn,refs,src in sources:
        im=Image.open(src).convert('RGBA');cols=len(refs);need(abs(im.width/im.height-cols/2)<0.001,'Wrong page geometry');small=np.array(im.resize((cols*64,128),Image.Resampling.NEAREST))
        for row,(form,pal,mask)in enumerate((('base',0,0),('fourth',16,15))):
            rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
            for col,n in enumerate(refs):
                cell=small[row*64:row*64+64,col*64:col*64+64];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
                v=np.zeros((384,384),np.uint8);v[124:188,128:192]=q;Image.fromarray(v).save(o/f'{form}_{n+1:03}_source_indices.png');a.rgba(v,pal).save(o/f'{form}_{n+1:03}_source.png')
                layers={b:np.array(Image.open(H/f'air_body_layers01/{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};body=compose(a,layers,mask)
                pics.extend([(f'{n} accepted new body',body),(f'{n+1} generated arm source',a.rgba(v,pal))])
                # Pixel-coordinate source table, usable without arbitrary interpolation.
                grid=Image.new('RGB',(64*18+40,64*18+40),(40,40,48));draw=ImageDraw.Draw(grid);cut=a.rgba(v,pal).crop((128,124,192,188)).convert('RGBA');grid.paste(cut.resize((1152,1152),Image.Resampling.NEAREST),(40,40),cut.resize((1152,1152),Image.Resampling.NEAREST))
                for y in range(64):
                    draw.text((3,y*18+43),str(y-36),fill='white')
                    for x in range(64):
                        if y==0:draw.text((x*18+40,20),str(x-32),fill='white')
                        if q[y,x]:draw.text((x*18+44,y*18+43),format(int(q[y,x]),'X'),fill=(255,255,255)if q[y,x]in(1,2,15)else(0,0,0))
                grid.save(o/f'{form}_{n+1:03}_grid.png')
                meta.append({'ref':n+1,'form':form,'source':src.relative_to(ROOT).as_posix(),'source_size':list(im.size),'global_source_scale':cols*64/im.width,'source_sha256':sha(src.read_bytes()),'pixel_sha256':sha(v.tobytes()),'full_source_candidate_not_registered':True})
            page(pics,a.composite(0,mask)[0],o/f'page{pn:02}_{form}_comparison.png',cols=2,scale=4)
    write(o/'source.json',{'rows':meta,'global_scale_from_page_dimensions_only':True,'alpha_threshold':128,'body_head_old_source_copied':False,'resource_written':False})
    print(json.dumps({'output':str(o),'count':len(meta)}))
if __name__=='__main__':main()
