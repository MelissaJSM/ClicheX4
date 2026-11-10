"""생성한 하강 다리만 인덱스 변환하여 원래 상체·사격 팔 픽셀을 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.normalize_nana_run import quantize
from scripts.prepare_nana_idle_shot import PILOT,INV,write
from scripts.project import digest
from scripts.extract_zero import save_image

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=ROOT/'work/ver_rin_nana/nana_art/fall_legs_v1';out=a.output.resolve()
 if not out.is_relative_to(d)or out.exists():raise ValueError('Fresh isolated fall output required')
 src=Image.open(d/'generated.png').convert('RGBA');pal=list(struct.unpack('<16H',(PILOT/'palette.bin').read_bytes()));rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31]for w in pal],np.int32);artroot=d.parent/'air_v1';oldart=json.loads((artroot/'normalized01/art.json').read_text('utf8'));oldpairs=json.loads((artroot/'paired03/pairs.json').read_text('utf8'));out.mkdir();body=out/'body';pairs=out/'pairs';body.mkdir();pairs.mkdir();records=[];checks=[];yy,xx=np.indices((80,96));board=Image.new('RGB',(3*384,3*320),'#222630');draw=ImageDraw.Draw(board)
 for i,n in enumerate((43,45,47)):
  before=np.array(Image.open(artroot/'normalized01'/f'run_{n:03d}.png'));shot_before=np.array(Image.open(artroot/'paired03'/f'shoot_{n:03d}.png'));crop=src.crop((round(i*src.width/3),0,round((i+1)*src.width/3),src.height));small=quantize(crop,(48,64),rgb);candidate=np.zeros_like(before);candidate[8:72,28:76]=small;cut={43:44,45:44,47:46}[n]
  # A common canvas scale is retained. Register translated head/torso only;
  # generated upper-body pixels are then discarded, not pasted into the game.
  compare=(yy>=16)&(yy<cut-1)&(xx>=32)&(xx<66);best=None
  for dy in range(-3,4):
   for dx in range(-3,4):
    v=np.zeros_like(before);sy0=max(0,-dy);sy1=min(80,80-dy);sx0=max(0,-dx);sx1=min(96,96-dx);v[sy0+dy:sy1+dy,sx0+dx:sx1+dx]=candidate[sy0:sy1,sx0:sx1]
    error=int(np.count_nonzero(((v!=0)!=(before!=0))&compare))*4+int(np.count_nonzero((v!=before)&compare));key=(error,abs(dx)+abs(dy),dx,dy)
    if best is None or key<best[0]:best=(key,v)
  key,v=best;mask=(yy>=cut)&(yy<70)&(xx>=37)&(xx<64);result=before.copy();result[mask]=v[mask]
  # Preserve the one-pixel hip seam under the unchanged skirt. The generated
  # bent thigh joins below this exact original attachment row.
  result[cut]=before[cut]
  shot=shot_before.copy();shot[mask]=result[mask]
  if not np.array_equal(before[mask],shot_before[mask]):raise ValueError('Leg mask touches existing shot arm')
  if not np.array_equal(before[~mask],result[~mask])or not np.array_equal(shot_before[~mask],shot[~mask]):raise ValueError('Change escaped legs')
  if np.count_nonzero(before!=result)<15:raise ValueError('Leg edit ineffective')
  save_image(result.tobytes(),(96,80),pal,body/f'run_{n:03d}.png')
  for name,img in [('run',result),('shoot',shot),('common',np.where(result==shot,result,0).astype(np.uint8)),('shoot_body',np.where(result!=shot,shot,0).astype(np.uint8)),('gun',np.array(Image.open(artroot/'paired03'/f'gun_{n:03d}.png')))]:save_image(img.tobytes(),(96,80),pal,pairs/f'{name}_{n:03d}.png')
  r=next(q for q in oldart['frames']if q['frame']==n);records.append({**r,'image':f'run_{n:03d}.png','leg_edit':True,'source_canvas_shift':[key[2],key[3]],'protected_hip_row':cut,'body_registration_unchanged':True});checks.append({'frame':n,'changed_pixels':int(np.count_nonzero(before!=result)),'outside_leg_mask_identical':True,'shooting_legs_identical':True,'upper_body_and_gun_identical':True,'mask':[37,cut,64,70],'source_alignment_error':key[0]})
  for row,img in enumerate((before,result,shot)):
   im=Image.open(artroot/'normalized01'/f'run_{n:03d}.png' if row==0 else pairs/f"{'run' if row==1 else 'shoot'}_{n:03d}.png").convert('RGBA').resize((384,320),Image.Resampling.NEAREST);board.paste(im,(i*384,row*320),im);draw.text((i*384+10,row*320+8),f'{n+int(row==2)} '+['before','bent knees','shoot'][row],fill='white')
 write(body/'art.json',{**oldart,'scope':'fall_legs','source':(d/'generated.png').relative_to(ROOT).as_posix(),'source_sha256':digest(d/'generated.png'),'frames':records,'edit_only_legs':True,'upper_body_unchanged':True});write(pairs/'pairs.json',{**oldpairs,'scope':'fall_legs','frames':[q for q in oldpairs['frames']if q['run']in (43,45,47)],'body_art':body.relative_to(ROOT).as_posix(),'body_manifest_sha256':digest(body/'art.json'),'leg_edit_only':True});board.save(pairs/'paired_4x.png');write(out/'leg_checks.json',checks);print(json.dumps({'output':str(out),'checks':checks}))
if __name__=='__main__':main()
