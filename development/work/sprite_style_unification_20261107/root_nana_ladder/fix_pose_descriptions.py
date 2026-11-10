from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
changes={3:[('rear-view nearing the top of the ladder with both hands above the head and one knee bent','rear-view climbing with one hand beside the head, the other held out at shoulder height and one knee bent'),('rear-view pulling over the top with elbows out and legs tucked','rear-view climbing over the top with both hands planted low to either side of the hips, elbows extending back, and knees tucked; the hands are below the head, not overhead')],4:[('side-view low landing crouch after stepping off the ladder','side-view leaning forward to the left with the body crouched, hands low in front and legs bent back, exactly as the edit target') ]}
for page,pairs in changes.items():
 out=D/f'inputs_page{page:02}';p=out/'prompt.txt';s=p.read_text('utf8')
 for old,new in pairs:assert old in s;s=s.replace(old,new)
 p.write_text(s,'utf8');m=json.loads((out/'manifest.json').read_text('utf8'))
 for q in m['inputs']:q['sha256']=hashlib.sha256((ROOT/q['path']).read_bytes()).hexdigest()
 (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8')
