from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;ROOT=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rp=O/'report.json';assert sha(rp)=='dc4d6c320acaedd14bbe4232198c2d5a7726aadcdbea29e89adaa19ebe10f02c'
r=json.loads(rp.read_text('utf8'));viewed=[]
for q in r['fresh_readback_sheets']:
    p=ROOT/q['path'];assert sha(p)==q['sha256'];viewed.append({'path':q['path'],'sha256':q['sha256']})
for n in(1,5):
    p=ROOT/f'work/sprite_style_unification_20261107/root_nana_ladder/packed_ladder07/readback_{n}.png'
    viewed.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
v={
 'scope':'독립 후보 재추출 전후5판(14참조×구/신 양폼56표시), 부분5판(10고유 본체×5부분50표시), 제작자 대기대조2판을 모두 view_image로 실제 열람했다.',
 'candidate_sha256':r['candidate_sha256'],'independent_report_sha256':sha(rp),'actually_viewed':viewed,
 'observations':[
   '143~149의 새 머릿결·베레모/포스 베일 명암, 소매 끝·치맛단·부츠가 이전의 큰 색면보다 분리된다. 대기와 나란히 본143/144/145에서도 장식과 신발 표현이 이어진다.',
   '네 반전쌍은 같은 새세부가 반대방향으로 이어진다. 올린 주먹에서 소매·어깨, 접힌 무릎과 발목까지 새로 확정되는 절단은 찾지 못했다.',
   '150/155의 권총·손목·사격팔이 새149 몸체로 이어진다. 팔과 얼굴/머리의 앞뒤 가림에서 별도 고립손이나 새머리 절단은 보이지 않았다. 원총구64조건 exact는 기술 근거이며 실제 발사실기와 구분한다.',
   '부분5판에서 머리만 장착했을 때 왕관/윗베일이 바뀌고, 팔만 장착했을 때 머리 장식 전체가 따라 바뀌는 문제는 보이지 않았다. 다리·몸통/다리 조합의 피부·신발과 뒤쪽 의상도 하나의 몸으로 읽힌다.',
   '153/154/183의 낮은 자세·사다리 끝은 새 머리/베일 방향을 유지하며 손·무릎·발이 몸체로 이어진다.155/183 대기대조에서도 추가로 확정되는 체형 급변을 찾지 못했다.'
 ],
 'new_confirmed_art_defects':[],
 'limitations':[
   '부분판은10고유 본체의 머리/몸통/팔/다리/몸통+다리5상태다. 모든448조합을 육안으로 봤다는 뜻이 아니며 나머지 조합은 독립 수치 대조 근거다.',
   '원표 연속 재생·실제 사다리 손발 접점·사격 효과·게임은 이 열람에서 수행하지 않았다.',
   '155는149새몸+새팔이라는 기존 Nana 제작 정책을 잇는다. 원US의 별도 전신 반동까지 복원했다는 주장과 분리한다.',
   '최종 미술 수용과 사용자 수용은 루트의 별도 결정이다.'
 ],
 'user_final_accepted':False,'runtime_verified':False
}
p=O/'visual_review.json';assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
