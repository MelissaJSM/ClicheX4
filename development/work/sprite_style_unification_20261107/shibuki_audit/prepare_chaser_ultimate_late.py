"""Ultimate 체이서170/174의 별도 네셀 입력. 첫 페이지와 독립 저장."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
def main():
    d=H/'chaser_ultimate_inputs02';need(not d.exists(),'새 입력 필요');p=H/'prepared_standing_fire_ultimate01/PL02_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)=='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad','Ultimate 부모 변경')
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size);old=Image.new('RGBA',target.size);crop=(112,112,208,208);rows=[]
    for row,n in enumerate((170,174)):
        new=Image.open(H/f'chaser_targets01/base_{n:03}.png').convert('RGBA')
        for col,(form,mask)in enumerate((('before',15),('after',0))):
            pos=(col*768,row*768);target.alpha_composite(new.crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            style.alpha_composite(a.composite(0 if row==0 else 92,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            old.alpha_composite(a.composite(n,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            rows.append({'ref':n,'form':form,'target_RGBA_sha256':sha(new.tobytes()),'target_metrics':metrics(new),'old_metrics':metrics(a.composite(n,mask)[0])})
    prompt=(H/'chaser_ultimate_inputs01/prompt.txt').read_text('utf8')
    start=prompt.index('The two rows are');end=prompt.index('Image2 is')
    prompt=prompt[:start]+'''The two rows are two different side-facing vehicle poses. Top170 is a seated rider leaning slightly forward, forearms reaching left, a bent knee pointing left and both legs tucked below. Bottom174 is the distinct upright transition pose with the torso nearly vertical, the near arm pointing left, the lower far hand bent close to the waist, and legs extending down. Preserve the EXACT Image1 pose of each row: gaze left, eye height, the two wrists/hand tips, both elbows, shoulder/hip points, knees, ankles and sole height. Do not turn174 into another crouch or stretch its calves. Both columns in each row must have identical anatomy and limb coordinates. Exactly two hands and two legs. Do not add a vehicle, handlebar, gun or extra limb.
''' +prompt[end:]
    prompt=prompt.replace('compact crouch','riding pose').replace('Do not paste an idle head onto the crouch','Do not paste an idle head onto the target pose')
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_style.png');old.save(d/'old_pose_context.png');(d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'refs':[170,174],'forms_by_column':['before','after'],'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(a.data)},'target_manifest':{'path':(H/'chaser_targets01/manifest.json').relative_to(ROOT).as_posix(),'sha256':sha((H/'chaser_targets01/manifest.json').read_bytes())},'layout':{'canvas':[1536,1536],'grid':[2,2],'logical_canvas':[192,192],'cell':[96,96],'origin':[48,48],'crop':list(crop)},'rows':rows,'policy':'새기본체이서170/174의 비율/관절을 유지하는 Ultimate 두의상 해석. 원작모든폼 동일성을 주장하지 않는다.','files':{q.name:sha(q.read_bytes())for q in d.iterdir()if q.is_file()}});print(d)
if __name__=='__main__':main()
