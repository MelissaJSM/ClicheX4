"""4/8 맨팔 국소 재작화: 새 재킷 자세와 두 완성 기준을 한 입력에 둔다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,write
def main():
 out=D/'arm48_inputs_v1';out.mkdir(exist_ok=False);a=Archive((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes());im=Image.new('RGBA',(1536,1536));src=[]
 for i,n in enumerate((4,8)):
  p=D/f'firing_pair_diagnostic_v1/before_{n:03}.png';v=np.array(Image.open(p));im.alpha_composite(a.rgba(v,16).crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i*768,0));src.append({'ref':n,'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)})
 for i,n in enumerate((0,34)):im.alpha_composite(a.composite(n,0)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i*768,768))
 im.save(out/'targets_and_style.png')
 prompt='''Use case: precise-object-edit. Edit ONLY the near extended firing arm of the TWO TOP sprites in this transparent 2x2 pixel-art sheet. The two bottom sprites are accepted style references and must remain unchanged. All sprites depict adult game heroine Nana.

TOP LEFT and TOP RIGHT are already in the exact correct firing poses, including shoulder, elbow, wrist, hand, small pink pistol and muzzle. Replace only their near pink jacket sleeve/cuff with a naturally shaded bare arm that occupies the INNER part of that same sleeve. Keep the pink jacket on the torso and the far arm: this output is an arm-only donor. Keep all head, face, hair, torso, legs, shoes, pistol and hand pixels in the top sprites fixed.

Important: do NOT lower or relocate either elbow. Follow the existing small bent sleeve's upper and lower contours exactly. Bare forearm should be one pixel slimmer than the jacket at most, with a complete connected three-tone skin shape. Retain a selective DARK GREY/TAN underside edge from elbow toward wrist: the arm cannot become a pale shapeless strip. Keep enough wrist thickness to connect the gripping hand. Never draw a new hanging U-shaped forearm below the current sleeve. Do not add a second arm. Do not change the pistol, gun size, hand or muzzle position.

The lower left accepted idle demonstrates the light skin contour and shading; lower right accepted air shot demonstrates a connected bare shoulder, elbow and wrist. Match that restrained skin shading, without a thick uniform black outline. This is neutral full-body 1990s PS1 Mega Man X4 game sprite art, crisp square pixels, no blur or gradients. Truly transparent background, same complete sheet and identical 2x2 cell positions/scale, no text, borders, effects or additional characters.'''
 (D/'prompt_arm48_v1.txt').write_text(prompt+'\n','utf8');write(out/'manifest.json',{'source_arc_sha256':digest(D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC'),'targets':src,'reference_refs':[0,34],'target_cells':[[0,0],[1,0]],'image_sha256':digest(out/'targets_and_style.png'),'prompt_sha256':digest(D/'prompt_arm48_v1.txt')})
 print(out)
if __name__=='__main__':main()
