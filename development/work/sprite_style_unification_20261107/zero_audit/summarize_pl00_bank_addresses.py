"""Bind read-only address evidence and its limits; no candidate creation."""
from pathlib import Path
import json,hashlib,html
ROOT=Path(__file__).resolve().parents[3]
D=Path(__file__).parent
OUT=D/'pl00_bank_relocation_audit01'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inv=read(OUT/'native_inventory.json');direct=read(OUT/'direct_gfx_pointer_reads.json')
evidence={}
for p in [OUT/'native_inventory.json',OUT/'direct_gfx_pointer_reads.json',D/'audit_pl00_bank_addresses.py',ROOT/'src/psx_player.py',ROOT/'src/psx_bank_repack.py',ROOT/'scripts/overhaul_nana_buffer_watch.py',ROOT/'scripts/verify_consistency_native.py',ROOT/'work/research/decomp/src/main/3D88.c',ROOT/'work/research/decomp/src/main/55C4.c',ROOT/'work/research/decomp/src/main/player_common.c',ROOT/'work/research/decomp/src/main/items/item_26_light_capsule.c']:
    evidence[p.relative_to(ROOT).as_posix()]=sha(p)
findings=[
 {'topic':'로더','status':'실제 원US/BR14 코드 확인','detail':'0x80014040..90은 entry type 상위16비트가0인 자원을 D_800F15BC[type]가 가리키는 슬롯에 바인딩하고 자원 길이만큼 다음 상주 주소를 전진한다. 실제 table[2]=0x1F800014. entry2 내부 은행 길이는 로더가 해석하지 않는다.'},
 {'topic':'은행 주소','status':'실제 원US/BR14 코드 확인','detail':'player_spawn 0x800353AC..C4, player_set_animation_frame 0x8003518C..A4, Zero setter 및 분신 init은 entry2 base + directory[bank]를 object+0x38에 저장한다. 확인된 30개 직접 scratch+14 읽기 지점의 문맥은 원US와 현재 동일하다. 무기2/3/5/6/7/8/9, capsule10..13도 같은 상대주소 방식이다.'},
 {'topic':'프레임 압축 주소','status':'실제 원US/BR14 코드 확인','detail':'0x80015F00..58은 object+0x38=bankBase, frame=object+0x47로 header[frame]를 읽어 src=bankBase+(header & 0xFFFFF), tileCount=header>>20을 계산한다. 0x80016FF4 디코더는 이 src의 종료 토큰까지 읽으며 은행 끝/고정 압축슬롯 크기를 전달받지 않는다.'},
 {'topic':'캐시','status':'실제 원US/BR14 코드 확인','detail':'은행 시작 포인터를 객체가 캐시하고 X player_set_animation은 composition만 다시 고른다. decompress_player_gfx는 frame+0x47==previous+0x48이면 포인터 변화 여부를 보지 않고 반환한다. 따라서 실행 중 상주 데이터만 옮기는 hot relocation에는 사용할 수 없다. 새 ARC의 정상 로드와 객체 초기화가 전제다.'},
 {'topic':'32타일과 효과','status':'실제 자원/코드 확인','detail':'본체 gfx0은 최대32타일이고 native 플레이어 버퍼0은4096B. 이것은 압축은행 크기 제한이 아니다. 현재 gfx6/7/9/10..13은 원래48타일을 포함하므로 모든 은행에32타일 상한을 새로 적용하지 않는다. 재배치만 한다면 각 ref의 기존 tileCount/raw 전체와 기존 객체 버퍼/업로드 조건을 보존한다.'},
 {'topic':'별도 정적 텍스처','status':'실제 로더 분기 확인','detail':'entry0x1xxxx 정적 텍스처는 high16 handler1의 VRAM 업로드 경로(0x800142BC)이며 entry2 directory가 아니다. entry2만 재배치하는 작업으로 해당 entry의 VRAM 위치나 데이터까지 재배치할 이유가 없다. entry3 조립 및 정적 entry 전체는 byte exact로 보호한다.'},
 {'topic':'주소 재배치 가능성','status':'정적 근거에 따른 조건부 판단','detail':'확인된 경로에서는 은행의 기존 물리 시작 offset을 고정 상수로 쓰는 제약을 찾지 못했다. entry2 총186228B를 유지하고 directory와 bank-relative header만 올바르게 갱신하면 같은 raw/조립을 찾아가는 구조다. 이는 새 재배치 후보 통과나 실기 성공의 선언이 아니다.'},
]
constraints=[
 'entry2 총길이186228B, ARC entry 순서/크기/외부 LBA 및 다른 entry byte exact. directory14개/첫offset56은 유지하고 기존 bank ID를 바꾸지 않는다.',
 '은행 시작4byte 정렬/정렬된 directory, alias [1,2] 및 [4,5] 유지. bank0~13의508 ref 전체 decoded raw·tileCount·프레임 수를 보존한다. 완전히 같은 raw/count의 stream을 합치는 것은 별도 증명 가능한 선택이며 owner 집합 변화는 명시한다. alias 중복을 실제 공간으로 두 번 계산하지 않는다.',
 '각 bank의 frame header는32bit: 상위12bit tileCount, 하위20bit unsigned bank-relative offset. 2byte stream 정렬, 표 영역 이후 시작, 종료 토큰 및 역참조 범위 검증. 전체 entry는1MiB 미만이므로 현재 범위에서20bit 한계에 접근하지 않는다.',
 'entry3 모든 조립/파트/CLUT/반전/원점, palette·EXE animation/timing·원효과는 byte exact. hidden texel을0으로 지우는 정리와 은행 주소 이동은 다른 작업이며 이번 읽기 조사에서는 둘 다 수행하지 않았다.',
 'raw exact이면 기존 partial upload의 미기록 VRAM carry도 같은 전이에서 같지만, tileCount/업로드 형태를 바꾸면 이 논리가 성립하지 않는다. 주소 이동을 이유로 원32tile·48tile 크기나 소비 타일을 바꾸지 않는다.',
 '캐시된 객체 pointer는 이전 bank 위치를 가리킬 수 있으므로 저장상태/실행 중 메모리만 덮기 금지. 정상 fresh load 이후 player/clone/weapon/capsule 초기화에서 새 directory를 읽는 검증을 분리한다.',
 '도구 src.psx_bank_repack.py의 fixed-bank-end 요구는 현 도구 설계다. native 주소 계약과 구별하며 허용 여부는 root의 별도 승인/구현 판단을 따른다.'
]
remaining=[
 '읽기 전용 조사이며 재배치 ARC나 EXE 패치, 새 MIPS 실행, 에뮬레이터 실행을 만들지 않았다.',
 '전체 EXE의 LUI 0x1F80 구축596곳에서 짧은 직선 상수전파로30개 SP+14 읽기를 찾았다. 임의 간접 포인터/자기수정/외부 스크립트의 부재까지 증명하는 whole-program 분석은 아니다. bank4는bank5의 현재동일offset 별칭이며 별도직접독자는 이검사에서 발견되지 않았다.',
 '본체의0/5..8 조립 외에 player clone도 bank0을 사용한다. gfx1..13를 옮길 경우 무기/캡슐 객체 경로도 보존 대상이다. raw exact가 아니면 이 주소 조사로 비가시 texel 삭제의 안전성을 대신 입증할 수 없다.',
 '기존 cpu_checks는 object+0x38을 Python이 직접 지정하므로 directory 주소 선택을 시험하지 않는다. verify_consistency_native는 raw/조립 변경만으로 대상 선별하면 주소만 바뀐 ref를 건너뛸 수 있다. 향후 승인된 후보에는 실제 directory 초기화 경로와 이동은행508ref 전체 디코드/업로드 비교를 명시해야 한다.',
 '3202B 부족과 다른은행 후미1086B 수치는 UI 담당의 공간 조사 통보다. 본 보고는 공간 확보 성공이나 충분함을 독립 검증하지 않았다.'
]
report={'passed':True,'passed_meaning':'읽기 증거 수집·원US/현재 명령어 및 자원 파싱 일치 검사. 재배치 후보 승인/동결/실기 통과를 뜻하지 않음.','analysis_only':True,'game_or_art_modified':False,'candidate_generated':False,'exe_modified':False,'live_process_opened':False,'native_cpu_executed':False,'source_discs':inv['disc_hashes'],'entry2':{'length':inv['entry2_length'],'sha256':inv['entry2_sha256'],'banks':14,'logical_refs':sum(len(b['frames']) for b in inv['banks']),'aliases':[[1,2],[4,5]]},'findings':findings,'constraints':constraints,'limitations_and_next_checks':remaining,'direct_reads':[{'address':x['load_address'],'banks':x['graphics_bank_ids'],'original_us_identical':x['original_us_identical']} for x in direct],'evidence':evidence}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
body=['<!doctype html><meta charset="utf-8"><title>PL00 은행 주소 읽기 조사</title><style>body{font:16px system-ui;background:#151d26;color:#e9edf2;margin:28px;max-width:1100px}a{color:#9ccfff}li{margin:12px 0}table{border-collapse:collapse}td,th{border:1px solid #506070;padding:10px;text-align:left;vertical-align:top}</style><h1>PL00 entry2 은행 주소 읽기 조사</h1><p>원US와 BR14의 실제 로더·플레이어·무기·캡슐 명령어를 확인했습니다. 확인된 경로는 디렉터리/은행 상대주소이며, 재배치 후보는 만들지 않았습니다.</p><p><a href="report.json">구조화 보고서</a> · <a href="native_inventory.json">현재 은행/decoded raw 목록</a> · <a href="direct_gfx_pointer_reads.json">30개 실제 코드 문맥</a></p><table><tr><th>항목</th><th>근거/판단</th></tr>']
for f in findings:body.append('<tr><td>'+html.escape(f['topic'])+'<br><small>'+html.escape(f['status'])+'</small></td><td>'+html.escape(f['detail'])+'</td></tr>')
body.append('</table><h2>반드시 유지할 제약</h2><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in constraints)+'</ul><h2>한계 / 다음 검증</h2><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in remaining)+'</ul>')
(OUT/'REPORT.html').write_text('\n'.join(body),encoding='utf8')
print(json.dumps({'passed':True,'report_sha256':sha(OUT/'report.json'),'logical_refs':report['entry2']['logical_refs'],'direct_reads':len(direct)},ensure_ascii=False))
