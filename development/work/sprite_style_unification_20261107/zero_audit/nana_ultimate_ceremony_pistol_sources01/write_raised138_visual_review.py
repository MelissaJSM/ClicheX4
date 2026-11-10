from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
ROOT=O.parents[3]
U=ROOT/'work/sprite_style_unification_20261107/nana_audit/ultimate_ceremony_repaint'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[U/'raised138_local_probe_v1/comparison.png',U/'settle_pair_probe_v1/comparison.png']
sources=[U/'raised138_local_probe_v1/manifest.json',U/'settle_pair_probe_v1/manifest.json']
record=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
d={
 'scope':'새138 위로 든 권총팔의 국소 정합2판 실제 view_image 열람. 패킹·원화 재구성·실기는 수행하지 않았다.',
 'actually_viewed':[record(p) for p in paths], 'source_metadata':[record(p) for p in sources],
 'observations':[
   '낮춰진 팔 초안과 달리 양폼 모두 권총팔이 머리 위까지 올라가 역사138의 동작 방향으로 돌아왔다.',
   '정합 마지막 열에서 새 머릿결·얼굴·배·허벅지·반대팔의 세부가 유지되고, 올라간 팔은 목·어깨로 이어진다. 이 두 정지판에서 새롭게 확정되는 팔 절단이나 다리 길이 급변은 찾지 못했다.',
   '의상 합성 마지막 열에서는 분홍 소매가 맨팔 피부로 바뀌고, 위손과 검정·분홍 권총 표시는 같은 위치를 유지한다. 어깨 시작과 가슴의 검정 옷 경계도 구별된다.'
 ],
 'next_checks':['정본 사랑이 모듈의 총열 길이/그립/손가림은 제작자의 다음 단계로 남긴다. 이 판만으로 그 크기·총구가 검증됐다고 하지 않는다.',
                '새138→139의 −1y 및136/137에서 이어지는 원순서 연결은 최종 등록 뒤 비교해야 한다.'],
 'art_direction_observation':'팔을 위로 든 동작 복원과 국소 합성 방향에 추가 확정 결함을 찾지 못함. 최종 미술 수용은 루트 별도.',
 'runtime_verified':False,'user_final_accepted':False
}
out=O/'raised138_visual_review.json'; assert not out.exists()
out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf-8')
print(sha(out))
