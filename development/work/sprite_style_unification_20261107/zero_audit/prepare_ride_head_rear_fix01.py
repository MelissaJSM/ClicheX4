"""후면 머리 두 각도의 높이 보완용 원화 입력을 별도로 만든다."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import rgba
D=Path(__file__).parent/'rin_extension';O=D/'ride_head_rear_fix01';O.mkdir(exist_ok=False)
j=json.loads((D/'ride_head01/inputs.json').read_text('utf8'));pal=j['palette_words']
new=Image.new('RGBA',(64,32));old=Image.new('RGBA',(64,32))
for i,n in enumerate((75,77)):
 a=np.array(Image.open(D/'ride_head_registered_v1'/f'head_{n}_indices16.png'));p=rgba(a,pal);new.paste(p,(i*32+8,8))
 old.paste(Image.open(D/'ride_head01'/f'head_{n}_native.png'),(i*32,0))
for name,p in [('input',new),('original_height_reference',old)]:
 p.save(O/f'{name}_native.png');p.resize((1024,512),Image.Resampling.NEAREST).save(O/f'{name}.png')
prompt='''Use case: precise-object-edit. Edit the FIRST transparent image only. It contains TWO tiny rear/three-quarter-back heads of the SAME Rin maid, in two fixed32x32 cells side by side enlarged16x, total1024x512. Preserve both cell centers, different facing/tilt, the tiny lower chin/neck attachment at native row23, and the side ribbon positions. There is no body, no mechanical cockpit, no scenery, no labels.
These two heads currently look vertically compressed: the occupied height is12 native pixels (top row12,bottom23). Restore the natural taller rear skull and maid bonnet to14 pixels (top row10,bottom23), filling TWO additional pixel rows at the crown while keeping the lower chin endpoint EXACTLY fixed. The second image supplies the original14-pixel silhouette and viewing angles ONLY; do not restore its plain white color blobs. Retain and improve the first image's fine cool-gray layered hair strands, selective navy contour and small white bonnet/ribbon. Do not enlarge width, move the head down, lengthen a neck, squash the face, expose new facial features on the rear view, or add decorations. Both heads must remain inside each central16x16 tile (native x8..23,y8..23), with its first column x8 transparent. Target actual occupied x9..22 or x10..22, y10..23. Use crisp intentional pixel clusters at16x magnification and at most15 cool white/gray/navy/cyan palette colors. The third image is accepted hair-detail style only, not a direction to copy its front-facing face. Transparent background and empty cell padding must remain transparent. Return exactly a1024x512 two-cell sheet.'''
prompt=prompt.replace('The third image is accepted hair-detail style only, not a direction to copy its front-facing face. ','')
(O/'prompt.txt').write_text(prompt+'\n','utf8')
r={'refs':[75,77],'native_canvas':[64,32],'cell':[32,32],'scale':16,'old_height':14,'candidate_height':12,'requested_height':14,'fixed_chin_y':23,'original_source':j['source_arc'],'original_sha256':j['source_sha256'],'references':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in (O/'input.png',O/'original_height_reference.png',D/'ride_head01/idle_head_style0.png')],'scope':'현재 새 머릿결은 유지하고 후두부/보닛 높이만 다시 제작합니다. 원래 단순 머리 덮기나 이미지 세로 늘리기를 하지 않습니다.'}
r['references']=r['references'][:2]
(O/'inputs.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(O)
