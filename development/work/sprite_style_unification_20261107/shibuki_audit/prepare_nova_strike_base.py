"""현재 Nova217의 효과를 분리한 두 의상 몸체 상세 입력."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics

def main():
    d=H/'nova_strike_base_inputs01';need(not d.exists(),'새 원화 입력');d.mkdir()
    s=H/'nova_strike_base_sources01';r=json.loads((s/'report.json').read_text('utf8'));need(r['passed'],'출처 확인')
    p=H/'prepared_nova_base01/PL00_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)==r['candidate_sha256'],'부모 변경')
    target=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1024));context=Image.new('RGBA',(1536,1024));crop=(112,96,208,224);rows=[]
    for col,(form,mask)in enumerate((('base',0),('fourth',15))):
        im=Image.open(s/f'{form}_217_body.png').convert('RGBA');pos=(768*col,0)
        target.alpha_composite(im.crop(crop).resize((768,1024),Image.Resampling.NEAREST),pos)
        style.alpha_composite(a.composite(0,mask)[0].crop(crop).resize((768,1024),Image.Resampling.NEAREST),pos)
        context.alpha_composite(a.composite(71,mask)[0].crop(crop).resize((768,1024),Image.Resampling.NEAREST),pos)
        rows.append({'form':form,'mask':mask,'ref':217,'metrics':metrics(im),'body_RGBA_sha256':sha(im.tobytes())})
    prompt='''Use case: identity-preserving pixel-art sprite refinement for a classic 32-bit console game.
Image1 is the EDIT TARGET. Keep the exact1536x1024 transparent canvas with TWO columns and ONE row. Each768x1024 cell is a96x128 logical pixel grid enlarged8x, origin(48,64). Preserve all transparent margins and each sprite's exact native size and coordinates. Do not crop, recenter, magnify, rotate or change aspect ratio.
The two figures are the SAME horizontal midair dash pose facing LEFT: head and ears at left, torso nearly horizontal, one fist tucked low in front of the face/chest and its elbow bent below the shoulder; opposite arm remains folded along the body/waist. Two legs extend back toward the viewer's RIGHT in the original foreshortened bent-knee configuration, with the two boot tips at their original coordinates. Preserve eyes, ears, face angle, both fists, elbows, knees, ankles and soles. Exactly two arms/two legs. No extra hand, lowered head, long stretched body or enlarged chest. Do not turn the pose upright. No gun, broom, motion aura, electricity, fire or dust: these effects are separate game assets.
Image2 is each costume's accepted IDLE reference for identity, proportions and detail density. Image3 is the accepted ground dash71 for hair/cloth folds and boot materials ONLY. Follow the POSE and body dimensions from Image1; do not copy the ground dash legs or stance.
LEFT BASE: lavender fox ears and layered lavender hair/braid with small red ribbons, gold eye; pale lavender-white sleeves with restrained purple fold shadows, red-and-white short outfit and compact white/lavender boots with red details. RIGHT FOURTH: same head/face anatomy, lavender hair with the accepted dark/gold head ornament; dark black-purple sleeves/bodice and boots with gold fasteners and small pale collar, small red waist tassel. The right has no broad white sleeves or red chest panel. Preserve the original costume coverage and garment identity.
Improve the flat old hair planes and blocky clothing by matching accepted restrained pixel clusters: clear ear interiors, layered hair highlights/shadows, fold lines and cuff/waist/hem separation, coherent boot-toe contours. Use crisp clean console pixel art with two or three tone shading, not noisy hatching or thick new outlines. Preserve exact short-limbed round proportions and existing outer silhouette/anchors. True transparent background, no halo, glow, ground shadow, text, labels or grid. Output only these TWO refined sprites in their same cells.'''
    target.save(d/'edit_target.png');style.save(d/'accepted_idle.png');context.save(d/'accepted_dash71.png');(d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(a.data)},'source_report':{'path':(s/'report.json').relative_to(ROOT).as_posix(),'sha256':sha((s/'report.json').read_bytes())},'layout':{'canvas':[1536,1024],'logical_canvas':[192,128],'grid':[2,1],'cell':[96,128],'origin':[48,64],'world_crop':list(crop)},'rows':rows,'policy':'새217 몸체만 제작. 158px 역사 외곽선과218/219/220 효과는 입력에서 분리하며 코드/시간표/속도는 변경하지 않는다.','files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()}});print(d)
if __name__=='__main__':main()
