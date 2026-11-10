"""완료된 새 재킷 팔의 관절/총구를 유지하는 맨팔 편집 입력."""
from pathlib import Path
import sys,shutil,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,write
VERS={'a':'v2','b':'v2','c':'v3','d':'v1'}
def main():
 out=D/'firing_pose_inputs_v2';out.mkdir(exist_ok=False);a=Archive((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes());meta=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));sources={}
 for page,ver in VERS.items():
  im=Image.new('RGBA',(1536,1536));sources[page]=[]
  for i,n in enumerate(meta['pages'][page]):
   p=D/f'firing_{page}_before_joint_probe_{ver}/before_{n:03}.png';v=np.array(Image.open(p));im.alpha_composite(a.rgba(v,16).crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768));sources[page].append({'ref':n,'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)})
  im.save(out/f'{page}_after_targets.png');shutil.copy2(D/f'firing_inputs_v1/{page}_after_targets.png',out/f'{page}_original_after_geometry.png')
  refs=','.join(map(str,meta['pages'][page]))
  prompt=f'''Use case: precise-object-edit. Image 1 is the edit target: a transparent 2x2 sheet of FOUR complete pixel-art frames of adult game heroine Nana, firing while running, frames {refs}. Change ONLY the near extended arm's pink jacket sleeve and cuff into a bare skin arm. Keep the rest of the pink jacket, full body, head, face, eyes, hair, legs, shoes and far arm exactly unchanged. This is an isolated arm donor, not a whole costume redesign.

The near firing arm is ALREADY in its correct pose in image 1. Preserve its actual shoulder, elbow bend, wrist, hand and pink pistol coordinates. Do not lower the elbow, move or enlarge the pistol, make a new straight arm trajectory, or add an extra arm. The resulting bare arm must fit INSIDE the existing pink sleeve outline, while retaining the same shallow elbow curve. A thinner skin arm is natural, but the original sleeve silhouette is a strict outer envelope. Keep the exact gun and gripping hand as drawn; remove the pink sleeve only between the real shoulder and wrist. No sleeve fragments or black chest/cuff bars along the arm. Selective skin shading must match the accepted idle rather than a thick uniform outlined skin tube.

Image 2 supplies this character's sleeveless outfit and skin colors only; its folded non-firing hand is NOT a pose guide. Image 3 is the accepted idle, standing shot, fresh air shot and dash shot style reference. Only the near extended arm of image 1 is edited. Preserve all other pixels and the exact position and scale of all four complete sprites in their 2x2 cells.

Crisp PS1 Mega Man X4 pixel art, discrete shading, no blur, no gradients. Truly transparent background. No labels, borders, ground, effects, or extra diagrams. Return the same four complete sprites with just that sleeve removed and the corresponding skin arm drawn inside it.'''
  (D/f'prompt_firing_{page}_after_v2.txt').write_text(prompt+'\n','utf8')
 shutil.copy2(D/'firing_inputs_v1/after_accepted_style.png',out/'after_accepted_style.png');write(out/'manifest.json',{'sources':sources,'images':{p.name:digest(p)for p in out.glob('*.png')},'scope':'새 재킷 사격팔의 바깥윤곽 안에서 같은 관절의 맨팔만 생성. 전신 몸체·머리·다리는 편집 출처에서 채택하지 않는다.'});print(out)
if __name__=='__main__':main()
