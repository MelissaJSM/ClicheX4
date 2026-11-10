"""미호출 page02의 역사 참고판에서 실제 출처가 확인된 번개46셀만 제외한다."""
from pathlib import Path
import json,sys,shutil
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
def main():
    d=H/'ultimate_arrival_inputs01/page02';need(not(d/'generated.png').exists(),'Already generated')
    old=d/'old_coordinate_reference.png';backup=d/'old_coordinate_reference_with_effects_internal.png';need(not backup.exists(),'Already cleaned');shutil.copyfile(old,backup)
    a=Archive((H/'prepared_ultimate_hurt02/PL02_U.ARC').read_bytes());src=H.parent/'zero_audit/shibuki_ultimate_arrival_relations01/effect_137.npy';need(sha(src.read_bytes())=='d7db442e1fdeed6696c500f0b73ca171b9a1eff0db32cd5af33d84d280b7ebfa','Effect source changed');fx=np.load(src);need(np.count_nonzero(fx)==46,'Wrong effect extent');out=Image.new('RGBA',(1536,1024))
    for row,mask in enumerate((15,0)):
        for col,n in enumerate((137,138)):
            im=a.composite(n,mask)[0]
            if n==137:v=np.array(im);v[fx>0]=0;im=Image.fromarray(v)
            out.alpha_composite(im.crop((112,128,208,192)).resize((768,512),Image.Resampling.NEAREST),(col*768,row*512))
    out.save(old);m=json.loads((d/'input.json').read_text('utf8'));m['files'][old.name]=sha(old.read_bytes());m['old_reference_effect_removal']={'source':src.relative_to(ROOT).as_posix(),'sha256':sha(src.read_bytes()),'pixels_per_form':46,'hidden_body_invented':False,'removed_from_reference_only':True,'not_for_generation_backup':backup.name};write(d/'input.json',m);print(sha(old.read_bytes()))
if __name__=='__main__':main()
