import json
from pathlib import Path
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent
groups={'air_dash':[33,35,37,39,41,43,45,49,55,57,59,65,67,71,77,83],
        'action':[85,88,89,90,97,98,100,101,106,110,120,133,135,137,138,204],
        'back_other':[143,144,145,146,148,151,152,153,154,156,157,162,174,183,207,217]}
for name,frames in groups.items():
    sheet=Image.new('RGB',(1280,1408),'#253546');draw=ImageDraw.Draw(sheet)
    for i,n in enumerate(frames):
        im=Image.open(D/f'base_{n:03}.png').convert('RGBA').crop((40,40,120,120)).resize((320,320),Image.Resampling.NEAREST)
        x=i%4*320;y=i//4*352;sheet.paste(im,(x,y+32),im);draw.text((x+12,y+12),str(n),fill='white')
    sheet.save(D/f'{name}_reference.png')
(D/'master_groups.json').write_text(json.dumps(groups,indent=2))
