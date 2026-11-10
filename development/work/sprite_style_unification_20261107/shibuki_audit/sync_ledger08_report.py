"""최종 Rising 두 후보의 동결 상태와 진행 중 공중 후보를 구별해 장부를 정리한다."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
def main():
    p=H/'fullform_ledger08.json';q=json.loads(p.read_text('utf8'))
    for r in q['references']:
        if r['ref']in(100,101,102,103,104,231,232)and r['form']in('base','fourth'):
            r['decision']='포스103 소매58px 국소 교정 v2의 독립 감사·원MIPS/GPU·루트 국소 비교 열람으로 동결. v1 반려본은 불변 보존. 실제 플레이/사용자 수용 별도.'
    q['unpacked_art_in_progress']={'group':'Ultimate air33..54','first_page':[33,35,39],'second_page':[37,41,43],'common_source_and_anchor_registration_pending':True,'candidate_resources_unchanged':True,'not_counted_as_frozen':True};p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8')
    u=H/'unique_art_keys08.json';r=json.loads(u.read_text('utf8'));r['source_ledger']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();u.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
    lines=['# 시부키 고유 표시 키 집계','',r['definition'],'','최신 근거: `fullform_ledger08.json`, `unique_art_keys08.json`. 완료율은 계산하지 않는다. 동결은 통합용 미술·정적/원MIPS/GPU 검사 상태이고 전체 실기·사용자 수용을 의미하지 않는다.','', '| 폼 | 참조 슬롯 | 디코딩 | 고유 표시 키 |','| --- | ---: | ---: | ---: |']
    for f,v in r['forms'].items():lines.append(f"| {f} | {v['native_reference_slots']} | {v['decoded_slots']} | {v['unique_visible_art_keys']} |")
    lines+=['','## 상태별 고유 키','']+[f'- `{k}`: {v}'for k,v in r['counts']['unique_key_status_counts'].items()]
    lines+=['','## 남은 핵심 동작군','']+[f"- {v['form']} / {v['group']}: {v['unique_keys']}개 키, refs {','.join(map(str,v['refs']))}"for v in r['pending_motion_groups']]
    lines+=['','Rising Fire 네 폼28표시는 별도 동결본이다. 현재 통합판 v9에 이미 적용됐다고 말하지 않는다. 기본/포스는 흰 소매가 남았던103을 별도 v2에서 교정한 뒤 동결했다.','Ultimate 공중 첫6몸체는 원화/등록 진행 중이며 위 동결 키에 포함하지 않았다.','pending에는 실제 재작화가 필요한 군과 효과·탑승·준비자세 추가 검토가 섞여 있으므로 새로운 원화 장수로 해석하지 않는다.','전체 미술 통일화 완료: 아니오.']
    (H/'UNIQUE_ART_KEYS.md').write_text('\n'.join(lines)+'\n','utf8')
if __name__=='__main__':main()
