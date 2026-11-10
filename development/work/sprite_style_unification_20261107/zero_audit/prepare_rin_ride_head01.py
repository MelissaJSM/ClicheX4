"""현재 탑승19참조의 5각도를 단일타일 고정격자 원화로 준비한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame,graphics_bank,decode_stream
D=Path(__file__).parent/'rin_extension';P=D/'prepared_bank1_recovery128/PL01_U.ARC';O=D/'ride_head01';O.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest();arc=P.read_bytes();assert sha(arc)=='07ec6077969f17d08c51ffd8e4326b476e1c6ab5635bea8420faee9528b39a89'
old=(D/'prepared_dash_saber01/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));ps=entry(arc,3);g=entry(arc,2)
families={};frames={};local={};before={}
for n in range(66,86):
 z=render(arc,1,5,n)[0];assert np.array_equal(z,render(old,1,5,n)[0]);c=composition_frame(ps,5,n);assert len(c['parts'])==1
 p=c['parts'][0];assert not p['flip_x']and not p['flip_y'];x=160+p['x'];y=160+p['y'];tile=z[y:y+16,x:x+16].copy();assert np.count_nonzero(tile)==np.count_nonzero(z)
 f=graphics_bank(g,1)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 if n==80:assert not tile.any();continue
 k=sha(tile.tobytes());master=next((m for m,t in local.items()if sha(t.tobytes())==k),n)
 if master==n:local[n]=tile;families[n]=[]
 families[master].append(n);before[n]=z
 frames[n]={'master':master,'world_bounds':[x,y,x+16,y+16],'part':p,'tile_count':f['tile_count'],'stream_offset':f['offset'],'raw_sha256':sha(raw),'tile_sha256':k,'nontransparent':int(np.count_nonzero(tile))}
 rgba(z,pal).save(O/f'b1_{n:03}_before.png')
assert list(local)==[66,75,77,78,81]
sheet=Image.new('RGBA',(64,96));masters=[]
for i,(n,t)in enumerate(local.items()):
 canvas=np.zeros((32,32),np.uint8);canvas[8:24,8:24]=t;im=rgba(canvas,pal);im.save(O/f'head_{n}_native.png');im.resize((1024,1024),Image.Resampling.NEAREST).save(O/f'head_{n}_reference.png');sheet.alpha_composite(im,(i%2*32,i//2*32))
 masters.append({'ref':n,'cell':[i%2,i//2],'local_tile_rect':[8,8,24,24],'aliases':families[n],'existing_native_bbox':im.getbbox()})
sheet.save(O/'input_native.png');sheet.resize((1024,1536),Image.Resampling.NEAREST).save(O/'input.png')
idle=render(arc,0,0,147)[0];rgba(idle,pal).crop((136,128,168,160)).resize((1024,1024),Image.Resampling.NEAREST).save(O/'idle_head_style.png')
rgba(idle,pal).crop((112,112,208,208)).resize((1536,1536),Image.Resampling.NEAREST).save(O/'idle_full_style.png')
sources=['scripts/prepare_rin_ride_heads.py','scripts/normalize_rin_ride_heads.py','scripts/build_rin_ride_heads.py','scripts/assemble_rin_chaser.py']
j={'source_arc':str(P.relative_to(ROOT)),'source_sha256':sha(arc),'palette_words':list(pal),'native_canvas':[64,96],'cell':[32,32],'columns':2,'rows':3,'scale':16,'empty_cell':[1,2],'masters':masters,'frames':frames,'blank80_preserved':True,'existing19_world_offsets_different_but_local5_exact':True,'prior222_ride_display_exact':True,'source_code':[{'path':s,'sha256':sha((ROOT/s).read_bytes())}for s in sources],'scope':'다섯 각도의 작은 머리만 재작화한다. 단일16×16타일과 원래 얼굴 위치·빈80을 보존한다. 전신이나 탈것은 생성 입력에 넣지 않는다.'}
(O/'inputs.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Edit FIRST image only, a transparent1024x1536 sprite sheet containing FIVE very small heads of the SAME Rin maid character. Grid is2columns by3rows, each32x32 native pixels enlarged16x; bottom-right cell is EMPTY and must remain empty. Each tiny head occupies the central16x16 native tile within its32x32 cell. Preserve the exact layout, head position, tilt, facing and neck/chin endpoint in every cell. Do NOT enlarge heads or add bodies, shoulders, a long neck, scenery, labels or other characters.
The second and third images are accepted HEAD DETAIL and full-character style references only. Do not copy their head angle into every cell. Refine the existing five angles individually: upper-left left-facing three-quarter; upper-right turning further left; middle-left mostly rear/back hair with no new face; middle-right and lower-left preserve their existing two left-facing tilts. Preserve the small side ribbon and white/cool-gray hair identity.
Replace large featureless white patches with controlled cool-gray layered hair, selective dark-navy edge pixels, compact visible cyan eye where already visible, a clear small cheek/chin, and readable side ornament. Use deliberate crisp native pixel clusters at the SAME tiny size, no smoothing, no gradients, no fine high-resolution painting that vanishes when sampled. Keep natural human head proportions and keep leftmost column of each16x16 tile completely transparent; do not grow outside the original tile. Maintain clear transparency and all cell padding. Output exactly this transparent2x3 sheet with only five refined heads.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8')
print(json.dumps({'path':str(O),'families':families,'source_sha256':sha(arc)}))
