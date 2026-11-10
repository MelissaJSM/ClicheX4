"""확인한 새 몸체·원효과에 출처 보존 오라 국소 정합을 결합한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
PBS=(0,5,6,7,8)
def main():
    src=D/'effect_probe_v1';aura=D/'aura_contact_probe_v2';out=D/'final_targets_v1'
    need(not out.exists(),'새 경로');out.mkdir()
    meta=json.loads((src/'manifest.json').read_text('utf8'))
    am=json.loads((aura/'manifest.json').read_text('utf8'));ar={q['ref']:q for q in am['frames']}
    body={pb:np.array(Image.open(D/'joint_layers_probe_v1'/f'layer{pb}_234.png'))for pb in PBS}
    union=np.logical_or.reduce([x>0 for x in body.values()]);changes=[]
    for ns,layerhashes in meta['targets'].items():
        n=int(ns)
        for pbs,oldhash in layerhashes.items():
            pb=int(pbs);z=np.array(Image.open(src/f'layer{pb}_{n:03}.png'))
            need(sha(z.tobytes())==oldhash,'진단 목표 불변')
            if n in ar and pb==0:
                fx=np.array(Image.open(aura/f'effect_{n:03}_indices.png'))
                expected=np.zeros_like(fx);oldfx=np.array(Image.open(src/f'effect_{n:03}_bank0.png'))
                for q in ar[n]['source_links']:
                    x,y=q['world'];sx,sy=q['source_world'];need(oldfx[sy+160,sx+160]==q['index'],'원오라 출처')
                    need(expected[y+160,x+160]==0,'오라 중복');expected[y+160,x+160]=q['index']
                need(np.array_equal(expected,fx),'오라 조각 재구성')
                need(not np.any((fx>0)&union),'부분의상 포함 오라 겹침')
                z=np.where(fx,fx,body[0]).astype(np.uint8);changes.append([n,pb])
            Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
            layerhashes[pbs]=sha(z.tobytes())
    meta.update({'scope':'새 피격13 최종 패킹용 목표. 기존 오라85/172px는 출처 보존 강체 정합, 새 몸체 불변. 아직 후보/실기 미수행.',
                 'diagnostic_targets_manifest_sha256':digest(src/'manifest.json'),'aura_registration_manifest_sha256':digest(aura/'manifest.json'),
                 'aura_registration':am,'changed_layers_from_diagnostic':changes,'runtime_verified':False})
    write(out/'manifest.json',meta);print(digest(out/'manifest.json'))
if __name__=='__main__':main()
