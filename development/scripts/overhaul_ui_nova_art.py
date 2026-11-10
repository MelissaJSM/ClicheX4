"""동일 나나 노바 3포즈의 기본/포스 의상 쌍을 15색 원점 격자에 등록한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_erosion
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.extract_zero import save_image
from scripts.overhaul_sprites_audit import sha
D=ROOT/'work/overhaul_20261105/ui/nana_fourth_nova'
SOURCE_SHA='4ff6522ef410c27445b137283de92832c53564ee5f88d4f9c59cc70d5a4a79d1'
ORDER=(213,215,217)
EYES={213:(75,68),215:(79,68),217:(65,80)}
HEIGHTS={213:42,215:47,217:27}

def main():
    source=D/'generated.png';assert sha(source.read_bytes())==SOURCE_SHA
    arc=(ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL00_U.ARC').read_bytes()
    base0=raster(entry(arc,2),entry(arc,3),0,0,0,(256,160))
    words=struct.unpack_from('<16H',entry(arc,9),32)
    rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)]for w in words],np.int32)
    src=Image.open(source).convert('RGBA');board=Image.new('RGB',(1152,768),(28,34,45));draw=ImageDraw.Draw(board);records=[]
    for row in range(2):
        for col,n in enumerate(ORDER):
            a=np.array(src.crop((col*512,row*512,(col+1)*512,(row+1)*512)))
            labels,_=label(a[:,:,3]>=224,np.ones((3,3)));sizes=np.bincount(labels.flat);sizes[0]=0;keep=labels==sizes.argmax()
            yy,xx=np.nonzero(keep);box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
            a[~keep,3]=0;crop=Image.fromarray(a).crop(box);height=HEIGHTS[n];width=round(crop.width*height/crop.height)
            v=normalize(crop,height,rgb,width=width)
            colors=np.array(crop).astype(np.int32);red,green,blue=colors[:,:,:3].transpose(2,0,1)
            eye=(green>red+8)&(green>blue+8)&(colors[:,:,3]>=224)
            gy,gx=np.nonzero(eye);assert len(gx)>0
            ex,ey=EYES[n];cx=(float(np.median(gx))+.5)*width/crop.width-.5;cy=(float(np.median(gy))+.5)*height/crop.height-.5
            dx,dy=round(ex-cx),round(ey-cy);target=np.zeros((160,256),np.uint8);target[dy:dy+height,dx:dx+width]=v
            # Reuse the approved eye/face at the registered native anchor. All
            # source colors remain the existing PS1 palette; no redraw in code.
            face=base0[65:74,73:82];target[ey-3:ey+6,ex-3:ex+6]=face
            rim=(target>0)&~binary_erosion(target>0,np.ones((3,3),bool))&(target==5)
            target[rim]=1
            kind='base'if row==0 else'fourth'
            im=save_image(target.tobytes(),(256,160),words,D/f'{kind}_{n}.png').convert('RGBA')
            crop=im.crop((32,32,128,128)).resize((384,384),Image.Resampling.NEAREST)
            board.paste(crop,(col*384,row*384),crop);draw.text((col*384+5,row*384+4),f'{kind} {n}',fill='white')
            sy,sx=np.nonzero(target)
            records.append({'kind':kind,'frame':n,'cell':row*3+col,'source_box':box,'native_dimensions':[width,height],
                'placement':[dx,dy],'eye':[ex,ey],'bbox_world':[int(sx.min()-80),int(sy.min()-80),int(sx.max()+1-80),int(sy.max()+1-80)],
                'approved_face_source':[73,65,82,74],'approved_face_exact':True,'opaque_pixels':len(sx)})
    board.save(D/'normalized_review.png')
    (D/'prepared.json').write_text(json.dumps({'source_sha256':SOURCE_SHA,'palette_words':list(words),
        'canvas_size':[256,160],'origin':[80,80],'records':records,
        'images':{f'{kind}_{n}.png':sha((D/f'{kind}_{n}.png').read_bytes())for kind in('base','fourth')for n in ORDER},
        'runtime_verified':False},indent=2)+'\n','utf8')
    print(json.dumps(records))
if __name__=='__main__':main()
