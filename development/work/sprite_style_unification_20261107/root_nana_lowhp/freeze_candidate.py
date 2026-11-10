"""Freeze the reviewed low-HP body and native proofs, excluding rejected splits."""
from pathlib import Path
import sys,json,hashlib,argparse
import pack_lowhp
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=D/'packed_lowhp01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--independent',required=True);ap.add_argument('--report-sha',required=True);ap.add_argument('--visual-sha',required=True);args=ap.parse_args()
 independent=(ROOT/args.independent).resolve();assert independent.is_relative_to(W/'zero_audit')
 assert not (out/'FROZEN.json').exists()
 for p in(out/'report.json',out/'reproduction.json',D/'lowhp_components_native_checks.json',D/'native_sequence01/browser_verification.json'):assert read(p)['passed']
 assert sha(independent/'report.json')==args.report_sha and sha(independent/'visual_review.json')==args.visual_sha
 assert sha(W/'root_review_checkpoint111.json')=='95afbe3aa84daa964ae6b649666de4f5da70b241c0f44d63071cac37f3e9617d'
 paths=set(D.glob('*.py'))
 for mod in list(sys.modules.values()):
  name=getattr(mod,'__file__',None)
  if name:
   p=Path(name).resolve()
   if p.suffix=='.py'and p.is_relative_to(ROOT)and'/work/tools/'not in p.as_posix():paths.add(p)
 for name in('inputs01','art01','registered01','joint_layers03'):
  folder=D/name;assert folder.is_dir();paths.update(p for p in folder.rglob('*')if p.is_file())
 bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
 write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
 write(out/'INPUT_FROZEN.json',{'scope':'저체력 새 원화·등록·입/접지호흡·최종 부분파츠03·패커 입력. 반려된 초기 분할은 제외.','files':[bound(p)for p in sorted(paths)]})
 proposal={'resource':'PL00_U.ARC','path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(out/'report.json')['before'],'after':sha(out/'PL00_U.ARC'),'refs':list(range(120,126)),'new_authored_body_refs':[122],'authored_mouth_sample_ref':123,'derived_refs':[120,121,123,124,125],'forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'preserved':['비대상 몸체·팔레트·EXE·원표6·판정·음향·사용자 저장'],'runtime_verified':False,'user_accepted':False}
 write(out/'proposal.json',proposal)
 proof=[out/'PL00_U.ARC',out/'report.json',out/'reproduction.json',out/'INPUT_FROZEN.json',out/'proposal.json',D/'lowhp_components.json',D/'lowhp_components_native_checks.json',D/'native_sequence01/report.json',D/'native_sequence01/browser_verification.json',independent/'report.json',independent/'visual_review.json',W/'root_review_checkpoint111.json']
 freeze={'frozen':True,'character':'nana','candidate_sha256':proposal['after'],'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[bound(p)for p in proof],'source_lock_sha256':sha(out/'INPUT_FROZEN.json'),'status':'새 한 몸·입1픽셀·접지호흡6참조. 원형 재현2·입력거부7·원MIPS/GPU·192부분조합·독립/루트 시각·원표6/16스텝/322canvas 검사. 실제 플레이 저체력 발동은 별도.','runtime_verified':False,'final_user_accepted':False}
 write(out/'FROZEN.json',freeze);print(json.dumps({'input_files':len(paths),'sha256':sha(out/'FROZEN.json'),'arc':proposal['after']}))
if __name__=='__main__':main()
