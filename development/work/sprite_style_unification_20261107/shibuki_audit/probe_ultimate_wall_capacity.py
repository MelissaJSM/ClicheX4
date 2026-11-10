"""첫 벽 세 자세의 양폼 무손실 패킹 가능성만 확인한다. ARC를 쓰지 않는다."""
from pathlib import Path
import sys,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent
ROOT=H.parents[2]
sys.path.insert(0,str(ROOT))
import native_pose_pack as packer
from native_pose_pack import need,sha,write

P=H/'prepared_ultimate_lowhp01/PL02_U.ARC'
S='3dd0d9a2cafd8e4d4355ef131c69c39f794698f6752524b39cf488f5b3bc737b'
def main():
    p=argparse.ArgumentParser();p.add_argument('--all-six',action='store_true');args=p.parse_args()
    O=H/('ultimate_wall_capacity02'if args.all_six else'ultimate_wall_capacity01')
    need(not O.exists(),'Fresh probe required')
    data=P.read_bytes();need(sha(data)==S,'Wrong cumulative source')
    I=H/'ultimate_wall_contacts_probe01'
    before={n:np.array(Image.open(I/'before'/f'{n:03}_indices.png'))for n in(55,57,59)}
    after={n:np.array(Image.open(I/'after'/f'{n:03}_indices.png'))for n in before}
    if args.all_six:
        J=H/'ultimate_wall_page02_contacts01'
        before.update({n:np.array(Image.open(J/'before'/f'{n:03}_indices.png'))for n in(61,63,65)})
        after.update({n:np.array(Image.open(J/'after'/f'{n:03}_indices.png'))for n in(61,63,65)})
    O.mkdir()
    # This private process adapts the reusable packer's input guard only after
    # independently matching the frozen cumulative parent above.
    packer.ARC_SHA=S
    try:
        result,proof=packer.packing(data,before,after)
        proof.update({'passed':True,'capacity_only':True,'arc_written':False,'not_ready_for_game':True,'source_sha256':S,'prospective_arc_sha256':sha(result),'selected_refs':sorted(before),'remaining_scope':'사격6짝 미완료. 이 시험은 중간 몸체만이며 최종 제안이 아님.'})
    except ValueError as e:
        proof={'passed':False,'capacity_only':True,'source_sha256':S,'arc_written':False,'reason':str(e),'art_simplified':False}
    write(O/'verification.json',proof)
    print({k:v for k,v in proof.items()if k in('passed','groups','parts_slack','graphics','reason')})

if __name__=='__main__':main()
