from pathlib import Path
import json,hashlib
D=Path(__file__).parent
m=json.loads((D/'manifest.json').read_text('utf8'))
for r in m['sheets']:
    p=D/Path(r['path']).name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
record={'actually_viewed':m['sheets'],'count':len(m['sheets']),'method':'view_image; whole group sheets and eight4x focused comparisons',
 'scope':'four full forms,bank0 allnonreserved references shown; not allpartialmasks or gameplay',
 'art_modified':False,'runtime_verified':False,
 'preserve_priority':{'all_forms':[0,115,116,117,118,119,141,142],'ride_heads':list(range(184,204)),'stand_body':[87,92]},
 'next_priority':[{'rank':1,'forms':['ultimate_before','ultimate_after'],'refs':list(range(33,67))+[93,94],'areas':['hair','sleeve','neck/shoulder'],'first_keys':[33,39,47,51]},
 {'rank':2,'forms':['all'],'refs':[98,99],'areas':['extended sleeves','chest/shoulder separation']},
 {'rank':3,'forms':['base','fourth'],'refs':list(range(143,156))+[183],'areas':['rear hair/veil','shooting sleeve']}],
 'limitations':['Blank/effect/vehicle heads are not fullbody failures.','New artwork status and observed deficiency are separate.','Selection/save/capsule and native gameplay not newly inspected in this pass.']}
(D/'review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8')
print(len(m['sheets']))
