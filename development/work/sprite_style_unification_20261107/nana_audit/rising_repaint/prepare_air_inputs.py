"""공중 라이징103/104 기본·포스4그림의 원점 보존 편집 입력. 새 도트 생성 없음."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 p=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';data=p.read_bytes()
 assert sha(data)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa'
 a=Archive(data);out=D/'air_inputs_v1';assert not out.exists();out.mkdir()
 targets=Image.new('RGBA',(1536,1536));guides=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));rows=[]
 for i,(form,mask,n) in enumerate([('base',0,103),('base',0,104),('fourth',15,103),('fourth',15,104)]):
  im=a.composite(n,mask)[0];origin=(i%2*768,i//2*768);box=(112,112,208,208)
  assert np.count_nonzero(np.array(im)[:,:,3])==np.count_nonzero(np.array(im.crop(box))[:,:,3])
  targets.alpha_composite(im.crop(box).resize((768,768),Image.Resampling.NEAREST),origin)
  gun=[3,-32,10,-23] if n==103 else [3,-40,10,-31]
  hand=[3,-24,10,-19] if n==103 else [2,-32,10,-25]
  guide=im.copy();draw=ImageDraw.Draw(guide);draw.rectangle(tuple(q+160 for q in gun),outline=(30,200,240,255));draw.rectangle(tuple(q+160 for q in hand),outline=(250,180,35,255))
  guides.alpha_composite(guide.crop(box).resize((768,768),Image.Resampling.NEAREST),origin)
  rows.append({'cell':i,'form':form,'ref':n,'crop_world':[-48,-48,48,48],'gun_guide_world':gun,'hand_guide_world':hand,
   'guide_status':'새 원화 목표. 기존 총구/물리 좌표 자체를 추출했다는 뜻은 아님. 원US 손과 효과 공간에 맞춰 네이티브 재검토 필요.',
   'source_RGBA_sha256':sha(im.tobytes())})
 for i,(n,mask) in enumerate([(0,0),(47,0),(0,15),(47,15)]):
  im=a.composite(n,mask)[0];style.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
 for name,im in [('edit_targets.png',targets),('geometry_guides.png',guides),('accepted_style.png',style)]:im.save(out/name)
 prompt='''Use case: style-transfer. Asset: four full-body adult Nana PS1 action-game pixel sprites, same character, two existing costumes.
Image 1 is the edit target: keep exactly its 2x2 cells, same canvas and each body origin. Upper row: basic outfit prep103 then upward firing104. Lower row: Fourth outfit prep103 then upward firing104. Image 2 is the style master: accepted idle and our recently detailed airborne sprite; match their face/eye size, hair strand clusters, fine gray folds and differentiated boot or bare-leg shading. Image 3 is only a coordinate guide, with blue boxes for the new vertical pistol and gold boxes for the holding hand; remove the guide colors completely in the output.
Redraw these four full bodies with the same small native pixel size and pose/leg lengths. Preserve each head position, eyes, hat or veil design, black clothes, reddish-pink hair and shoes. Do not stretch the body, widen the face, make long plain strips or fill a garment as one black shape. Add the same purposeful hair strands and clothing shading visible in image2, never smooth or blur the pixel edges.
Critical pose correction: the raised pistol arm must be on the VIEWER-RIGHT of the face, at the blue and gold guide boxes, instead of the old viewer-left. Redraw that single gun-bearing arm from its shoulder through a bent elbow and cuff to the hand, and remove the old raised left-side arm/gun. This is not whole-body mirroring. Keep the other arm naturally bent by the torso. Exactly two arms and two legs, one pistol.
Nana keeps her small black-and-pink pistol Sarang-i. The pistol points straight upward, roughly eight native pixels long; preserve this small consistent weapon scale. In firing104 its muzzle is at world x+6,y-40 and the gripping hand at x+6,y-28; prep103 is slightly lower as shown by the guide. Connect the cuff, wrist and pistol grip naturally. No energy projectile, no flame, no effect, no armor cannon, no empty fist replacing the pistol.
Keep the basic costume's fitted black boots and Fourth costume's bare legs and small dark red shoes exactly as the style master, with the same head and limb proportions across costumes. Output the four complete sprites at the same cell positions on a genuinely transparent background. No labels, grid, extra characters, guide marks, shadows, watermark or glow. Crisp deliberate pixel clusters, no anti-aliased illustration or photorealism.'''
 (out/'prompt.txt').write_text(prompt+'\n','utf8')
 report={'source_arc_sha256':sha(data),'canvas':[1536,1536],'grid':[2,2],'cell':[768,768],'native_cell':[96,96],'scale':8,'frames':rows,
  'inputs':{name:sha((out/name).read_bytes())for name in('edit_targets.png','geometry_guides.png','accepted_style.png','prompt.txt')},
  'native_contact_proof':'work/sprite_style_unification_20261107/nana_audit/rising_repaint/native_contacts_v1/manifest.json',
  'native_art_modified':False,'game_modified':False,'runtime_verified':False}
 (out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(out)
if __name__=='__main__':main()
