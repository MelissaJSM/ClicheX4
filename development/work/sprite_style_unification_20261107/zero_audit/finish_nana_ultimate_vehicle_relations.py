from pathlib import Path
import json,hashlib,html
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_ultimate_vehicle_relations01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'))
assert all(q['historical_unshifted_fallback_reconstructed_exact']and not q['separate_generated_body']for q in r['normalized_alias_reconstruction'])
assert all(q['current_before_equals_historical']and q['current_after_equals_normalized']for q in r['historical_provenance'])
for q in r['relations']:
 if q['archive'].startswith('original_US'):assert all(x['changed']==0 for x in q['forms'].values())
seen=[]
for q in r['boards']:
 p=ROOT/q['path'];assert sha(p)==q['sha256'];seen.append({**q,'actually_viewed':True,'finding':'윗줄 before는 몸 전체가 원래Y위상대로 이동한다. 아래 after는 머리/몸통의 남은 색면과 접힌 팔·허벅지 무늬가 단순평행이동과 다름을 실제 비교했다. 별도의 의도된 새몸체9장이라는 근거는 아니다.'})
result={'report_sha256':sha(O/'report.json'),'current_sha256':r['current_sha256'],'conclusions':['원US PL00·PL02의 두폼과 현재before는162군Y+1/+3/−1,166군동일,170군Y+1/+2/−1이 실제표시exact이다. 174는독립한4번째키다.','현재after는각9별칭에서135~203셀차이가 있으나 별도생성원화가아니다. 역사normalization의마스터무이동복사+기존acquired차이셀/overlay밖원base복원+공통정리과정을9개모두독립재구성했다.','현재before13은과거vehicle_packed_v4의등록원화13과exact이고after13은normalized13과exact이다. 원US별도반동이나관절변형을새로발견한결과가아니다.','새4고유키양폼과원Y위상9를일관되게전개하는제작정책은원US실제관계에근거할수있다. 다만현재옛after픽셀exact복원과구분해기록하고손·발접점및부분소유를검사해야한다.'],'sheets':seen,'source_code_evidence':['scripts/prepare_nana_ultimate_vehicle.py:ORDER 및 artwork의alias translation','scripts/overhaul_sprites_costume.py:normalize의 aliases_added 및 shared_pose_coherence'],'scope':'기존원화·등록파생·현재자원을읽기비교한관계보고. 새원화제작/ARC수정/MIPS/실기없음.'}
(O/'conclusions.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
page=['<!doctype html><meta charset="utf-8"><title>나나 Ultimate 차량 별칭 관계</title><style>body{font:16px sans-serif;background:#182333;color:#eee;margin:24px}img{max-width:100%}a{color:#9cddff}</style><h1>나나 Ultimate 차량 별칭 관계</h1><p><a href="report.json">원자료 대조</a> · <a href="conclusions.json">결론과 실제열람3판</a></p>']
for q in result['conclusions']:page.append('<p>'+html.escape(q)+'</p>')
for q in seen:page.append('<img src="'+Path(q['path']).name+'">')
(O/'INDEX.html').write_text('\n'.join(page),'utf8')
print(json.dumps({'report':sha(O/'report.json'),'conclusions':sha(O/'conclusions.json'),'boards':len(seen)}))
