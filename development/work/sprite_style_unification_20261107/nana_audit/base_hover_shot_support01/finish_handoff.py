"""완성 자원 동결이 아닌, 독립 사격팔 지원 후보의 전달 스냅샷."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 out=D/'handoff01';r=json.loads((out/'report.json').read_text('utf8'));assert r['passed']and r['root_sources_unchanged']
 viewed=[D/'arm_joint_probe_v2'/f'comparison_{i}.png'for i in range(1,5)]+[out/f'muzzle_contacts_{i}.png'for i in range(1,5)]
 write(out/'visual_review.json',{'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in viewed],'findings':['222/224의 길게 뻗은 검정소매에 윗면/아랫면 명암과 손목이 구분된다.226/228은 팔꿈치가 손 아래로 접히는 형상이다.','팔 마스크 밖 원새몸을 유지한 마지막열에서 얼굴·머리·하체가 donor 전신으로 교체되지 않았음을 확인했다.','원점+1의 총입구와 원첫188px 효과를 같은 원점으로 겹친 중립 합성에서 총끝이 효과와 연결된다.','85와 비교하여 소매가 한 픽셀 선으로 끊기거나 손/총이 분리되는 추가 확정 결함은 이 8판에서 찾지 못했다.'],'limitations':['생산자 정적 시각검토이며 루트 최종수용/독립 자원검사/게임실기는 아니다.','원효과의 중립색 합성으로 실제 CLUT/렌더순서/시간표까지 검증한 것은 아니다.','양폼 공통손 및 부분아머 최종 소유·루트230과 연결은 루트 합류 후 별도이다.']})
 files=[p for p in sorted(D.rglob('*'))if p.is_file()and'__pycache__'not in str(p)and p.name not in ('HANDOFF_LOCK.json',)]
 write(out/'HANDOFF_LOCK.json',{'kind':'지원팔 후보 스냅샷, 게임자원 FROZEN 아님','parent':r['parent'],'refs':[222,224,226,228],'forms':['base_legs','fourth'],'source_sheet_count':2,'new_arm_cells':8,'root_sources_read_only':True,'apply_instructions':['body_alignment01 각 body_ref의 원래 해시를 확인한 뒤 대응 edit_mask에서 arm_indices를 대입하면 후보 indices와 정확히 일치한다.','팔 바깥 몸체/머리/하체를 이 후보 donor로 교체하지 않는다.','정본85는 20셀 모듈을 원발사점+1에 강체이동하고 실제 새 피부손만 그립 앞에 가린다.','최종 공통층/부분조건/패킹은 루트 담당이며 이 지원후보만으로 게임검증 완료 처리하지 않는다.'],'report_sha256':digest(out/'report.json'),'visual_review_sha256':digest(out/'visual_review.json'),'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in files]})
 print(json.dumps({'report':digest(out/'report.json'),'visual':digest(out/'visual_review.json'),'handoff_lock':digest(out/'HANDOFF_LOCK.json'),'files':len(files)}))
if __name__=='__main__':main()
