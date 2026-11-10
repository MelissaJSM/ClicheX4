from pathlib import Path
import sys,json,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=W/'root_nana_standing/packed_standing03/PL00_U.ARC';assert sha(src)=='87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e';a=Archive(src.read_bytes())
out=D/'inputs01';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=target.copy();frames=[]
for row,(form,mask) in enumerate((('base',0),('fourth',15))):
 for col,n in enumerate((90,91)):
  im=a.composite(n,mask)[0];target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  ref=a.composite(0 if col==0 else 89,mask)[0];style.alpha_composite(ref.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  frames.append({'cell':row*2+col,'form':form,'mask':mask,'ref':n,'bbox':im.getbbox(),'palette_start':16 if mask else 0})
prompt='''Use case: style-transfer. Precisely refine this 2x2 sheet of four Nana PS1 Mega Man X4 game sprites in place. Output actual transparent background.
Image1 is the EDIT TARGET. Top row black beret, long layered pink hair, fitted black blouse and skirt, asymmetric black stockings and boots. Bottom row the Fourth outfit: folded black hood and rear veil, pink hair, black dress with white ornamental skirt trim, pale legs and burgundy shoes. Keep each costume exactly its own.
Image2 is STYLE ONLY: accepted idle in the left column and approved detailed raised-pistol pose in the right column. Match their selective one-native-pixel dark outline, small green eye, layered three-tone pink hair locks, articulated black clothing folds and crisp hem/boot contours. Do not transfer their pose.
Target LEFT column is ref90: wide planted stance, slightly forward leaning body, left-visible forearm raised diagonally toward upper left, holding the small pink-and-black Sarang pistol, rear arm bent by hip. Target RIGHT column is ref91: same wide planted stance, leaning slightly forward, front arm outstretched and pistol pointed horizontally left as it returns from recoil. Preserve these exact two poses and every eye, shoulder, elbow, wrist, grip, muzzle, waist, knee and foot position. Preserve head and body size, foot baseline, individual gun angle and size. Keep the two costumes on identical underlying anatomy.
The target's long hair currently reads as a flat pink wedge, and sleeves and torso as broad black blocks. Repaint these with the reference's readable locks, narrow highlights and shadow separations, defined cuffs and fitted fabric folds. Keep the native pixel scale and clean restrained edge. Do not thicken outlines, flatten the hair, smooth into gradients, make chibi proportions, add ornaments, duplicate limbs or redesign the clothing. Do not change the pistol's size or turn the arm into a buster.
Keep the complete 1536x1536 2x2 layout and all original transparent padding. Every768x768 cell represents96x96 native pixels enlarged8x; retain exact cell coordinates. No bounding-box recentering, fitting, crop, scaling, text, labels, grid lines, scenery or ground shadows. Four whole sprites only.'''
target.save(out/'target.png');style.save(out/'style.png');(out/'prompt.txt').write_text(prompt,'utf8')
(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(src),'frames':frames,'native_cell':[96,96],'source_files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':sha(out/f)}for f in('target.png','style.png','prompt.txt')],'preserved_ref86_reason':'Actual root comparison: accepted85 body and detail with original recoil shift; no new confirmed simplification.','runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print('prepared recoil 90/91 in two outfits;86 preserved')
