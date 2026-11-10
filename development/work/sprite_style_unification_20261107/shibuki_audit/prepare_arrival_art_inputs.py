"""현재 개조 캐릭터만으로 두 소량 등장 원화 페이지를 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive

def main():
 data=(H/'prepared_victory_ladder01/PL00_U.ARC').read_bytes();need(sha(data)=='02f092d7b0ed67ce1174fd30250b86f73c81b42dbfa08c8c3ca06fc638b89acf','Source changed');a=Archive(data)
 out=H/'arrival_inputs01';need(not out.exists(),'Output exists');out.mkdir()
 pages=[[(133,0),(135,0)],[(137,0),(138,0),(138,15)]]
 for i,targets in enumerate(pages,1):
  board=Image.new('RGBA',(len(targets)*512,512))
  for col,(n,mask)in enumerate(targets):
   if n==137:
    raw=np.array(Image.open(H/'arrival_remaining01/effects/137_body_indices.png'));pic=a.rgba(raw)
   else:pic=a.composite(n,mask)[0]
   bb=pic.getbbox();need(bb[0]>=128 and bb[1]>=128 and bb[2]<=192 and bb[3]<=192,'Cropped source')
   board.alpha_composite(pic.crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,0))
  board.save(out/f'page{i:02}_poses.png')
 style=Image.new('RGBA',(1536,1024))
 for row,mask in enumerate((0,15)):
  for col,n in enumerate((0,156,204)):
   pic=a.composite(n,mask)[0];style.alpha_composite(pic.crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
 style.save(out/'accepted_style.png')
 common='''Use case: style-transfer sprite production edit. Image 1 is the exact pose/layout edit target; Image 2 is the accepted character design and detail reference. Redraw the sprites of image 1 with the same fine pixel clusters and costume detail as image 2, while preserving the pose, scale, origin, feet, hands and head center from image 1. Character: Tenko Shibuki, a compact plump fox-spirit girl with long lavender hair and fox ears. Match the accepted compact body proportions, short torso/limbs, broad soft sleeves, softly rounded thighs, readable layered hair. A crouch compresses the torso/legs, never shrinks the head. Do not make her lanky or thin. No new clothing design. Each cell represents an exact 64x64 logical pixel area enlarged8x; keep the same feet and hands on the logical grid. 1997 console pixel art: clean single logical-pixel contour, 2/3 tone readable planes, layered lavender hair locks and ear interiors, face, tiny eye, side bow, red collar and sleeve folds. No big flat lavender hair plate, no unstructured white sleeve blob, no heavy black outlines or noisy scribble strands. Transparent background and empty margins exactly as image1. No labels/text, no effects/lightning/ring/background, no weapons. Do not add another figure or copy an idle pose over these motion poses. Image2 top row is BASE costume: white broad bell sleeves with pale blue shadows/red trim, red shrine maiden short dress and waist bow, white/pale-blue legwear and red shoes. Image2 bottom row is FOURTH costume: charcoal/purple clothing, gold collar/waist trim, long dark/purple split coat tails, dark legwear and gold-tipped shoes. Its sleeves must be dark with gold cuff trim, never white base sleeves. Costume details must remain identifiable at the native 1x grid. Do not globally resize or center by a new bounding box.'''
 prompts=[common+'''\nOutput exactly a1024x512 transparent sheet, TWO equal512x512 cells in one row. BOTH cells BASE costume. Left133: original deep landing crouch, torso leaning slightly forward, one bent knee low, far leg grounded; forward hand near the ground, other hand tucked near body. Preserve original hand/foot locations. Right135: stand in original ready transition, facing left three-quarter, one forearm raised near the chin/upper chest, other arm across the waist; grounded feet apart. Preserve the original mild body tilt and hands. Redraw hair and cloth details without replacing these gestures with idle. Keep the left crouched head the same absolute size as the right standing head and accepted reference, not scaled down with body.''',common+'''\nOutput exactly a1536x512 transparent sheet, THREE equal512x512 cells in one row. Left137 BASE costume: facing slightly left, both elbows bent outward and fists near each side of the head, original low hands/raised forearms and grounded feet. Middle138 BASE: arms fully raised together above the head, hands meet, feet together closer as source. Right138 FOURTH: EXACTLY the middle sprite's joints/head/hands/feet and silhouette body proportions; only replace outfit with the accepted charcoal/purple/gold fourth costume. Keep the arms/hands above the head at original coordinates. The new middle/right hair, ears, face and joint locations must be identical. Dark sleeves and long split tails in the right cell; white broad sleeves/red short skirt in the middle. Keep all three native heads at accepted width/height. Do not stretch the arms into long thin poles.''']
 for i,prompt in enumerate(prompts,1):(out/f'page{i:02}_prompt.txt').write_text(prompt+'\n','utf8')
 write(out/'manifest.json',dict(source_arc='prepared_victory_ladder01/PL00_U.ARC',source_sha256=sha(data),pages=[dict(page=i+1,targets=[dict(ref=n,mask=m)for n,m in rows])for i,rows in enumerate(pages)],native_crop=[128,128,192,192],source_grid=64,scale=8,reference_scope='existing mod character only; no original game player artwork sent',shared=[dict(master=135,ref=136,dy=-1,external_sparks_preserved=True),dict(master=138,ref=139,dy=-1,both_forms=True)],used_animation_ids={'133':[2],'135':[2],'137':[2],'138':[2,95,96],'139':[2,95,96]},body_137_external_sparks_removed_from_art_input=True,previous_141142_preserved=True))
 print(out)
if __name__=='__main__':main()
