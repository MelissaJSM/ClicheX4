"""벽 누적본 뒤에도 남은 큰 본체 동작을 대기와 다시 대조한다."""
from pathlib import Path
import sys,json,hashlib
from collections import Counter
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
sha=lambda b:hashlib.sha256(b).hexdigest()
O=H/'remaining_after_wall01'
SOURCES={'PL00_U.ARC':('prepared_arrival_victory01','78b329a07d888682c24b440386cb365f826572402346b3ee6620216ce951617e'),'PL02_U.ARC':('prepared_ultimate_wall01','c851fb17b2369281667970c414be63eb31fb1f02fe5641ad667bfb4b5c8507cf')}
SELECT={'base':[3,11,17,25,33,35,39,45,67,71,79,100], 'fourth':[3,11,17,25,33,35,39,45,67,71,79,100], 'ultimate_before':[33,35,39,45,67,71,79,143,144,156,162,213], 'ultimate_after':[33,35,39,45,67,71,79,143,144,156,162,213]}
def main():
    assert not O.exists();O.mkdir();a={}
    for file,(d,s)in SOURCES.items():
        raw=(H/d/file).read_bytes();assert sha(raw)==s;a[file]=Archive(raw)
    rows=[]
    for form,refs in SELECT.items():
        file='PL02_U.ARC'if form.startswith('ultimate')else'PL00_U.ARC';mask=15 if form in('fourth','ultimate_before')else 0
        for i in range(2):
            ns=refs[i*6:(i+1)*6];p=O/f'{form}_{i:02}.png';page([(str(n),a[file].composite(n,mask)[0])for n in ns],a[file].composite(0,mask)[0],p,cols=3,scale=5);rows.append({'form':form,'refs':ns,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())})
    (O/'manifest.json').write_text(json.dumps({'source':SOURCES,'sheets':rows,'art_changed':False,'runtime':False},ensure_ascii=False,indent=2)+'\n','utf8')
    print({'sheets':len(rows),'path':str(O)})
if __name__=='__main__':main()
