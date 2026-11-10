"""수용된 린 질감과 원작 특수기술의 대응 시트를 준비한다."""
import json,math,shutil,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_rin_idle import entry
from scripts.project import digest
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_ryuenjin import NEW_BODY as RISE
from src.psx_raijingeki import NEW_BODY as THRUST
from src.psx_rakuhouha import BODY as BURST
from scripts.build_riko_idle import SHIPPUUGA_NEW

OUT=ROOT/'work/ver_rin_nana/style_revision/v4_special'
PARENT=ROOT/'out/ver_rin_nana/rin_style_revision_20261028T230555391846Z'
MASTER=ROOT/'work/ver_rin_nana/style_revision/v3'
GROUPS={'rise':(1,RISE),'burst':(1,BURST),'thrust':(1,THRUST),'dashslash':(0,SHIPPUUGA_NEW)}

def main():
    if OUT.exists():raise ValueError('Do not overwrite special art work')
    pm=json.loads((PARENT/'manifest.json').read_text('utf-8'));arc=(PARENT/'modified.arc').read_bytes()
    if digest(PARENT/'modified.arc')!=pm['modified_archive_sha256']:raise ValueError('Parent changed')
    original=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.arc').read_bytes()
    _,g=entry(original,2);_,parts=entry(original,3);_,pal=entry(original,9);words=struct.unpack_from('<16H',pal)
    OUT.mkdir();frozen=json.loads((MASTER/'master.json').read_text('utf-8'))
    for name in ('master_preview_147.png','accepted_stride.png','accepted_stride_source.png'):
        shutil.copy2(MASTER/name,OUT/name)
    frozen.update({'parent':PARENT.relative_to(ROOT).as_posix(),'bin_sha256':pm['modified_bin']['sha256'],'groups':{}})
    idle=Image.open(OUT/'master_preview_147.png').convert('RGBA');stride=Image.open(OUT/'accepted_stride.png').convert('RGBA');batches=[]
    for group,(bi,ids) in GROUPS.items():
        folder=OUT/group;folder.mkdir();frames={};aliases={};seen={};unique=[];pictures={}
        for n in sorted(ids):
            f=graphics_bank(g,bi)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            pixels,size,bounds,_=compose_indices(raw,f['tile_count'],composition_frame(parts,0 if bi==0 else 5,n));key=(pixels,size,bounds)
            if key in seen:aliases[str(n)]=seen[key];continue
            seen[key]=n;unique.append(n);p=folder/f'before_{n:03d}.png';pictures[n]=save_image(pixels,size,words,p).convert('RGBA')
            frames[str(n)]={'before':p.name,'sha256':digest(p),'bounds':bounds,'size':size}
        guide={'group':group,'graphics_bank':bi,'parts_bank':0 if bi==0 else 5,'parent':frozen['parent'],'parent_sha256':frozen['bin_sha256'],'frames':frames,'aliases':aliases,'sheets':[]}
        (folder/'guide.json').write_text(json.dumps(guide,indent=2)+'\n','utf-8')
        for start in range(0,len(unique),8):
            ns=unique[start:start+8];count=len(ns)+1;cols=3 if count>4 else 2;rows=math.ceil(count/cols);slots=[None,*ns]+[None]*(rows*cols-count)
            template=Image.new('RGBA',(cols*96,rows*96));poses=Image.new('RGBA',template.size);label=Image.new('RGB',template.size,(35,38,48));draw=ImageDraw.Draw(label)
            for i,n in enumerate(slots):
                x=i%cols*96;y=i//cols*96
                template.alpha_composite(idle if n is None else stride,(x+20 if n is None else x+27,y+24))
                if n is None:poses.alpha_composite(idle,(x+20,y+24))
                else:
                    b=frames[str(n)]['bounds'];poses.alpha_composite(pictures[n],(x+48+b[0],y+48+b[1]))
                draw.text((x+3,y+3),'idle' if n is None else str(n),fill='white')
            label.paste(poses,(0,0),poses);batch=start//8
            for name,img in [('template',template),('poses',poses),('guide_labeled',label)]:img.resize((img.width*6,img.height*6),Image.Resampling.NEAREST).save(folder/f'{name}_{batch}.png')
            choreography={'rise':'Rising uppercut: 144/146 wind up;148/150/152/154 show her BACK toward the viewer, torso rotating away, one gloved fist raised above her head, face mostly hidden;156/158 recover. A rear turn, never a forward-facing static uppercut.',
              'burst':'Crouch and brace, turn through the precise original silhouettes, then press one gloved hand toward the floor. The colorful sparks visible in image2 are NOT part of her body: draw only Rin with a short handle in her hand. Original aura is composed separately.',
              'thrust':'Grounded saber lightning thrust, changing from windup into a deep planted forward lunge. Extend her gloved hand exactly along the original attack direction, short handle only. Respect rear torso rotations, never draw a long mop or lightning.',
              'dashslash':'Quick dash slash, the original body turns its back toward the viewer in160 and onward. Match torso twist and extended arm direction. Keep her body compact and connected, no long torso.'}[group]
            prompt=f'''Use case: identity-preserve pixel animation edit. Image1 is the EDIT TARGET, a {cols} column x {rows} row sheet of the USER APPROVED slender Rin. Image2 is ONLY the original Zero choreography in corresponding cells. Image3 is a close view of approved Rin art. First cell and all spare idle cells are CALIBRATION: preserve their idle pose, scale and slender silhouette exactly. Change ONLY the pose in other cells to the corresponding pose in image2. Frame order: {slots}. Keep all{len(slots)} isolated sprites in exactly this layout.
{choreography}
Preserve the narrow angular head, pointed chin, neck gap, narrow waist and long slender lower legs. Navy SHORT sleeves, small angular white cuffs, dark gloves, silver white bob with blue forelock, tiny cyan eyes, cobalt apron over dark navy dress, white apron folds and connected blue/white rear ribbon. No bulky puffy white sleeves, no oversized round face or pillow gloves, no simplified white blobs. Thin single native pixel navy outline and cool gray-blue stepped shading, sharp angular folds, the exact same shading density as image1. Original Zero is ONLY a pose guide; never import armor, helmet, muscular shape or hair. Back views keep a silver bob, blue headband and blue/white trailing ribbon, navy dress back with white apron tie. The hand holds a SHORT mop grip; no long shaft, blade, mop head or effects.
Standing calibration is48 native pixels high on a96x96 native cell. Keep identical head and limb thickness across EVERY pose. Bent and curled poses must stay naturally shorter, never enlarged to fill a cell. Crisp square pixel art at identical pitch throughout, no airbrushing, no glow, no outlines around the whole sheet, no text. Genuinely transparent background. Exact {cols}:{rows} canvas ratio. Keep full silhouettes inside their own cells with clear transparent gaps.'''
            (folder/f'prompt_{batch}.txt').write_text(prompt+'\n','utf-8')
            batches.append({'id':f'{group}_{batch}','group':group,'batch':batch,'slots':slots,'columns':cols,'rows':rows,'template':str(folder/f'template_{batch}.png'),'poses':str(folder/f'poses_{batch}.png'),'prompt':str(folder/f'prompt_{batch}.txt'),'output':str(folder/f'generated_{batch}.png')})
        frozen['groups'][group]={'graphics_bank':bi,'refs':sorted(ids),'unique':len(unique),'aliases':aliases}
    (OUT/'master.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n','utf-8');(OUT/'batches.json').write_text(json.dumps(batches,indent=2)+'\n','utf-8')
    print(json.dumps({'groups':frozen['groups'],'batches':len(batches)}))

if __name__=='__main__':main()
