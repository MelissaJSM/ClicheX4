"""빙열참 준비144와 회전 두 기준 자세의 자체 제작 원화를 준비한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent/'rin_extension';P=D/'prepared_ice01/PL01_U.ARC';O=D/'ice_spin02';O.mkdir(exist_ok=True)
assert not(O/'inputs.json').exists();sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
arc=P.read_bytes();assert sha(arc)=='70b483ba78dedefa9c4af45c9b4c5fe4fb8ef915290a4c92c1dd5dea6b0b01d8'
pal=struct.unpack_from('<16H',entry(arc,9));bank=graphics_bank(entry(arc,2),1);crop=(112,112,208,208);native=Image.new('RGBA',(288,96));records=[]
for i,n in enumerate((144,161,163)):
 a=render(arc,1,5,n)[0];pic=rgba(a,pal);outside=a.copy();outside[crop[1]:crop[3],crop[0]:crop[2]]=0;assert not outside.any()
 native.paste(pic.crop(crop),(i*96,0));Image.fromarray(a).save(O/f'b1_{n:03}_before_indices.png');pic.save(O/f'b1_{n:03}_before.png');f=bank['frames'][n]
 records.append({'key':f'b1_{n:03}','bank':1,'ref':n,'cell':[i,0],'bounds':pic.getbbox(),'source_canvas_sha256':sha(a.tobytes()),'same_stream_refs':[g['index']for g in bank['frames']if g['offset']==f['offset']],'tile_count':f['tile_count'],'part_count':len(composition_frame(entry(arc,3),5,n)['parts'])})
native.save(O/'native_input.png');native.resize((2304,768),Image.Resampling.NEAREST).save(O/'input.png')
for label,b,n in [('idle147',0,147),('refined_tuck213',0,213),('refined_ice138',1,138)]:rgba(render(arc,b,b*5,n)[0],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(O/f'{label}.png')
data={'actual_input_arc':rel(P),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':3,'rows':1,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':records,'generated':False,'game_unchanged':True,'scope':'빙열참 별도 준비144와 공중회전161/163 두 방향의 새 정밀 원화. 회전 확장 때159.5 중심과 원검기 보호. 기타방향의 원래대각선 차이는 별도 검토.'}
(O/'inputs.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='Use case: precise-object-edit. Edit FIRST image only: one horizontal row of THREE Rin maid sprites, three equal 96x96 native cells enlarged8x. The other images are accepted finely detailed pixel-art STYLE references of the exact same character. Left pose is a crouched preparation with both feet planted. Middle pose is an airborne tightly tucked spinning pose. Right pose is the same style of tucked airborne body tilted diagonally almost horizontally, head pointing left and feet pointing right. Keep those exact distinct poses, each facing and head center, glove and short mop grip positions, bent knee shapes, boot angles and toe positions, and trailing blue ribbon direction. Do not straighten or rotate any body. Repaint ENTIRE body with the refined references level of separated cool-gray hair locks, compact face and cyan eye, selective navy contours, structured collar and chest bow, substantial cuff folds, apron/skirt seams and boot highlights/shadow planes. Preserve compact original height and substantial thighs/upper arms; no flat white blobs, enlarged head or thin stick limbs. Keep each exact pose scale and position in its cell. For the two spin poses preserve their existing rotation pivot and tuck. No long weapon shaft, blade, trail, ice or effects. Output exactly2304x768, THREE sprites in one row only, unchanged cell margins. Crisp native pixel-art clusters. Transparent background. No text, labels, grid, scene, ground shadows, blur, extra characters or fourth sprite.'
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(O)
