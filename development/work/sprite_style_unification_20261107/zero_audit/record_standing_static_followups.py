from pathlib import Path
import json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];B=D.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
items=[('nana_ultimate_special_first_visual01',B/'nana_audit/ultimate_special_finish_repaint/first_registered_v1/comparison_1.png',[
 '95의 주된 길이 이탈은 허벅지~종아리다. 치마/반바지 밑선과 팔·커프도 기존보다 대략1~2px 낮게 읽혀 골반 높이부터 무릎/발목까지 국소 원화 정합이 적절하다.',
 '98은 가슴~허리 길이가 크게 늘었다기보다 벌어진 허벅지/정강이와 보폭이 커진 인상이 강하며 어깨 중심은 비교적 유지된다.',
 '숫자는 확대판의 시각 근사이며 landmark 측정 결과가 아니다. 후폼/최신 국소 결과는 이판에서 검토하지 않았다. 미채택 첫후보를 수용/동결로 바꾸지 않는다.']),
 ('shibuki_standing_fire_modules_visual02',B/'shibuki_audit/standing_fire_modules_probe02/gun_regions.png',[
 '새89 분리 영역에서 이전 보호창의 뾰족한 귀 상단이 제거되어 버스터의 둥근 뒤쪽 외곽으로 읽힌다.',
 '85/86 하부 윤곽을 포함한 모듈은 이전 좁은 직사각창보다 완성된 총 외곽으로 읽힌다. 실제34→85/86 60+11 exact는 제작자 보고이며 이 정적검토에서 재실행하지 않았다.',
 '87/90/91/92의 각도별 작은 버스터를 봤으나 단독 모듈판만으로 새손 접합/원총구를 최종수용하지 않는다. 전체몸체 합성과 실제소유 검토가 다음 근거다.'])]
for name,p,notes in items:
 out=D/name;out.mkdir(exist_ok=True);r={'source':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p),'actually_viewed':True,'findings':notes,'scope':'읽기 전용 정적 한 판 의견','source_or_art_modified':False,'native_or_gameplay_executed':False,'final_art_accepted':False}
 q=out/'report.json';q.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(name,sha(q))
