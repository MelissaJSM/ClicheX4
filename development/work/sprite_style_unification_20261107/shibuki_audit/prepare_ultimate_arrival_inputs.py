"""수용한 새 기본 등장 포즈의 좌표를 고정한 Ultimate 의상 입력. 게임은 수정하지 않는다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,choices=(1,2),default=1);z=ap.parse_args()
    refs=(133,135)if z.page==1 else(137,138)
    d=H/f'ultimate_arrival_inputs01/page{z.page:02}';need(not d.exists(),'Fresh input folder')
    pp=H/'prepared_ultimate_hurt02/PL02_U.ARC';bp=H/'prepared_hurt_base01/PL00_U.ARC'
    need(sha(pp.read_bytes())=='b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94','Ultimate parent changed')
    need(sha(bp.read_bytes())=='87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b','New base pose source changed')
    a=Archive(pp.read_bytes());b=Archive(bp.read_bytes());target=Image.new('RGBA',(1536,1024));styles=Image.new('RGBA',(1536,1024));old=Image.new('RGBA',(1536,1024));rows=[]
    for row,(form,mask)in enumerate((('before',15),('after',0))):
        for col,n in enumerate(refs):
            if n==137:
                idx=np.array(Image.open(H/'arrival_native01/base_137_indices.png'));pic=b.rgba(idx)
            else:pic=b.composite(n,0)[0]
            cut=pic.crop((112,128,208,192));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(pic)[:,:,3]),'Body cut clips')
            target.alpha_composite(cut.resize((768,512),Image.Resampling.NEAREST),(col*768,row*512))
            current=a.composite(n,mask)[0]
            if n==137:
                fx=np.load(H.parent/'zero_audit/shibuki_ultimate_arrival_relations01/effect_137.npy');v=np.array(current);v[fx>0]=0;current=Image.fromarray(v)
            cc=current.crop((112,128,208,192));need(np.count_nonzero(np.array(cc)[:,:,3])==np.count_nonzero(np.array(current)[:,:,3]),'Coordinate cut clips')
            old.alpha_composite(cc.resize((768,512),Image.Resampling.NEAREST),(col*768,row*512))
            rows.append({'form':form,'ref':n,'new_pose_metrics':metrics(pic),'new_pose_rgba_sha256':sha(pic.tobytes()),'current_ultimate_metrics':metrics(current),'current_rgba_sha256':sha(current.tobytes())})
        for col,n in enumerate((0,120,55)):
            pic=a.composite(n,mask)[0];cut=pic.crop((128,128,192,192));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(pic)[:,:,3]),'Style cut clips')
            styles.alpha_composite(cut.resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
    d.mkdir(parents=True);target.save(d/'edit_target.png');styles.save(d/'accepted_ultimate_style.png');old.save(d/'old_coordinate_reference.png')
    prompt='''Edit Image1, a transparent 1536x1024 sheet with exactly four 768x512 cells. Each cell is a fixed 96x64 logical-pixel area enlarged 8x, with logical origin (48,32). Image1 supplies the newly accepted detailed Shibuki poses and precise body scale, hand/foot coordinates and joints. Change only the costume and its necessary contours to match Image2, the accepted Ultimate costume styles. Do not copy the old coarse body from Image3; Image3 is only the historical coordinate reference. Preserve Image1's compact, softly rounded body, head size including ears, short torso and limbs, full thighs, hair flow and facial angle. Never lengthen the body, shrink the whole pose, move the feet, or replace a movement pose with idle. The same pose in top and bottom rows must have identical head, gold glasses, hands, knees, ankles and feet; outfit changes alone differ.
Top row: Ultimate before acquisition, the accepted pale lavender/white cropped jacket with dark navy collar and cuff shadows, small pink center zipper/trim, short dark inner swimsuit and bare legs/sandals. Bottom row: Ultimate after acquisition, the accepted pale lavender one-piece swimsuit, small pink chest accent, bare arms and bare legs/sandals. No jacket sleeve fragments on the bare arms. The lavender hair, fox ears, golden glasses on the head and tiny gold details must have the same readable shapes as Image2. Preserve layered hair locks, clear ear interiors, small face details, the jacket collar/zipper/cuffs and compact hands. Use clean 1997 console pixel clusters and moderate 2-3 tone planes, neither huge flat white/purple patches nor excessive scribbled dark lines. Keep native clarity at 1x. Exactly two arms and two legs. Transparent background, no text, no extra sprites, no weapons, no glow/lightning/beam/effect. Retain the same fixed cell layout and generous transparent margins, with no global or per-body rescaling.
'''
    if z.page==1:prompt+='Left column133: preserve the deep landing crouch, bent torso, raised compact head, low forward hand and grounded feet exactly from Image1. Right column135: preserve the transition ready pose with one compact fist near the upper chest/chin and the other arm bent near the waist. Do not substitute idle, make legs straight, or merge the two hands. Both rows use the same joints.\n'
    else:prompt+='Left column137: preserve both elbows bent outward and the fists near each side of the head from Image1, without extending the forearms. Right column138: both arms rise together above the head and the hands meet at the existing highest coordinate; retain the close grounded feet, exact head width and folded sleeves/arm joints. Do not mistake a hand for an extra ear or make long pole arms. Both rows use the same joints.\n'
    (d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'refs':list(refs),'ultimate_parent':{'path':pp.relative_to(ROOT).as_posix(),'sha256':sha(pp.read_bytes())},'new_base_pose_source':{'path':bp.relative_to(ROOT).as_posix(),'sha256':sha(bp.read_bytes())},'source_layout':{'size':[1536,1024],'native_cell':[96,64],'native_origin':[48,32],'scale':0.125,'crop':[112,128,208,192]},'rows':rows,'effect_pixels_sent_to_generation':False,'source_137_body_only':z.page==2,'raw_game_original_sent':False,'new_art_generated':False,'shared_aliases_and_glows_pending_independent_read':True,'accepted_idle_141_142_protected':True,'files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()}})
    print(d.relative_to(ROOT).as_posix())

if __name__=='__main__':main()
