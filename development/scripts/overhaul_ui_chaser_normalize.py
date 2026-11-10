"""리코 체이서 한 장의 원화를 공통 픽셀 배율과 기존 팔레트로 등록한다."""
import json, sys, struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_inventory import load,entry
from scripts.overhaul_sprites_audit import rgba,sha
from scripts.prepare_rin_run import connected_groups
OUT=ROOT/'work/overhaul_20261105/ui/riko_chaser'

def main():
    raw,_=load('ver_buki_riko');words=struct.unpack_from('<16H',entry(raw['PL01_U.ARC'],9))
    colors=np.array([[(int(w)>>s&31)*255//31 for s in (0,5,10)] for w in words[1:]],np.int32)
    image=Image.open(OUT/'generated.png').convert('RGBA');crops=[];boxes=[]
    for i in range(6):
        box=(i%3*image.width//3,i//3*image.height//2,(i%3+1)*image.width//3,(i//3+1)*image.height//2)
        a=np.array(image.crop(box));a[:,:,3]=np.where(a[:,:,3]>=224,255,0);im=Image.fromarray(a);b=im.getbbox()
        assert b;crops.append(im.crop(b));boxes.append([box,b])
    scale=46/crops[0].height
    board=Image.new('RGB',(3*400,2*350),(40,46,58));d=ImageDraw.Draw(board);frames={}
    for i,n in enumerate([0,14,22,30,38,147]):
        im=crops[i].resize((round(crops[i].width*scale),round(crops[i].height*scale)),Image.Resampling.NEAREST)
        a=np.array(im);dist=((a[:,:,:3].astype(np.int32)[:,:,None]-colors)**2).sum(-1);idx=(np.argmin(dist,-1)+1).astype(np.uint8);idx[a[:,:,3]<128]=0
        groups=connected_groups(idx>0);noise=[]
        for g in groups[1:]:
            if len(g)>3:raise ValueError('Detached large feature')
            idx[g[:,0],g[:,1]]=0;noise.append(len(g))
        path=OUT/f'prepared_{n}.png';pim=Image.fromarray(idx,'P');pim.putpalette([v for w in words for v in [(w>>s&31)*255//31 for s in (0,5,10)]]+[0]*720);pim.info['transparency']=0;pim.save(path)
        shown=rgba(idx,words).resize((idx.shape[1]*7,idx.shape[0]*7),Image.Resampling.NEAREST);board.paste(shown,(i%3*400+20,i//3*350+24),shown);d.text((i%3*400+10,i//3*350+4),f'{n} {idx.shape[1]}x{idx.shape[0]}',fill='white')
        frames[str(n)]={'file':path.name,'sha256':sha(path.read_bytes()),'size':[idx.shape[1],idx.shape[0]],'crop':boxes[i],'noise':noise}
    board.save(OUT/'normalized_review.png')
    (OUT/'prepared.json').write_text(json.dumps({'source_sha256':sha((OUT/'generated.png').read_bytes()),'palette_words':words,'scale':scale,'alpha_threshold':224,'frames':frames,'per_pose_scaling':False},indent=2)+'\n','utf8')
    print(json.dumps({'scale':scale,'sizes':{n:f['size'] for n,f in frames.items()}}))
if __name__=='__main__':main()
