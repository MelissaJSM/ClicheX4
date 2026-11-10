"""사다리 후반 기존 수용 관절을 기준으로 Ultimate 의상 편집 입력을 구성."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
from prepare_ultimate_ladder_inputs import B,U,BS,US,cell

def main():
    out=H/'ultimate_ladder_inputs02';need(not out.exists(),'Fresh folder');out.mkdir();need(sha(B.read_bytes())==BS and sha(U.read_bytes())==US,'Changed source');base=Archive(B.read_bytes());ult=Archive(U.read_bytes())
    style=Image.open(H/'ultimate_ladder_inputs01/accepted_ultimate_style.png');style.save(out/'accepted_ultimate_style.png');back=Image.new('RGBA',(1536,1024))
    for row,form in enumerate(('before','after')):
        for col,n in enumerate((143,144,146)):back.alpha_composite(cell(Image.open(H/f'ultimate_ladder_native03/{form}_{n:03}.png')),(512*col,512*row))
    back.save(out/'new_ladder_style_reference.png');allrows=[]
    specs={2:((149,151,153),'Column1 ref149: face left, bent knees, screen-right arm high above the head, the other fist bent forward. Column2 ref151: back view, screen-left arm straight overhead, screen-right hand lower, bent knees. Column3 ref153: back view, both arms lowered outward, knees tucked in a short elevated pose. Preserve each different silhouette and exact endpoints.'),3:((154,183),'Column1 ref154: a strongly crouched side-facing-left landing, head deliberately LOW near the world origin and both hands in front. Column2 ref183: a short hunched rear view, head low, elbows out and knees bent. Do not stand up or enlarge either crouch. Third column is completely transparent in both rows; only FOUR figures.')}
    for pn,(refs,spec)in specs.items():
        d=out/f'page{pn:02}';d.mkdir();poses=Image.new('RGBA',(1536,1024));old=poses.copy()
        for row,mask in enumerate((15,0)):
            for col,n in enumerate(refs):
                p=base.composite(n,0)[0];o=ult.composite(n,mask)[0];poses.alpha_composite(cell(p),(512*col,512*row));old.alpha_composite(cell(o),(512*col,512*row));allrows.append({'page':pn,'row':row,'ref':n,'pose_metrics':metrics(p),'old_ultimate_metrics':metrics(o)})
        poses.save(d/'new_pose_reference.png');old.save(d/'old_coordinate_reference.png')
        prompt=f'''Edit the FIRST image, new_pose_reference.png, into Tenko Shibuki's two accepted Ultimate outfits, while keeping the exact newly detailed poses and compact proportions. The SECOND image accepted_ultimate_style.png supplies the accepted idle and new wall outfits. The THIRD image new_ladder_style_reference.png shows the new detailed ladder hair and clothes in the same two outfits; use its style, NOT its different poses. Preserve the FIRST image's exact head/ear size, shoulder angles, hip and knee joints, all hands and feet at the original positions.
Transparent1536x1024, 3 columns x2 rows of512x512 cells. Each cell is64x64 native pixels enlarged8x, origin(32,32) in that cell. Keep all empty margins and exact scale; no recentering, stretching, zoom or fitting-to-bounds. {spec}
TOP ROW: short loose WHITE jacket over the white/navy sailor swimsuit, navy collar/trim, small gold details, natural full sleeves and cuffs with lavender fold shadows. BOTTOM ROW: the SAME pose, face, long hair, ears, hands, bare legs and sandals, but remove the jacket and every sleeve to reveal BARE ARMS and the short white/navy SLEEVELESS sailor swimsuit. The two rows are one body with only clothing changed, not alternate body sizes or joint positions. Both rows have bare legs and little white/pink sandals. Do not retain the FIRST pose-reference image's red shrine outfit, boots, wraps, socks or red flowers.
Lavender fox ears, long flowing layered lavender hair with readable midtone locks, human golden eyes only when a face is actually visible, dark navy flower at the side of the head. GOLD HEART sunglasses sit at the FRONT of the head above the eyes. For BACK-VIEW figures the face and front lenses are hidden by the head: NO gold heart outlines on the back hair and NO eyes on the back of the head. Keep rear hair detailed like reference3 with soft coherent light/mid/shadow pixel clusters; no flat purple mass and no random black curly scratches. No animal muzzle or tail.
Exactly TWO connected arms and two legs per figure. Keep the intentional compact crouching proportions and original palm/foot locations, no extra fist behind the hair. Short substantial limbs, not long thin legs. Crisp tiny collar/cuff/hem seams and clean outlines at the actual native scale. Do not paste the old coarse Ultimate body or copy a standing idle head over a different head angle. No ladder, gun, muzzle, shot, particle, text, guide marker, panel line, floor, painted checkerboard or shadow. True transparent background with opaque sprites and no surrounding glow.'''
        (d/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
    write(out/'manifest.json',{'sources':{B.relative_to(ROOT).as_posix():BS,U.relative_to(ROOT).as_posix():US},'new_style_reference':{'path':'ultimate_ladder_native03','state':'앞선 후보. 접점/공통층 등록은 별도이며 게임 미적용.'},'pages':{'2':[149,151,153],'3':[154,183]},'rows':allrows,'scale':8,'origin_in_cell':[32,32],'files':{p.relative_to(out).as_posix():sha(p.read_bytes())for p in out.rglob('*')if p.is_file()},'generated':False});print(str(out))
if __name__=='__main__':main()
