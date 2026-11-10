from pathlib import Path
import sys,json,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
src=W/'root_nana_return/packed_return03/PL00_U.ARC';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(src)=='6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9';a=Archive(src.read_bytes())
for label,refs in [('a',(162,166)),('b',(170,174))]:
 out=D/f'inputs_{label}01';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));frames=[]
 for row,(form,mask)in enumerate((('base',0),('fourth',15))):
  for col,n in enumerate(refs):
   pic=a.composite(n,mask)[0];target.alpha_composite(pic.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
   st=a.composite(0 if col==0 else 37,mask)[0];style.alpha_composite(st.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
   frames.append({'cell':row*2+col,'form':form,'mask':mask,'ref':n,'bbox':pic.getbbox()})
 target.save(out/'target.png');style.save(out/'style.png')
 prompt='''Repaint the FOUR gameplay sprites in the FIRST transparent2x2 sheet to precisely match the small crisp detailed pixel-art style of the SECOND reference sheet. Do not replace the target poses with the reference poses. Both sheets use96x96 native pixel cells enlarged8x,1536x1536 overall. Keep the target original blank margins, fixed origin and joint positions; never crop each body to fit a box.
These are Nana riding a high-speed hoverbike, shown as the character only. Top row basic outfit: black beret, tailored black blouse and skirt, asymmetric dark stockings and small boots. Bottom row Fourth outfit: folded black hood, short rear veil, black and burgundy dress with white edging, small burgundy shoes. Use the second sheet's exact hair highlights, precise eyes and face, fabric folds, normal slender build, thin variable game outline. Preserve each original target's facing left, leaned torso, arm reach to the invisible handlebar, exact front hand fingertip, hips, tucked knees, bent lower legs and foot contact. Hands grip an invisible handlebar, no pistol. The four targets are two different riding poses, repeated in two outfits. The same-column two forms must have the same anatomy, pose, head size and joint positions, with only clothing differing. Replace the current bottom sprites' broad flat unshaded leg blobs with clearly separated, correctly bent slender legs, using the base pose's anatomy and reference rendering detail; do not fill between legs. Maintain target feet endpoints. Hair and short veil trail to the right, with individual game-scale highlight clusters and a few sharp tips. Keep eyes at their current target location. Maintain every shoulder-to-hand connection.
No chibi scaling, enlarged head, overweight silhouette, thick uniform outline, long arms, smooth cartoon blobs or smudged hair. Do not add bike, wheels, scene, ground shadow, text, grid, effects, extra sprites or backgrounds. Transparent RGBA background; keep all four sprites in their original cells. The second sheet is reference only and must not appear as additional sprites in the output.'''
 (out/'prompt.txt').write_text(prompt,'utf8');(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(src),'frames':frames,'native_cell':[96,96],'source_files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':sha(out/f)}for f in('target.png','style.png','prompt.txt')],'runtime_verified':False},indent=2)+'\n','utf8')
print('two pages of four poses each prepared')
