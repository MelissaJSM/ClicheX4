"""수용된 새 라이징 포즈에 Ultimate 전후 의상만 입히는 편집 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,need,write

def main():
 out=D/'ultimate_inputs_v1';out.mkdir(exist_ok=False);bp=D/'packed_base_candidate_v1/PL00_U.ARC';up=N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC';need(digest(bp)=='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42','Pose source');need(digest(up)=='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9','Ultimate master');a=Archive(bp.read_bytes());u=Archive(up.read_bytes());box=(112,112,208,208);records=[]
 for page,ns in(('air',(103,104)),('charge',(100,101)),('recovery',(102,231))):
  target=Image.new('RGBA',(1536,1536));rows=[]
  for i,(mask,n)in enumerate((m,n)for m in(15,0)for n in ns):
   # Both rows deliberately begin with the exact same approved bare-leg
   # Fourth pose. Only the headgear and costume are authored in the edit.
   im=a.composite(n,15)[0];ar=np.array(im)[:,:,3].copy();ar[112:208,112:208]=0;need(not ar.any(),'No pose crop');target.alpha_composite(im.crop(box).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768));rows.append({'cell':i,'ref':n,'ultimate_mask':mask,'source_pose_mask':15,'source_pose_rgba_sha256':sha(im.tobytes())})
  target.save(out/f'{page}_targets.png');records.append({'page':page,'frames':rows})
 master=Image.new('RGBA',(1536,1536))
 for i,(mask,n)in enumerate(((15,0),(15,47),(0,0),(0,47))):master.alpha_composite(u.composite(n,mask)[0].crop(box).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
 master.save(out/'ultimate_style.png')
 prompt='''Use case: precise-object-edit. Production asset: four neutral full-body adult Nana PS1 pixel-art game sprites, two poses in the two approved Ultimate costumes.
Image 1 is the exact pose edit target, a 2x2 transparent page. The upper row is prep103 then upward firing104 in the BEFORE costume; the lower row repeats those exact two poses in the AFTER costume. These four source bodies currently wear a black veil/black costume. Replace their costume and headgear with the respective accepted design in image 2. Image 2 is solely the style/costume master: upper row pink jacket BEFORE idle and airborne; lower row black-and-pink one-piece AFTER idle and airborne. Keep the mature adult proportions, pink hair with fine strand clusters, tall ears and small crown accessory, green eyes, little green ankle bands and black shoes as that master. Use identical face size and deliberate small-pixel shading across all four.
CRITICAL: Keep exactly the full-canvas layout, each 96-pixel native cell, body origin, eye position, raised hand, pistol, bent knees, ankle positions and feet of image1. Both poses raise their pistol on the VIEWER-RIGHT of the face. Do not mirror the body, do not move the pistol to the left, do not replace it with a fist or arm cannon. The same tiny black-and-pink pistol Sarang-i remains eight native pixels long, at exactly the shown hand/muzzle location. Preserve the natural shoulder-elbow-wrist connection. The opposite arm stays bent beside the torso. Exactly two arms, two legs, one pistol.
Change the costume/headgear only, retaining all the newly drawn fine body pose and limb proportions. Before: pink jacket with sleeves and matching black inner outfit; after: the exact black-and-pink one-piece and bare arms from the master, no remaining jacket sleeve, no extra frills or black veil. Keep the bare-leg shape and tiny shoe size; do not thicken or lengthen the legs. Light-facing skin edges use skin/gray tones while the shadow side keeps a fine dark contour, never an uninterrupted heavy black outline. Hair should have clear layered locks, not a large flat pink blob.
Output the same four complete sprites in their same 2x2 cells, on genuine transparent alpha with no background or halo. No words, labels, guide lines, shadows, effects, flame or projectiles. No enlargement, cropping, smoothing, diagonal stretch or changed canvas placement. Crisp native-pixel clusters, matching the accepted idle style.'''
 (out/'air_prompt.txt').write_text(prompt+'\n','utf8');write(out/'manifest.json',{'pose_arc_sha256':digest(bp),'ultimate_style_arc_sha256':digest(up),'canvas':[1536,1536],'native_cell':[96,96],'fixed_scale':8,'pages':records,'input_files':{p.name:digest(p)for p in out.iterdir()if p.is_file()},'scope':'같은 신규 포즈의 Ultimate 전후 의상 제작 입력. 기존 게임/원화 변경 없음.'});print(out)
if __name__=='__main__':main()
