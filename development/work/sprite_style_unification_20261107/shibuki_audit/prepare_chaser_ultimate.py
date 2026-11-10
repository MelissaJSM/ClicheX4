"""새 체이서 자세를 보존하며 실제 Ultimate 의상을 적용할 입력."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics

def main():
    d=H/'chaser_ultimate_inputs01';need(not d.exists(),'새 입력 필요');p=H/'prepared_standing_fire_ultimate01/PL02_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)=='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad','Ultimate 부모 변경')
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size);old=Image.new('RGBA',target.size);crop=(112,112,208,208);rows=[]
    for row,n in enumerate((162,166)):
        new=Image.open(H/f'chaser_targets01/base_{n:03}.png').convert('RGBA')
        for col,(form,mask)in enumerate((('before',15),('after',0))):
            pos=(col*768,row*768);target.alpha_composite(new.crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            style.alpha_composite(a.composite(0 if row==0 else 92,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            old.alpha_composite(a.composite(n,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            rows.append({'ref':n,'form':form,'target_RGBA_sha256':sha(new.tobytes()),'target_metrics':metrics(new),'old_metrics':metrics(a.composite(n,mask)[0])})
    prompt='''Use case: identity-preserving console pixel-art sprite costume edit.
Image1 is the EDIT TARGET, a transparent1536x1536 page with exactly2columns and2rows. Each768x768 cell is a96x96 logical-pixel square enlarged8x, origin(48,48), with generous empty margins. Preserve all sprite positions, overall body scale and head size. Do not crop, recenter or fill cells.
The two rows are two different side-facing riding poses: top162 is a compact crouched rider leaning forward with both arms reaching left toward unseen handlebars, thighs bent and feet tucked beneath; bottom166 leans farther forward with a distinct head/neck angle. Keep these exact joints and silhouette: gaze left, same eye height, wrist/hand tips, elbows, shoulder/hip point, bent knees, ankles and sole height. Both columns in each row must have identical anatomy and limb coordinates. Exactly two hands and two legs. Do not add a vehicle, handlebar, gun or extra limb.
Image2 is the authoritative Ultimate costume reference for the SAME character. Left column is the pale-jacket outfit, right column is its jacket-off version. Top reference row is accepted idle0 and bottom is detailed recovery92. Change only the target's red costume, ribbon and boots to these Ultimate designs while retaining the new coherent hair locks, body volume and pose.
LEFT: pale lavender-white short jacket with navy collar/cuff shadows, opening and fine zipper/fold structure, over the reference lavender one-piece outfit with its narrow pink center detail; bare lower legs and sandals. RIGHT: the exact reference lavender one-piece outfit with narrow pink center detail, bare shoulders, bare arms, bare legs and sandals. No jacket sleeve, white cuff, skirt, shorts, stockings or boots on the right. Keep the garment design and coverage exactly as the actual style reference. The left and right outfits differ only by jacket presence.
Replace the red hair ribbon with the accepted small gold sunglasses resting on top of the head, correctly foreshortened to each left-facing head tilt. Preserve the lavender fox ears, long hair and backward braid, gold eye, controlled purple edges and restrained2-3tone shading. Do not paste an idle head onto the crouch or enlarge the sunglasses. Preserve the target compact game-sprite proportions and the reference detail density.
Image3 supplies older Ultimate pose context only. Do not copy its coarse old hair or flat clothing, and do not preserve incorrect old sleeve shapes in the jacket-off version. Keep the newly detailed target pose and scale from Image1.
Use clean native pixel clusters, readable cloth folds, coherent hair planes and sandal/foot structure. Avoid scratchy hatching or extra black outlines. True transparent background: no halo, glow, projectile, floor shadow, text, grid or labels. Output the same four-cell page.'''
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_style.png');old.save(d/'old_pose_context.png');(d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'refs':[162,166],'forms_by_column':['before','after'],'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(a.data)},'target_manifest':{'path':(H/'chaser_targets01/manifest.json').relative_to(ROOT).as_posix(),'sha256':sha((H/'chaser_targets01/manifest.json').read_bytes())},'layout':{'canvas':[1536,1536],'grid':[2,2],'logical_canvas':[192,192],'cell':[96,96],'origin':[48,48],'crop':list(crop)},'rows':rows,'policy':'새 기본형 체이서4키 중 첫2자세의 비율/관절을 보존하고 실제 Ultimate 의상으로 제작. 현재Ultimateafter9파생을 원래exact별칭이라고 하지 않음. 기존거부135와 다른 동작.','files':{q.name:sha(q.read_bytes())for q in d.iterdir()if q.is_file()}})
    print(d)
if __name__=='__main__':main()
