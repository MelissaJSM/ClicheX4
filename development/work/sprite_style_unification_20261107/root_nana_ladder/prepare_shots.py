from pathlib import Path
import sys,json,hashlib
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((D/'first_inputs01/manifest.json').read_text('utf8'));p=ROOT/m['source_arc'];assert sha(p)==m['source_arc_sha256'];a=Archive(p.read_bytes())
out=D/'shot_inputs01';out.mkdir(exist_ok=False);targets=Image.new('RGBA',(1536,1536));new=Image.new('RGBA',(1536,1536));records=[]
for row,(form,mask) in enumerate((('base',0),('fourth',15))):
 for col,ref in enumerate((150,155)):
  im=a.composite(ref,mask,2)[0];newim=Image.open(D/'contact_registration02'/f'{form}_149_rgba.png').convert('RGBA')
  for src,dst in((im,targets),(newim,new)):
   dst.alpha_composite(src.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  records.append({'cell':row*2+col,'form':form,'mask':mask,'ref':ref,'body_reference':149,'muzzle_world':[-24,-9]if ref==150 else[-21,-13]})
targets.save(out/'targets.png');new.save(out/'new_body_reference.png')
prompt='''Edit a transparent pixel-art sprite sheet for our existing nonsexual action platformer. Four fully clothed adult heroine sprites, fixed 2 by 2 equal cells. Image 1 is the OLD POSE/COORDINATE guide: left column is150 firing left horizontally while hanging by the right hand; right column is155 firing left with a slightly raised wrist during recoil. Top row basic costume (black beret, black jacket, opaque closed black skirt, tall black boots, pink hair); bottom row Fourth costume (black folded veil, long sleeves, fully opaque closed layered black dress, burgundy low shoes). Image2 is the NEW accepted detailed ladder-rest body reference149 in exactly the same world registration. Image3 is the accepted idle style/material reference. Use the new detailed body and its clean separated hair strands and sculpted cloth folds, changing ONLY the lower/front shooting arm so it stretches toward the LEFT and firmly grips the tiny black/pink handgun at the original guide muzzle coordinate. Match the style, head scale, thin dark purple contour, small hard-edged highlight clusters, cloth volume and skin shading of the accepted references. Preserve the nonshooting raised hand, head, clothing and soles exactly at the coordinates of Image2. Avoid bare hips: maintain the opaque skirt/dress and coverage from Image2. This is a neutral side-view functional climbing animation, no camera emphasis on the body. The shooter holds a compact handgun, not a buster or forearm cannon; retain a clear wrist/palm/short barrel. Do not stretch the arm or enlarge the gun. Preserve the common full-body size across all four cells, no automatic fit-to-cell resizing. Output ONLY the four complete sprites on true transparent background, same cell margins/alignment; no text, grid, scenery, effects, pedestal, shadow, antialiasing, gradient or blur. This is the same character/same scale across poses. The only intended differences150 versus155 are the shooting forearm/pistol aim and recoil. Final exact muzzle pixels will be registered separately to the game's unchanged firing origin.'''
(out/'prompt.txt').write_text(prompt,'utf8')
inputs=[out/'targets.png',out/'new_body_reference.png',D/'first_inputs01/style.png']
(out/'manifest.json').write_text(json.dumps({'source_arc':m['source_arc'],'source_arc_sha256':m['source_arc_sha256'],'frames':records,'inputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in inputs],'prompt_sha256':sha(out/'prompt.txt')},ensure_ascii=False,indent=2)+'\n','utf8')
print(out)
