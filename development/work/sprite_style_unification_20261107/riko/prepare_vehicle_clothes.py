"""체이서의 서로 다른 기울기3개를 실제 원점과 팔/발 위치로 준비한다."""
from pathlib import Path
import sys,json,hashlib,struct
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
W=ROOT/'work/sprite_style_unification_20261107';P=W/'riko/prepared_jump_clothes_v1/PL01_U.ARC'
sha=lambda b:hashlib.sha256(b).hexdigest();arc=P.read_bytes()
assert sha(arc)=='95867666de2ab6a0a3712de5b047a0c6f44fb827d74cc6b2d873f854739b84e9'
D=W/'riko/vehicle_clothes09';D.mkdir(exist_ok=False)
pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,192);sheet=Image.new('RGBA',(2304,640));rows=[]
for i,n in enumerate([25,33,41]):
    a=render(arc,1,5,n)[0];pic=rgba(a,pal);pic.save(D/f'b1_{n:03}_source.png')
    sheet.paste(pic.crop(crop).resize((768,640),Image.Resampling.NEAREST),(768*i,0))
    rows.append(dict(bank=1,ref=n,cell=i,source_sha256=sha(a.tobytes())))
sheet.save(D/'targets.png');style=Image.new('RGBA',(2304,640))
for i,(b,n)in enumerate([(0,147),(1,17),(0,213)]):
    pic=rgba(render(arc,b,b*5,n)[0],pal);style.paste(pic.crop(crop).resize((768,640),Image.Resampling.NEAREST),(768*i,0))
style.save(D/'accepted_style.png')
(D/'inputs.json').write_text(json.dumps(dict(parent=str(P.relative_to(ROOT)),sha256=sha(arc),native_cell=[96,80],crop=crop,frames=rows),indent=2)+'\n','utf8')
prompt='''Refine the FIRST supplied sprite sheet, exactly THREE cells in one row, transparent background. Each cell is96x80 native pixels shown8x(768x640). These are three DIFFERENT lean angles of Riko riding a fast hoverbike in PlayStation Mega Man X4. Preserve the first reference's precise lean, bent knees, forward extended hands gripping an invisible handlebar, boot sole locations, shoulder-to-hand reach, head angle, green hair outline and head size. Do not draw the vehicle. Do not straighten to standing or enlarge the crouched body. SECOND sheet is detail/style only: accepted idle, detailed riding posture and airborne outfit. Make FIRST poses match that same pixel craft: detailed white fitted jacket, collar, short pleated white waist/skirt, light-gray cloth folds, layered white cuffs and gray boot side planes/heels, thin selective dark outline. Keep the cyan-lined white cape attached at the same shoulder and flowing in the first reference's direction, with original silhouette. Keep joints and limb lengths, purple eye and green bob hair. No thick dark outline, no blurred or smooth illustration, no solid featureless boots, no smaller chibi body. Do not merge three poses; keep each centered at its original coordinate inside its own cell. No text, grid, weapons, scenery or effects. Preserve all original contact coordinates while refining only pixel detail.'''
(D/'prompt.txt').write_text(prompt+'\n','utf8')
print(str(D))
