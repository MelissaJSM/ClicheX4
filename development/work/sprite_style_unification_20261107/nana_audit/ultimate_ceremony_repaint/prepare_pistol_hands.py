"""등장 원화에서 빠진 권총과 쥔 손만 보완하는 고정 셀 입력."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
GROUPS={'a':(133,135),'b':(136,137)}
BOX={133:(-23,5,-9,22),135:(-18,-17,-3,-1),136:(-20,-24,-5,-4),137:(-19,-35,-5,-14)}
POSE={133:'LOWERED pistol beside the lower screen-left hand, muzzle pointing DOWN and slightly LEFT, away from her leg',135:'pistol held near CHEST HEIGHT, muzzle pointing UP and slightly LEFT, clear of her face',136:'pistol held beside her CHIN, muzzle pointing UP and slightly LEFT, clear of her face',137:'pistol held ABOVE her forehead, muzzle pointing UP, distinct from the bunny-ear accessory'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('group',choices=GROUPS);args=ap.parse_args();refs=GROUPS[args.group];out=D/f'pistol_hands_{args.group}_inputs_v1';out.mkdir(exist_ok=False)
 arc=N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC';a=Archive(arc.read_bytes());target=Image.new('RGBA',(1536,1536));guide=Image.new('RGBA',(1536,1536));frames=[]
 for i,(form,n)in enumerate((f,n)for f in('before','after')for n in refs):
  p=D/f'costume_pair_probe_v3/{form}_{n:03}.png';z=np.array(Image.open(p));pal=16 if form=='before'else 0;pic=a.rgba(z,pal).crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST);xy=(i%2*768,i//2*768);target.paste(pic,xy);guide.paste(pic,xy);x0,y0,x1,y1=BOX[n];draw=ImageDraw.Draw(guide);draw.rectangle((xy[0]+(x0+48)*8,xy[1]+(y0+48)*8,xy[0]+(x1+48)*8,xy[1]+(y1+48)*8),outline=(0,210,255,255),width=3);draw.text((xy[0]+30,xy[1]+30),f'{n} {form} - HAND / GUN ONLY',fill=(0,210,255,255));frames.append({'cell':i,'ref':n,'form':form,'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'guide_box_world':BOX[n]})
 target.save(out/'edit_target.png');guide.save(out/'edit_guide.png')
 # Historical pose only: these old registered bodies are not current style masters.
 hist=Image.new('RGBA',(1280,720));draw=ImageDraw.Draw(hist)
 for i,n in enumerate(refs):
  p=ROOT/f'work/ver_rin_nana/nana_art/arrival_v1/production02/frame_{n}.png';im=Image.open(p).convert('RGBA');im=im.crop((32,32,128,128)).resize((640,640),Image.Resampling.NEAREST);hist.paste(im,(i*640,60));draw.text((i*640+25,20),f'{n} HISTORICAL GUN DIRECTION ONLY',fill='white')
 hist.save(out/'historical_direction.png')
 z=a.layer(85)[0];yy,xx=np.indices(z.shape);mask=(xx>=138)&(xx<=145)&(yy>=149)&(yy<=154)&np.isin(z,range(1,10));need(int(mask.sum())==20,'권총20표본');gun=np.where(mask,z,0).astype(np.uint8);Image.fromarray(gun).save(out/'canonical85_indices.png');style=Image.new('RGBA',(1536,768));draw=ImageDraw.Draw(style)
 for i,masknum in enumerate((15,0)):
  im=a.composite(0,masknum)[0].crop((112,112,208,208)).resize((600,600),Image.Resampling.NEAREST);style.paste(im,(i*620,100));draw.text((i*620+20,30),'ACCEPTED IDLE / EXACT IDENTITY',fill='white')
 gi=a.rgba(gun).crop((136,147,148,157)).resize((288,240),Image.Resampling.NEAREST);style.paste(gi,(1230,200));draw.text((1220,160),'SARANGI: compact pink pistol',fill='white');draw.text((1220,460),'8 native pixels long',fill='white');style.save(out/'style_and_weapon.png')
 prompt=f'''Use case: precise-object-edit. Edit the FOUR full-body adult game sprites in Image1. Keep the exact1536x1536 canvas, 2x2 grid, origins and scale. Top row is the pink-jacket costume, bottom row is the same woman in her accepted black/pink athletic stage costume with bare arms. Left column is pose{refs[0]}, right column pose{refs[1]}.
Change ONLY the screen-left weapon HAND and the compact pistol it holds. These recent full-body sprites accidentally omitted her signature small pink handgun, Sarangi. Image2's cyan rectangles identify the local editing region; use the NEW hand position in Image1, do not move the body to an old hand box. Image3 shows HISTORICAL GUN DIRECTIONS ONLY, not the desired old flat body style. Image4 shows accepted identity and the EXACT SMALL PISTOL DESIGN. The barrel length is8 native pixels, approximately64 image pixels. Keep a compact pink barrel and dark separate bent grip, not a large black fist or a long weapon.
Left column: {POSE[refs[0]]}. Right column: {POSE[refs[1]]}. Naturally curl the existing fingers around the grip. Preserve wrist location, forearm length and continuous sleeve/bare-arm connection. The same gun, palm and fingertips occupy matching positions in the top and bottom version. Do not leave a second empty hand, add a second gun or grow an extra arm. Never merge the pistol into the hair/ear. The two bunny ears remain unchanged.
Every other pixel-art feature stays as in Image1: detailed face/green eye and hair strands, head dimensions, shoulders and torso, costume coverage, opposite hand, knees, calves, ankles, shoes, stance and floor. Do not simplify or rescale the figure. Do not change the pose, torso angle or expression. Only a small hand/grip adjustment is allowed. Keep full figures and ample transparent padding in all four fixed cells; do not crop or enlarge them. Clean16-color-like native game pixel clusters, hard contours and original shading. Output only four corrected sprites on true transparency. No cyan guides, labels, grid, glow, effects, shadow or background. Neutral nonsexual full-body animation assets.'''
 (out/'prompt.txt').write_text(prompt,'utf8');report=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ceremony_pistol_sources01/report.json';write(out/'manifest.json',{'group':args.group,'refs':refs,'frames':frames,'parent_arc_sha256':digest(arc),'historical_direction_only':True,'provenance_report':report.relative_to(ROOT).as_posix(),'provenance_report_sha256':digest(report),'canonical_ref':85,'canonical_source_pixels':20,'canonical_indices_sha256':sha(gun.tobytes()),'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('edit_target.png','edit_guide.png','historical_direction.png','style_and_weapon.png','prompt.txt')],'native_packed':False});print(out)
if __name__=='__main__':main()
