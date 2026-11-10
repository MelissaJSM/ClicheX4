"""일치한 원점·눈높이·발바닥 그대로 회복128 원화를 등록한다."""
from pathlib import Path
import json,hashlib,shutil,sys,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'bank1_recovery128';O=D/'bank1_recovery128_registered_v1';assert not O.exists();O.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();assert sha(arc)==info['archive_sha256'];src=A/'native_fixed/b1_128_indices.png';z=np.array(Image.open(src));old=render(arc,1,5,128)[0]
assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<=15;assert int(np.where(z>0)[0].max())==int(np.where(old>0)[0].max())==183;assert z[154,143]==old[154,143]==15
out=O/'b1_128_indices.png';shutil.copyfile(src,out)
for name,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(arc,9),row*32);page([('128 old',rgba(old,pal)),('128 new',rgba(z,pal))],rgba(render(arc,0,0,147)[0],pal),O/(name+'_comparison.png'),cols=2,scale=6)
 r=Image.new('RGB',(1440,400),'#64717b')
 for i,(label,b)in enumerate([('125 new',render(arc,1,5,125)[0]),('128 old',old),('128 new',z),('107 new',render(arc,1,5,107)[0])]):
  p=rgba(b,pal).crop((112,112,192,192)).resize((360,360),Image.Resampling.NEAREST);r.paste(p,(i*360,20),p)
 r.save(O/(name+'_recovery_connection.png'))
j={'source_arc_sha256':sha(arc),'source_generated_sha256':sha((A/'generated.png').read_bytes()),'records':[{'key':'b1_128','bank':1,'ref':128,'source_native':str(src.relative_to(ROOT)),'source_native_sha256':sha(src.read_bytes()),'whole_translation':[0,0],'operations':[],'output_sha256':sha(out.read_bytes()),'old_head_override':False,'manually_invented_colors':False}],'scope':'뇌신격 마지막 회복128과 원래 전신이 정확 같은129/130/131. 새 원화를 고정배율로 그대로 사용하며 원눈(143,154)·발바닥183·손/발 방향을 유지한다.','runtime_verified':False,'user_accepted':False}
(O/'registration.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out.read_bytes()))
