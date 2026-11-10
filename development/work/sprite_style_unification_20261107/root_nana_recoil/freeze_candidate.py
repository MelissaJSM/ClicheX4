from pathlib import Path
import sys,json,hashlib
import pack_recoil
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=D/'packed_recoil03';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
def main():
 independent=W/'zero_audit/nana_base_recoil2_independent01';assert not(out/'FROZEN.json').exists()
 checks=[out/'report.json',out/'reproduction.json',D/'recoil_components_native_checks.json',D/'native_sequence01/browser_verification.json',independent/'report.json']
 for p in checks:assert read(p)['passed'],p
 assert read(independent/'report.json')['candidate_sha256']==sha(out/'PL00_U.ARC')
 visual=read(independent/'visual_review.json');assert visual
 assert sha(W/'root_review_checkpoint121.json')=='0f9f7687adc324eaab3692c8366558db40733df0919ef9a9ed343ff5ec7a488f'
 paths=set(D.glob('*.py'))
 for mod in list(sys.modules.values()):
  s=getattr(mod,'__file__',None)
  if s:
   p=Path(s).resolve()
   if p.suffix=='.py' and p.is_relative_to(ROOT) and '/work/tools/' not in p.as_posix():paths.add(p)
 for name in ('inputs01','art01','registered01','joint_layers02'):
  paths.update(p for p in(D/name).rglob('*') if p.is_file())
 bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
 write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
 write(out/'INPUT_FROZEN.json',{'scope':'새90/91 두 의상. 동일20texel8px총, 새상단베일 head5 소유02. 기존head9조립레코드에 새머리픽셀 보존. 반려pack01/02 제외.','files':[bound(p) for p in sorted(paths)]})
 proposal={'resource':'PL00_U.ARC','path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(out/'report.json')['before'],'after':sha(out/'PL00_U.ARC'),'refs':[90,91],'new_authored_body_refs':[90,91],'derived_refs':[],'forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'preserved':['비대상 몸체·팔레트·EXE·시간표·발사체·판정·음향·저장'],'runtime_verified':False,'user_accepted':False}
 write(out/'proposal.json',proposal)
 proof=[out/'PL00_U.ARC',out/'report.json',out/'reproduction.json',out/'INPUT_FROZEN.json',out/'proposal.json',D/'recoil_components.json',D/'recoil_components_native_checks.json',D/'native_sequence01/report.json',D/'native_sequence01/browser_verification.json',independent/'report.json',independent/'visual_review.json',W/'root_review_checkpoint121.json']
 write(out/'FROZEN.json',{'frozen':True,'character':'nana','candidate_sha256':proposal['after'],'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[bound(p) for p in proof],'source_lock_sha256':sha(out/'INPUT_FROZEN.json'),'status':'새90/91 몸체4셀. 재현2/거부7·원MIPS/GPU·64부분조합·독립/루트시각·원표91/7스텝/262canvas 통과. 실기발동 별도, 전체 미술 완료 아님.','runtime_verified':False,'final_user_accepted':False})
 print(json.dumps({'inputs':len(paths),'freeze_sha256':sha(out/'FROZEN.json'),'arc':proposal['after']}))
if __name__=='__main__':main()
