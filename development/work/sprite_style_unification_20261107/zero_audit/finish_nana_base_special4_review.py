from pathlib import Path
import json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
R=D/'nana_special95_98_relations01';O=D/'nana_base_special4_independent01'
r=json.loads((R/'report.json').read_text('utf8'));v=json.loads((O/'report.json').read_text('utf8'))
relation={'technical_report_sha256':sha(R/'report.json'),'actually_viewed':r['boards']}
relation['findings']=['현재ac1e/원US 모두95→96과98→99는5층x+1·32RGBA조건exact.각쌍raw를공유하고다른쌍/외부참조raw공유없음.',
 '현재95/96/98/99의각조립레코드는다른참조와주소중복없음.같은raw공유쌍도x값이다른별도조립레코드를쓴다.',
 '원표95=138,139(event80),96,95,96,96종료.표96=138,139,96(event80),95,96종료.표97=96clone대기.',
 '원표104/105=97,81,99,99(event80),98,99,99종료.차이는99유지8대55calls이며마지막96calls는상태종료조건과구분.',
 '95/96은프로스트타워/소울바디·clone,98/99는더블사이클론원표와연결된다.같은숫자Zero함수는X행동근거로쓰지않는다.',
 '실제현재판에서138/139높이든팔및97준비몸체는95/98과별도포즈다.새4후보의비대상으로보존하며그상세통일완료를주장하지않는다.']
relation['runtime_verified']=False
(R/'conclusions.json').write_text(json.dumps(relation,ensure_ascii=False,indent=2)+'\n','utf8')
visual={'candidate_sha256':v['candidate_sha256'],'independent_report_sha256':sha(O/'report.json'),
 'actually_viewed':v['readback_sheets'],'observations':[
 '최종ARC에서독립추출한전체2판(구/신·기본/포스16표시)과부분2판(10표시)을직접열람했다.',
 '95/96 새사선권총·손목·소매가이어지고부츠/맨다리의구분과머릿결/의상명암이개선됐다.',
 '98/99 양팔자세에서새수평권총과손접점이붙어보이며소매/가슴/뒤머리경계에새확정절단을찾지못했다.',
 '부분head/body/arms/legs/body+legs에서베일이별도조각으로뜨거나소매가빠지는새확정결함을찾지못했다.95목아래한행의body소유는전체표시를바꾸지않는것으로독립재구성했다.'],
 'new_confirmed_visual_defects':[],'new_runtime_or_native_execution':False,'user_accepted':False,
 'limits':['원시간표10판은이감사에서새로열람하지않았다.원표바이트/연결은별도관계보고,루트최종원순서열람은별도근거다.',
 '전체캐릭터완료나연결138/139/97의신규미술완료를뜻하지않는다.']}
(O/'visual_review.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'relations':sha(R/'conclusions.json'),'visual':sha(O/'visual_review.json')}))
