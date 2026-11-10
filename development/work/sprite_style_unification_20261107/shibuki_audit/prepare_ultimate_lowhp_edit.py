"""세부묘사를 유지할 다음 국소편집 입력과47px 좌표 가이드를 보존한다."""
from pathlib import Path
import json,shutil,hashlib
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;I=H/'ultimate_lowhp_inputs01';O=H/'ultimate_lowhp_edit01'
assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(I/'generated.png')=='24a216ae930580ed2938cd956540ee99a753d8d05b404d5de86745d2f569a6ba'
for src,dst in(('generated.png','edit_source.png'),('pose_reference.png','pose_only_reference.png'),('accepted_style.png','accepted_style.png')):shutil.copyfile(I/src,O/dst)
plate=Image.open(I/'pose_reference.png').convert('RGBA');bg=Image.new('RGB',plate.size,(26,32,43));bg.paste(plate,(0,0),plate);d=ImageDraw.Draw(bg)
for col in(0,1):
 x=col*512
 # These are coordinate guides, never generated replacement character pixels.
 d.line((x,8*8,x+511,8*8),fill='#e6d37d',width=1)
 d.line((x,55*8,x+511,55*8),fill='#8bd4de',width=1)
 d.line((x+31*8,8*8,x+31*8,55*8),fill='#526c7e',width=1)
 d.text((x+8,8),'LEFT FACING 3/4 FATIGUE / 64 NATIVE CELL',fill='white')
 d.text((x+8,8*8-14),'head/ears top y=-24',fill='#e6d37d')
 d.text((x+8,55*8+8),'soles y=22 / next empty row y=23',fill='#8bd4de')
bg.save(O/'pose_alignment_guide.png')
prompt='''Edit edit_source.png, keeping its fine pixel-art materials and accessories, into exactly TWO compact 3/4-facing LEFT low-health sprites. The current generated source is too front-facing and51 native pixels tall. Correct ANATOMY/POSTURE, not by scaling the whole image or making a smaller copy of the same frontal pose.
Repose the shoulders, head, hips and knees to match pose_only_reference.png: tired head lowered and tilted slightly toward screen-left, three-quarter visible face rather than a symmetric frontal face; near shoulder gently forward/down, one hand against upper chest, the other hanging lower; two planted feet and a small natural knee bend. Keep the accepted compact figure's shoulder/sleeve width, short torso, thigh fullness and rounded body; do not restore the old thin featureless body.
pose_alignment_guide.png has only technical reference lines. In each64x64 native cell, x/y world origin is(32,32). Total head/ears-to-sole height should be47 native pixels maximum: ears at cell row8 (world-24), feet bottom row54 (world22). Native ground/foot center x is31 (world-1). Use the original left/right sole positions from the pose reference, without shifting the character. Each cell is enlarged8x to512x512, so final canvas remains1024x512. Preserve transparent margins. Do not draw those guide lines or words in the result.
accepted_style.png is the definitive head size, compact proportions and contrast. Preserve the new source's separate lavender hair locks, gold heart sunglasses resting on head, navy flower and small pale side accessory, clean closed tired eyelids, human face, sailor collar, pink tie, crisp short pleats and sandals. LEFT retains the oversized white/navy jacket with gold piping and detailed cuff/hem folds. RIGHT retains the same white/light-lavender sleeveless sailor swim dress without the jacket. It is a one-piece swim dress, not a bikini. Both sprites must have precisely identical hair/head/eyes/neck, bare hands, body joints, legs, sandals and tail, so the only difference is the jacket. The sleeveless silhouette must stay inside the jacket silhouette at shared body points.
Do not simplify the new garment/hair detail back to the old pose reference. Preserve clean low-resolution clusters and restrained outlines; no face/eyes ghosting, noisy gold specks, elongated torso or limbs, straight rigid symmetrical stance, oversized ears, random black hair scratches, added objects/text/background. Two complete unclipped transparent pixel sprites only.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8')
record={'parent_generated_sha256':sha(I/'generated.png'),'input_sha256':{p.name:sha(p)for p in O.glob('*.png')},'reason':'첫 새 원화 디테일은 개선됐으나51px/정면화로 보류. 전체축소가 아니라3/4 피로 굽힘·어깨각도·47px대기비율을 다시 그린다.','same_source_detail_preserved':True,'guide_is_diagnostic_not_sprite_art':True,'native_ground_world_y':22,'native_ear_top_world_y':-24,'new_after_alpha_outside_before_current':19,'generation_started':False,'queue':'Riko wall4 -> Nana base4 -> Shibuki lowHP edit','game_modified':False}
(O/'inputs.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8')
print(str(O))
