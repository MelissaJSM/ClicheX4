from pathlib import Path
import sys,json,contextlib,io
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.riko_master_sheet import split
from scripts.project import write_json
D=Path(__file__).parent;M=ROOT/'work/ver_buki_riko/production_master/20261024T012141953805Z'
record=json.loads((M/'master.local.json').read_text('utf8'));layout={r['key']:r for r in record['layout']['frames']}
results=[]
for name,n,world in [('side_head',39,(-10,-22)),('shared_body_conflict',42,(-7,3))]:
 im=Image.open(M/'riko_master_indexed.png');r=layout[f'bank0_{n:03}'];b=record['source_frames'][f'bank0_{n:03}']['bounds']
 # Native rect is positioned at cell origin + source bounds.
 x,y=r['cell'][0]+48+world[0],r['cell'][1]+56+world[1]
 if name=='side_head':
  hx,hy,hw,hh=record['protected_head_rectangles'][f'bank0_{n:03}']
  px,py=r['cell'][0]+48+b[0]+hx,r['cell'][1]+56+b[1]+hy
  points=[(px+xx,py+yy) for yy in range(hh) for xx in range(hw) if im.getpixel((px+xx,py+yy))]
  x,y=points[0]
 im.putpixel((x,y),15 if im.getpixel((x,y))!=15 else 12)
 path=D/f'negative_{name}.png';im.save(path,transparency=0,bits=4)
 before=set((ROOT/'work/ver_buki_riko/master_split').iterdir())
 try:
  with contextlib.redirect_stdout(io.StringIO()):split(M/'master.local.json',path)
  raise AssertionError('Bad master was accepted')
 except ValueError as e:
  expected='Protected head' if name=='side_head' else 'conflicting'
  if expected not in str(e):raise
  assert set((ROOT/'work/ver_buki_riko/master_split').iterdir())==before
  results.append({'case':name,'rejected':True,'reason':str(e),'output_created':False})
write_json(D/'guard_checks.json',{'checks':results});print(json.dumps(results))
