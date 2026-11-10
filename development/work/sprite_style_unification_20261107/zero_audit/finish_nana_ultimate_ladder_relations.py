from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
O=D/'nana_ultimate_ladder_relations01';r=json.loads((O/'report.json').read_text('utf8'));a=Archive((ROOT/r['source']).read_bytes())
modulep=ROOT/'out/ver_rin_nana/nana_ultimate_low_hp_shape_20261104T102858790508Z/ultimate_gun_size/pistol_module.png'
module=np.array(Image.open(modulep));guns=[]
for n,(x,y)in((150,(-24,-11)),(155,(-21,-15))):
 z=a.layer(n)[0];assert np.array_equal(z[y+160:y+167,x+160:x+168],module)
 guns.append({'ref':n,'world_box':[x,y,x+8,y+7],'actual_width_height':[8,7],'opaque':int((module>0).sum()),'historical_module_exact':True,'module_path':modulep.relative_to(ROOT).as_posix(),'module_sha256':sha(modulep)})
v={'report_sha256':sha(O/'report.json'),'scope':'Ultimate 사다리 관계 결론·실제 열람','candidate_or_runtime_audit':False,'source_sha256':r['source_sha256'],'canonical_guns':guns,
 'conclusions':['143..155·183의 원시 스트림은 9그룹이다:143 /144·145 /146·147 /148·149·150 /151·152 /153 /154 /155 /183. 이들 스트림에 대상 밖 소유자는 없다.',
 '전폼 5층 exact 반전이라고 쓰면 안 된다. 재킷 before(mask15)는145=mirror144−1,147=mirror146,148=mirror149,152=mirror151을 모두 정확 만족하지만, 맨팔 after(layer0)는 각각159/244/183/150픽셀 다르다. overlay5 자체와 빈6/7/8은 반전 exact이다. 새 양폼 반전 공통화는 새 제작정책으로 명시해야 한다.',
 '150/155의 현재 before는149와 차이가 각각144/120픽셀로 팔·총 주변에 국한된다. after는197/210픽셀 차이이며155는머리 높이 y−26까지 차이가 있어149+팔만의 정확복원이라고 할 수 없다.154는948~1003픽셀이 달라155 몸체짝으로 복사할 근거가 없다.',
 '역사 prepare_nana_ultimate_ladder.py는150/155를 새149몸체에 사격팔로 제작했다고 명시한다. 원US155 별도 반동을 완전히 복원한 것이라는 의미는 아니다. 현재 두폼 차이와 새 정책을 분리해야 한다.',
 '현재총은 옛PL00 84픽셀 그림이 아니다. 당시 Ultimate의 8×7 정본 모듈이 실제150/155 각각에 exact이며, 원총구는(-24,-9),(-21,-13)이다. 두 의상/두arm 팔레트의 해당 총구 첫8열 RGBA가 동일하다.',
 '6/7/8 빈층의 record주소는97,86/87/132,105/119/160/161/220,218,219,85/95/96/115..118/213/214 등 비대상과 공유한다. 기존 레코드를 덮기보다 새 타깃 레코드를 별도 배치하고 비대상 전체조립을 보호해야 한다.',
 '5개 실제 재추출판에서 별도 광선·번개 같은 효과는 보이지 않는다. 이것은 원 게임의 별도 무기 객체 효과가 없다는 뜻이 아니다. 원92/93은150→155→150이고93초기 유지시간은호출자가수정한다는 기존원코드보고를 연결한다.'],
 'actually_viewed':[{'path':q['path'],'sha256':q['sha256']}for q in r['sheets']],
 'first_three_new_static_review':{'files':[],'observations':['a_layers_probe_v1 comparison/partial 두 판을 실제 열람했다.144의 새 주먹 끝·검정 커프·손목은 두 의상에서 한 흐름으로 연결되며 이 판에서 새 고립 손이나 뚜렷한 관절 단절을 찾지 못했다.','143/146과 함께 새 머릿결·재킷/맨팔 명암 방향도 이어진다. 실제 사다리 접점/전순서/최종자원 검증은 이 정적 의견에 포함하지 않는다.']},
 'producer_functions_called':False,'runtime_verified':False,'MIPS_executed':False,'user_accepted':False}
for name in('comparison.png','partial.png'):
 p=D.parent/'nana_audit/ultimate_ladder_repaint/a_layers_probe_v1'/name;v['first_three_new_static_review']['files'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
for p in('scripts/prepare_nana_ultimate_ladder.py','scripts/prepare_nana_ultimate_ladder_reference.py','scripts/prepare_nana_fourth_ladder_art.py'):
 v.setdefault('historical_code_read',[]).append({'path':p,'sha256':sha(ROOT/p)})
(O/'conclusions.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'conclusions_sha256':sha(O/'conclusions.json'),'guns':guns}))
