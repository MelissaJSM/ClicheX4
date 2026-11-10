"""검증된 다층 패커를 새Ultimate 특수3 입력에만 연결하는 별도 실행기.

기존 승리 패커 파일은 수정하지 않는다. 이 프로세스의 입력 상수만 명시적으로
설정하고 동일한 전체raw/층/부분조합/비대상 검사를 재사용한다.
"""
from pathlib import Path
import sys,json,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
import pack_ultimate_victory as engine
from prepare_ultimate_special_targets import P,PARENT,PBS,REFS
TD=H/'ultimate_special_targets01'
MANIFEST='8c40bd581cb7029cfa574519922af098738486f1b2b8a4e948c57ae98b6ddbf3'

def validate(data,read=lambda p:p.read_bytes()):
    import io
    import numpy as np
    from PIL import Image
    need(sha(data)==PARENT,'Wrong exact parent')
    blob=read(TD/'manifest.json');need(sha(blob)==MANIFEST,'Target manifest changed')
    meta=json.loads(blob)
    for name,digest in meta['source_files'].items():need(sha(read(ROOT/name))==digest,'Source changed '+name)
    for n in REFS:
        for b in PBS:
            v=np.array(Image.open(io.BytesIO(read(TD/f'{n:03}_bank{b}_indices.png'))))
            need(sha(v.tobytes())==meta['targets'][str(n)][str(b)],'Target pixels changed')
    return meta

def build(data,progress=lambda x:None):
    validate(data)
    engine.P=P;engine.PARENT=PARENT;engine.PBS=PBS;engine.REFS=REFS;engine.TD=TD
    out,proof=engine.build(data,MANIFEST,progress)
    proof.update(scope='Ultimate 특수95/96/97 고정은행3참조 후보. 새 원화15층 보존, 원MIPS/독립/최종미술/실기는 별도.',
                 reused_packer={'path':'pack_ultimate_victory.py','sha256':sha((H/'pack_ultimate_victory.py').read_bytes()),
                    'explicit_process_only_configuration':{'parent':PARENT,'refs':list(REFS),'targets':TD.relative_to(ROOT).as_posix()},
                    'producer_file_modified':False})
    return out,proof

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='ultimate_special_pack01');args=ap.parse_args()
    out=(H/args.output).resolve();need(out.is_relative_to(H.resolve()) and not out.exists(),'Fresh own output');out.mkdir()
    logs=[]
    def log(row):logs.append(row);write(out/'progress.json',logs);print(json.dumps(row),flush=True)
    try:candidate,proof=build(P.read_bytes(),log)
    except Exception as ex:write(out/'report.json',{'passed':False,'error':str(ex),'arc_written':False});raise
    (out/'PL02_U.ARC').write_bytes(candidate);arc=Archive(candidate)
    for form,mask in (('before',15),('after',0)):
        page([(f'{n} actual {form}',arc.composite(n,mask)[0]) for n in REFS],arc.composite(0,mask)[0],out/f'{form}_readback.png',cols=2,scale=5)
    for n in (95,97):page([(f'{n} mask{mask:X}',arc.composite(n,mask,1)[0]) for mask in range(16)],arc.composite(0,0)[0],out/f'partial_{n:03}.png',cols=4,scale=3)
    write(out/'report.json',proof);print(json.dumps({'candidate':sha(candidate),'counts':proof['counts'],'graphics':proof['graphics']}))

if __name__=='__main__':main()
