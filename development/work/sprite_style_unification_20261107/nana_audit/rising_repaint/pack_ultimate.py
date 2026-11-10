"""동결된 기본 라이징 패커를 읽어 Ultimate 7참조를 별도 ARC로 준비한다."""
from pathlib import Path
import sys,json,argparse,importlib.util
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
PARENT=N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC'
BEFORE='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'
TD=D/'ultimate_layers_probe_v2'
PACKER_SHA='6eb5672d6397f341084702fd0fe57f5acb7b52658d2973c075b15ff4a9affb2f'
REFS=(100,101,102,103,104,231,232);PBS=(0,5,6,7,8)

def load_packer():
    p=D/'pack_native.py';need(digest(p)==PACKER_SHA,'동결 기본 패커 불변')
    spec=importlib.util.spec_from_file_location('nana_rising_ultimate_packer',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.BEFORE=BEFORE;m.PARENT=PARENT
    return m

def targets():
    manifest=json.loads((TD/'manifest.json').read_text('utf8'))
    target={(n,pb):np.array(Image.open(TD/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS}
    return target,manifest

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='packed_ultimate_candidate_v1');args=ap.parse_args()
    out=(D/args.out).resolve();need(out.is_relative_to(D.resolve())and not out.exists(),'새 자체 출력 경로')
    target,manifest=targets();m=load_packer();result,report=m.build(PARENT.read_bytes(),target,manifest)
    report['scope']='새 Ultimate 라이징7 기술후보. 전후 의상/기타층과 비대상 보존. 새 게임 실행 미수행.'
    report['borrowed_packer_sha256']=PACKER_SHA;report['targets_manifest_sha256']=digest(TD/'manifest.json')
    out.mkdir();(out/'PL02_U.ARC').write_bytes(result);a=Archive(PARENT.read_bytes());b=Archive(result)
    for i,ns in enumerate(((100,101),(102,103),(104,231))):
        helper.grid([(f'Ultimate Rising {n}',[('before idle',b.composite(0,15)[0]),('new before',b.composite(n,15)[0]),('after idle',b.composite(0,0)[0]),('new after',b.composite(n,0)[0])])for n in ns],out/f'readback_{i+1}.png',7)
    report['physical_stream_offsets_231_232']={str(n):b.banks[0]['frames'][n].get('offset')for n in(231,232)}
    report['same_decoded_231_232']=m.raw(b,0,231)==m.raw(b,0,232)
    write(out/'verification.json',report)
    write(out/'proposal.json',{'project':'ver_rin_nana','baseline_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','parent_arc_sha256':BEFORE,
        'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','working_parent_before':BEFORE,'after':sha(result)}},
        'changed_from_working_parent':list(REFS),'candidate_only':True,'runtime_verified':False})
    print(json.dumps({'after':sha(result),'raw':report['raw_checked'],'rgba':report['rgba_combinations'],'slack':report['composition_slack'],'packing':report['packing']}))
if __name__=='__main__':main()
