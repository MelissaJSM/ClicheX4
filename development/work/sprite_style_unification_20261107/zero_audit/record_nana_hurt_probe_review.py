from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
P=D.parent/'nana_audit/hurt_repaint/effect_probe_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[P/f'comparison_{n}.png'for n in(1,2,3)]
j={'scope':'새 나나 기본/포스 피격 효과 진단판3장 실제 정적 열람. 최종후보/실기 수용 아님.',
 'source_manifest':{'path':(P/'manifest.json').relative_to(ROOT).as_posix(),'sha256':sha(P/'manifest.json')},
 'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],
 'findings':[
  {'refs':[107,108,111],'observation':'새 머릿결·소매·치마·부츠가 기존 큰 단색면보다 분리되어 보인다. 이 정적판에서 목/무릎/발목의 새로운 명백한 절단은 보이지 않았다. 원 번개선은 몸보다 넓은 별도 효과이며 접촉하는 모든 선끝을 몸 윤곽으로 옮길 근거는 없다.'},
  {'refs':[109,112,113,114],'observation':'새 몸과 함께 실루엣이 바뀌었고 114의 내부 명암선도 새 몸을 따른다. 작은 머릿결/치맛단 때문에 외곽이 더 촘촘해진 것은 새알파의 결과로 읽힌다. 실제 빠른 점멸의 가독성과 게임CLUT는 이 정적판만으로 판정하지 않았다.'},
  {'refs':[235,236],'observation':'235의 오라와 새 뒤쪽 머리끝,236의 머리/모자 바깥 흰선이 일부 붙거나 새 머리에 가려져 간격이 달라 보인다. 기존 오라가 새몸과 겹친다는 제작자 진단에 동의하며, 그대로 최종수용했다고 기록하지 않는다. 새머리/몸체를 옛외곽에 맞춰 잘라내는 해결은 권하지 않는다.'}
 ],
 'producer_quantitative_evidence_separate':'제작자가 보고한 오라중첩8/13px는 이 미술열람에서 독립 재계산한 수치가 아니다.',
 'new_confirmed_body_cut':False,'aura_alignment_pending':True,'source_or_game_modified':False,'final_candidate_accepted':False,'runtime_verified':False}
out=D/'nana_hurt_relations01/new_effect_probe_review.json';out.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
