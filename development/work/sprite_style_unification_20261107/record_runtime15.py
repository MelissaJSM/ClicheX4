"""Bind actual review scope, preserving incomplete asynchronous observations."""
from pathlib import Path
import json,hashlib
from PIL import Image
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bind=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(p,d):
    assert not p.exists();p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
records=[];reviewed=[]
for name in ('rin_arrival15','rin_burst15','rin_dash_follow15'):
    play=R/(name+'_play');v=read(play/'evidence.json');close=ROOT/v['session']/'close.local.json'
    assert read(close)['exited'] and v['error'] is None and v['keys_released']
    assert not v['memory_written'] and not v['save_keys_sent']
    pages=read(R/(name+'_review')/'manifest.json')['pages']
    if name=='rin_arrival15':pages+=read(R/(name+'_detail')/'manifest.json')['pages']
    row={'name':name,'record':bind(play/'evidence.json'),'captures':v['frames'],'encoded_webp_frames':Image.open(play/'play.webp').n_frames,
         'root_viewed_pages':[{**bind(ROOT/p['path']),'root_actually_viewed':True} for p in pages]}
    reviewed.extend(row['root_viewed_pages'])
    if name!='rin_arrival15':
        obs=read(R/(name+'_watch')/'evidence.json');seen={tuple(x) for x in obs['verified_bank_frames']}
        targets={(1,f) for f in [177,178,179,180,181,186,187,188,189]} if name=='rin_burst15' else {(0,f) for f in [155,156,158,160,162,164,166,168,170,172]}
        assert targets<=seen
        row.update(observer=bind(R/(name+'_watch')/'evidence.json'),verified_bank_frames=obs['verified_bank_frames'],new_targets_verified=sorted(targets),unverified_events=[obs['events'][i] for i in obs['unverified_events']])
    else:row['limitation']='창 녹화의 실제 등장/대기 연결만 검토.247..253 각각의 RAM/GPU 업로드는 이 녹화에서 관측하지 않았다.'
    records.append(row)
summary={'disc_sha256':v['bin_sha256'],'session':v['session'],'fresh_boot':True,'save_route':'시험카드 사본1 DATA1 정상린/8보스 후 아이리스 대화→우주항',
 'runs':records,'close':bind(close),'protection':bind(W/'protection_checkpoint23.json'),
 'findings':['등장319창과10판, 낙봉파303창과20판, 질풍아/용염인351창과12판을 직접 검토했다.','낙봉파 새9참조와 질풍아 후속 새10참조 각각에 실제 RAM/GPU 일치 표본이 있다. 낙봉파 미검증사건은0이다.','흰 부츠/파란 발등과 손·구체 연결, 머리/치마/다리 및 대기로 복귀하는 연결에 추가 확정 절단을 찾지 못했다.'],
 'limits':['정상색 실기이며 레드·차량·사다리·승리·회복 전체 실기는 아니다.','질풍아155/164 안정표본 부족,168 GPU불일치, 기존 용염인 b1_148 GPU불일치 사건은 원인 미확정으로 보존한다. 각 참조 다른 성공 표본과 구분한다.','약16fps 창 기록과 비동기 메모리 관측으로 모든60Hz 표시를 검증한 것은 아니다.'],
 'all_character_runtime_complete':False,'final_user_accepted':False}
dest=R/'rin_checkpoint15_summary.json';write(dest,summary)
write(W/'root_review_checkpoint56.json',{'actual_runtime_review_images':reviewed,'summary':bind(dest),'findings':summary['findings'],'limits':summary['limits'],'final_user_accepted':False})
print(json.dumps({'new_targets':19,'reviewed_pages':len(reviewed),'captures':[r['captures'] for r in records],'summary_sha256':sha(dest)}))
