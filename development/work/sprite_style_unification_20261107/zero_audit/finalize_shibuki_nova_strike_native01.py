"""기존 원코드 실행 결과를 읽어 감시 훅 진단과 통과 결과를 별도 결속한다."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit';O=D/'shibuki_nova_strike2_renderer_native02'
sha=lambda b:hashlib.sha256(b).hexdigest()
tracked={}
def read(p):
 b=p.read_bytes();tracked[p.relative_to(R).as_posix()]=sha(b);return b
def js(p):return json.loads(read(p))
a=js(D/'shibuki_nova_strike2_renderer_native01/report.json');b=js(O/'report.json');diag=js(D/'shibuki_nova_strike2_renderer_single_observer01/diagnostic.json')
assert a['passed'] and b['passed'] and a['cases']==b['cases']
assert a['executed_address_bytes_sha256']==b['executed_address_bytes_sha256']
assert b['renderer_memory_observer']=='none' and len(b['cases'])==136
assert not diag['passed'] and 'total7' in diag['error']
directory=js(D/'shibuki_nova_strike2_directory_native01/report.json');assert directory['passed']
for p in [D/'verify_shibuki_nova_strike_renderer01.py',D/'verify_pl00_directory_native.py',Path(__file__),O/'executed_addresses.json',D/'shibuki_nova_strike2_renderer_native01/executed_addresses.json',H/'prepared_nova_strike_base01/PL00_U.ARC',H/'prepared_nova_base01/PL00_U.ARC',H/'prepared_nova_strike_base01/INPUT_LOCK.json',H/'prepared_nova_strike_base01/PREPARED_LOCK.json',D/'shibuki_nova_part_count_read01/read_data.json',D/'shibuki_nova_part_count_read01/conclusions.json',W/'nana_audit/sprite_part_capacity_read01/report.json']:
 read(p)
summary={'passed':True,'scope':'시부키 기본/포스 노바217/220의 독립 원 RAM 로더·원 애니 초기화·decode/upload·실제 본체/아머 renderer 격리 실행. 새 ARC 제작 및 게임 실기 아님.','candidate_sha256':b['candidate_sha256'],'full_directory_reference_count':508,'renderer_cases_per_run':136,'matching_unobserved_runs':2,'all_cases_and_packet_hashes_equal':True,'renderer_memory_write_observer_used_for_pass':False,'mask_facing_arm_cases':128,'near_capacity_cases':8,'ref220_mask15':{'base_parts':31,'armor_parts':7,'total_packets':38,'primitive_bytes':1520,'drawmode_bytes':304,'body_counter_increment':31,'boundary_start_counter':969,'boundary_start_slot':986,'boundary_end_counter':1000,'boundary_end_slot':1024},'checks':['실제 RAM loader에서 scratchpad에 entry2/3 포인터를 저장한 뒤 실제 애니 wrapper가 directory를 읽어 객체+38/+3c를 설정했다. Python으로 graphics/composition bank 포인터를 주입하지 않았다.','원래 decoder/upload의 실제 출력·4096B 버퍼 guard 및 native record directory lookup을 확인했다.','실제 본체·아머 루프가 모든 파트를 순서대로 읽고 40B/8B packet cursor를 증가시켰으며 원래 OT commit과 스택 복원이 이루어졌다.','할당구간 밖의 두 전체 pool 및 전후64B를 실행 전후 비교했다. 메모리 쓰기 hook을 사용한 개별 write 감시 통과로 표현하지 않는다.','base/partial renderer 실행 기계어는 US 원본과 동일하고 유일한 실행 차이는 기존 수용된 PL00 부분아머 wrapper이다.'],'observer_diagnostic':{'candidate_fault_confirmed':False,'single_memory_write_hook_changes_execution':True,'reproduces_with_7_parts':True,'observed_symptom':'0x80024844 addiu 반복 및 packet pool 범위 밖 변화. 같은 code-hook과 fixture에서 메모리 hook 제거 시 136조건을 두 번 통과.','internal_unicorn_cause':'미확인. PC 읽기·RA 변경·delay-slot 가설을 확정 원인으로 채택하지 않음.','diagnostic_path':'work/sprite_style_unification_20261107/zero_audit/shibuki_nova_strike2_renderer_single_observer01/diagnostic.json'},'limits':['전체 게임 dispatcher/CD 로딩·다른 동시 객체·혼잡 장면·GPU 래스터화·60Hz 실기를 실행하지 않았다.','counter 시작+31<=1000 및 두 pool 시작+38<=1024의 fixture 조건을 확인했으며 후속 전체 장면 사용자까지 여유를 보장하지 않는다.','1000 초과 경로는 정상 cursor/OT commit을 생략하므로 안전한 자동 clip이라고 주장하지 않는다.'],'source_and_evidence':tracked.copy(),'resource_modified':False}
for name,data in [('conclusions.json',summary)]:
 p=O/name;assert not p.exists();p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');read(p)
p=O/'READER_LOCK.json';assert not p.exists();p.write_text(json.dumps({'scope':'원코드 독립 실행 증거 잠금; 후보 자체 동결 아님','files':tracked},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'conclusions':sha((O/'conclusions.json').read_bytes()),'lock':sha(p.read_bytes()),'report':sha((O/'report.json').read_bytes()),'diagnostic':sha((D/'shibuki_nova_strike2_renderer_single_observer01/diagnostic.json').read_bytes())}))
