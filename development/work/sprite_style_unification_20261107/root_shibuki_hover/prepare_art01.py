from pathlib import Path
import sys,json,hashlib
from PIL import Image
W=Path(__file__).resolve().parent.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
D=Path(__file__).resolve().parent
p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(p.read_bytes())=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e';a=Archive(p.read_bytes())
target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size);crop=(112,112,208,208)
for row,n in enumerate((221,223)):
 for col,mask in enumerate((8,15)):
  pos=(768*col,768*row)
  target.alpha_composite(a.composite(n,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
  style.alpha_composite(a.composite(0 if row==0 else 45,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
for name in('art01_inputs_actual.png','style_inputs_actual.png','art01_prompt.txt','art01_inputs_actual.json'):assert not(D/name).exists()
target.save(D/'art01_inputs_actual.png');style.save(D/'style_inputs_actual.png')
prompt='''Use case: identity-preserve.
Asset type: transparent console pixel-art sprite sheet refinement.
Image 1 is the EDIT TARGET. Exactly two columns and two rows, each cell a 96x96 logical-pixel square enlarged eight times. Keep the exact cell layout, origin(48,48), head size, eyes, foot soles and large silhouette. Do not crop, recenter or stretch the figures. Image 2 is the accepted DETAIL STYLE reference (top idle, bottom airborne), not a replacement pose.
Both columns depict the same lavender-haired fox-eared heroine facing LEFT; the columns differ only in the torso costume. Both retain identical dark-purple/black flight boots, bent knees and rear trailing boot. Keep the exact two boot soles/ankles in Image 1 because fixed jet effects join them later. Do not draw flames, shadows, weapons, energy effects, labels or grid.
TOP ROW: floating in a slightly side-on posture, her near arm bent with a raised fist above/just behind her head; opposite forearm is held near her waist. BOTTOM ROW: floating in the same direction, but the raised near hand is lowered to the forehead/saluting height, with the elbow bent forward. Preserve the distinct hand heights and original shoulders/waist/knees. Each figure has exactly two arms and legs.
LEFT COLUMN: white/light-lavender sleeves with purple folded shadows, red-and-white short shrine outfit, red ribbon by the fox ears, lavender braid and gold eye. These are the accepted basic upper clothes with dark flight boots.
RIGHT COLUMN: black/dark purple body and sleeves with gold trim, buttons/fasteners, restrained pale collar, small dark/gold head ornament. Lavender ears/hair/braid and gold eye remain the same. Preserve the visible rear draped cloth. No broad white sleeves or red head ribbon on this column.
Refine the overly flat target hair into the accepted idle's clearly separated lavender strands/planes, keep clean ear interiors, one clear gold iris, coherent clothing folds and cuff/waist/hem separation. Detail and contour weight must match Image 2. Preserve short rounded proportions and all anchors. Use controlled two-to-three-tone pixel clusters with a thin dark contour; no thick black halo, blur, scratchy hatching or antialiasing. All four subjects retain the target poses, with the same amount of empty space. True transparent background.'''
(D/'art01_prompt.txt').write_text(prompt,'utf8')
report={'parent_sha256':sha(p.read_bytes()),'refs':[221,223],'masks':[8,15],'style_refs':[0,45],'crop':list(crop),'cell_native':[96,96],'origin_in_cell':[48,48],'grid':[2,2],'image_roles':{'art01_inputs_actual.png':'편집 대상','style_inputs_actual.png':'대기·공중 세부 묘사 기준'},'correction':'처음 mask0 입력은 아머 전용 하체가 없어 제외했다. 실제 비완전체 호버의 다리파츠8과 전체15를 사용한다. 최초 입력은 진단용으로 보존.','files':{n:sha((D/n).read_bytes())for n in('art01_inputs_actual.png','style_inputs_actual.png','art01_prompt.txt')}}
(D/'art01_inputs_actual.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(report,ensure_ascii=False))
