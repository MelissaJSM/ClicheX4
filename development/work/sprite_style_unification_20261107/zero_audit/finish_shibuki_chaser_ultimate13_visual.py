from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;O=D/'shibuki_chaser_ultimate13_independent01'
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
p=O/'report.json';r=json.loads(p.read_text('utf8'));assert sha(p.read_bytes())=='6d7feb53df135880090056b2e00b593a7e9c70a7252935b787c95e76011ec100'
for s in r['readback_sheets']:assert sha((ROOT/s['path']).read_bytes())==s['sha256']
v={'scope':'최종2b8faa 실제독립재추출12판 정적미술열람','candidate_sha256':r['candidate_sha256'],'report':rel(p),'report_sha256':sha(p.read_bytes()),'actually_viewed':r['readback_sheets'],'observations':['새162/166은 금색안경·머릿결·소매와 접힌다리/샌들 구분이 선명해졌다. 전후폼 머리·사지 일관성과 맨팔의 어깨→팔꿈치→손목 연결에서 추가확정절단을 찾지 못했다.','새170 발목/샌들35셀−1y 정합 뒤 정강이와 발끝은 이어져 읽힌다. 관절9셀가림은 재구성으로확인했으며 숫자만으로미술수용을대신하지않았다.','174 양폼의 긴다리→샌들 연결과 손/몸 접점을 실제판에서 확인했다. 귀정점/머리폭이 새기본형보다각1px추가라는 제작자한계를 유지하며 무조건bbox축소하지않는다.','부분0/1/2/4/8/15판은재킷overlay5만선택되는현재Ultimate구조와일치한다. 완성후폼에새옛소매띠나떨어진점은확정하지못했다.','4개별칭판에서 머리·사지 모양은그대로이고원Y흔들림만이어진다. 원시간표의실시간체이서상하운동과차량손잡이/발판접점은이판만으로판정하지않는다.'],'producer_functions_called':False,'new_MIPS_execution':False,'runtime_verified':False,'final_user_art_acceptance':False,'overall_complete':False}
p=O/'visual.json';assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
inputs=dict(r['inputs'])
for q in [D/'verify_shibuki_chaser_ultimate13_independent.py',D/'verify_shibuki_ultimate_hurt13_independent.py',Path(__file__),O/'report.json',p]+[ROOT/s['path']for s in r['readback_sheets']]:inputs[rel(q)]=sha(q.read_bytes())
for name,h in inputs.items():assert sha((ROOT/name).read_bytes())==h,name
p=O/'READER_LOCK.json';assert not p.exists();p.write_text(json.dumps({'count':len(inputs),'inputs':inputs,'candidate_sha256':r['candidate_sha256'],'producer_calls':False,'source_writes':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'visual_sha256':sha((O/'visual.json').read_bytes()),'lock_sha256':sha(p.read_bytes()),'inputs':len(inputs)}))
