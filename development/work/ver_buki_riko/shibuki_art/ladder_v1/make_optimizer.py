from pathlib import Path
p=Path(__file__).parent
s=(p.parent/'hurt_v1/optimize03.py').read_text()
s=s.replace('production03','production04').replace('shibuki_wall_20261026T135224131979Z','shibuki_hurt_20261026T141724356492Z')
s=s.replace("for q in plan['groups']:","for n in (143,144,146,149,151,153,154,155,183):\n q=next(r for r in plan['groups'] if r['frame']==n)\n if n==149:q={**q,'writable':list(range(11))}")
s=s.replace('target,target,w)',"target,np.array(Image.open(a/'frame_150.png')) if n==149 else target,w)")
s=s.replace("'rects':layout['rects'],'mapping'","'rects':layout['rects'],'run_rects':layout.get('run_rects',[]),'shot_rects':layout.get('shot_rects',[]),'mapping'")
s=s.replace("r['rects'],[],[],","r['rects'],r.get('run_rects',[]),r.get('shot_rects',[]),")
s=s.replace('12000','20000')
s=s.replace("i=rng.randrange(len(r['rects']));r['rects'][i][rng.randrange(2)]+=rng.choice((-2,-1,1,2))","key=rng.choice([k for k in ('rects','run_rects','shot_rects') if r.get(k)]);i=rng.randrange(len(r[key]));r[key][i][rng.randrange(2)]+=rng.choice((-2,-1,1,2))")
s=s.replace('rng.sample(w,2)','rng.sample([t for t in w if t or n not in (144,146,149,151)],2)').replace('rng.choice(w)','rng.choice([t for t in w if t or n not in (144,146,149,151)])')
s=s.replace("target,target,winner['rects'],[],[],set(w)","target,np.array(Image.open(a/'frame_150.png')) if n==149 else target,winner['rects'],winner.get('run_rects',[]),winner.get('shot_rects',[]),set(w)")
(p/'optimize04.py').write_text(s)
