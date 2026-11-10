from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
B=ROOT/'out/ver_buki_riko/riko_motion_20261023T235701617389Z'
inv=json.loads((ROOT/'work/ver_buki_riko/animation_inventory/20261023T095844768051Z/inventory.json').read_text('utf8'))
def picture(n):
 name=f'{"idle" if n in (0,1,2,146,147,148) else "frame"}_{n:03d}.png'
 im=Image.open(B/name).convert('RGBA');bounds=inv['frames'][f'bank0_{n:03}']['bounds']
 canvas=Image.new('RGBA',(96,80));canvas.alpha_composite(im,(48+bounds[0],40+bounds[1]));return canvas
def sheet(seq,cols,scale,path,labels=None):
 cw,ch=96*scale,80*scale+20;board=Image.new('RGBA',(cols*cw,((len(seq)+cols-1)//cols)*ch),(40,43,55,255));d=ImageDraw.Draw(board)
 for i,n in enumerate(seq):
  px,py=i%cols*cw,i//cols*ch
  board.alpha_composite(picture(n).resize((96*scale,80*scale),Image.Resampling.NEAREST),(px,py+20))
  d.text((px+5,py+5),f'{labels[i] if labels else "Frame"} {n}',fill='white')
 board.save(path)
all_frames=[0,1,2,146,147,148,*range(3,35),*range(44,53)]
sheet(all_frames,8,2,B/'riko_current_frames_2x.png')
seq=[147,7,10,14,17,147,3,4,44,45,46,47,48,46,47,49,50,51,52,147]
sheet(seq,5,3,B/'dash_context_sheet.png',['Approved basis']*5+['Dash entry']*5+['Dash loop']*5+['Dash exit']*5)
(B/'contact_sheet_metadata.json').write_text(json.dumps({'all_sheet_frames':all_frames,'dash_context':seq,'kind':'Aligned native sprite previews, not game capture','world_origin':[48,40],'uniform_integer_scale':True,'complete_character_sheet':False},indent=2),encoding='utf8')
