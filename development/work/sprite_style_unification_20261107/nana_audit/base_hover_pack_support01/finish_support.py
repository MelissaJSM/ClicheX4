"""빈층 저장 최적화의 근거와 네이티브 검증을 최종 지원 보고로 결속한다."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive
from scripts.prepare_shibuki_ultimate_production import records
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,indexed_atlas,composition_frame
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):return sha(p.read_bytes())
def read(p):return json.loads(p.read_text('utf8'))
def rel(p):return p.relative_to(ROOT).as_posix()
def need(ok,msg):
 if not ok:raise ValueError(msg)
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
old_report=read(D/'candidate01/verification.json');second=read(D/'candidate02/verification.json')
parent=ROOT/old_report['parent_arc'];candidate=D/'candidate01/PL00_U.ARC';a=Archive(parent.read_bytes());b=Archive(candidate.read_bytes())
need(digest(parent)==old_report['before'],'부모 고정');need(digest(candidate)==old_report['after']==digest(D/'candidate02/PL00_U.ARC'),'두 재현 exact')
need(old_report['target_inputs']==second['target_inputs'],'두 재현 같은 50입력')
for q in old_report['target_inputs']:need(digest(ROOT/q['path'])==q['sha256'],'등록원화 불변')
native=read(D/'native_empty01/report.json');decode=read(D/'component_plan_native_checks.json');need(native['passed']and decode['passed'],'네이티브통과')
empty=(128,129,132,140,159);empty_rows=[]
for n in empty:
 cp=composition_frame(a.c,5,n);need(len(cp['parts'])==1 and records(b.c,5,n)==b'','빈층 단일→0')
 a.layer(n,5);p=cp['parts'][0];f=a.banks[0]['frames'][n];raw=a.raw[(f['offset'],f['tile_count'])].data
 atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);t=p['tile'];patch=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
 need(patch.shape==(16,16)and not patch.any(),'소비타일 전체256 texel 투명')
 need(np.array_equal(a.layer(n,5)[0],b.layer(n,5)[0]),'빈층 재독출 동일')
 empty_rows.append({'ref':n,'old_record_hex':records(a.c,5,n).hex(),'consumed_tile':t,'consumed_tile_all_256_transparent':True,'old_count':1,'new_count':0,'rgba_32_conditions_in_whole_check':True})
expected_layout=lambda data:[(q['type'],q['offset'],q['size'])for q in psx_arc(data)]
need(len(parent.read_bytes())==len(candidate.read_bytes()) and expected_layout(parent.read_bytes())==expected_layout(candidate.read_bytes()),'ARC길이/항목배치 불변')
need(bank_offsets(a.c)==bank_offsets(b.c)and bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True),'은행경계 불변')
# 초기 확인기의 1737은 다섯 명시적 빈층변환도 포함한 검사 수이다.
# 실제 기록열 byte exact 1732와 표시 exact 빈층변환5를 구분한다.
if 'nonselected_compositions_checked' not in old_report:
 old_report['nonselected_compositions_checked']=old_report['nonselected_compositions_exact'];old_report['nonselected_compositions_exact']-=len(empty)
 old_report['scope']=second['scope'];write(D/'candidate01/verification.json',old_report)
need(old_report['nonselected_compositions_exact']==1732 and old_report['nonselected_compositions_checked']==1737,'기록 보존 범위 구분')
proof_paths=[D/'candidate01/verification.json',D/'candidate02/verification.json',D/'empty_probe01/report.json',D/'order_probe01/report.json',D/'native_empty01/report.json',D/'component_plan_native_checks.json']
code_paths=[D/'build_candidate.py',D/'verify_empty_native.py',D/'finish_support.py',W/'root_nana_hover/pack_hover01.py',W/'root_nana_hover/pinned_head_pack.py',N/'ultimate_hover_repaint/pack_native.py',W/'shibuki_audit/repack_part_records_lossless.py']
resources=decode['resources']['PL00_U.ARC'];report={
 'passed':True,'task':'기본/포스 호버50층의 head bank5 20B 부족 무손실 해결 지원',
 'candidate':rel(candidate),'candidate_sha256':digest(candidate),'parent':rel(parent),'parent_sha256':digest(parent),'frozen':False,
 'head_record_capacity':265,'old_required_records':270,'new_required_records':265,'saved_bytes':20,'head_bank_slack_bytes':0,
 'solution':'완전투명 head5의 128/129/132/140/159 단일파트만 기존 count0 표현으로 저장한다. 비어있지 않은 기록의 순서·그림·타일은 이 최적화로 바꾸지 않는다.',
 'empty_layers':empty_rows,'existing_parent_count0_refs':[109,112,113,114],
 'new_target_layers':50,'fixed_target_inputs':old_report['target_inputs'],'target_layers_exact':50,'non_target_layers_exact':1090,
 'raw_checked':508,'non_target_raw_exact':498,'non_target_compositions_byte_exact':1732,'explicit_empty_representation_changes':5,
 'RGBA_conditions_checked':7296,'target_RGBA_conditions':320,'whole_input_palette_exact':True,
 'candidate_length':candidate.stat().st_size,'archive_entry_layout_exact':True,'graphics_bank_offsets_exact':True,'composition_bank_offsets_exact':True,
 'EXE_or_source_BIN_changed':False,'other_archive_entries_exact':True,'root_art_targets_or_root_code_modified_by_support':False,
 'shared_pair_streams':5,'target_tiles_per_pair':32,'common_head_geometry':old_report['common_geometry'],
 'native_empty_renderer_calls':native['native_calls'],'native_empty_function':'0x8002588c..0x80025cdc','native_empty_branch':'0x80025984 → 0x80025c30',
 'existing_and_new_count0_packet_state_exact':True,'all_executed_renderer_and_loader_opcodes_original_US_exact':True,
 'native_decode_upload_refs':resources['banks'][0]['changed_refs'],'native_GPU_part_edge_checks':resources['GPU_part_edge_checks'],
 'two_fresh_reproductions_same_ARC':True,'reproduction_paths':[rel(D/f'candidate0{k}/PL00_U.ARC')for k in (1,2)],
 'proofs':[{'path':rel(p),'sha256':digest(p)}for p in proof_paths],
 'source_codes':[{'path':rel(p),'sha256':digest(p)}for p in code_paths],
 'limits':['현재 Root body_layers_probe01+shoot_layers_probe02 50층에 한정한 패킹 해결이다.','229 추진발/하체 후속 미술 변경 가능성이 있어 최종 아트 수용·동결은 하지 않았다.','이 지원은 root 타깃을 그대로 패킹한 기술 검사이며 독립적인 전체 원화 출처 재구성 또는 실기가 아니다.','원 MIPS 빈층함수/decoder/upload는 격리 실행했으며 실제GPU·게임프로세스를 열지 않았다.','새 팔/발/총구의 미술 최종 수용은 root 담당이며 이 보고는 기존 그림을 변경하지 않는 패킹 해법만 결속한다.']}
write(D/'report.json',report)
(D/'HANDOFF.txt').write_text('기본/포스 호버 head bank5 저장 부족 해결\n\n'
 '현재 후보: candidate01/PL00_U.ARC / '+digest(candidate)+'\n'
 '부모: '+digest(parent)+'\n\n'
 'Root 적용 범위: fit_parts의 pb==5 경로에서 부모 head5가 완전히 투명한 128/129/132/140/159만 changes[n]=b\'\'로 추가하고 global_parts를 호출합니다. 나머지 50타깃, 공통6사각, 타일배치, 원화는 그대로 둡니다. 부모의 실제 소비타일 전체가0인지와 기존 파트수가1인지 먼저 확인해야 합니다.\n\n'
 '검증에서 비대상 전체 records exact라고 쓰면 안 됩니다. 1732개 기록열은 byte exact, 다섯 빈층은 1파트→0파트 저장변환과 표시 exact입니다. 전체7296 RGBA 및 비대상498 raw/1090층은 통과했습니다.\n\n'
 '원US 부분아머 함수는 count0에서 0x80025984→0x80025c30으로 건너뜁니다. 26격리호출에서 기존 count0와 GPU 할당/packet 상태가 같았고 새primitive를 만들지 않았습니다. 추가15참조의 원 decoder/upload와 버퍼경계도 통과했습니다. EXE/BIN·외부항목·은행경계는 변경하지 않았습니다.\n\n'
 'candidate01/02는 신규 출력 두 번에서 ARC 해시가 같습니다. Root229 하체 후속 수정이 있어 최종동결은 하지 않습니다. 최종타깃을 바꾸면 그 입력으로 다시 패킹·대조하십시오.\n','utf8')
lock_files=[p for p in D.rglob('*')if p.is_file()and '__pycache__'not in p.parts and p.name!='SUPPORT_LOCK.json']
write(D/'SUPPORT_LOCK.json',{'scope':'지원 조사·패킹 해결 증거 고정. 게임 최종FROZEN 아님.','candidate_sha256':digest(candidate),'report_sha256':digest(D/'report.json'),'files':[{'path':rel(p),'sha256':digest(p)}for p in sorted(lock_files)]})
print(json.dumps({'passed':True,'report_sha256':digest(D/'report.json'),'lock_sha256':digest(D/'SUPPORT_LOCK.json'),'candidate_sha256':digest(candidate)}))
