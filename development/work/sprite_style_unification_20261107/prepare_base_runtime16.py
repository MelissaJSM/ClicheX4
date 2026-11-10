from pathlib import Path
import json
W=Path(__file__).resolve().parent;R=W/'runtime'
source=R/'load_fourth_rn16.py';dest=R/'load_base_rn16.py';assert not dest.exists()
s=source.read_text('utf8').replace('full-armor DATA3','basic DATA1')
s=s.replace('(0,15,2,0)','(0,0,0,0)').replace('t[7]<=2','t[7]<=0').replace('t[7]<2','t[7]<0')
s=s.replace('(0,48,2,15,255,0)','(0,48,0,0,255,0)').replace('Unexpected full-armor record','Unexpected basic record')
dest.write_text(s,'utf8')
events=[(1,.1,['square']),(3,.22,['cross']),(3.18,.1,['square']),
        (5,.08,['left']),(6,.1,['square']),(8,.22,['cross']),(8.18,.1,['square'])]
p=R/'nana_base_rising16_plan.json';assert not p.exists()
p.write_text(json.dumps({'duration':11,'events':[dict(at=t,hold=h,keys=k) for t,h,k in events]},indent=2)+'\n','utf8')
print(dest)
