from pathlib import Path
import sys,json,hashlib
import pack_special
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=D/'packed_special02';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
def main():
 independent=W/'zero_audit/nana_base_special4_independent01';assert not(out/'FROZEN.json').exists()
 for p in(out/'report.json',out/'reproduction.json',D/'special_components_native_checks.json',D/'native_sequence01/browser_verification.json'):assert read(p)['passed']
 assert sha(independent/'report.json')=='8d2d71d3bfb971c8cedd97d3d3d70cc760b91454e00ae3a02c330b370afac138'
 assert sha(independent/'visual_review.json')=='47212c8a2c9c664d19a653342697f734eeca909e5d6030c3ed3de6f9e3053b83'
 assert sha(W/'root_review_checkpoint114.json')=='80729a2ceea9b8572007ae81ee64296b5e9141160f51bf00324feca235009668'
 paths=set(D.glob('*.py'))
 for mod in list(sys.modules.values()):
  s=getattr(mod,'__file__',None)
  if s:
   p=Path(s).resolve()
   if p.suffix=='.py'and p.is_relative_to(ROOT)and'/work/tools/'not in p.as_posix():paths.add(p)
 for name in('inputs01','art01','registered01','joint_layers04'):
  paths.update(p for p in(D/name).rglob('*')if p.is_file())
 bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
 write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
 write(out/'INPUT_FROZEN.json',{'scope':'특수95/98 새 원화와96/99 원래X+1 관계. 최종 소매/베일/목 소유04와 네이티브 패커 입력. 이전 반려후보 제외.','files':[bound(p)for p in sorted(paths)]})
 proposal={'resource':'PL00_U.ARC','path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(out/'report.json')['before'],'after':sha(out/'PL00_U.ARC'),'refs':[95,96,98,99],'new_authored_body_refs':[95,98],'derived_refs':[96,99],'forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'preserved':['비대상 몸체·팔레트·EXE·원표·발사체·판정·음향·저장'],'runtime_verified':False,'user_accepted':False}
 write(out/'proposal.json',proposal)
 proof=[out/'PL00_U.ARC',out/'report.json',out/'reproduction.json',out/'INPUT_FROZEN.json',out/'proposal.json',D/'special_components.json',D/'special_components_native_checks.json',D/'native_sequence01/report.json',D/'native_sequence01/browser_verification.json',independent/'report.json',independent/'visual_review.json',W/'root_review_checkpoint113.json',W/'root_review_checkpoint114.json']
 write(out/'FROZEN.json',{'frozen':True,'character':'nana','candidate_sha256':proposal['after'],'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[bound(p)for p in proof],'source_lock_sha256':sha(out/'INPUT_FROZEN.json'),'status':'새95/98 몸체4셀·96/99원래x+1. 최종재현2/7입력거부·원MIPS/GPU·128부분조합·독립/루트시각·원표5/26스텝/430canvas 통과. 이전그림138139/97은별도잔여. 실기발동별도.','runtime_verified':False,'final_user_accepted':False})
 print(json.dumps({'inputs':len(paths),'freeze_sha256':sha(out/'FROZEN.json'),'arc':proposal['after']}))
if __name__=='__main__':main()
