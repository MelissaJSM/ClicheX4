"""기존 모드 원화만으로 낙봉파 몸체7키 입력과177 정확공유 후보를 준비한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
R=D/'rin_extension';P=R/'prepared_arrival01/PL01_U.ARC';S=R/'burst_remaining_probe01';arc=P.read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
assert sha(P)=='adf3b9475dd95cad5ff53ba627e4461dc9cb7ec18d202482b59744b0587c0322'
pal=struct.unpack_from('<16H',entry(arc,9));inventory=read(S/'inventory.json');crop=(112,120,208,184)
for dirname,ids in [('burst_charge01',[178,179,180,181]),('burst_recovery01',[186,188,189])]:
 O=R/dirname;O.mkdir(exist_ok=False);sheet=Image.new('RGBA',(192,128));meta=[]
 for i,n in enumerate(ids):
  body=np.array(Image.open(S/f'b1_{n:03}_body_indices.png'));outside=body.copy();outside[crop[1]:crop[3],crop[0]:crop[2]]=0
  # 186의 바닥 y184는 회복페이지에서 1행 여유가 있는 동일크기 창을 쓴다.
  c=(112,121,208,185)if dirname=='burst_recovery01'else crop;outside=body.copy();outside[c[1]:c[3],c[0]:c[2]]=0;assert not outside.any()
  pic=rgba(body,pal).crop(c);pic.save(O/f'b1_{n:03}_body_native.png');Image.fromarray(body).save(O/f'b1_{n:03}_body_indices.png');sheet.paste(pic,(i%2*96,i//2*64))
  y,x=np.nonzero(body);r=next(r for r in inventory['refs']if r['ref']==n);meta.append({'ref':n,'bank':1,'cell':[i%2,i//2],'native_canvas':[96,64],'world_crop':c,'world_origin':[160,160],'body_source_sha256':sha(S/f'b1_{n:03}_body_indices.png'),'original_body_bbox':r['body_bbox'],'floor_y':int(y.max()),'floor_x':np.where(body[y.max()]>0)[0].tolist(),'effect_pixels_excluded':r['effect_pixels']})
 sheet.save(O/'input_native.png');sheet.resize((1536,1024),Image.Resampling.NEAREST).save(O/'input.png')
 for label,gb,pb,n in [('idle_detail',0,0,147),('accepted_low_stance',1,5,182),('accepted_ready_stance',1,5,101)]:rgba(render(arc,gb,pb,n)[0],pal).crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST).save(O/f'{label}.png')
 j={'source_arc':rel(P),'source_arc_sha256':sha(P),'native_sheet_size':[192,128],'requested_size':[1536,1024],'scale':8,'masters':meta,'no_original_game_asset_uploaded':True,'all_effects_excluded':True,'blank_cells':[]if len(ids)==4 else [[1,1]],'rule':'기존 모드의 정확한 효과 이전 원화이며 새 그림에도 효과를 넣지 않는다. 손/짧은자루와 발 접점은 원래좌표로 별도 검사.'};(O/'inputs.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
 count='FOUR'if len(ids)==4 else 'THREE'
 motion=('Top-left raises one gloved arm nearly straight up; top-right has the raised arm slightly bent. Bottom-left swings that raised forearm behind/above her right shoulder while the other hand stays in front. Bottom-right leans forward with one hand extended left and the other trailing on the right. Keep these four distinct arm directions, hands and short grips EXACTLY at their current places.'if len(ids)==4 else 'Top-left is a deep kneeling grounded follow-through, with one boot stretched right. Top-right is the next low stance with a short grip reaching down-left. Bottom-left stands up into recovery. Keep the lower height of the first two stances, not a standing body squashed to fit. Bottom-right MUST stay empty and transparent.')
 prompt=f'''Use case: precise pixel-art sprite style edit. Edit IMAGE 1 only: a transparent 1536 x 1024 sheet of {count} distinct poses of the SAME adult silver-blue-haired maid character, Aokumo Rin. Other images are accepted SAME-character fine-detail references; do not replace the target poses with their poses.

Keep the exact two columns by two rows. The native sheet is 192 x 128 pixels, each cell96x64 enlarged8. Preserve whole-canvas positions, camera angle, body lean, each original hand/glove/short handle, elbow, boot direction and sole contact. {motion}

Redraw the sparse old interior clusters into the fine detail of the references: structured silver/blue hair planes with inner shadow, folded white bonnet, small clear cyan eye/cheek/chin, connected short neck, navy sleeves with selective blue-gray outlines, white cuffs with small folds, blue apron with shaped pleats and white frill, boots with articulated ankle and gray-blue shaded planes. Do not create a round oversized head, long neck, long shins, pin-thin legs, tiny hips, swollen sleeves, mitten hands or broad flat white patches. Keep adult compact body proportions and pose-specific foreshortening. Keep existing ribbon gesture and outfit identity.

This is a detailed pixel-art reworking, not a simple palette filter or smooth painted upscale. Crisp hand-placed square clusters, thin selective dark contour, restrained16-color style, no blur, antialiasing, texture noise or invented ornaments. Preserve all body gestures and core contacts; do not recenter, uniformly resize, lengthen limbs, straighten the crouched knees or copy idle limbs. The short hand grip is part of the pose and must stay its original size and orientation.

ABSOLUTELY NO orb, aura, flame, magic, slash trail, glow, large mop, long shaft, weapon replacement, platform, shadow, grid, text, numbers or labels. The original magic effect was deliberately removed and will be reapplied separately at fixed game coordinates. True transparent background. Output one1536x1024 RGBA image with only the edited sprites in the original cells.'''
 (O/'prompt.txt').write_text(prompt+'\n','utf8')
O=R/'burst177_reuse_probe01';O.mkdir(exist_ok=False);body=render(arc,1,5,101)[0];fx=np.array(Image.open(S/'b1_177_effect_indices.png'));combined=body.copy();combined[fx>0]=fx[fx>0];Image.fromarray(body).save(O/'b1_177_body_indices.png');Image.fromarray(combined).save(O/'b1_177_combined_indices.png')
for form,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(arc,9),row*32);board=Image.new('RGB',(1536,384),'#313b4d');dr=ImageDraw.Draw(board)
 for i,(tag,z)in enumerate([('accepted101',body),('old177',render(arc,1,5,177)[0]),('new177',combined),('original effect',fx)]):
  pic=rgba(z,words).crop((112,112,208,208)).resize((384,384),Image.Resampling.NEAREST);board.paste(pic,(i*384,0),pic);dr.text((i*384+4,4),tag,fill='white')
 board.save(O/f'{form}_comparison.png')
print(json.dumps({'pages':['burst_charge01','burst_recovery01'],'new_masters':7,'alias186187':True,'reuse177':'current b1_101 at exactly identical original body coordinates','effect177_pixels':int(np.count_nonzero(fx))},ensure_ascii=False))
