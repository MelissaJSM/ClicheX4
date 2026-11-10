"""현재 Ultimate 특수기 추출판의 실제 정적 검토를 별도로 기록한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent/'ultimate_special_review01';ROOT=D.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=json.loads((D/'report.json').read_text('utf8'))
 result={'reviewer':'overhaul_audio','source':report['source'],'source_sha256':report['source_sha256'],
 'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in [D/f'comparison_{i}.png' for i in range(1,5)]],
 'findings':[
  {'refs':[85,86],'status':'preserve_reviewed','observation':'머리카락 층과 재킷 주름이 대기 기준과 비교적 가까워 이번 네 판에서는 새 제작이 꼭 필요한 세부 손실을 찾지 못했다. 두 참조 자체는 완전 동일 그림이 아니므로 서로 복사하지 않는다.'},
  {'refs':[88,89,90,91],'status':'needs_redraw','observation':'넓은 분홍 뒷머리와 소매가 큰 단색 면으로 뭉쳐 대기보다 머릿결·팔 안쪽 주름이 적다. 후폼90/91 어깨 주변의 분홍 직사각형 면은 의상 의미를 별도로 확인할 대상이다.88의 뒤쪽 흰 효과를 몸체로 간주하지 않는다.'},
  {'refs':[95,96,97,98,99],'status':'needs_redraw','observation':'큰 분홍 머리 띠와 단순한 팔/소매 면이 대기보다 거칠다.98/99의 후폼 팔 옆 분홍 막대와 긴 명암 없는 면은 새로운 전후 의상 정합 시 확인한다.95/96의 사선 권총 방향 및97의 위로 든 권총은 독립적으로 보존해야 한다.'}
 ],
 'relations':['95→96 x+1은 재킷층과 빈층은 exact이나 후폼base0는118색인/20alpha 차이가 있다.','98→99 x+1 역시 재킷층과 빈층은 exact이나 후폼base0는117색인/25alpha 차이가 있다.','88/89의 효과·몸체 파생 관계는 역사 출처 읽기가 필요하며 단순 동일 몸체로 확정하지 않는다.'],
 'limits':['현재493bf 부모의 양폼 정지 비교4판이다. 실제 게임이나 새 원화/패킹 수용이 아니다.','다른 폼의 기본/포스 x+1 관계를 Ultimate5층 전체 관계로 확대하지 않는다.','사다리 거부 보정과 독립적인 다른 모션 검토이며 해당 보류7참조는 변경하지 않는다.'],
 'new_art_created':False,'game_asset_modified':False,'runtime_verified':False}
 out=D/'visual_review.json';assert not out.exists();out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
if __name__=='__main__':main()
