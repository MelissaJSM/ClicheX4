"""Join completed independent sprite audits and check the protected inputs once."""
from pathlib import Path
import json, sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from verify_prepared import ROOT, PARENT, digest, need, write

def load(p):return json.loads(p.read_text('utf8'))
def link(p):return {'path':str(p.relative_to(ROOT)),'sha256':digest(p)}

def main():
    projects={}
    for character,(mode,_,parent_hash) in PARENT.items():
        p=HERE/(mode+'_disc_independent.json');r=load(p)
        need(r['passed'] and r['parent_sha256']==parent_hash,'Disc proof incomplete')
        need(digest(ROOT/r['bin'])==r['bin_sha256'],'Final disc proof stale')
        r['disc_independent_evidence']=link(p);projects[mode]=r
    proofs={}
    for name in ('nana_prepared_independent','nana_frost_independent','shibuki_prepared_independent'):
        p=HERE/(name+'.json');r=load(p)
        need(r['passed'],'Prepared audit incomplete')
        need(digest(ROOT/r['arc'])==r['arc_after_sha256'],'Prepared ARC proof stale')
        need(digest(ROOT/r['proposal'])==r['proposal_sha256'],'Prepared proposal proof stale')
        proofs[name]={**link(p),'arc_sha256':r['arc_after_sha256']}
        # The exact proposal must also be present in the all-sector proof.
        owner='ver_buki_riko' if name.startswith('shibuki') else 'ver_rin_nana'
        need(any(q['sha256']==r['proposal_sha256'] for q in projects[owner]['audited_proposals']),
             'Final BIN did not consume this exact audited proposal')
    visual=load(HERE/'visual_review.json')
    for key in ('nana_PL00','nana_PL02','shibuki_final'):
        need(visual[key]['recommended'] and not visual[key]['new_confirmed_visual_defect'],'Visual audit incomplete')
        for rel in visual[key]['viewed']:need((ROOT/rel).is_file(),'Missing visual evidence')
    snapshot=ROOT/'work/sprite_reaudit_20261106/protection_before.json'
    protected=load(snapshot)
    need(protected['count']==len(protected['files'])==75,'Unexpected protection snapshot')
    checked={}
    for rel,spec in protected['files'].items():
        p=ROOT/rel
        need(p.stat().st_size==spec['size'] and digest(p)==spec['sha256'],'Protected input changed: '+rel)
        checked[rel]=spec
    report={'passed':True,'scope':'시부키 얼티밋 다리 재질, 나나 부분 베일 소유 및 얼티밋 프로스트 실드 종아리 명암 교정의 독립 검증.',
            'projects':projects,'prepared_audits':proofs,'visual_review':link(HERE/'visual_review.json'),
            'protection_snapshot':link(snapshot),'protected_file_count':len(checked),'protected_files':checked,
            'protected_files_exact':True,'original_inputs_current_parents_first_release_reference_art_F1_cards_pointers_preserved':True,
            'all_executable_audio_UI_HUD_text_other_sprites_preserved':True,
            'game_or_state_or_pointer_written_by_this_audit':False,'runtime_verified_by_this_audit':False,
            'followup_art_candidates':[{'character':'shibuki','form':'ultimate_before/ultimate_after','refs':[35,37,45,47],
                'observation':visual['shibuki_final']['remaining_visual_limitation'],
                'recommendation_scope':visual['shibuki_final']['recommendation_scope']}],
            'limits':['정적 합성·실제 출력 파일 검증이며 이번 수정 후 게임 내 장면을 직접 검증한 결과는 아니다.',
                      '외부 효과 객체·화면 혼합·시간 진행·물리·좌우 GPU 실기 검증과 사용자 수용은 별도로 구분한다.']}
    write(HERE/'final_independent.json',report)
    print(json.dumps({'passed':True,'protected':len(checked),'sha256':digest(HERE/'final_independent.json')}),flush=True)

if __name__=='__main__':main()
