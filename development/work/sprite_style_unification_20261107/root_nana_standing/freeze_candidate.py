from pathlib import Path
import sys,json,hashlib
import pack_standing
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=D/'packed_standing03';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
def main():
 independent=W/'zero_audit/nana_base_standing3_independent01';assert not(out/'FROZEN.json').exists()
 checks=[out/'report.json',out/'reproduction.json',D/'standing_components_native_checks.json',D/'native_sequence01/browser_verification.json',independent/'report.json']
 for p in checks:assert read(p)['passed'],p
 assert read(independent/'report.json')['candidate_sha256']==sha(out/'PL00_U.ARC')
 visual=read(independent/'visual_review.json');assert visual
 assert sha(W/'root_review_checkpoint117.json')=='cd1f54a23bc607ff18552bbec14ca312a5a8adf8da79491e886de13facc1ea3c'
 paths=set(D.glob('*.py'))
 for mod in list(sys.modules.values()):
  s=getattr(mod,'__file__',None)
  if s:
   p=Path(s).resolve()
   if p.suffix=='.py' and p.is_relative_to(ROOT) and '/work/tools/' not in p.as_posix():paths.add(p)
 for name in ('inputs01','art01','registered01','joint_layers06'):
  paths.update(p for p in(D/name).rglob('*') if p.is_file())
 bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
 write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
 write(out/'INPUT_FROZEN.json',{'scope':'새89/97 두 의상과88 원래X-1/83효과. 눈 양자화·새총 공통화·베일 소유06 입력. 반려01..05/pack01..02 제외.','files':[bound(p) for p in sorted(paths)]})
 proposal={'resource':'PL00_U.ARC','path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(out/'report.json')['before'],'after':sha(out/'PL00_U.ARC'),'refs':[88,89,97],'new_authored_body_refs':[89,97],'derived_refs':[88],'forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'preserved':['비대상 몸체·팔레트·EXE·시간표·발사체·판정·음향·저장'],'runtime_verified':False,'user_accepted':False}
 write(out/'proposal.json',proposal)
 proof=[out/'PL00_U.ARC',out/'report.json',out/'reproduction.json',out/'INPUT_FROZEN.json',out/'proposal.json',D/'standing_components.json',D/'standing_components_native_checks.json',D/'native_sequence01/report.json',D/'native_sequence01/browser_verification.json',independent/'report.json',independent/'visual_review.json',W/'root_review_checkpoint117.json']
 write(out/'FROZEN.json',{'frozen':True,'character':'nana','candidate_sha256':proposal['after'],'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[bound(p) for p in proof],'source_lock_sha256':sha(out/'INPUT_FROZEN.json'),'status':'새89/97 몸체4셀·88 원효과파생. 재현2/거부7·원MIPS/GPU·96부분조합·독립/루트시각·원표3/21스텝/506canvas 통과. 실기발동 별도, 인접90/91및138139의 세부는 후속 잔여.','runtime_verified':False,'final_user_accepted':False})
 print(json.dumps({'inputs':len(paths),'freeze_sha256':sha(out/'FROZEN.json'),'arc':proposal['after']}))
if __name__=='__main__':main()
