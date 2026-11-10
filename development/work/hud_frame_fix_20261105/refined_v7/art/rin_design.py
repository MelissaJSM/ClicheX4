"""린 기존 HUD 심볼의 수동 색인 도트 설계와 게임 팔레트 검수 미리보기."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_common import read_disc
from scripts.prepare_riko_ui import entry
from scripts.prepare_hud_emblems import all_compositions,composed,render_pixels
from scripts import hud_larger_aligned as maker
from scripts import hud_frame_underlay as engine

ROWS=[
 [(9,'99')],
 [(7,'995599')],
 [(6,'955555669')],
 [(6,'95666666699')],
 [(5,'956779999679')],
 [(5,'956790009679')],
 [(4,'9567900009679')],
 [(3,'95679')],
 [(3,'95679'),(9,'9999999999')],
 [(2,'955555555555555579')],
 [(2,'956666677777777779')],
 [(2,'956679'),(15,'9679')],
 [(1,'956679'),(16,'9679')],
 [(1,'95679'),(16,'9679')],
 [(0,'956679'),(8,'99'),(16,'96779')],
 [(0,'95679'),(8,'955555556679')],
 [(0,'9679'),(8,'97777777779')],
 [(1,'979'),(9,'999999999')],
 [(2,'9')],
]

def main():
    a=np.zeros((19,21),np.uint8)
    for y,segments in enumerate(ROWS):
        for x,colors in segments:
            assert x+len(colors)<=21
            values=np.array([int(c,16)for c in colors],np.uint8)
            a[y,x:x+len(colors)]=values
    out=Path(__file__).parent
    data={'character':'rin','width':21,'height':19,'origin':[-18,23],
          'palette_indices':[0,5,6,7,9],'rows':[''.join(format(int(v),'X')for v in row)for row in a],
          'method':'manual native index contour and lighting clusters; no filtering or automatic palette reduction',
          'identity':'upper bent loop, broad middle stroke, descending left stroke and lower right foot'}
    (out/'rin.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
    assets,_=read_disc(ROOT/'out/ver_rin_nana/overhaul_20261105_candidate04/rin_nana.bin',['PL01_U.ARC','COL00_0X.ARC'])
    current,_=read_disc(ROOT/'out/ver_rin_nana/hud_larger_aligned_20261105_v6/rin_nana.bin',['PL01_U.ARC'])
    native,_=read_disc(ROOT/'MegaMan X4.bin',['PL01_U.ARC'])
    old,_,bb,_=composed(entry(current['PL01_U.ARC'],0x10206),all_compositions(entry(current['PL01_U.ARC'],3))[1,69])
    symbols,_,sb,_=composed(entry(assets['PL01_U.ARC'],0x10206),all_compositions(entry(assets['PL01_U.ARC'],3))[1,69])
    original,_,nb,_=composed(entry(native['PL01_U.ARC'],0x10206),all_compositions(entry(native['PL01_U.ARC'],3))[1,69])
    assert bb==sb==nb
    maker.configure();engine.WHITE_ONLY=True
    # Rebuild the existing v6 white metal body/groove without its old symbol.
    empty=maker.aligned.WHITE_BODY(old,original,np.zeros_like(old),bb)
    left,top=bb[:2]
    for y in range(29,34):
        for x in range(-19,2):
            empty[y-top,x-left] = 12 if y in (29,33) or x in (-19,1) else 11 if y==32 else 10
    new=empty.copy();layer=np.zeros_like(old)
    layer[23-top:42-top,-18-left:3-left]=a
    assert not np.any((layer!=0)&(original==14))
    new[layer!=0]=layer[layer!=0]
    palette=entry(assets['COL00_0X.ARC'],5)[17*32:18*32]
    sprite=render_pixels(a,palette)
    sprite.save(out/'rin_native.png')
    sprite.resize((336,304),Image.Resampling.NEAREST).save(out/'rin_enlarged.png')
    board=Image.new('RGB',(768,544),'#536273');draw=ImageDraw.Draw(board)
    for i,(label,arr)in enumerate([('V6 BEFORE',old),('V7 MANUAL REFINEMENT',new)]):
        draw.text((i*384+12,8),label,fill='white');im=render_pixels(arr,palette).resize((arr.shape[1]*7,arr.shape[0]*7),Image.Resampling.NEAREST)
        board.paste(im,(i*384+20,40),im)
    board.save(out/'rin_hud_review.png')
    components=[];seen=set()
    for y,x in zip(*np.where(a)):
        if(y,x)in seen:continue
        todo=[(int(y),int(x))];seen.add(todo[0]);count=0
        while todo:
            cy,cx=todo.pop();count+=1
            for yy,xx in((cy-1,cx),(cy+1,cx),(cy,cx-1),(cy,cx+1)):
                if 0<=yy<19 and 0<=xx<21 and a[yy,xx] and (yy,xx) not in seen:
                    seen.add((yy,xx));todo.append((yy,xx))
        components.append(count)
    proof=dict(size=[21,19],origin=[-18,23],color_indices=sorted(map(int,np.unique(a))),
        opaque_pixels=int(np.count_nonzero(a)),four_connected_components=components,
        native_number_aperture_overlap_pixels=0,whole_HUD_preview='rin_hud_review.png',
        existing_palette_preserved=True,game_or_resource_files_written=False)
    (out/'rin_review.json').write_text(json.dumps(proof,indent=2)+'\n','utf8')
    print(json.dumps(proof))
if __name__=='__main__':main()
