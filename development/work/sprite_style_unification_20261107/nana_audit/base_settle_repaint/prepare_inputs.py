"""기본/포스138의 원래 높이 든 권총자세와139 y−1 연결을 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need

def main():
 p=N.parent/'root_nana_ladder/packed_ladder07/PL00_U.ARC';need(digest(p)=='509cc9785cb5eb3dca9f7a8a3fd1d3ea334887a98d3834b9f327266b3c6bbdce','동결원화부모');a=Archive(p.read_bytes());out=D/'body_inputs_v1';out.mkdir(exist_ok=False)
 relations=[]
 for pb in(0,5,6,7,8):
  z=a.layer(138,pb)[0];q=a.layer(139,pb)[0];t=np.zeros_like(z);t[:-1]=z[1:];need(np.array_equal(t,q),'139 y−1 exact');relations.append({'layer':pb,'source':138,'target':139,'translation':[0,-1],'target_sha256':sha(q.tobytes()),'exact':True})
 target=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1536));frames=[]
 for col,mask in enumerate((0,15)):
  im=a.composite(138,mask)[0];target.alpha_composite(im.crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(col*768,0))
  for row,n in enumerate((0,100)):style.alpha_composite(a.composite(n,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
  y,x=np.nonzero(np.array(im)[:,:,3]);frames.append({'ref':138,'form':'base'if mask==0 else'fourth','mask':mask,'cell':col,'world_bbox':[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)],'source_rgba_sha256':sha(im.tobytes())})
 target.save(out/'targets.png');style.save(out/'style.png')
 hist=Image.new('RGBA',(1024,512));paths=[ROOT/'work/ver_rin_nana/nana_art/arrival_v1/generated.png',ROOT/'work/ver_rin_nana/nana_fourth_armor/ceremony_v1/generated_first.png'];crops=[(512,512,1024,1024),(0,0,512,512)]
 for i,(hp,box)in enumerate(zip(paths,crops)):hist.alpha_composite(Image.open(hp).convert('RGBA').crop(box),(512*i,0))
 hist.save(out/'historical138.png')
 prompt='''Use case: style-transfer. Two neutral full-body adult heroine game sprites on an exact1536x1024 transparent canvas. Image1 is the EDIT TARGET: one horizontal row, LEFT basic black-dress costume and RIGHT Fourth costume with the established dark gray/black layered veil, matching the same woman's accepted designs. Each768x1024cell is96x128 native pixels; preserve the exact origin, body size and planted shoes.
Redraw the two figures at the fine pixel-detail level of Image2's accepted idle and special sprites. Keep separated pink hair locks, compact green eyes, crown/hat or layered dark veil details, readable lapels and sleeve/cuff folds, dark stocking/boot planes in the left outfit, skin shadows and light costume panels in the right. Do not substitute outfits between the two characters. Preserve all current outfit coverage and the original body proportions.
The gesture is specific: the screen-left arm holds her compact pink handgun VERTICALLY ABOVE HER HEAD, muzzle UP. The gun is a separate small8-native-pixel barrel and bent grip firmly held by fingers, NOT part of her crown, veil or hair. The other empty arm stays bent near the chest/shoulder. Both legs and feet keep the existing upright grounded stance and original spacing. Image3 is historical gesture reference confirming the raised pistol and the other bent arm; do not copy its background or old coarse shading. Do not lower the pistol or change to salute/standing fire.
Preserve the exact head size, face/eye and shoulder/wrist/knee/ankle positions, gun/hand contact and floor row in Image1. Both costume versions share the same character identity and joint positions. Improve broad flat hair and sleeve areas with clean clusters, not extra body bulk or a different pose. Do not lengthen the legs, shrink the boots, or enlarge the head.
Output only these TWO full sprites at the same positions, genuine transparency, no halo, shadow, effects, text, labels, panel borders or background. Crisp small pixel clusters and selective shadow contours, no smooth gradients or tiny high-resolution linework. No extra weapon or limb.'''
 (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'art_parent_arc':p.relative_to(ROOT).as_posix(),'art_parent_arc_sha256':digest(p),'final_packing_parent_pending_root_other_PL00_work':True,'frames':frames,'native_cell':[96,128],'render_scale':8,'world_crop':[-48,-64,48,64],'relations139':relations,'historical':[{'path':hp.relative_to(ROOT).as_posix(),'sha256':digest(hp),'crop':list(box)}for hp,box in zip(paths,crops)],'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','historical138.png','prompt.txt')],'scope':'138 새 전신 한 자세×기본/포스2의상.139는모든5층 y−1 exact 파생.루트95/98·89/97 작업과겹치지않으며 최종부모는나중합류.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
