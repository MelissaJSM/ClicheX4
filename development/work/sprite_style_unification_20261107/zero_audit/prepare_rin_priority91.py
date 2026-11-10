"""Read-only source review for pending movement, wall and hurt poses."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
from src.psx_player import graphics_bank
D=Path(__file__).parent/'rin_extension';O=D/'priority_after91';O.mkdir(exist_ok=True)
P=D/'prepared_victory_details_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='1a4e16a126b551e5f9d291401a5b9249e66c84aa0252b929b2fd31fa541b143e'
pal=struct.unpack_from('<64H',entry(arc,9));black=list(pal);black[:16]=struct.unpack_from('<16H',entry(arc,9),13*32)
done=set(json.loads((D/'progress_ledger.json').read_text('utf8'))['new_art_prepared_refs'])
groups=[('movement_wall',list(range(34,46))+[193]),('hurt_lowhp',list(range(130,147))+list(range(149,155)))]
rows=[];bank=graphics_bank(entry(arc,2),0)
for group,refs in groups:
 for n in refs:
  a,m=render(arc,0,0,n);key=f'b0_{n:03}'
  rows.append({'key':key,'group':group,'already_refined':key in done,'bbox':rgba(a,pal).getbbox(),'tiles':m['tile_count'],'shared_stream_refs':[f['index']for f in bank['frames']if f['offset']==m['stream_offset']],'index_sha256':sha(a.tobytes())})
 for form,words in [('normal',pal),('black',black)]:
  for i in range(0,len(refs),8):page([(f'b0_{n:03} '+('NEW'if f'b0_{n:03}'in done else'pending'),rgba(render(arc,0,0,n)[0],words))for n in refs[i:i+8]],rgba(render(arc,0,0,147)[0],words),O/f'{group}_{form}_{i//8:02}.png',cols=4,scale=4)
all_display=[]
for b in(0,1):
 for f in graphics_bank(entry(arc,2),b)['frames']:
  n=f['index']
  if b==1 and 42<=n<=49:continue
  a=render(arc,b,b*5,n)[0];all_display.append((b,n,a))
for r in rows:
 n=int(r['key'][3:]);a=render(arc,0,0,n)[0]
 r['exact_all_display_aliases']=[f'b{b}_{k:03}'for b,k,z in all_display if np.array_equal(a,z)]
(O/'manifest.json').write_text(json.dumps({'source':str(P.relative_to(ROOT)),'sha256':sha(arc),'rows':rows,'art_review_pending':True,'scope':'승리91 이후 남은 벽·피격 원화 후보. 새그림이 아닌 현재 자원의 재추출이다.'},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'output':str(O),'refs':len(rows)}))
