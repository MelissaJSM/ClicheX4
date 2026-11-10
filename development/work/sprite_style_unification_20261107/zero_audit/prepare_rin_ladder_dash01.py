"""사다리 베기 후속2·질풍아 준비2의 정확 포즈 입력과 공유 근거."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent/'rin_extension';P=D/'prepared_followthrough01/PL01_U.ARC';O=D/'ladder_dash01';assert not O.exists();O.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();arc=P.read_bytes();assert sha(arc)=='d3bee17d11b9181d96395fcd0274353f78ef5f7f1bc7c8c5428e573fae3d88b8'
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,104,208,200);native=Image.new('RGBA',(192,192));frames=[];aliases={199:[199,201],202:[202,204,206,208,210],155:[155],156:[156]}
for i,n in enumerate((199,202,155,156)):
 a=render(arc,0,0,n)[0];pic=rgba(a,pal);outside=a.copy();outside[104:200,112:208]=0;assert not outside.any();x,y=i%2,i//2;native.paste(pic.crop(crop),(x*96,y*96));pic.save(O/f'b0_{n:03}_before.png');Image.fromarray(a).save(O/f'b0_{n:03}_before_indices.png')
 for ref in aliases[n]:assert np.array_equal(a,render(arc,0,0,ref)[0])
 bank=graphics_bank(entry(arc,2),0);f=bank['frames'][n];frames.append({'key':f'b0_{n:03}','bank':0,'ref':n,'cell':[x,y],'bounds':pic.getbbox(),'source_canvas_sha256':sha(a.tobytes()),'same_stream_refs':[q['index']for q in bank['frames']if q['offset']==f['offset']],'exact_display_aliases':aliases[n],'tile_count':f['tile_count'],'part_count':len(composition_frame(entry(arc,3),0,n)['parts'])})
native.save(O/'native_input.png');native.resize((1536,1536),Image.Resampling.NEAREST).save(O/'input.png')
for label,b,n in [('idle147',0,147),('refined_ladder197',0,197),('refined_dash49',0,49)]:rgba(render(arc,b,b*5,n)[0],pal).crop(crop).resize((768,768),Image.Resampling.NEAREST).save(O/(label+'.png'))
info={'actual_input_arc':rel(P),'archive_sha256':sha(arc),'source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','character':'rin','crop':crop,'native_cell':[96,96],'columns':2,'rows':2,'scale':8,'native_origin':[160,160],'palette_words':list(pal),'frames':frames,'game_unchanged':True,'scope':'사다리 베기 animation93 후속199/202 두키의 정확사본7참조와 질풍아155/156 준비2. 원래손/팔/무릎/발/머리각도·타이밍·검기 별도 자원 보존.'}
(O/'inputs.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n','utf8')
prompt='''Use case: precise-object-edit. Edit FIRST image only, four original Rin maid pixel sprites, in exactly the same 2x2 layout. Each cell is96x96 native pixels enlarged8x, output1536x1536 with transparent background. Other images are the approved precise new Rin idle, ladder-saber raised-hand and dash poses for character/style reference only.
TOP LEFT and TOP RIGHT: two DIFFERENT airborne/ladder saber follow-through poses facing screen left, front glove extended diagonally down-left, rear arm held to the right, long descending leg and a bent back knee. Keep their differences in arm angles, head position, skirt tilt and flowing ribbon. BOTTOM LEFT and BOTTOM RIGHT: two DIFFERENT low horizontal ground-dash preparation poses facing screen left, chest forward, deeply folded front knee, trailing extended leg and rightward ribbon. Do not turn these into upright running.
Preserve the exact source pose, head angle/eye location, short neck, elbow/wrist/glove centers, shoulder line, hip/knee/ankle/toe positions and each silhouette's overall native width and height. Add finer hair-strand shadow planes, cyan iris, collar and blue bow, structured folds in dark bodice and large white cuffs, a crisp paneled apron/hem, and natural substantial thigh/boot details comparable to the reference. Use selective navy/gray contours rather than flat blobs. Do not make the calf longer, enlarge the head, widen the silhouette, merge the two feet or change the knee bend. The top two descending toes must stay at their original height. Do not copy a reference head into a different angle. No long weapon, new blade/shaft, extra effects, scenery, guide lines, labels or extra sprites. Maintain blank cell margins, no cell recentering or resizing. Crisp readable native pixel clusters, no blur or smooth illustration.'''
(O/'prompt.txt').write_text(prompt+'\n','utf8');print(json.dumps({'out':str(O),'keys':4,'proven_alias_refs':sum(map(len,aliases.values()))}))
