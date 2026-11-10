"""실제 강제mask15의217 옛몸을 대기 after 의상의 독립 새몸으로 제작할 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
P=H/'prepared_nova_ultimate01/PL02_U.ARC';PARENT='687fb27b10b9a7c13dd6d0c9fd6976dbb04f88f9b3b775f3d33482ebb7efb86f'
def main():
    d=H/'nova_strike_ultimate_inputs01';need(not d.exists(),'새 입력');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모 변경')
    z=a.layer(217,0)[0];need(int((z>0).sum())==840,'원840몸체');im=a.rgba(z,0);need(im.tobytes()==a.composite(217,15)[0].tobytes(),'217 강제표시 몸체')
    target=im.crop((96,96,224,224)).resize((1024,1024),Image.Resampling.NEAREST);style=Image.new('RGBA',(1536,1024));rows=[]
    for col,n in enumerate((0,73)):
        ref=a.composite(n,0)[0];style.alpha_composite(ref.crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(col*768,0));rows.append({'ref':n,'mask':0,'RGBA_sha256':sha(ref.tobytes()),'metrics':metrics(ref)})
    prompt='''Use case: identity-preserving pixel-art character sprite refinement for a classic console game.
Image1 is the EDIT TARGET, a1024x1024 transparent canvas containing one horizontal midair dash sprite. Its whole canvas is a128x128 native pixel grid enlarged8x, with the character origin at(64,64). Keep all transparent margins and the exact existing native size and position. Do not crop, recenter, zoom, rotate, stretch or change aspect ratio.
Preserve this precise foreshortened horizontal pose facing LEFT: head and two fox ears at left, torso low and nearly horizontal, the front fist tucked under the face/chest with its elbow bent down; the other arm folded beside the waist. Two knees bend backward and both feet extend toward viewer-right at the exact original locations. Keep the same eye, ear tips, fists, wrists, elbows, shoulder, hip, knee, ankle and sole coordinates. Exactly two arms and two legs. No extra hand or fingers, no upright pose, no long legs and no enlarged torso.
Image2 is the accepted COSTUME AND DETAIL reference. Its LEFT panel is accepted idle0 and its RIGHT panel is accepted ground dash73. The new target must wear this same lavender one-piece outfit with narrow pink center detail, bare arms and lower legs, and small lavender sandals. Preserve the reference garment coverage and adult character design. Remove the old target's white jacket sleeves and cuffs as part of changing to the accepted reference outfit. Do not add shorts, skirt, boots, gloves or a long coat. The source pose stays exactly as Image1; do not copy the ground dash leg angles.
Use the accepted small GOLD SUNGLASSES resting on the head, following the target's head tilt. Lavender fox ears with dark inner shadows, detailed layered lavender hair and backward braid, gold eye and short rounded proportions. Match the reference's restrained cluster shading and clear purple contour, retaining fine hair locks and coherent skin/cloth/sandal planes. Do not use flat old hair blocks or cover the face with the sunglasses.
This image contains the body ONLY. No gun, energy aura, electricity, flame, dust or motion lines; those effects are stored separately in the game. Clean native console pixel art, crisp pixel clusters, two or three tones per material. Genuinely transparent background; no halo, glow, cast shadow, grid, text or labels. Return only one improved sprite at its original size and location.'''
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_after_style.png');Image.fromarray(z).save(d/'old217_indices.png');im.save(d/'old217_body.png');(d/'prompt.txt').write_text(prompt,'utf8')
    reader=H.parent/'zero_audit/shibuki_nova_hover_relations01/report.json'
    write(d/'input.json',{'parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'relation_report':{'path':reader.relative_to(ROOT).as_posix(),'sha256':sha(reader.read_bytes())},'ref':217,'engine_render_mask':15,'old_body_pixels':840,'old_body_metrics':metrics(im),'style_refs':rows,'layout':{'canvas':[1024,1024],'logical_canvas':[128,128],'cell':[128,128],'origin':[64,64],'crop':[96,96,224,224]},'policy':'217~230은 원코드 강제mask15. 기존217 흰재킷840셀을 새 after 대기 의상으로 통일하는 별도 신규몸 정책이며 원코드/속도/타이밍은 변경하지 않는다. 효과는 별도 보존·파생검사. 거부135 편집과 별개다.','files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()}});print(d)
if __name__=='__main__':main()
