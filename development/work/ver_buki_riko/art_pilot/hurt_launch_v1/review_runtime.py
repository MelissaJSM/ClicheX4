"""Make a contact sheet from actual framebuffers and run negative controls."""
from pathlib import Path
import sys,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from src.epsxe_state import match_sprite,framebuffer
D=Path(__file__).parent;R=ROOT/'work/ver_buki_riko/launch_hurt_runtime/20261025T091722509767Z'
record=json.loads((R/'verification.local.json').read_text());assert record['verified_frames']==[135,*range(139,146)]
board=Image.new('RGB',(8*240,300),(32,36,48));draw=ImageDraw.Draw(board);checks=[]
for i,n in enumerate(record['verified_frames']):
 pic=Image.open(R/f'expected_{n:03d}.png');v=(R/f'vram_{n:03d}.bin').read_bytes();screens=[framebuffer(v,0,page) for page in (0,256)]
 matches=[(page,m) for page,screen in zip((0,256),screens) for m in match_sprite(screen,pic)]
 assert matches
 wrong=pic.copy();pixels=list(pic.getdata());at=next(j for j,p in enumerate(pixels) if p);color=pic.convert('RGB').getpixel((at%pic.width,at//pic.width));palette=pic.getpalette()
 replacement=next(j for j in range(1,16) if tuple(palette[j*3:j*3+3])!=color)
 wrong.putpixel((at%pic.width,at//pic.width),replacement)
 assert not any(match_sprite(screen,wrong) for screen in screens)
 result={'frame':n,'exact_match':True,'one_pixel_mutation_rejected':True,'right_facing':all(m['flip_x'] for _,m in matches)}
 if any(p>=32 for p in pixels):
  wrong=pic.copy();wrong.putdata([p-32 if p>=32 else p for p in pixels]);assert not any(match_sprite(screen,wrong) for screen in screens)
  result['flattening_clut2_to_clut0_rejected']=True
 checks.append(result)
 page,m=matches[0];screen=screens[0 if page==0 else 1];x=m['x']+pic.width//2-40;y=m['y']-10
 cell=screen.crop((x,y,x+80,y+90)).resize((240,270),Image.Resampling.NEAREST);board.paste(cell,(i*240,25));draw.text((i*240+5,5),f'ACTUAL {n}',fill='white')
board.save(D/'actual_launch_verified.png')
(D/'runtime_negative_controls.json').write_text(json.dumps(checks,indent=2),'utf8')
print(json.dumps({'same_sample_verified':len(checks),'clut_negative_controls':sum('flattening_clut2_to_clut0_rejected' in c for c in checks),'contact_sheet':str(D/'actual_launch_verified.png')}))
