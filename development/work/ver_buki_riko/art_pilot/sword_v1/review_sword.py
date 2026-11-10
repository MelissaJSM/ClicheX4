from inspect_sword import *
from fit_sword import PAIRS,BODY
from src.epsxe_state import framebuffer,match_sprite
import math
new=json.loads((D/'recipe.json').read_text('utf8'))
def composed(n,current=True):
 a,b,s=original(n);folder=D if current else old;rec=new if current else recipe
 im=Image.new('RGBA',(192,192));im.alpha_composite(rgba(np.array(Image.open(folder/rec['frames'][str(n)]['file']))),(96+b[0],96+b[1]))
 e=PAIRS.get(n)
 if e:
  a,eb,s=original(e);ep=np.array(Image.open(folder/rec['frames'][str(e)]['file']));im.alpha_composite(rgba(ep,epal),(96+eb[0],96+eb[1]))
 return im
def preview():
 ns=[61,65,71,75,87,91,107,113,117,127,134,213,217,225,229,234,242,246]
 board=Image.new('RGBA',(6*384,6*280),(35,40,50));draw=ImageDraw.Draw(board)
 for i,n in enumerate(ns):
  for k,current in enumerate((False,True)):
   pic=composed(n,current).crop((36,44,132,112)).resize((384,272),Image.Resampling.NEAREST)
   row=i//6*2+k;board.alpha_composite(pic,(i%6*384,row*280+8));draw.text((i%6*384+4,row*280+1),f'{n} '+('SWORD' if current else 'BEFORE'),fill='white')
 board.save(D/'before_after_composite.png')
def runtime(folder):
 report=json.loads((folder/'verification.local.json').read_text());assert report['modified_bin_sha256']=='3d57273eed913b5894c6a3e8aa1696c30e9c37af533c1ffe2673f4a9b9e85353'
 results=[]
 for n in BODY:
  e=PAIRS.get(n)
  if str(n) not in report['frames']:continue
  full=composed(n);sprite=full.crop(full.getbbox());matches=[]
  paths=list(folder.glob(f'*vram*_{n:03d}.bin'))
  for path in paths:
   vram=path.read_bytes()
   if len(vram)!=1048576:continue
   for page in (0,256):
    screen=framebuffer(vram,0,page);m=match_sprite(screen,sprite)
    if m:
     target=folder/f'sword_composite_actual_{n:03d}_{page}.png';screen.save(target)
     sprite.save(folder/f'sword_composite_expected_{n:03d}.png')
     matches.append({'vram':path.name,'page_y':page,'matches':m,'actual':target.name})
  results.append({'body_frame':n,'effect_frame':e,'custom_effect_addition':str(e) in new['sword_effect_edits'],'whole_composite_verified':bool(matches),'evidence':matches})
 target=folder/'sword_composite_verification.json';target.write_text(json.dumps({'runtime_report':str(folder/'verification.local.json'),'full_opaque_comparison':True,'frames':results},indent=2),'utf8')
 print(json.dumps({'report':str(target),'verified':[(r['body_frame'],r['effect_frame']) for r in results if r['whole_composite_verified']]}))
if __name__=='__main__':
 if len(sys.argv)>1:runtime(Path(sys.argv[1]))
 else:preview()
