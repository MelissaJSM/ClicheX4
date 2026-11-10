"""원US 발사표에 정본총을 맞춘 국소팔 편집 입력. 원몸/효과 불변."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
Y,X=np.indices((384,384));Y-=160;X-=160
def main():
 p=N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());rel=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_hover_muzzle01/report.json';rm=json.loads(rel.read_text('utf8'));origins={q['ref']:q['direction0_xy']for q in rm['origins']};cm=json.loads((D/'canonical_cases_probe_v4/manifest.json').read_text('utf8'));coords=cm['canonical_source_texels'];need(len(coords)==20,'정본총20')
 for page,refs in [('a',[222,224,226,228]),('b',[230])]:
  out=D/f'muzzle_arm_{page}_inputs_v1';out.mkdir(exist_ok=False);side=1536 if len(refs)>1 else 768;boards={name:Image.new('RGBA',(side,side))for name in('current_art','target_pistols','cleared_arm_guide')};frames=[]
  for i,n in enumerate(refs):
   source=D/f'shot_joint_probe_v2/body_{n:03}_indices.png';z=np.array(Image.open(source));ox,oy=origins[n];dx,dy=ox+23,oy+9;gun=np.zeros_like(z)
   for x,y,v in coords:gun[y+dy+160,x+dx+160]=v
   # This is a layout/mask guide only, never a generated or accepted arm.
   head=(X>=-8)&(Y<=-10);erase=(X<1)&(Y>=-15)&(Y<1)&~head;guide=z.copy();guide[erase]=0;guide[gun>0]=gun[gun>0]
   placement=(i%2*768,i//2*768)if len(refs)>1 else(0,0)
   for name,v in [('current_art',z),('target_pistols',gun),('cleared_arm_guide',guide)]:boards[name].alpha_composite(a.rgba(v).crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),placement)
   Image.fromarray(gun).save(out/f'target_gun_{n}.png');Image.fromarray(erase.astype(np.uint8)*255).save(out/f'edit_mask_{n}.png');frames.append({'ref':n,'cell':i,'source':source.relative_to(ROOT).as_posix(),'source_sha256':digest(source),'engine_projectile_origin':origins[n],'canonical_translation':[dx,dy],'muzzle_left_x':ox+1,'barrel_rows':[oy-1,oy],'target_gun_sha256':sha(gun.tobytes()),'policy':'원US 총입구 x=발사점+1을 근거로 정본8px 총을 강체이동. y의 두 총열행은 발사점−1/0. 새 팔만 다시 제작, native 원점/탄환 코드는 불변.'})
  for name,im in boards.items():im.save(out/f'{name}.png')
  count='four sprites in exactly the same 2x2 cells'if len(refs)>1 else'one sprite in exactly the same full canvas'
  prompt=f'''Edit the FIRST transparent pixel-art sheet of an adult game character. Return {count}, preserving the full square canvas, cell margins and character scale. This is a precise LOCAL FIRING-ARM correction, not a redesign. FIRST is the detailed artwork to preserve. SECOND contains the small canonical pink-and-black pistols at their required final coordinates. THIRD is a cleared-arm layout guide showing the unchanged body and the required pistol positions, with the old front arm removed only for clarity. Restore a natural arm in the cleared area, without copying the erased boundary into the final art.
Replace ONLY the horizontal forward shooting arm, wrist and grip so it joins the SAME shoulder on the first image to the EXACT pistol position in SECOND. Keep each pistol horizontal and left-facing, with precisely the same compact size, barrel length, colors and silhouette as SECOND. The first and second poses need a farther-reaching arm, while the third and fourth need a shorter bent elbow; follow each corresponding pistol location individually. Never move the whole body or shoulder to reach the pistol. Never lengthen or enlarge the gun. There must be exactly two arms and exactly one pistol, with no leftover gun at the prior position. The other raised/back arm stays unchanged. Preserve the first image's face, eyes, ears, hair curls and shading, torso, black-and-pink outfit and coverage, hip/waist, both legs and propulsion shoes. No flames, bullets, glow, text, markers or guide lines.
Use the same sharp native pixel clusters, fine dark lower contour, tan skin midtone and small wrist/finger shadows as the first image. The new forearm must have plausible consistent thickness and a visible elbow; no blank pale strip, no straight black chest bar, no floating hand and no pink sleeve. Keep the exact detailed body design and coverage. Neutral side-view action-game sprite sheet, no anatomical emphasis. Transparent RGBA background. All edits confined to the existing forward-arm area plus the gap to the new target pistol, with every other body part fixed.'''
  if len(refs)==1:prompt=prompt.replace('The first and second poses need a farther-reaching arm, while the third and fourth need a shorter bent elbow; follow each corresponding pistol location individually.','This one pose needs the wrist slightly farther left and higher to meet its target pistol; follow the exact SECOND-image location.').replace('The other raised/back arm stays unchanged.','The other lowered/back arm stays unchanged.')
  (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'parent_arc_sha256':digest(p),'source_relations':{'path':rel.relative_to(ROOT).as_posix(),'sha256':digest(rel)},'frames':frames,'input_cell_size':[768,768],'native_cell_size':[96,96],'body_art_preserved':True,'files':[{'path':q.relative_to(ROOT).as_posix(),'sha256':digest(q)}for q in sorted(out.iterdir())if q.is_file()],'native_packed':False,'runtime_verified':False})
 print('muzzle arm a4+b1 input saved')
if __name__=='__main__':main()
