"""138 위로든팔을 보존하는 두 의상의 의미영역 초기 합성."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
POLY=[(-15,-23),(-9,-23),(-9,-20),(-9,-17),(-8,-14),(-6,-11),(-3,-10),(2,-10),(5,-8),(7,-4),(8,0),(9,4),(7,6),(4,5),(3,3),(0,4),(-4,4),(-6,3),(-7,0),(-8,-5),(-7,-7),(-10,-10),(-12,-14),(-14,-18)]
def main():
    a=Archive((N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC').read_bytes());out=D/'settle_pair_probe_v1';out.mkdir(exist_ok=False);bp=D/'raised138_local_probe_v1/before_138_indices.png';dp=D/'raised138_local_probe_v1/after_138_indices.png';b=np.array(Image.open(bp));donor=np.array(Image.open(dp));common=b.copy();common[b==15]=13
    mi=Image.new('L',(384,384));ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in POLY],fill=1);m=np.array(mi)>0;after=common.copy();after[m]=donor[m];outside=(after>0)&(b==0)
    for tag,z in(('before',b),('after',after),('donor',donor),('costume_mask',m.astype(np.uint8)*255),('outside_mask',outside.astype(np.uint8)*255)):Image.fromarray(z).save(out/f'{tag}_138.png')
    helper.grid([('138',[('after idle',a.composite(0)[0]),('new jacket',a.rgba(b,16)),('new bare donor',a.rgba(donor)),('new shared body',a.rgba(after))])],out/'comparison.png',8)
    x0,y0,x1,y1=-18,-32,18,10;s=20;w=(x1-x0)*s+50;board=Image.new('RGB',(2*w,(y1-y0)*s+60),'#b6c0c7');dr=ImageDraw.Draw(board)
    for i,(z,pal,title)in enumerate(((b,16,'new jacket'),(donor,0,'bare donor'))):
        ox=i*w+35;oy=50;pic=a.rgba(z,pal).crop((160+x0,160+y0,160+x1,160+y1)).resize(((x1-x0)*s,(y1-y0)*s),Image.Resampling.NEAREST);board.paste(pic,(ox,oy),pic);dr.text((ox,3),title,fill='black')
        for x in range(x0,x1):dr.text((ox+(x-x0)*s,30),str(x),fill='black')
        for y in range(y0,y1):dr.text((ox-30,oy+(y-y0)*s),str(y),fill='black')
        for x in range(x0,x1+1):dr.line((ox+(x-x0)*s,oy,ox+(x-x0)*s,oy+(y1-y0)*s),fill='#879099')
        for y in range(y0,y1+1):dr.line((ox,oy+(y-y0)*s,ox+(x1-x0)*s,oy+(y-y0)*s),fill='#879099')
    board.save(out/'semantic_grid.png')
    record={'ref':138,'before_source':bp.relative_to(ROOT).as_posix(),'before_source_sha256':digest(bp),'after_source':dp.relative_to(ROOT).as_posix(),'after_source_sha256':digest(dp),'costume_polygon':POLY,'common_gray15_to_after13_count':int((b==15).sum()),'new_outside_before':[[int(x-160),int(y-160),int(after[y,x])]for y,x in np.argwhere(outside)],'components':[int(label(z>0,np.ones((3,3)))[1])for z in(b,after)],'old_pixels_copied':0,'alpha_clipped':False,'before_sha256':sha(b.tobytes()),'after_sha256':sha(after.tobytes())};write(out/'manifest.json',{'frames':[record],'native_packed':False,'runtime_verified':False,'scope':'138 새로운 위로든팔과새전신을두의상공통으로정합하는의미영역초기안.정본권총/원손접점·최종원순서미검증.'});print(json.dumps(record))
if __name__=='__main__':main()
