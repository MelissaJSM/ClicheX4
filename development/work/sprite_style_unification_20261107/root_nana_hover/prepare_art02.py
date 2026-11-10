from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
m=json.loads((D/'input_audit.json').read_text('utf8'));src=ROOT/m['input']['path'];assert hashlib.sha256(src.read_bytes()).hexdigest()==m['input']['sha256'];a=Archive(src.read_bytes())
frames=[(225,8),(225,15),(227,8),(227,15)];sheet=Image.new('RGBA',(1152,1152));out=D/'art02_inputs.png';assert not out.exists()
for cell,(n,mask) in enumerate(frames):
 im=a.composite(n,mask)[0];crop=im.crop((112,112,208,208));assert np.count_nonzero(np.array(im)[:,:,3])==np.count_nonzero(np.array(crop)[:,:,3])
 sheet.alpha_composite(crop.resize((576,576),Image.Resampling.NEAREST),(cell%2*576,cell//2*576))
sheet.save(out)
(D/'art02_input_audit.json').write_text(json.dumps({'parent_sha256':m['input']['sha256'],'pose_order':frames,'fixed_native_cell':96,'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2)+'\n','utf8')
print(out)
