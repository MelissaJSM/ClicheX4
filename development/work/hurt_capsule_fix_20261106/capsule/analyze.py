"""최신 입력을 읽기 전용으로 복원해 캡슐 몸체와 효과를 대조한다."""
from pathlib import Path
import sys,json,struct,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive,animation_map
from scripts.discover_inputs import DiscReader
SOURCE=ROOT/'out/ver_buki_riko/boss_voice_restored_20261105_v2/shibuki_riko.bin'
HASH='ef2fcec562f02f6ba6b372e26b021924ea595abe4d654a9fc4e632a529804bb7'
def sha(v):return hashlib.sha256(v).hexdigest()
def main():
 assert sha(SOURCE.read_bytes())==HASH
 with SOURCE.open('rb') as f:
  d=DiscReader(f,SOURCE.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']}
  assets={n:d.read(rs[n]['lba'],rs[n]['size']) for n in ('PL02_U.ARC','SLUS_005.61')}
 for n,a in assets.items():(H/n).write_bytes(a)
 arc=Archive(assets['PL02_U.ARC']);anims,_=animation_map(assets['SLUS_005.61']);a=anims[107]
 refs=list(dict.fromkeys([0]+[s['frame'] for s in a['steps']]))
 board=Image.new('RGB',(1000,700),'#263642');dr=ImageDraw.Draw(board)
 for i,n in enumerate(refs):
  for j,mask in enumerate((0,15)):
   im,_=arc.composite(n,mask);im.save(H/f'body_{n}_mask{mask}.png');im=im.crop((120,120,210,210)).resize((270,270),Image.Resampling.NEAREST)
   x=i*300;y=j*320;board.paste(im,(x,y+30),im);dr.text((x,y),f'body ref{n} mask{mask}',fill='white')
 board.save(H/'body_comparison.png')
 colors=np.array([(0,0,0,0),(255,255,255,255),(130,220,255,255),(70,120,255,255)]+[(255,80,80,255)]*12,np.uint8)
 board=Image.new('RGB',(6*210,2*240),'#263642');dr=ImageDraw.Draw(board)
 stats=[]
 for n in range(12):
  px,meta=arc.layer(n,18,10);im=Image.fromarray(colors[px%16]);im.save(H/f'ghost10_{n}.png')
  x=n%6*210;y=n//6*240;crop=im.crop((120,110,200,195)).resize((200,212),Image.Resampling.NEAREST);board.paste(crop,(x,y+24),crop);dr.text((x,y),f'ghost 10/{n}',fill='white');stats.append({'frame':n,'pixels':int(np.count_nonzero(px)),'parts':len(meta['parts'])})
 board.save(H/'ghost_comparison.png')
 report={'baseline':SOURCE.relative_to(ROOT).as_posix(),'baseline_sha256':HASH,'files':{n:{'sha256':sha(v),'record':rs[n]} for n,v in assets.items()},'capsule_player_animation':a,'refs':refs,'ghosts':stats}
 (H/'analysis.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
 print(json.dumps(report))
if __name__=='__main__':main()
