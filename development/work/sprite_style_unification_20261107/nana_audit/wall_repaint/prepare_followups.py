"""Native reference sheets only: no repainting or recoloring."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D.parent),str(D.parent/'native_restore')]
from prepare_wall_inputs import page
from preview_restore import Archive,sha,digest,write,need
from PIL import Image,ImageDraw,ImageFont
import numpy as np

def main():
    m=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/m['source_arc']).read_bytes());need(sha(a.data)==m['source_sha256'],'Input')
    page(a,[(f'POSE {n}',n,0)for n in[59,63,64,66]],D/'basic_remaining_and_fire.png')
    page(a,[(f'FIRING {n}',n,0)for n in[56,58,60,62]],D/'basic_firing_keys.png')
    page(a,[(f'FOURTH {n}',n,15)for n in[55,57,61,65]],D/'fourth_wall_keys.png')
    page(a,[('FOURTH IDLE 0',0,15),('FOURTH FIRE 85',85,15),('NEW FOURTH RUN 7',7,15),('NEW FOURTH RUN 15',15,15)],D/'fourth_style_master.png')
    cell=640;board=Image.new('RGBA',(1280,790),(0,0,0,0));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',22)
    for i,n in enumerate([0,85]):
        sprite=a.composite(n)[0].crop((144,132,176,164)).resize((640,640),Image.Resampling.NEAREST);board.alpha_composite(sprite,(i*cell,40));draw.text((i*cell+20,6),f'ACCEPTED HEAD {n}',font=font,fill='#65707a')
    colors=[((int(w)>>0&31)*255//31,(int(w)>>5&31)*255//31,(int(w)>>10&31)*255//31,255)for w in a.words[:16]]
    for i in range(1,16):draw.rectangle((i*80-70,700,i*80,750),fill=colors[i]);draw.text((i*80-70,755),str(i),font=font,fill='#65707a')
    board.save(D/'head_palette_master.png')
    report={}
    for n in [55,57,61,65]:
        old=a.layer(n)[0];new=np.array(Image.open(D/f'basic_registered_probe_v1/base_{n:03}.png'));ey=next(q for q in m['frames']if q['ref']==n)['eye_world'][1]
        def hist(ar):
            scope=ar[int(ey)+149:int(ey)+165,145:185];return {str(i):int((scope==i).sum())for i in range(5,10)}
        report[n]={'current_upper_hair_palette_counts':hist(old),'candidate_upper_hair_palette_counts':hist(new),'interpretation':'Native-index area only, not a perceptual quality score. Candidate bright bang area is visibly larger and is queued for source-art correction.'}
    write(D/'followup_inputs.json',{'source_arc_sha256':sha(a.data),'paths':{p.name:digest(p)for p in[D/'basic_remaining_and_fire.png',D/'basic_firing_keys.png',D/'fourth_wall_keys.png',D/'fourth_style_master.png',D/'head_palette_master.png']},'hair_observations':report})
    print(json.dumps({'prepared':5}))
if __name__=='__main__':main()
