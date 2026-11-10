"""既存比較画像を実際に読んだ静的意見だけを保存する。"""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;R=O.parents[3];D=R/'work/sprite_style_unification_20261107/root_shibuki_hover'
assert not (O/'visual_review.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
panels=[D/f'shot_composed01/comparison_{n}.png'for n in(222,224,226,228,230)]+[D/f'shot_registered01/comparison_{n}.png'for n in(222,224,228,230)]
read_files=panels+[D/'compose_shots01.py',D/'register_shots01.py',D/'shot_registered01/manifest.json',D/'shot_composed01/manifest.json']
v={'scope':'기존 합성5판과 원화등록4판 실제 열람에 따른 팔/손목·소매의 정적 의견. 대상 픽셀과 원화는 수정하지 않음.',
 'actually_viewed':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p)}for p in panels],
 'observations':[
  {'refs':[222,224],'finding':'발사팔의 밝은 윗소매와 아래 보라색 그늘이 손목까지 이어진다. 포스의 검보라 소매도 피부손목에서 총 뒷부분으로 연결되어, 이번 판에서 손이나 총이 떨어진 확정 틈은 찾지 못했다. 팔꿈치가 비교적 길고 수평이지만 새 원화등록판에도 같은 소매 굴곡이 있으며 억지로 붙인 별도 막대팔로 보이지 않는다.'},
  {'refs':[222,224,230],'finding':'발사로 바뀐 쪽의 이전 높은 주먹이 따로 남아 세 번째 팔처럼 보이는 형상은 찾지 못했다.222/230 반대편의 높은 팔 한 개는 정상적으로 남고,224의 반대팔은 가슴앞에 접힌 자세로 읽힌다.'},
  {'refs':[226,228],'finding':'얼굴 가까이 총을 든 접힌 자세에서 아래쪽 손목/커프와 굽힌 소매가 구분된다.228의 복원된 정본 총은 이전 원화등록의 총보다 손 위쪽에 명확히 놓이며, 짧은 전완과 끊겨 떠 있는 모습이나 별도 두 번째 총열은 이번 합성판에서 찾지 못했다.'},
  {'refs':[230],'finding':'발사팔의 피부손목 아래에 기본의 밝은 소매와 포스의 어두운 소매가 각각 연결된다. 높은 반대손·얼굴과 발사팔을 구별할 수 있고 추가 확정 어깨 단절은 찾지 못했다.'},
  {'refs':[222,224,226,228,230],'finding':'코드를 읽어 새팔은 기본 원화의 공통0과 포스 소매7로 배정되고, 지정피부는 공통화하며 총 모듈/투명가드는0층에 복원되는 정책임을 확인했다. 이 코드 이해를 원화 재양자화나 모든 부분조합 검증의 실행 결과로 세지 않는다.'}
 ],
 'limits':['정본60+투명11 및 원발사점의 수치 검증은 HUD 담당이며 본의견에서 재실행하지 않음','팔 길이/두께의 세계좌표 전수 측정은 하지 않았음','226 원화등록 비교판은 이번 실제열람목록에 없음;226 합성판은 실제 열람','전체80부분·얼굴/하체 exact·실기·GPU·원MIPS는 본검토범위 밖','실제 원화파일 직접열람이 아닌 기존 등록비교판 열람인 항목을 구분'],
 'producer_imported_or_called':False,'source_or_resource_changed':False}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lock={'inputs':{p.relative_to(R).as_posix():sha(p)for p in read_files},'visual_sha256':sha(O/'visual_review.json'),'recorder_sha256':sha(Path(__file__))}
(O/'READER_LOCK.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'visual':sha(O/'visual_review.json'),'lock':sha(O/'READER_LOCK.json'),'actually_viewed_files':len(panels)}))
