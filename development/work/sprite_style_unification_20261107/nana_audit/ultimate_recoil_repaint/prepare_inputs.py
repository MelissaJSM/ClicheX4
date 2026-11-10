"""Ultimate 90/91의 독립적인 상세화 입력. 기존 원점과 수용 기본형 관절을 대조한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def main():
 p=N/'ultimate_standing_repaint/packed_standing_candidate_v1/PL02_U.ARC';need(digest(p)=='0e69e9e3823c95bfce5b10746f77c587cd6f9e177cdd69b04938e868f3b77331','고정후보');a=Archive(p.read_bytes())
 bp=N.parent/'root_nana_recoil/packed_recoil03/PL00_U.ARC';need(digest(bp)=='ef69d0a13ad11ede874f2642bd9df719cbb2d864798801867b6738f728df6df4','기본형포즈');b=Archive(bp.read_bytes())
 out=D/'a_inputs_v1';out.mkdir(exist_ok=False);refs=[90,91];crop=(112,112,208,208);target=Image.new('RGBA',(1536,1536));style=target.copy();pose=Image.new('RGBA',(1536,768));frames=[]
 for row,(form,mask)in enumerate((('before',15),('after',0))):
  for col,n in enumerate(refs):
   im=a.composite(n,mask)[0];target.alpha_composite(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768));alpha=np.array(im)[:,:,3];alpha[112:208,112:208]=0;need(not alpha.any(),'고정입력창')
   ref=0 if col==0 else 89;style.alpha_composite(a.composite(ref,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768));frames.append({'ref':n,'form':form,'mask':mask,'cell':row*2+col,'source_rgba_sha256':sha(im.tobytes())})
 for col,n in enumerate(refs):pose.alpha_composite(b.composite(n)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,0))
 target.save(out/'targets.png');style.save(out/'style.png');pose.save(out/'accepted_pose_reference.png')
 prompt='''Use case: style-transfer. Refine four neutral full-body adult heroine game sprites in an exact1536x1536 transparent 2x2 sheet. Each768cell represents96x96 native game pixels enlarged8x. These are two specific standing pistol recovery poses, not new gestures.
Image1 is the EDIT TARGET. Top row is Nana in the accepted pink jacket outfit. Bottom row is the same adult character in her accepted black sleeveless athletic outfit and pink waistband. Keep every outfit's existing coverage and the green shoes, long pink hair, rabbit-ear hair accessory, green eyes. Image2 is STYLE ONLY: idle at left and the newly detailed raised-pistol pose89 at right, with the same costume rows. Do not copy their gestures. Image3 is POSE DETAIL ONLY: already accepted base-costume versions of the90/91 joints and gun orientation. Do not copy that black dress, beret or boots.
LEFT column90 has the pistol arm still angled up-left and bent, returning from a raised-arm pose. RIGHT column91 lowers the shooting forearm into a horizontal left-pointing pistol position. Keep each separate wrist/elbow/shoulder placement and gun muzzle location, the opposite hand, face/eye position, head size, knee angles, toe positions, shoe size and ground baseline. Both rows share exactly the same anatomy and pose; only the jacket versus sleeveless clothing differs. Maintain the compact pink-and-black Sarang pistol and clear fingers gripping it. No extra hand, enlarged weapon or detached wrist.
Replace broad flat pink rear-hair planes with layered locks, burgundy shadows and small highlights at the same game-pixel scale as Image2. Improve the jacket's sleeve/cuff/fold separation and selective skin shading without heavy uniform black outlines. The bottom row's actual arms must be bare as in Image2, without stray pink jacket sleeve blocks. Keep the same body proportions, silhouette volume and clothing coverage. Do not lengthen legs, enlarge hair/head, narrow ankles, or simplify the details already present.
Preserve the full-cell padding and fixed positions; no recentering, bounding-box fitting, body scaling, sprite cropping, added effect, beam, text, label, grid, shadow, background or halo. Output exactly four complete connected sprites with genuine transparency and crisp game-sized pixel clusters.'''
 (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'parent_status_at_input':'입력잠금 후보, 동결 전이며 최종패킹은 동결부모 확인 후 순차 진행','pose_reference_arc':bp.relative_to(ROOT).as_posix(),'pose_reference_sha256':digest(bp),'refs':refs,'columns':2,'rows':2,'native_cell':[96,96],'world_crop':[-48,-48,48,48],'frames':frames,'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','accepted_pose_reference.png','prompt.txt')],'scope':'별개 Ultimate90/91 특수 연결자세. 사다리 보류/거부 자료를 사용하지 않음.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
