from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
D=Path(__file__).resolve().parent
def main():
    out=D/'arm_source_inspection';out.mkdir(exist_ok=True)
    rows=[]
    for n in(68,70,72,76,78,80,82,84):
        folder='basic_firing_a_registered_v1'if n<72 else'basic_firing_lowreach_registered_v1'if n<78 else'basic_firing_b_registered_v1'
        im=Image.open(D/folder/f'source_{n:03}.png').convert('RGBA');base=Image.new('RGBA',im.size,(214,222,227,255));base.alpha_composite(im);d=ImageDraw.Draw(base)
        for x in range(0,im.width,25):d.line((x,0,x,im.height),fill=(80,130,180,90));d.text((x+1,0),str(x),fill='blue')
        for y in range(0,im.height,25):d.line((0,y,im.width,y),fill=(80,130,180,90));d.text((0,y+1),str(y),fill='blue')
        base.save(out/f'source_{n:03}_grid.png');rows.append({'ref':n,'source':str(D/folder/f'source_{n:03}.png'),'size':im.size})
    (out/'sources.json').write_text(json.dumps(rows,indent=2),'utf8')
if __name__=='__main__':main()
