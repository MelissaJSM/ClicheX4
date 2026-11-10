"""수용된 단일 샘플과 원작 동작으로 고정 축척 편집 시트를 준비한다."""
import json,math,shutil,struct,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_rin_idle import entry
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch

OUT=ROOT/'work/ver_rin_nana/style_revision/v3'
OLD=OUT.parent/'v1'
PILOT=OUT.parent/'v2'

def main():
    OUT.mkdir(exist_ok=True)
    frozen=json.loads((OLD/'master.json').read_text('utf-8'))
    for name in ('master_preview_147.png','master_preview_000.png','master_8x.png','master_generated_idle.png','master_idle_style_recipe.json'):
        shutil.copy2(OLD/name,OUT/name)
    if digest(OUT/frozen['master_file'])!=frozen['master_sha256']:raise ValueError('Frozen idle differs')
    frozen.update({'accepted_stride':'accepted_stride.png','accepted_stride_sha256':digest(PILOT/'stride_indexed.png'),'acceptance_quote':'이제야 질감이랑 가깝게느껴지네 이대로 해줄래?','calibration':'same sheet idle height48; bent poses never fill-height scaled'})
    shutil.copy2(PILOT/'stride_indexed.png',OUT/'accepted_stride.png');shutil.copy2(PILOT/'generated_stride.png',OUT/'accepted_stride_source.png')
    (OUT/'master.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n','utf-8')
    arc=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.arc').read_bytes();_,gfx=entry(arc,2);_,parts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<64H',pal)
    idle=Image.open(OUT/'master_preview_147.png').convert('RGBA');stride=Image.open(OUT/'accepted_stride.png').convert('RGBA');batches=[]
    for group in frozen['groups']:
        dest=OUT/group;dest.mkdir(exist_ok=True);guide=json.loads((OLD/group/'guide.json').read_text('utf-8'));ids=list(map(int,guide['frames']));bi=guide['graphics_bank']
        for n in ids:shutil.copy2(OLD/group/guide['frames'][str(n)]['before'],dest/guide['frames'][str(n)]['before'])
        (dest/'guide.json').write_text(json.dumps(guide,indent=2)+'\n','utf-8')
        batch_size=5 if group=='run' else 15
        for start in range(0,len(ids),batch_size):
            ns=ids[start:start+batch_size];cells=len(ns)+1;cols=4 if cells>9 else min(cells,3);rows=math.ceil(cells/cols);slots=[None,*ns]+[None]*(cols*rows-cells)
            template=Image.new('RGBA',(80*cols,80*rows));poses=Image.new('RGBA',template.size)
            for i,n in enumerate(slots):
                x=i%cols*80;y=i//cols*80
                template.alpha_composite(idle if n is None else stride,(x+16 if n is None else x+21,y+16))
                if n is None:poses.alpha_composite(idle,(x+16,y+16))
                else:
                    f=graphics_bank(gfx,bi)['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;px,sz,b,_=compose_launch(raw,f['tile_count'],composition_frame(parts,0 if bi==0 else 5,n));pic=save_image(px,sz,words,dest/f'original_{n:03d}.png').convert('RGBA');poses.alpha_composite(pic,(x+40+b[0],y+40+b[1]))
            batch=start//batch_size;template.resize((template.width*7,template.height*7),Image.Resampling.NEAREST).save(dest/f'template_{batch}.png');poses.resize((poses.width*7,poses.height*7),Image.Resampling.NEAREST).save(dest/f'poses_{batch}.png')
            prompt=f'''Use case: identity-preserve, precise pixel animation edit. Image 1 is the EDIT TARGET: {cols} columns by {rows} rows, {len(slots)} separate sprites. This exact drawing of Rin is USER APPROVED. Image 2 is ONLY the pose choreography reference at identical cell positions. Image 3 is the approved single source art for close inspection.
Keep the first cell and any other Rin idle cells EXACTLY the same idle pose and scale: calibration figures. For the remaining cells, change ONLY the pose of the character in image1 to the corresponding original Zero pose in image2. Never copy Zero's helmet, armor, bulk, hair, face or colors. This batch is {group}, frames {ns}. Every sprite must stay inside its own cell and the rows/columns/padding must remain unchanged. Preserve ALL {len(slots)} figures, no labels or empty cells.
Animate the SAME slender pixel character, not a redesign. Preserve the narrow vertically tapered head and small pointed chin, visible neck, narrow waist, long slender shins, tiny cyan eye and the little angular cuffs. Hair, head, hands, limb thickness and clothing detail must be the same native size in EVERY cell, including calibration. Bent or curled poses will naturally be SHORTER than standing: never enlarge them to fill their cell. The reference is not chibi and has no inflated rounded head, pillowy hands or puffy white sleeves. Navy short sleeves, separate small white cuffs with dark gloves and gray undersides. Thin separated white chest trim over navy, angular cobalt apron with white folded edge, silver white bob/blue forelock, connected blue/white rear ribbon. Carefully retain cool gray-blue stepped shading in hair, cuffs and boots; angular notches separate chin/neck, glove/cuff, waist/apron and knee/shin. Do not simplify these into white blobs or a thick black contour. Match image1's exact pixel-density and slender shape. Original motion lean, back-facing turns, alternating legs, torso twist and short handle hand position must follow image2. No frozen torso, no long weapon, no attack effects.
Each cell has an80x80 native canvas; the unbent idle is48 native pixels high. Single-native-pixel navy outline, crisp square pixels at the SAME grid pitch across every cell, with native grayscale planes rather than tiny smooth painted details. Whole-number enlarged pixel art, genuinely transparent background. No blur, gradients, glow, ground, shadow, decorative text or contact-sheet borders. Maintain the exact {cols}:{rows} canvas aspect and cell layout of image1.'''
            (dest/f'prompt_{batch}.txt').write_text(prompt+'\n','utf-8')
            batches.append({'id':f'{group}_{batch}','group':group,'batch':batch,'slots':slots,'columns':cols,'rows':rows,'template':str(dest/f'template_{batch}.png'),'poses':str(dest/f'poses_{batch}.png'),'prompt':str(dest/f'prompt_{batch}.txt'),'output':str(dest/f'generated_{batch}.png')})
    (OUT/'batches.json').write_text(json.dumps(batches,indent=2)+'\n','utf-8');print(json.dumps({'batches':len(batches),'unique_poses':sum(sum(n is not None for n in b['slots']) for b in batches)}))

if __name__=='__main__':main()
