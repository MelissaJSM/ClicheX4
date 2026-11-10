"""221의 위로 돌아온 오른손 도달높이를 원손 가이드로 교정한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from prepare_hover_ultimate_inputs import P,PARENT
def main():
    d=H/'hover221_reach_inputs01';need(not d.exists(),'기존입력보호');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모변경');src=H/'hover221_arm_native01/221_indices.png';z=np.array(Image.open(src));target=a.rgba(z).crop((96,96,224,224)).resize((1024,1024),Image.Resampling.NEAREST);d.mkdir();target.save(d/'edit_target.png');a.composite(221,15)[0].crop((96,96,224,224)).resize((1024,1024),Image.Resampling.NEAREST).save(d/'original_pose.png')
    guide=target.copy();dr=ImageDraw.Draw(guide);dr.rectangle((63*8,36*8,69*8,42*8),outline=(0,255,120,255),width=3);dr.line((67*8,45*8,65*8,39*8),fill=(0,255,120,255),width=3);dr.text((70*8,35*8),'RIGHT FIST TARGET',fill=(0,255,120,255));guide.save(d/'reach_guide.png')
    prompt='''Use case: precise local pixel-art arm pose correction.
Image1 is the edit target: one existing detailed hovering gameplay sprite,1024x1024 transparent, native128x128 grid enlarged8x, origin(64,64). Image2 is the original intended pose. Image3 is a POSITION GUIDE only: the green rectangle marks the required higher RIGHT fist location. Do not reproduce guide marks.
Only the viewer-RIGHT raised arm is still too short/low. Its hand currently stops beside the right ear; the intended right fist reaches ABOVE the ears, about three native pixels higher than the unchanged viewer-left fist. Rebuild this ONE right elbow/forearm/hand to match Image2's reach and Image3's green box. Move the right fist about4 native pixels UP and2 pixels LEFT, so its top outline reaches native worldY=-28, with the small fist around worldX=+1,Y=-25. The forearm must reconnect naturally down to the same right shoulder; do not stretch the whole character, repeat pixel rows, make a huge hand, or add an arm. Both hands remain raised, exactly TWO arms/hands. Preserve the viewer-LEFT arm and hand completely.
Preserve the entire new head/ears, hair details and braid, gold head sunglasses, face/eye, lavender garment, pink front detail, torso dimensions, hips, legs and both shoes from Image1. Only pixels that the corrected raised right arm genuinely covers may change within the head-side area. Do not restore the older simple hair or white sleeve from Image2. Keep the corrected right arm BARE with the existing warm skin shading and purple contour. Keep the previously cleared waist free of an extra fist.
Maintain exact canvas, transparent margins, origin, scale, body pose and foot locations. Pixel-art console style, square native clusters with restrained shades. No weapon, effect, text, labels, green lines, background, shadow, glow or halo. Return one sprite in the exact original placement with only its right raised arm reaching the specified original higher point.'''
    (d/'prompt.txt').write_text(prompt,'utf8');write(d/'input.json',{'ref':221,'source_new_body':{'path':src.relative_to(ROOT).as_posix(),'sha256':sha(src.read_bytes())},'parent_sha256':PARENT,'layout':{'logical_canvas':[128,128],'origin':[64,64],'crop':[96,96,224,224]},'previous_approximate_point':[4,-27],'corrected_visual_fist_center':[1,-25],'actual_original_skin_top':-27,'actual_new_skin_top':-23,'original_top_contour':-28,'policy':'첫교정은팔방향만복구했고피부손상단4px낮음.원손부근시각가이드로손/전완만국소재작화하며나머지새몸보존.','files':{p.name:sha(p.read_bytes())for p in sorted(d.iterdir())if p.is_file()}});print(d)
if __name__=='__main__':main()
