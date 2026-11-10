"""Rin native indexed HUD: bonnet, ribbon wings, knot and tails."""
import json,sys,hashlib
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

def design():
    im=Image.new('L',(21,19),0); d=ImageDraw.Draw(im)
    # Native coordinates are authored individually, never scaled from reference.
    # Bonnet upper scallops and curved crown, with a genuine open centre.
    d.polygon([(6,7),(6,3),(7,2),(8,2),(8,1),(9,0),(10,0),(11,1),(12,1),(13,1),(15,2),(17,4),(17,6),(16,8),(14,9),(13,7),(14,6),(14,5),(13,4),(10,4),(9,5),(9,7)],fill=9)
    d.polygon([(7,6),(7,3),(9,2),(9,1),(11,2),(12,1),(14,2),(16,4),(16,6),(15,7),(15,5),(13,3),(10,3),(8,5),(8,7)],fill=6)
    d.line([(7,4),(8,3),(10,2),(13,2),(15,3)],fill=5,width=1)
    d.point((9,1),fill=5);d.point((12,1),fill=5)
    d.line([(16,5),(16,6),(15,8)],fill=7,width=1)
    # Lower scalloped bonnet trim remains visible under the front ribbon.
    scallops=[[(5,11),(5,13),(6,14),(8,14),(10,12)],
              [(10,11),(11,13),(12,14),(14,15),(16,14),(17,12)]]
    for curve in scallops:d.line(curve,fill=9,width=3)
    for curve in scallops:d.line(curve,fill=5,width=1)
    d.line([(12,14),(14,15),(16,14)],fill=6,width=1)
    d.line([(6,15),(8,15)],fill=7,width=1)
    # Left loop sits behind the broad descending ribbon tail.
    d.polygon([(2,10),(2,8),(3,7),(5,6),(7,6),(9,7),(11,9),(10,11),(8,12),(5,12),(3,11)],fill=9)
    d.polygon([(3,9),(3,8),(5,7),(7,7),(9,8),(10,9),(9,10),(7,10),(5,9)],fill=5)
    d.line([(3,10),(5,11),(8,11),(10,10)],fill=7)
    # Right tail projects diagonally from the knot, separate from the bow wing.
    d.polygon([(12,10),(15,10),(18,12),(20,14),(18,17),(16,14),(14,13)],fill=9)
    d.polygon([(14,11),(17,12),(19,14),(18,15),(16,13)],fill=6)
    d.line([(15,11),(17,12),(19,14)],fill=5)
    d.line([(16,13),(18,16)],fill=7)
    # Long left ribbon tail: broad sweep, pointed end and a clean dark edge.
    d.polygon([(11,9),(12,11),(10,13),(7,15),(4,18),(2,17),(0,14),(2,12),(5,10),(8,9)],fill=9)
    d.polygon([(10,10),(10,11),(8,13),(6,14),(3,17),(1,14),(3,12),(6,10)],fill=6)
    d.line([(1,14),(3,12),(6,10),(9,10)],fill=5)
    d.line([(3,17),(6,14),(8,13),(10,11)],fill=7)
    # Open right wing, slanted lower crease and the independent centre knot.
    d.polygon([(12,9),(15,7),(18,7),(19,8),(19,10),(18,13),(15,12),(13,11)],fill=9)
    d.polygon([(13,9),(15,8),(18,8),(18,10),(17,12),(15,11)],fill=6)
    d.line([(13,9),(15,8),(18,8)],fill=5)
    d.line([(14,10),(17,12)],fill=7)
    d.polygon([(10,8),(12,8),(13,9),(12,11),(10,10)],fill=9)
    d.point((11,9),fill=5);d.point((12,9),fill=6);d.point((11,10),fill=7)
    # Keep the little left ribbon loop open instead of reading as a solid bar.
    d.line([(5,8),(7,8)],fill=0)
    d.line([(4,9),(6,9)],fill=0)
    d.point((4,8),fill=9);d.point((8,8),fill=9);d.point((7,9),fill=9)
    return np.asarray(im,dtype=np.uint8)

def main():
    a=design();out=Path(__file__).parent
    assert a.shape==(19,21) and set(np.unique(a))=={0,5,6,7,9}
    data={'character':'rin','width':21,'height':19,'origin':[-18,23],
      'palette_indices':[0,5,6,7,9],'rows':[''.join(format(int(v),'X') for v in row) for row in a],
      'method':'manual native indexed contour and shade clusters, alpha-composited reference reviewed',
      'identity':'rounded scalloped bonnet crown, centre knot, left/right bow wings and diagonal ribbon tails'}
    (out/'rin.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
    assets,_=read_disc(ROOT/'out/ver_rin_nana/overhaul_20261105_candidate04/rin_nana.bin',['COL00_0X.ARC'])
    current,_=read_disc(ROOT/'out/ver_rin_nana/hud_refined_symbols_20261105_v7/rin_nana.bin',['PL01_U.ARC'])
    native,_=read_disc(ROOT/'MegaMan X4.bin',['PL01_U.ARC'])
    old,_,bb,_=composed(entry(current['PL01_U.ARC'],0x10206),all_compositions(entry(current['PL01_U.ARC'],3))[1,69])
    original,_,nb,_=composed(entry(native['PL01_U.ARC'],0x10206),all_compositions(entry(native['PL01_U.ARC'],3))[1,69])
    assert bb==nb
    maker.configure();engine.WHITE_ONLY=True
    empty=maker.aligned.WHITE_BODY(old,original,np.zeros_like(old),bb)
    left,top=bb[:2]
    for y in range(29,34):
      for x in range(-19,2):
        empty[y-top,x-left]=12 if y in(29,33)or x in(-19,1)else 11 if y==32 else 10
    layer=np.zeros_like(old);layer[23-top:42-top,-18-left:3-left]=a
    assert not np.any((layer!=0)&(original==14))
    assert np.all(layer[:23-top]==0)
    new=empty.copy();new[layer!=0]=layer[layer!=0]
    palette=entry(assets['COL00_0X.ARC'],5)[17*32:18*32]
    sprite=render_pixels(a,palette);sprite.save(out/'rin.png')
    sprite.resize((336,304),Image.Resampling.NEAREST).save(out/'rin_16x.png')
    board=Image.new('RGB',(768,544),'#536273');draw=ImageDraw.Draw(board)
    for i,(label,arr) in enumerate([('V7 BEFORE',old),('V8 BONNET + RIBBON',new)]):
      draw.text((i*384+12,8),label,fill='white');im=render_pixels(arr,palette).resize((arr.shape[1]*7,arr.shape[0]*7),Image.Resampling.NEAREST)
      board.paste(im,(i*384+20,40),im)
    board.save(out/'rin_HUD_old_new.png')
    review=Image.new('RGB',(730,340),'#474d5a');draw=ImageDraw.Draw(review)
    ref=Image.open(ROOT/'character/ver_rin_nana/rin(zero)_mark.webp').convert('RGBA')
    ref.thumbnail((310,290),Image.Resampling.LANCZOS)
    review.paste(ref,(15,45),ref);draw.text((15,12),'RIN REFERENCE: ALPHA COMPOSITED',fill='white')
    review.paste(sprite.resize((336,304),Image.Resampling.NEAREST),(375,30),sprite.resize((336,304),Image.Resampling.NEAREST));draw.text((375,12),'V8 NATIVE INDEXED PIXELS',fill='white')
    review.save(out/'rin_reference_review.png')
    proof={'size':[21,19],'origin':[-18,23],'color_indices':sorted(map(int,np.unique(a))),
      'opaque_pixels':int(np.count_nonzero(a)),'native_number_aperture_overlap_pixels':0,
      'no_symbol_index_E':bool(not np.any(a==14)),'health_fill_y22_untouched':True,
      'existing_palette_preserved':True,'v7_art_files_written':False,'game_or_resource_files_written':False}
    (out/'rin_review.json').write_text(json.dumps(proof,indent=2)+'\n','utf8');print(json.dumps(proof))
if __name__=='__main__':main()
