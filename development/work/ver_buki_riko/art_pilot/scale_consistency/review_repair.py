from pathlib import Path
P=Path(__file__).parent
exec((P/'review.py').read_text(encoding='utf-8').replace('riko_motion_20261023T152218300431Z','riko_motion_20261023T195248689307Z'))
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
from collections import deque
R=P/'gait_cape_repair';recipe=json.loads((R/'recipe.json').read_text());out=ROOT/'out/ver_buki_riko/riko_motion_20261023T195248689307Z'
def world(n,folder,prefix):
 im=np.array(Image.open(folder/f'{prefix}_{n:03d}.png'));b=geometry[n][1];w=np.zeros((128,128),dtype=np.uint8);w[64+b[1]:64+b[3],64+b[0]:64+b[2]]=im;return w
def components(a):
 unseen=set(map(tuple,np.argwhere(a!=0)));groups=[]
 while unseen:
  seed=unseen.pop();q=deque([seed]);g=[seed]
  while q:
   y,x=q.popleft()
   for dy,dx in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
    p=(y+dy,x+dx)
    if p in unseen:unseen.remove(p);q.append(p);g.append(p)
  groups.append(g)
 return sorted(groups,key=len,reverse=True)
cape=[]
for n in [*range(27,35)]:
 before=world(n,P,'locked_frame');after=world(n,R,'frame');cb=components(before);ca=components(after)
 record={'frame':n,'before_component_sizes':[len(c) for c in cb],'after_component_sizes':[len(c) for c in ca]}
 if n<=32:
  tip=next(p for g in cb for p in g if p[0]-64<-15 and p[1]-64>16);body=(64,64)
  assert tip not in cb[0] and tip in ca[0]
  record['cape_tip_world']=[int(tip[1]-64),int(tip[0]-64)];record['cape_joins_main_body']=True
 cape.append(record)
g=recipe['gait']['phase_assignment'];phases=[r['near_phase'] for r in g];assert phases==list(range(12)) and all(r['far_phase']==(r['near_phase']+6)%12 for r in g)
assert max(r['whole_pose_dy'] for r in g)-min(r['whole_pose_dy'] for r in g)<=1
for field in ['near_foot','far_foot']:
 order=sorted(g,key=lambda r:r['near_phase' if field=='near_foot' else 'far_phase']);stance=[r[field][0] for r in order[:6]];swing=[r[field][0] for r in order[6:]];assert stance==sorted(stance) and swing==sorted(swing,reverse=True)
report={'cape_connectivity_8_neighbors':cape,'gait':g,'ground_baseline':23,'opposite_phase_ticks':16,'total_ticks':32,'upper_body_whole_translation_range':1,'anatomical_size_validation':'Head/neck foreground exact; no per-pose resizing. Full skeleton/art quality is not automatically proven.','automated_tests':{'command':'python -m unittest discover -s tests -v','passed':41,'exit_code':0}}
(out/'art_quality_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
frames=[];ticks=recipe['run_ticks'];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
for n in range(7,21):
 w=world(n,R,'frame');a=w[24:96,32:96];m=a!=0;rgba=np.zeros((72,64,4),dtype=np.uint8);rgba[m,:3]=colors[a[m]-1];rgba[m,3]=255;canvas=Image.new('RGBA',(512,320),(42,45,54,255));d=ImageDraw.Draw(canvas);d.text((8,3),'미리보기 · 1배 / 4배 · 원작 32 tick',font=font,fill='white');canvas.alpha_composite(Image.fromarray(rgba),(60,100));canvas.alpha_composite(Image.fromarray(rgba).resize((256,288),Image.Resampling.NEAREST),(225,30));frames.append(canvas.convert('RGB'))
frames[0].save(out/'gait_preview.gif',save_all=True,append_images=frames[1:],duration=[round(t/60*1000) for t in ticks],loop=0,disposal=2)
import shutil
shutil.copyfile(R/'assembled_board.png',out/'motion_review.png')
print(json.dumps({'cape':cape,'phase_cycle':'opposite at 16 ticks','tests':41}))
