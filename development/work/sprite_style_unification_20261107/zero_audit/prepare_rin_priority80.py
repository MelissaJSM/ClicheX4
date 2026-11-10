"""Review pending bodies and prepare four upward-slash rear poses, no art edits."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
from src.psx_player import graphics_bank
D=Path(__file__).parent/'rin_extension';O=D/'priority_after80';O.mkdir(exist_ok=True)
P=D/'prepared_rear_continuation2_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='a565e55fb422764432b03fe60d53430fcd5ede2aa95829a655a9c22bcc902c4d'
pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
ledger=json.loads((D/'progress_ledger.json').read_text('utf8'));done=set(ledger['new_art_prepared_refs'])
groups=[('rising_rear',[(1,n)for n in(148,150,152,154)]),('victory_return',[(1,n)for n in(1,3,6,7)]),('movement_wall',[(0,n)for n in(34,36,38,41,45)]),('hurt_lowhp',[(0,n)for n in(135,139,149,152)]),('air_wall_special',[(0,229),(1,54),(1,133)]),('ride',[(1,17),(1,31)]),('spin',[(1,n)for n in(161,163,167,173)]),('burst_transition',[(1,n)for n in(177,179,186,189)])]
keys=[(label,b,n)for label,keys in groups for b,n in keys];rows=[]
for label,b,n in keys:
 key=f'b{b}_{n:03}';assert key not in done
 a,m=render(arc,b,b*5,n);bank=graphics_bank(entry(arc,2),b)
 rows.append({'key':key,'group':label,'bbox':rgba(a,pal).getbbox(),'tiles':m['tile_count'],'shared_stream_refs':[f['index']for f in bank['frames']if f['offset']==m['stream_offset']]})
for form,words in [('normal',pal),('black',black)]:
 for i in range(0,len(keys),8):page([(f'b{b}_{n:03} {label}',rgba(render(arc,b,b*5,n)[0],words))for label,b,n in keys[i:i+8]],rgba(render(arc,0,0,147)[0],words),O/f'{form}_{i//8:02}.png',cols=4,scale=4)
(O/'manifest.json').write_text(json.dumps({'source':str(P.relative_to(ROOT)),'sha256':sha(arc),'refs':rows,'scope':'80수정분 이후 남은 대표30참조의 우선순위 재검토. 전동작 새그림 수를 뜻하지 않으며 자동완료판정 없음.','art_review_pending':True},ensure_ascii=False,indent=2)+'\n','utf8')
I=D/'rising_rear01';assert not I.exists();I.mkdir();crop=(112,112,208,192);native=Image.new('RGBA',(192,160));frames=[]
for i,n in enumerate((148,150,152,154)):
 a,m=render(arc,1,5,n);im=rgba(a,pal);outside=a.copy();outside[crop[1]:crop[3],crop[0]:crop[2]]=0;assert not np.any(outside)
 native.paste(im.crop(crop),(i%2*96,i//2*80));Image.fromarray(a).save(I/f'b1_{n:03}_before_indices.png');frames.append({'key':f'b1_{n:03}','bank':1,'ref':n,'cell':[i%2,i//2],'bounds':im.getbbox(),'preserve_effect_ref':n+1})
native.save(I/'native_input.png');native.resize((1536,1280),Image.Resampling.NEAREST).save(I/'input.png')
for name,n in [('idle147',147),('refined_rear186',186)]:rgba(render(arc,0,0,n)[0],pal).crop(crop).resize((768,640),Image.Resampling.NEAREST).save(I/f'{name}.png')
meta={'actual_input_arc':str(P.relative_to(ROOT)),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,80],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':frames,'game_unchanged':True,'generated':False,'scope':'뒤쪽을 향해 몸을 돌려 올려치는 용염인4몸체. 기존 검기·불꽃149/151/153/155는 생성입력에 넣지 않고 네이티브 공유보존 대상으로 별도 관리한다.'}
(I/'inputs.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Repaint only the FIRST image, four different upward-slash body sprites of Rin, a white bob-haired maid, in a fixed 2-column2-row transparent sprite sheet. Second image is her newly refined rear-view pose for the exact hair-strand and outfit-fold quality; third is approved idle for fine native pixel rendering and body proportions. Preserve each target's original body position, size and distinct bent-knee/boot pose. These are rear-three-quarter views turned away while raising the hand at the RIGHT above the head; do not turn them into front-facing uppercuts. Keep the existing crown, neck, shoulders, raised wrist/hand center and the tiny tool grip fixed. Do not create a long blade or mop head: the original game will draw the separate attack effect. Do not copy the front idle head into a rear pose. Retain the source's lower hand, elbow, waist, bent knee, both ankles/toes, ribbon length and curve. Preserve the existing differences between all four poses instead of drawing one pose four times. The bodies are intentionally LEFT of each cell center and retain those coordinates. Add delicate cool-grey hair lock/shadow planes and selective thin navy contours, clear cuff folds and wrist anatomy, back-uniform seams/apron straps, waist and layered pleated skirt/hem detail, and coherent stocking/boot shading. Match the approved idle's slender but solid upper arms, waist, thighs and calves; no pencil-thin neck/forearm or long thin boot. The raised arm must still connect naturally through shoulder/elbow/wrist while keeping its hand fixed. Do not broaden silhouettes arbitrarily or lengthen a leg to add detail. Use crisp clustered late-1990s action-game pixel art, not smooth illustration, scribbled texture, thick outlines, or plain flat colored masses. Exactly four transparent sprites, no labels/borders/grid/background, no ladder, fire, energy, saber effects or extra equipment. Fixed logical192x160 canvas, four96x80cells, enlarged8x to1536x1280; preserve all per-cell anchors and offsets. Change rendering detail, not motion or outfit identity.'''
(I/'prompt.txt').write_text(prompt+'\n','utf8');print(json.dumps({'review':str(O),'remaining_keys':len(keys),'next_input':str(I)}))
