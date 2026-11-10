"""큰 분홍뒤머리 면만 대기/새89·97의 군집 명암으로 보완할 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def main():
 p=N.parent/'root_nana_standing/packed_standing03/PL00_U.ARC';need(digest(p)=='87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e','루트스타일부모');a=Archive(p.read_bytes());out=D/'hair_inputs_v1';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1024));sources=[]
 for i,form in enumerate(('base','fourth')):
  path=D/'contacts_probe_v1'/f'{form}_138_indices.png';z=np.array(Image.open(path));start=16 if i else 0;target.alpha_composite(a.rgba(z,start).crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(i*768,0));sources.append({'form':form,'path':path.relative_to(ROOT).as_posix(),'sha256':digest(path)})
  for col,n in enumerate((0,89,97)):style.alpha_composite(a.composite(n,15 if i else 0)[0].crop((128,124,192,188)).resize((512,512),Image.Resampling.NEAREST),(col*512,i*512))
 target.save(out/'targets.png');style.save(out/'style.png')
 prompt='''Use case: precise-object-edit. Two adult heroine game sprites on the exact1536x1024 transparent canvas, one row of two768x1024cells. Image1 is the edit target. LEFT is the basic black-dress outfit; RIGHT is the dark-veiled Fourth outfit. Image2 is the accepted native game-detail reference: columns idle, pose89, pose97; top basic and bottom Fourth.
Edit ONLY the visible LONG PINK HAIR behind the cheek/neck and trailing down the back, including the pink hair visible below the dark veil in the RIGHT sprite. The current large medium-pink interior is too flat at native game size. Subdivide that existing pink area into two or three flowing lock directions using deliberate dark burgundy shadow wedges, medium pink planes and lighter pink strands matching Image2. Preserve the existing exact hair silhouette, width, length, endpoints and overall volume. Create meaningful compact pixel clusters inside the current hair, not thin high-resolution scratches or a different hairstyle.
This canvas is an8x enlargement of a96x128 native cell per sprite. Shading features need to survive that8x reduction: use purposeful native-pixel-sized stepped highlight/shadow clusters, not smooth gradients or sub-pixel scribbles. Keep the selective dark outer boundary and avoid turning the hair into either a solid pink slab or an all-dark mass.
Do not modify face, eye location, bangs across the face, hat/crown, dark veil, ear, skin, jacket/dress, hands, arms, legs or feet. Preserve the raised handgun and all its existing8-native-pixel module, wrist and muzzle coordinates exactly. Do not move, scale, thicken or lengthen anything. Do not add hair outside the old alpha silhouette. Both figures retain their exact neutral upright raised-pistol pose.
Output the same two complete sprites with only the inner long-pink-hair shading changed. Genuine transparency, no background or halo, no text, labels, borders, effects or extra objects.'''
 (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'target_sources':sources,'style_arc':p.relative_to(ROOT).as_posix(),'style_arc_sha256':digest(p),'refs':[138],'forms':['base','fourth'],'native_cell':[96,128],'world_crop':[-48,-64,48,64],'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','prompt.txt')],'scope':'루트검토에서큰분홍면세부미달.뒤머리내부명암만새원화로보완하며139y−1/몸/권총/손발/알파는보존.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
