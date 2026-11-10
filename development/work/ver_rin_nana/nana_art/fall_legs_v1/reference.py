import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from scripts.prepare_nana_idle_shot import write
d=Path(__file__).parent;source=d.parent/'air_v1';art=json.loads((source/'normalized01/art.json').read_text('utf8'))
sheet=Image.new('RGBA',(3*384,512),(0,0,0,0))
for i,n in enumerate((43,45,47)):
 im=Image.open(source/'normalized01'/f'run_{n:03d}.png').convert('RGBA').crop((28,8,76,72)).resize((384,512),Image.Resampling.NEAREST);sheet.alpha_composite(im,(i*384,0))
sheet.save(d/'current_fall.png')
plan=json.loads((source/'plan.json').read_text('utf8'));plan['paired_frames']=[q for q in plan['paired_frames']if q['frames'][0]in (43,45,47)];plan['run_animation']=plan['animations']['11'];write(d/'plan.json',plan)
write(d/'source_registration.json',{'frames':[q for q in art['frames']if q['frame']in (43,45,47)],'crop':[28,8,76,72],'scale':8})
print(d/'current_fall.png')
