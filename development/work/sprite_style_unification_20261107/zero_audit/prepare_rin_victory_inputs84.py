"""Prepare distinct victory keys; preserve idle0/refined5 and derive flashes later."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';P=D/'prepared_rising_rear_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='223e553f97ecc85d52b085f3e0e6cd46ecc914063f1adcef43fd1d34c25d298e'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,192)
for name,refs,cols,scale in [('victory_detail01',[1,2,3,4],2,8),('victory_detail02',[6],1,16)]:
 O=D/name;assert not O.exists();O.mkdir();rows=(len(refs)+cols-1)//cols;im=Image.new('RGBA',(96*cols,80*rows));frames=[]
 for i,n in enumerate(refs):
  a,_=render(arc,1,5,n);v=rgba(a,pal);outside=a.copy();outside[112:192,112:208]=0;assert not np.any(outside)
  im.paste(v.crop(crop),(i%cols*96,i//cols*80));Image.fromarray(a).save(O/f'b1_{n:03}_before_indices.png');frames.append({'key':f'b1_{n:03}','bank':1,'ref':n,'cell':[i%cols,i//cols],'bounds':v.getbbox()})
 im.save(O/'native_input.png');im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST).save(O/'input.png')
 for label,b,n in [('idle147',0,147),('refined_victory5',1,5)]:rgba(render(arc,b,b*5,n)[0],pal).crop(crop).resize((768,640),Image.Resampling.NEAREST).save(O/f'{label}.png')
 meta={'actual_input_arc':str(P.relative_to(ROOT)),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,80],'columns':cols,'rows':rows,'scale':scale,'native_origin':[160,160],'palette_words':list(pal),'frames':frames,'game_unchanged':True,'generated':False,'scope':'이미 세밀한대기0/147·승리5는 보존. 전신 동일이 아닌나머지승리자세를 각기 재작화한다.7/8섬광은 새3에서별도네이티브파생.'}
 (O/'inputs.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8')
 quantity='four distinct target poses in their exact2x2cells'if len(refs)==4 else 'one target pose in its exact single cell'
 prompt=f'''Use case: precise-object-edit. Repaint only the FIRST image: {quantity}, Rin, the white bob-haired blue-and-white maid. Second image is approved idle and third is her newly refined raised-hand victory pose; match their detailed native pixel-art quality, not their poses. Keep the first image's exact view direction, head/crown/eye centers, neckline, hand and short tool-grip positions, elbow bends, waist, thigh/knee angles, ankles and grounded toe positions. The character faces RIGHT here; never paste a left-facing idle head. Preserve each subtle turn and different arm placement; do not duplicate one pose across cells. No redesign, no enlarged head or new long weapon. Improve grey hair strand/shadow planes and thin selective navy contours, clear facial planes, chest ribbon/cuff/apron straps, skirt pleats and layered hem, stocking/boot seams and coherent cool shading. Keep idle-comparable solid arm/waist/thigh/calf widths, especially avoid pencil-thin supporting legs; do not lengthen limbs or shrink the body. Preserve blue ribbon-tail path and length. Fine late-1990s action-game pixel clusters, not smooth painted faces, messy checker noise, heavy outlines, or flat blank clothes. Existing good fine detail is the style target. Preserve all empty margins and each target's position within the logical96x80cell. The first input canvas is enlarged by exactly{scale} with nearest-neighbor; keep the same composition. Transparent background, no labels/borders/grids/shadows/effects, no white departure outline, no extra accessories. Only repaint visual detail in the target poses, no motion redesign.'''
 (O/'prompt.txt').write_text(prompt+'\n','utf8')
# Reproduce current flash formulas independently before authoring any new pose.
source=render(arc,1,5,3)[0];flashes=[]
for n,r in[(7,1),(8,2)]:
 out=np.zeros_like(source)
 for dy in range(-r,r+1):
  for dx in range(-r,r+1):
   if abs(dx)+abs(dy)<=r:out[np.roll(np.roll(source>0,dy,0),dx,1)]=11 if n==7 else 10
 pale=np.array([0,10,10,10,11,11,10,11,11,11,10,10,11,10,11,11],np.uint8);out[source>0]=source[source>0]if n==7 else pale[source[source>0]]
 assert np.array_equal(out,render(arc,1,5,n)[0]);flashes.append({'ref':n,'body':3,'radius_manhattan':r,'current_reproduction_difference_pixels':0,'future_requires_new_body_sync':True})
report={'source_sha256':sha(arc),'actually_viewed':['victory_after84/normal_0_to_7.png','victory_after84/black_0_to_7.png'],'body0_equals_idle147':bool(np.array_equal(render(arc,1,5,0)[0],render(arc,0,0,147)[0])),'ref5_already_refined_and_preserved':True,'new_distinct_keys':[1,2,3,4,6],'exact_fullbody_aliases_between_targets':False,'flash_reproduction':flashes,'visual_observations':['1/2는 머리·가슴의 넓은 단색 면과 짧은 단색 앞치마가 대기보다 단순하다. 손과 리본끝의 위치는 서로 달라 같은 전신으로 묶지 않는다.','3/4는 몸의 회전과 팔이 다르다. 검정 상의 내부가 뭉쳐 보이고 머리 안쪽 음영·커프·치마 주름도 새5보다 부족하다.','6은 새5와 이어지는 손 올림이지만 기존 흰 머리 덩어리·가슴 단색·긴 단순 부츠가 남아 신규원화가 필요하다.','7/8은 독립 새 몸체가 아니라3에서 파생한 흰 외곽 섬광이다. 새3과 동시에 실루엣을 동기화하고 순수빛9..13은 보존해야 한다.'],'planned_art_pages':['victory_detail01','victory_detail02'],'generated':False,'runtime_verified':False}
(D/'victory_after84/plan.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'pages':report['planned_art_pages'],'flash_exact':True}))
