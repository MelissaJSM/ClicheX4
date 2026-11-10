"""새 Ultimate234의 두 의상 팔 관절 정합용 국소 편집 입력."""
from pathlib import Path
import sys, shutil
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
PROMPT='''Use case: precise-object-edit.
Edit the supplied 1536x1024 transparent four-pose sprite sheet. Make ONE local correction in the BOTTOM-RIGHT character only: her bare arms must take exactly the same compact defensive curled-fist pose as the TOP-RIGHT jacket character.
The top-right character is the precise joint-position reference. In particular the viewer-left fist is a small closed fist beside the cheek, centered at the same horizontal coordinate and 512 pixels lower than the top-right fist. The forearm descends from that fist toward the elbow below it. It must NOT form a horizontal skin bar across her mouth. The viewer-right fist and elbow likewise match the top-right pose, with both elbows, shoulders and fists at the same local coordinates. Remove only the jacket sleeves to reveal natural bare upper arms and forearms inside the same sleeve silhouette. Exactly two arms and two small closed fists, with readable wrist and elbow anatomy.
Keep the BOTTOM-RIGHT swimsuit, pink neck bow, face, closed eyes, gold sunglasses on the hair, navy hair bow, fox ears, lavender hair, head tilt, bent knees, ankles, sandals, body height and body position UNCHANGED. Retain the existing compact accepted proportions. Do not scale, stretch, rotate, mirror or move the whole figure. Do not change the face or add a third hand. Do not fill the removed wrong arm with a flat skin patch; restore the small exposed upper chest/neckline naturally while preserving the original swimsuit collar.
Preserve the other THREE characters exactly. Preserve the exact 2x2 layout, 768x512 cells, character placements and 1536x1024 canvas. Keep the same detailed crisp low-resolution pixel-art rendering and material shading. No text, labels, guides, border, glow, floor or shadow. The background must be fully transparent with clean alpha, not a painted checkerboard or gray cloud. Return the whole four-pose sheet, not a crop.'''
def main():
 d=H/'ultimate_hurt234_arm01';need(not d.exists(),'Fresh output');d.mkdir()
 p=H/'ultimate_hurt_inputs01/page02/generated.png';need(sha(p.read_bytes())=='08ca83d93a247ce348f1eae7081504efb5c6a3264c798439c4b0d519dfce6944','Source changed')
 shutil.copyfile(p,d/'edit_target.png');(d/'prompt.txt').write_text(PROMPT+'\n','utf8')
 write(d/'input.json',{'edit_target':p.relative_to(ROOT).as_posix(),'edit_target_sha256':sha(p.read_bytes()),'prompt_sha256':sha((d/'prompt.txt').read_bytes()),'scope':'새after234 팔만 동일새before234 관절에정합.다른몸/옷/머리 보호.','ref':234,'source_layout':{'size':[1536,1024],'cell':[768,512],'native_cell':[96,64],'scale':0.125},'arc_changed':False})
 print(d.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
