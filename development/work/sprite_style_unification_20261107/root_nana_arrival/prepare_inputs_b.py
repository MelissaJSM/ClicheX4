from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/ultimate_ceremony_repaint'),str(W/'nana_audit/native_restore')]
from scripts.export_x_consistency import Archive
from prepare_effect_probe import render
from src.psx_player import composition_frame
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((W/'staging_rn_v27.json').read_text('utf8'));src=ROOT/plan['resources']['PL00_U.ARC']['path'];assert sha(src)==plan['resources']['PL00_U.ARC']['after'];a=Archive(src.read_bytes())
out=D/'inputs_b01';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=target.copy();frames=[]
for row,(form,mask)in enumerate((('base',0),('fourth',15))):
 for col,n in enumerate((136,137)):
  parts=composition_frame(a.c,0,n)['parts'];fx=render(a,n,[p for p in parts if p['tile']==7]);z=render(a,n,[p for p in parts if p['tile']!=7]);assert int((fx>0).sum())==46
  assert np.array_equal(np.where(fx,fx,z),a.layer(n)[0])
  im=a.rgba(z);target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  ref=a.composite(0 if col==0 else 138,mask)[0];style.alpha_composite(ref.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  Image.fromarray(z).save(out/f'{form}_{n:03}_original_body.png');Image.fromarray(fx).save(out/f'effect_{n:03}.png');frames.append({'cell':row*2+col,'form':form,'mask':mask,'ref':n,'bbox':im.getbbox(),'effect_parts':[p for p in parts if p['tile']==7],'effect_pixels':46})
prompt='''Precisely repaint this2x2 sheet of four Nana PS1 Mega Man X4 game sprites in place. True transparent background.
Image1 is the POSE EDIT TARGET. LEFT column136 is an upright planted arrival preparation stance, front arm bent inward with small pink-and-black pistol near face and chest; the face and upper torso lean slightly forward. RIGHT column137 is the next arriving stance: front arm bent overhead with pistol angled up-left, body and head angled, rear arm bent behind the waist, same planted feet. Preserve both exact poses, head size, face position, shoulders, wrists, knees and foot endpoints. Keep the native pixel scale and original cell coordinates.
Image2 is the approved STYLE AND CLOTHING REFERENCE, idle on left and detailed raised-hand pose on right. Match its crisp restrained dark outline, small green eye, separated three-tone long pink hair locks, fabric folds and small highlights. Do not transfer its pose. TOP row clothing is black beret, tailored black blouse and skirt, asymmetric dark stockings and black boots. BOTTOM row is Fourth costume: folded black hood and long rear veil, black dress, white decorative skirt trim and burgundy shoes. Reconstruct this bottom clothing on the same target anatomy and exact poses. The old bottom target currently lacks the Fourth costume, correcting that is intentional.
Replace the target's flat pink hair wedges and indistinct broad black fabric blocks with the idle's layered locks, defined cuffs, fitted fabric folds and clear hem/boot contours. Keep the tiny Sarang pistol and grip; no large cannon. No chibi proportions, stretched limbs, thick outlines, extra ornaments, aura, glow or lightning. Original game effects have intentionally been excluded from the targets and will be restored unchanged later.
Keep exact1536x1536 layout, four768x768 cells, each96x96 native pixels enlarged8x. Preserve all transparent padding. No bounding-box fitting, recentering, cropping, scaling, text, labels, grids, backgrounds or shadows. Four sprites only.'''
target.save(out/'target.png');style.save(out/'style.png');(out/'prompt.txt').write_text(prompt,'utf8');(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(src),'frames':frames,'native_cell':[96,96],'source_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in sorted(out.iterdir())],'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print('arrival136/137 extracted,46 original effect pixels per pose excluded')
