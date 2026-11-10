"""노바213/215의 새 자세·규모를 유지하고 실제 Ultimate 의상 두 폼을 제작."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
def main():
    d=H/'nova_ultimate_inputs01';need(not d.exists(),'새 입력');p=H/'prepared_chaser_ultimate01/PL02_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)=='2b8faa71d3a94bc6d52ac0e389c6121d530d6455e664ad852061c43c77789b5c','부모 변경')
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size);old=Image.new('RGBA',target.size);crop=(112,112,208,208);rows=[]
    for row,n in enumerate((213,215)):
        new=Image.open(H/f'nova_base_targets01/base_{n:03}.png').convert('RGBA')
        for col,(form,mask)in enumerate((('before',15),('after',0))):
            pos=(768*col,768*row);target.alpha_composite(new.crop(crop).resize((768,768),Image.Resampling.NEAREST),pos);style.alpha_composite(a.composite(0 if row==0 else 205,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos);old.alpha_composite(a.composite(n,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos);rows.append({'ref':n,'form':form,'target_metrics':metrics(new),'old_metrics':metrics(a.composite(n,mask)[0]),'new_RGBA_sha256':sha(new.tobytes())})
    prompt='''Use case: identity-preserving console pixel-art sprite costume edit.
Image1 is the EDIT TARGET: a1536x1536 transparent page with exactly2columns and2rows, each768-square cell a96x96 logical square enlarged8x, origin(48,48). Keep all four existing sprite positions, head sizes, body volume and joint coordinates. Do not crop, recenter or enlarge the figures.
Top row213 is a compact crouch facing viewer-left with a bent fist near the face and the opposite hand near the waist. Bottom row215 keeps one fist ABOVE THE HEAD on viewer-left with the elbow bent behind the head; the other hand stays beside the waist on viewer-right. Preserve the distinct asymmetric bent knees and foot positions. Exactly two arms and two legs. Do not lower the raised arm. Keep the existing eye height, wrist tips, elbows, shoulders, hips, knees, ankles and sole heights.
Image2 is the accepted Ultimate COSTUME reference, with idle0 above and detailed victory205 below. Use its costume and restrained detail density, but follow Image1's poses. LEFT column: the accepted short pale lavender-white jacket with navy shaded collar/cuffs, fine folds and zipper opening over the lavender one-piece outfit with narrow pink center detail, legs and sandals as in the reference. RIGHT column: the same accepted lavender one-piece outfit with narrow pink center detail, arms without jacket sleeves, and the same legs and sandals. Keep the reference garment coverage and design. No white sleeve or cuff, shorts, skirt, stockings or boots on the right. The two columns differ only by the jacket; their limb positions and anatomy must match.
Replace the red ribbon with the accepted small GOLD SUNGLASSES resting on top of the head, adapted to each head tilt. Preserve the target's newly detailed lavender fox ears, layered hair locks and backward braid, gold eyes, round short-limbed proportions and controlled purple outline. Do not paste the idle head onto a pose or enlarge the sunglasses.
Image3 shows the older Ultimate poses only for costume context. Do not copy its large flat hair planes or coarse body. Keep Image1's new detailed body and exact scale. No gun, energy effect or extra object.
Clean native pixel clusters, two or three shaded planes, coherent cloth folds and sandal contours. Actual transparent background, no halo/glow/cast shadow, no grid or labels. Return the same four-cell page.'''
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_style.png');old.save(d/'old_pose_context.png');(d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'refs':[213,215],'forms_by_column':['before','after'],'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(a.data)},'target_manifest':{'path':(H/'nova_base_targets01/manifest.json').relative_to(ROOT).as_posix(),'sha256':sha((H/'nova_base_targets01/manifest.json').read_bytes())},'layout':{'canvas':[1536,1536],'grid':[2,2],'logical_canvas':[192,192],'cell':[96,96],'origin':[48,48],'crop':list(crop)},'rows':rows,'policy':'새 준비2몸체 자세를 유지한 Ultimate 의상 편집.현재213214/215216동일은 수용제작 정책,원US 완전복원 아님.217이후 강제mask15와 별도.135거부편집 재시도 아님.','files':{q.name:sha(q.read_bytes())for q in d.iterdir()if q.is_file()}});print(d)
if __name__=='__main__':main()
