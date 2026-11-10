"""140 독립5판 실제 열람과 기존 실행근거를 분리 결속한다."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;U=W/'nana_audit/base_flash140_restore01';P=U/'packed_flash_candidate_v1';O=D/'nana_base_flash140_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(R).as_posix()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(name,data):
 p=O/name;assert not p.exists(),p;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
r=read(O/'report.json');assert r['passed']and sha(O/'report.json')=='934a442a3faf35a213b5223be65ca866aa94ced544f40a714373a638ce1b1488'
for p,h in r['inputs'].items():assert sha(R/p)==h,p
reader=D/'verify_nana_base_flash140_independent01.py';ast.parse(reader.read_text(encoding='utf8'))
v={
 'actually_viewed':True,'candidate_sha256':r['candidate_sha256'],'sheets':r['readback_sheets'],
 'findings':[
  '독립 재추출1판과 부분4판, 합5판을 실제 열람했다. 기본 섬광 외곽과 양옆 원46효과는 전후 동일하게 읽힌다.',
  '포스 전체15에서 기존 기본머리 실루엣에 빠져 있던 긴 뒤베일/맨다리 바깥이 현재포스 대기 알파와 이어진다. 새 단색 실루엣이 현재 대기보다 임의로 커진 것이 아니라 현재알파149셀 추가임을 수치와 함께 확인했다.',
  '부분0..15의 모자/몸통/팔/다리 선택을 모두 대조했다.8/10/12/14 등 머리파츠 없이 다리만 선택한 판에서 뒤베일 끝의 작은 분리점은 동일idle 부분에도 있는 형태이며 새140 단절로 계산하지 않는다.',
  '이5판에서 추가 확정 절단은 찾지 못했다. 정지 재추출 검토이며 실시간 번쩍임·CLUT 변화·게임 내 수용을 증명하지 않는다.'
 ],
 'runtime_verified':False,'new_art_generated':False,'original_US_restoration_claimed':False
}
write('visual_review.json',v)
cycle=read(U/'native_cycle_v1/verification.json');manifest=read(U/'native_cycle_v1/manifest.json')
assert cycle['passed']and cycle['canvas_native_checks']==30 and cycle['candidate_arc_sha256']==r['candidate_sha256']==manifest['candidate_arc_sha256']
assert manifest['native_table_bytes_exact']and manifest['exe_sha256']=='93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616'
assert sha(R/manifest['caller_evidence']['path'])==manifest['caller_evidence']['sha256']
evidence={}
for p in(P/'INPUT_FROZEN.json',P/'reproduction.json',U/'native_components_v1_native_checks.json',U/'native_cycle_v1/manifest.json',U/'native_cycle_v1/verification.json',D/'nana_base_effect_callers01/report.json',D/'nana_base_effect_callers01/conclusions.json'):
 evidence[rel(p)]=sha(p)
write('evidence_binding.json',{'candidate_sha256':r['candidate_sha256'],'independent_scope':r['counts'],'producer_execution_evidence':evidence,'scope_separation':['원MIPS1/18GPU·재현1/7거부·원표2/30canvas는 제작자 기존 결과에 해시를 결속했다. 이reader의 새 실행으로 표시하지 않는다.','원표 시간/140event1 실제코드 의미는 기존 caller 보고서의 읽기 근거다. 여기서는 caller 새실행과 실기 미수행.','현재idle 파생은 새원화 생성 없이 선택의상 알파를 반영하는 정책이며208..212는 변경하지 않았다.']})
inputs={**r['inputs'],**evidence,rel(reader):sha(reader),rel(Path(__file__)):sha(Path(__file__))}
outputs={rel(p):sha(p)for p in sorted(O.iterdir())if p.is_file()}
write('READER_LOCK.json',{'candidate_sha256':r['candidate_sha256'],'inputs':inputs,'outputs':outputs,'report_visual_flag':'report.json은 열람 전 스냅샷이므로 actually_viewed=false이며, 최종 visual_review.json에 실제5판 열람을 결속했다.','resources_modified':False})
print(json.dumps({p.name:sha(p)for p in(O/'report.json',O/'visual_review.json',O/'evidence_binding.json',O/'READER_LOCK.json')}))
