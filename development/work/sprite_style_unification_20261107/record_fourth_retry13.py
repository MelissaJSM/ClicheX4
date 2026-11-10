"""Record limited follow-up proof and the inherited firing-style discrepancy."""
from pathlib import Path
import hashlib,json,subprocess
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def bind(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
obs=read(R/'shibuki_fourth_dash13_retry_watch/evidence.json')
vid=read(R/'shibuki_fourth_dash13_retry_play/evidence.json')
close=ROOT/vid['session']/'close.local.json'
assert read(close)['exited'] and vid['error'] is None
assert not vid['memory_written'] and not vid['save_keys_sent']
hits=[e for e in obs['events'] if e['frame']==68]
assert len(hits)==4 and all(e['verified'] for e in hits)
assert {e['facing_raw'] for e in hits}=={0,64}
previous=read(R/'shibuki_checkpoint13_summary.json')['runs'][1]
union=set(previous['new_targets_verified'])|{f for b,f in obs['verified_bank_frames'] if b==0}
targets=set(range(67,85))|{93,94}
assert targets<=union
files={}
for name,old in read(W/'protection_before.json')['files'].items():
    p=ROOT/name;now={'size':p.stat().st_size,'sha256':sha(p)}
    assert now==old,name
    files[name]=now
cards=read(W/'protection_checkpoint20.json')['test_cards']
for c in cards:assert sha(ROOT/c['source'])==sha(ROOT/c['copy'])==c['sha256']
processes=subprocess.check_output(['powershell','-NoProfile','-Command','(Get-Process epsxe* -ErrorAction SilentlyContinue | Measure-Object).Count'],text=True)
assert processes.strip()=='0'
write(W/'protection_checkpoint21.json',{'passed':True,'protected_files':len(files),'files':files,'test_cards':cards,'epsxe_process_count':0})
pages=[R/'shibuki_fourth_dash13_retry_review'/f'try_{i}_00.png' for i in range(1,5)]
summary={'session':vid['session'],'disc_sha256':vid['bin_sha256'],'actual_window_frames':vid['frames'],
    'encoded_webp_frames':191,'recording':bind(R/'shibuki_fourth_dash13_retry_play/evidence.json'),
    'observer':bind(R/'shibuki_fourth_dash13_retry_watch/evidence.json'),
    'verified_68_events':hits,'new20_verified_across_two_runs':sorted(targets),
    'unverified_events':[obs['events'][i] for i in obs['unverified_events']],
    'root_viewed_pages':[{**bind(p),'root_actually_viewed':True} for p in pages],
    'findings':['68 양방향 총4관측에서 안정 RAM/VRAM 일치. 이전 실기와 합쳐 새20참조 각각의 성공 표본을 확보했다.',
      '기존 포스2/4 직전사격에서 흰 가슴/옷깃 덩어리가 넓어 새대시보다 밝게 보인다. 정적 모음집에서도 같은 모습이며 잔여 상세/명암 통일 대상으로 분류한다.',
      '아머 플래그15가 유지됐으며 파츠 소실로 확정하지 않는다.'],
    'limits':['각 참조의 성공 표본과 모든 전환/모든60Hz 표시의 검증은 다르다.',
      '이번2/74/76의 일부 비동기 실패 표본 원인은 미확정이며 다른 성공 관측과 별도 보존.',
      '실제창191개 중 시작구간4비교판을 직접 보았으며 나머지4판은 검토 증거에 포함하지 않는다.'],
    'static_comparison':bind(R/'fourth_fire_transition13/comparison.png'),
    'close':bind(close),'protection':bind(W/'protection_checkpoint21.json'),
    'all_character_runtime_complete':False,'user_accepted':False}
write(R/'shibuki_fourth_retry13_summary.json',summary)
art=[W/'nana_audit/ultimate_run_repaint/arm48_registered_v1/comparison.png',
     W/'shibuki_audit/ultimate_dash_contacts05/before_new_comparison.png',
     W/'shibuki_audit/ultimate_dash_contacts05/after_new_comparison.png',
     R/'fourth_fire_transition13/comparison.png']
write(W/'root_review_checkpoint45.json',{'art_review_images':[{**bind(p),'root_actually_viewed':True} for p in art],
    'actual_runtime_review_images':summary['root_viewed_pages'],
    'findings':['나나 맨팔4/8 재작화는 이전 클립안보다 팔꿈치 아래선과 손목 두께가 좋아져 진행 방향 수용.',
                '시부키 Ultimate93/94 두 의상 머릿결·재킷/맨팔·구부린 다리 세부 방향 수용.',
                '시부키 포스 기존2/4의 밝은 가슴덩어리와 새68의 차이를 정적/실제 화면에서 확인. 후속 재작업에 포함.'],
    'limits':['원화 후보와 실제 BIN 적용 증거를 분리한다. 전 캐릭터 완료 아님.'],
    'runtime_summary':bind(R/'shibuki_fourth_retry13_summary.json'),'final_user_accepted':False})
print(json.dumps({'verified_new_targets':len(targets),'root_review_pages':len(pages)+len(art),'protected':len(files)}))
