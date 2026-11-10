"""후속 사다리 세 후폼의 하의 디자인만 새 원화로 교정하는 입력."""
from pathlib import Path
import sys,json
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
def main():
 out=D/'b_costume_inputs_v1';out.mkdir(exist_ok=False);p=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());target=D/'b_v1/generated.png';need(digest(target)=='3cff8603b891726357d167e1a7f1918991d9128b7bbe6c8a7c409c6cff1d81da','입력후속원화');im=Image.new('RGBA',(1536,1024));crop=(128,124,192,188)
 for row,mask in enumerate((15,0)):
  for col,n in enumerate((0,79,61)):im.alpha_composite(a.composite(n,mask)[0].crop(crop).resize((512,512),Image.Resampling.NEAREST),(512*col,512*row))
 im.save(out/'style.png');im.crop((0,0,512,1024)).save(out/'style_idle.png')
 prompt='''Use case: precise-object-edit. Technical costume-color correction on six adult game-character sprites. Image1 is the edit target, an exact1536x1024 canvas with3columns by2rows. Preserve the top row completely. Preserve every face, ear, hair lock, head size, torso, arm, hand, leg, shoe, pose and pixel placement in all six sprites.
Correct ONLY the three BOTTOM-ROW hip garments: they were mistakenly drawn as white/gray shorts. Change that existing clothing fabric to the established BLACK lower costume with a narrow PINK waistband, matching the BOTTOM sprite in Image2. Image2 contains the two accepted idle costumes stacked vertically, with jacket before on top and sleeveless after below. Use clothing colors and seams only, never copy its idle pose. Keep the current covered area and body contour; do not expose more skin or change the garment's coverage. No white or silver central shorts panel should remain on the bottom row. Do not recolor skin, legs, hair, shoe highlights or black hand cuffs.
Keep the bottom row's bare upper arms and existing black sleeveless top unchanged. Preserve the top row's pink jacket and gray/white clothing exactly. This is neutral full-body climbing sprite work with no anatomy emphasis. Maintain native-sized pixel clusters rather than smooth gradients. No extra body part, effect, background, halo, text or border. Output the same six complete sprites in exactly the same positions on a genuinely transparent canvas.'''
 (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'target':target.relative_to(ROOT).as_posix(),'target_sha256':digest(target),'style_source':p.relative_to(ROOT).as_posix(),'style_source_sha256':digest(p),'style_refs':[0,79,61],'style_sha256':digest(out/'style.png'),'prompt_sha256':digest(out/'prompt.txt'),'edit_scope':'후폼149/151/153 기존하의천 영역만 검정/분홍 의상으로 수정. 피부노출/몸윤곽 변경 없음. 원화등록후 하의 의미영역만 사용.','native_packed':False});print(out)
if __name__=='__main__':main()
