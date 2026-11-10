from pathlib import Path
import json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'shibuki_selection8_relations01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'));assert sha(O/'report.json')=='10700e74dc99b842a4745f933a285ef5aa9490d2a13194e856351571dff12011'
seen=[]
for q in r['readback_sheets']:
 p=ROOT/q['path'];assert sha(p)==q['sha256'];seen.append({**q,'actually_viewed':True,'finding':'현재UI와 변환한기존game은 실제로같고 새game의머릿결·의상차이가 별도열에보인다. 이는 기대사본 비교이며 새UI후보실제재추출이 아니다.'})
v={'technical_report_sha256':sha(O/'report.json'),'sheets':seen,'shared_tile_detail':{'tile':4,'nonzero_texels':0,'whole256_indices_sha256':'5341e6b2646979a70e57653007a1f310169421ec9bdd9f1a5648f75ade005af1','other_consumers':[0,23],'preserve_empty':True},'conclusions':['선택1..8는85..92에대응,전부X반전없음. Y차는−1/0/0/0/0/−1/−2/0이며 실제ea216색인·RGBA에서확인했다.','대상50타일 중49전용. 공유tile4는0/23도소비하는완전빈타일이므로그대로보호한다. 대상조립레코드를소비하는다른bank2프레임은없다.','기존19/20 mirror+1및18/23Y−1·21그대로를fdba와직접대조했다. 1..8동기화에일괄반전/일괄Y보정불가.','새사본패킹·용량·GPU검사·실기수행은아직이보고범위밖이다.'],'resources_modified':False,'runtime_verified':False,'new_candidate_created':False}
(O/'conclusions.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report':sha(O/'report.json'),'conclusions':sha(O/'conclusions.json')}))
