"""새 등장5몸체의 고정 원점 입력과 부모 섬광 파생 증거를 만든다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.rin_effects import derive_arrival
R=Path(__file__).parent/'rin_extension';P=R/'prepared_chaser01/PL01_U.ARC';O=R/'arrival_detail01';O.mkdir(exist_ok=False)
arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
assert sha(arc)=='99603ab0c003149a4fa415b3dcea78a0967a3be615d226471888bb3ece092a11'
g=entry(arc,2);ps=entry(arc,3);pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
def native(n):
 f=graphics_bank(g,0)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 return compose_indices(raw,f['tile_count'],composition_frame(ps,0,n))
b,size,bb,_=native(249);derived=derive_arrival(g,ps,(b,size));flash=[]
for n,(pixels,sz)in derived.items():
 current= native(n);assert pixels==current[0] and sz==current[1]
 flash.append({'ref':n,'parent_native_exact':True,'body_source':249,'fill_index':11,'outline_index':10,'radius':2 if n==247 else 0,'pixels_sha256':sha(pixels),'bounds':current[2]})
sheet=Image.new('RGBA',(192,192));crop=(112,120,208,184);masters=[]
for i,n in enumerate(range(249,254)):
 a=render(arc,0,0,n)[0];Image.fromarray(a).save(O/f'b0_{n:03}_indices.png');pic=rgba(a,pal).crop(crop);pic.save(O/f'b0_{n:03}_native.png');sheet.paste(pic,(i%2*96,i//2*64))
 yy,xx=np.nonzero(a);eye=np.argwhere((a==15)&(np.indices(a.shape)[0]<160));floor=int(yy.max());f=graphics_bank(g,0)['frames'][n];c=composition_frame(ps,0,n)
 masters.append({'ref':n,'bank':0,'cell':[i%2,i//2],'world_origin':[160,160],'world_crop':crop,'native_canvas':[96,64],'bbox':rgba(a,pal).getbbox(),'eye_world':eye[:,::-1].tolist(),'floor_y':floor,'floor_x':np.where(a[floor]>0)[0].tolist(),'tile_count':f['tile_count'],'parts_count':len(c['parts']),'source_sha256':sha(a.tobytes())})
sheet.save(O/'input_native.png');sheet.resize((1536,1536),Image.Resampling.NEAREST).save(O/'input.png')
for name,n,bank,pb in [('idle_full_reference',147,0,0),('new_victory6_detail_reference',6,1,5)]:
 rgba(render(arc,bank,pb,n)[0],pal).crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST).save(O/f'{name}.png')
for form,words in [('normal',pal),('black',black)]:
 board=Image.new('RGB',(1536,768),(28,34,45));dr=ImageDraw.Draw(board)
 for i,n in enumerate([147,*range(249,254)]):
  a=render(arc,0,0,n)[0];pic=rgba(a,words).crop((112,112,208,208)).resize((384,384),Image.Resampling.NEAREST);x=i%4*384;y=i//4*384;board.paste(pic,(x,y),pic);dr.text((x+4,y+4),str(n),fill='white')
 board.save(O/f'{form}_source_review.png')
j={'source':rel(P),'source_sha256':sha(arc),'masters':masters,'master_count':5,'native_sheet_size':[192,192],'output_size':[1536,1536],'scale':8,'blank_cell':[1,2],'body_refs':list(range(249,254)),'derived_flash_refs':[247,248],'parent_flash_rule_reproduction':flash,'pure_beam_refs_preserve':list(range(53,61)),'only_authored_mod_sprites_used':True,'original_game_assets_sent':False,'scope':'등장5몸체의 원포즈/발바닥/손 위치를 유지하며 세부를 재작화한다.247/248은 새 원화로 그리지 않고 부모에서 정확히 재현한 기존규칙으로249에서 파생한다.'}
(O/'inputs.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise pixel-art sprite style edit. Edit IMAGE 1 only. It is a transparent 1536 x 1536 sprite sheet of FIVE distinct arrival poses of the SAME adult blue-haired maid character, Aokumo Rin. Images 2 and 3 are accepted same-character style/detail references only, not pose replacements.

Keep the exact TWO columns by THREE rows. Each native cell is 96 x 64 pixels enlarged 8 times; the underlying full sheet is 192 x 192 native pixels. The bottom-right sixth cell must remain EMPTY and transparent. Do not add a sixth pose. Keep all five original whole-canvas positions and the original camera/left-facing angles. Top-left and top-right are nearly straight arrival stances with the boots close together, middle-left is beginning to spread her feet, middle-right and bottom-left settle into the wider ready stance. Preserve their FIVE distinct arm/hand gestures, leg bends, boot directions, skirt sway, head angles, and body widths.

Redraw the interiors and selective outlines to match the refined pixel detail in reference images: fine blue hair strand planes and inner shadows, readable tiny cyan eye and cheek/jaw, folded white bonnet, dark sleeves with selective blue-gray contour, white cuffs with folds, royal-blue chest/apron with pleats, small white frill details, boots with shaped gray-blue shadows and thin articulated ankles. Maintain this character's maid outfit and compact adult proportions. The existing large flat color chunks should become crisp 16-color-style hand-placed pixel clusters with small meaningful detail, NOT extra decoration, smoother painting, blur or a dense noisy texture.

Critical: keep the same native scale and each pose's eye/face position, chin, original glove positions and boot sole contacts. Do not lengthen necks, thighs or shins, enlarge a rounded head, shrink the torso, widen every silhouette, or make legs thin lines. The nearly straight poses are taller than the wider ready pose because their legs are straight; do not resize them to have the same total bounding-box height. The bottommost boot line in each cell remains native y=63. Keep each original foot X and each individual hand gesture. Do not copy the idle stance or victory gesture into these arrival poses. Do not move or recenter the whole body.

No beam, glow, outline aura, sparkles, weapon, prop, platform, labels, numbers, text, grid or reference panels. Actual transparent background. Output exactly one 1536 x 1536 RGBA sheet, five edited poses in their original cells, last cell empty.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(json.dumps({'masters':masters,'flash_proof':flash},ensure_ascii=False))
