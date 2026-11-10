"""Ultimate 고유 효과 진단과 출처 보존 오라 후보를 합친65목표층."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=D/'effect_probe_v1';aura=D/'aura_contact_probe_v2';out=D/'final_targets_v1';out.mkdir(exist_ok=False)
    m=json.loads((source/'manifest.json').read_text('utf8'));links=[]
    for ns in m['targets']:
        n=int(ns)
        for ps in m['targets'][ns]:
            p=int(ps);s=(aura if n in(235,236)else source)/f'layer{p}_{n:03}.png';dest=out/s.name;dest.write_bytes(s.read_bytes())
            z=np.array(Image.open(dest));m['targets'][ns][ps]=hashlib.sha256(z.tobytes()).hexdigest();links.append({'ref':n,'bank':p,'source':str(s),'source_sha256':sha(s),'target_sha256':sha(dest)})
    m['aura_registration']=json.loads((aura/'registration.json').read_text('utf8'));m['source_files']=links;m['scope']='新Ultimate 피격13 대상65층. 현재고유효과·양폼새몸·오라성분 정합후 패킹 입력. 미술/패킹/독립/실기는 각 별도 증거.'
    m['frames']=[q for q in m['frames']if q['ref']not in(235,236)]+m['aura_registration']['frames']
    (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8')
    print(sha(out/'manifest.json'))
if __name__=='__main__':main()
