"""138/139의 생성 원화 소매 오류만 교정할 두 자세 입력.135는 포함하지 않는다."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write

def main():
    d=H/'ultimate_arrival_overhead_arms01';need(not d.exists(),'Fresh correction inputs')
    sources={138:H/'ultimate_arrival_inputs01/page02/generated.png',139:H/'ultimate_arrival_separate_inputs02/generated.png'}
    hashes={138:'b6f77ba7481b70b8bc8f97a06f3a38edb9f0ec8529172193e388436d1672566c',139:'0b7ed3dd1e8da4998814f0cc4414656e9cc0410161d069fa60261e282374b43d'}
    target=Image.new('RGBA',(1536,1024));rows=[]
    for col,n in enumerate((138,139)):
        p=sources[n];need(sha(p.read_bytes())==hashes[n],'Source art changed');im=Image.open(p).convert('RGBA');need(im.size==(1536,1024),'Original fixed page size')
        for row,form in enumerate(('before','after')):
            cut=im.crop((768,row*512,1536,(row+1)*512));dy=32 if n==138 else 0
            # Only changes the source crop origin: native world positions stay unchanged.
            target.alpha_composite(cut,(col*768,row*512+dy))
            rows.append({'ref':n,'form':form,'source':p.relative_to(ROOT).as_posix(),'sha256':hashes[n],'source_cell':[768,row*512,1536,(row+1)*512],'input_canvas_translation':[0,dy],'body_scale_changed':False})
    d.mkdir();target.save(d/'edit_target.png');target.save(d/'old_coordinate_reference.png')
    style=H/'ultimate_arrival_inputs01/page01/accepted_ultimate_style.png';Image.open(style).save(d/'accepted_ultimate_style.png')
    prompt='''Edit only the two raised arms in the BOTTOM ROW of Image1. The top row is a locked reference and must remain unchanged. Preserve the exact transparent 1536x1024 sheet with four 768x512 cells, representing 96x64 logical pixels enlarged 8x, origin(48,36). Left column is overhead pose138; right column is its separate pose139. This is a local correction to two overhead-arm poses, not a redesign of the character or body.
The two bottom sprites wear the accepted lavender one-piece swimsuit from the bottom row of Image2, but their raised forearms incorrectly still contain WHITE JACKET SLEEVES. Redraw those sleeve regions as properly shaped BARE FOREARMS with the same skin palette, small elbow shadow and clean skin contour as the accepted swimsuit sprites in Image2. Remove all white fabric, folded cuff and navy cuff bands from those bottom raised arms. Preserve the existing wrist positions and the two hands clasped together above the head; do not lower the hands or invent additional hands. Keep both shoulders and elbows at the corresponding top-row pose's exact locations. The rear arm remains mostly hidden by the head, exactly as in the reference, rather than adding a third limb. Make a natural continuous shoulder-elbow-wrist connection within the existing arm silhouette; this is not a uniform flat recolor.
Everything outside the bottom raised-arm regions must remain exactly the same: layered lavender hair, fox ears, gold glasses, face and gaze, head size, navy side hair ornament, swimsuit torso/pink accent, hips, legs, sandals, silhouette, ground position and all top-row jacket artwork. Do not change the torso cut, add bare skin anywhere else, stretch or scale the body, change the hand gesture, or change the pose. Use crisp small 1997 console pixel clusters and preserve the current native detail. True transparent background, no glow, effects, text, labels or new sprite. Four cells only.'''
    (d/'prompt.txt').write_text(prompt+'\n','utf8');parent=H/'prepared_ultimate_hurt02/PL02_U.ARC'
    write(d/'input.json',{'refs':[138,139],'ultimate_parent':{'path':parent.relative_to(ROOT).as_posix(),'sha256':sha(parent.read_bytes())},'source_layout':{'size':[1536,1024],'native_cell':[96,64],'native_origin':[48,36],'scale':.125,'crop':[112,124,208,188]},'rows':rows,'edit_scope':'138/139 후폼의 흰 소매만.135 자세/입력/반려 편집은 포함하지 않는다.','protected_regions':['새머리/얼굴/장식','의상몸통','다리/발','전폼 전체'],'new_art_generated':False,'arc_written':False,'files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()}})
    print(d.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
