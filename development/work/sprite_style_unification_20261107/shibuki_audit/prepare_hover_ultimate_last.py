"""남은 호버229 독립 한 자세의 원점과 두 높은 손을 고정한 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
from prepare_hover_ultimate_inputs import P,PARENT
def main():
    d=H/'hover_ultimate_inputs02';need(not d.exists(),'기존입력보호');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모변경');im=a.composite(229,15)[0];q=np.array(im)[:,:,3].copy();q[96:224,96:224]=0;need(not q.any(),'입력절단');d.mkdir();im.crop((96,96,224,224)).resize((1024,1024),Image.Resampling.NEAREST).save(d/'edit_target.png');style=Image.new('RGBA',(1536,1024))
    for col,n in enumerate((0,41)):style.alpha_composite(a.composite(n,0)[0].crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(col*768,0))
    style.save(d/'accepted_after_style.png');prompt='''Use case: identity-preserving pixel-art sprite refinement.
Image1 is the EDIT TARGET, exactly one hovering full-body adult character sprite on a transparent1024x1024 canvas. It is a128x128 native grid enlarged8x, origin(64,64). Preserve every transparent margin, full canvas, character scale and world position. No crop, zoom, recentering, stretch or whole-body rotation.
Improve its old flat hair and costume clusters to match Image2's accepted detailed idle and airborne identity. Lavender fox ears and layered hair with purple contour/shadow locks, long backward braid, gold eyes, small GOLD sunglasses resting on the head. Use the accepted lavender one-piece garment with narrow pink center detail, bare arms and lower legs, keeping its coverage and compact adult design. No white jacket sleeves, added shorts, skirt, gloves or long coat. Keep compact dark-lavender hover footwear at exactly Image1's toe/heel/sole/ankle positions; separately stored thrust effects connect there.
CRITICAL POSE: BOTH arms and BOTH hands are RAISED ABOVE THE HEAD in Image1. Keep two visible raised fists, one above each side of the head, and the two forearms rising along the sides of the head. Do not lower either hand to the waist, chest or face. Follow Image1's exact shoulder, elbow, wrist and fist coordinates; Image2 is detail/style only. Keep the original head/eye location, ear-tip height, torso length and hip position. The knees are compactly bent and the feet are tucked below the torso; preserve the distinct target knee/ankle/heel positions, leg foreshortening and any originally occluded far-leg parts. Exactly two arms and two legs, no additional hand or long straight standing legs.
Repaint within the original proportions using intentional square pixel clusters: fine separated hair strands, restrained small fabric folds, warm skin highlights/pink midtones and dark purple edges, coherent knee and shoe planes. Preserve hair volume and the original overall footprint. Do not replace the pose with either reference or simplify the detailed reference style into flat blocks.
BODY ONLY. No gun, jets, flames, energy aura, bullets, dust, motion lines, cast shadow, background, text or grid. Genuinely transparent RGBA. No blur, glow or antialiased halo. Return one improved sprite at the original exact canvas placement.''';(d/'prompt.txt').write_text(prompt,'utf8');im.save(d/'old229.png')
    write(d/'input.json',{'parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'ref':229,'actual_mask':15,'style_refs':[0,41],'style_mask':0,'layout':{'canvas':[1024,1024],'logical_canvas':[128,128],'cell':[128,128],'origin':[64,64],'crop':[96,96,224,224]},'original_metrics':metrics(im),'source_RGBA_sha256':sha(im.tobytes()),'policy':'실제강제15 after의상 독립229 새몸체. 기존 원추진12/13/14위상·원230 발사점(-24,-11)은 별도보존·후속정합. 두손위 자세를 유지한다.','files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()}});print(d)
if __name__=='__main__':main()
