"""포스 노바 누락을 원본과 대조하고 기존 승인 그림/포즈 참고를 준비한다."""
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_inventory import load,entry,BUILDS
from scripts.overhaul_sprites_audit import render,rgba,sha
from scripts.overhaul_ui_nana_legs import full_preview
from src.psx_player import composition_frame,graphics_bank
OUT=ROOT/'work/overhaul_20261105/ui/nana_fourth_nova'

def sheet(items,name):
    board=Image.new('RGBA',(3*384,2*384));d=ImageDraw.Draw(board)
    for i,(label,pic) in enumerate(items):
        tile=pic.crop((112,112,208,208)).resize((384,384),Image.Resampling.NEAREST)
        board.alpha_composite(tile,((i%3)*384,(i//3)*384))
    board.save(OUT/name)

def main():
    OUT.mkdir(exist_ok=True)
    original,_=load('original');nana,_=load('ver_rin_nana');shibuki,_=load('ver_buki_riko')
    og=original['PL00_U.ARC'];arc=nana['PL00_U.ARC'];c=entry(arc,3)
    words=struct.unpack_from('<64H',entry(arc,9));ow=struct.unpack_from('<64H',entry(og,9))
    rows=[]
    for n in range(213,221):
        a,m=render(arc,0,0,n);b,_=render(og,0,0,n);s,_=render(shibuki['PL00_U.ARC'],0,0,n)
        rows.append({'frame':n,'nana_base_indices_equal_original':bool(np.array_equal(a,b)),
                     'shibuki_base_indices_equal_original':bool(np.array_equal(s,b)),
                     'nana_layer_counts':{str(k):len(composition_frame(c,k,n)['parts'])for k in(0,5,6,7,8)},
                     'stream':m})
    assert all(r['nana_base_indices_equal_original']for r in rows)
    assert all(not r['shibuki_base_indices_equal_original']for r in rows)
    sheet([(str(n),rgba(render(arc,0,0,n)[0],words))for n in(0,100,71)]+
          [(str(n),full_preview(arc,n))for n in(0,100,71)],'approved_styles.png')
    sheet([(str(n),rgba(render(og,0,0,n)[0],ow))for n in(213,215,217)]+
          [(str(n),full_preview(nana['PL02_U.ARC'],n))for n in(213,215,217)],'native_nova_poses.png')
    (OUT/'reference.json').write_text(json.dumps({'baseline':BUILDS['ver_rin_nana'],
        'refs':rows,'same_character_poses_to_generate':[213,215,217],
        'approval_basis':'C04 confirmed original-body omission; reuse accepted Nana basic/Fourth identity and native Nova posture.',
        'native_code_evidence':'work/overhaul_20261105/ui/c04_visual_review/frame_usage.json',
        'warning':'Fourth Nova is usable with armor body bit2; earlier ultimate_separate coverage classification was wrong.',
        'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
    print(str(OUT))
if __name__=='__main__':main()
