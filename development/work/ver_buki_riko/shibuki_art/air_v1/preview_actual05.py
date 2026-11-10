"""실행 증거를 검증한 뒤 이 시험본을 현재 포인터에 등록한다. 일회성 기록."""
import sys,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest,write_json
d=Path(__file__).parent;a=d/'production05';build=ROOT/'out/ver_buki_riko/shibuki_air_20261026T104016307897Z';m=json.loads((build/'manifest.json').read_text());expected='57994d528b0508586cee2e7c4723e5aa8f84aca665862ac04786cbbaede97164'
assert digest(build/'shibuki_riko.bin')==expected
recipe=ROOT/'work/ver_buki_riko/shibuki_air/20261026T103933348163Z/recipe.json'
for name in ('20261026T103933348163Z','20261026T104017052747Z'):assert (ROOT/'work/ver_buki_riko/shibuki_air'/name/'modified.arc').read_bytes()==(build/'modified.arc').read_bytes()
rec=json.loads(recipe.read_text());assert rec['paired_manifest_sha256']==digest(a/'pairs.json')
assert (build/'recipe.json').read_bytes()==recipe.read_bytes()
groups=[];actual=Image.new('RGB',(6*200,4*240),'#28394b');draw=ImageDraw.Draw(actual)
for row,name in enumerate(('20261026T104549844783Z','20261026T104558184994Z','20261026T104620494883Z','20261026T104612029229Z')):
 path=ROOT/'work/ver_buki_riko/shibuki_run_runtime'/name/'verification.local.json';r=json.loads(path.read_text());nums=list(range(34 if r['shoot'] else 33,55,2))
 assert r['modified_bin_sha256']==expected and r['air'] and r['verified_frames']==nums and not r['unverified_frames']
 for n,f in r['frames'].items():
  assert f['verified'] and f.get('render_palette_is_base',True)
  assert any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in f['samples'])
  im=Image.open(path.parent/f'expected_{int(n):03d}.png');assert f['matches'][0]['opaque_pixels_equal']==sum(v!=0 for v in im.tobytes())
 groups.append({'direction':r['direction'],'shoot':r['shoot'],'evidence':str(path.relative_to(ROOT)),'whole_opaque_matched':nums,'base_palette':True})
 for col,n in enumerate((34,40,46,50,52,54) if r['shoot'] else (33,39,45,49,51,53)):
  match=r['frames'][str(n)]['matches'][0];screen=Image.open(path.parent/f"actual_{n:03d}_{match['page_y']}.png");im=Image.open(path.parent/f'expected_{n:03d}.png');bb=im.getbbox()
  if match['flip_x']:bb=(im.width-bb[2],bb[1],im.width-bb[0],bb[3])
  x,y=match['x'],match['y'];crop=screen.crop((max(0,x+bb[0]-7),max(0,y+bb[1]-7),min(320,x+bb[2]+7),min(240,y+bb[3]+7)));crop=crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST);actual.paste(crop,(col*200+(200-crop.width)//2,row*240+28));draw.text((col*200+8,row*240+7),f"actual {r['direction']} {n}",fill='white')
actual.save(build/'air_actual_review.png')
