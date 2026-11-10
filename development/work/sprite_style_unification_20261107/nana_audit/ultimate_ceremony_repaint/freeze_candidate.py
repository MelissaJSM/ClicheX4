"""Ultimate 등장10의 완료 근거를 검증하고 기존 동결과 분리해 저장한다."""
from pathlib import Path
import json, hashlib
D=Path(__file__).resolve().parent; ROOT=D.parents[3]; P=D/'packed_arrival_candidate_v1'
FINAL='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
PARENT='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
    out=P/'FROZEN.json'; assert not out.exists(), '동결 덮어쓰기 거부'
    assert sha(P/'PL02_U.ARC')==FINAL
    proposal=read(P/'proposal.json'); assert proposal['parent_arc_sha256']==PARENT
    assert proposal['files']['PL02_U.ARC']['after']==FINAL
    independent=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_arrival10_independent01/report.json'
    assert sha(independent)=='197475f4b28c26e194d3f60db29fd8db81b40905615e9bd305f3908082ca47f4'
    iv=independent.parent/'visual_review.json'
    assert sha(iv)=='6abd49a46b38c4c2ada943dc6802ad61688566685eb54b1f2a7bc619a19ec2b0'
    ij=read(independent); assert ij['passed'] and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
    lockpath=P/'INPUT_FROZEN.json'; assert sha(lockpath)==ij['input_lock_sha256']
    lock=read(lockpath); assert lock['candidate_sha256']==FINAL
    for q in lock['files']: assert sha(ROOT/q['path'])==q['sha256'],q['path']
    target=D/'arrival_targets_probe_v2/manifest.json'; assert sha(target)==ij['target_manifest_sha256']
    checkpoints=[];viewed=[]
    for n,s in {107:'6a70aafc6620c4f215a9fb467325ed2976893ddee1c26806dcc36fea106265e2',110:'7a4b0e65e36d22e2fe34647d69562ae3471608f442bc87373f9a18b8746d8b65'}.items():
        p=ROOT/f'work/sprite_style_unification_20261107/root_review_checkpoint{n}.json'; assert sha(p)==s; checkpoints.append(p)
        for q in read(p)['root_actually_viewed']:
            if '/nana_audit/ultimate_ceremony_repaint/' in q['path']:
                f=ROOT/q['path']; assert sha(f)==q['sha256']; viewed.append(f)
    proofs=[P/'verification.json',P/'source_reconstruction.json',P/'reproduction.json',D/'native_components_v1_native_checks.json',D/'native_cycle_v1/verification.json',independent]
    for p in proofs: assert read(p)['passed'],rel(p)
    assert read(P/'verification.json')['after']==FINAL
    assert read(P/'reproduction.json')['candidate_sha256']==FINAL
    assert read(D/'native_components_v1_native_checks.json')['resources']['PL02_U.ARC']['candidate_sha256']==FINAL
    assert read(D/'native_cycle_v1/verification.json')['candidate_arc_sha256']==FINAL
    files=list(dict.fromkeys([P/'PL02_U.ARC',P/'proposal.json',lockpath,target,*proofs,iv,*checkpoints,*viewed,D/'native_components_v1.json',D/'native_cycle_v1/manifest.json',D/'native_cycle_v1/REVIEW.html',D/'verify_sources.py',D/'verify_reproduction.py',D/'make_native_cycle.py',D/'verify_native_cycle.py',Path(__file__).resolve()]))
    result={'frozen':True,'status':'나나 Ultimate 등장10 준비본 동결. 새 게임 통합/실기는 별도.','character':'nana','forms':['ultimate_before','ultimate_after','partial_masks_arm1_arm2'],
      'refs':[130,131,133,134,135,136,137,138,139,141],'new_authored_body_keys':[133,135,136,137,138],'derived_body_effect_refs':[130,131,134,139,141],
      'preserved_related_refs':[132,140,142,156,157,158],'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL02_U.ARC']['before'],
      'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':len(lock['files']),'independent_counts':ij['counts'],'root_art_review_checkpoints':[rel(p)for p in checkpoints],
      'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,
      'reproduction':'별도 프로세스 재제작 byte-exact, 잘못된 입력8종 거부. 최초7296RGBA와 재현320목표RGBA/전체raw·층·조립 검사를 구분.',
      'body_provenance':'새 원화7장22고정셀부터 의상 의미영역·실제경계6셀·새 손·138 위로 든 팔과 국소 종아리까지 재구성. 옛몸 덮기/단색 채움 없음.',
      'weapon_policy':'직접 선행 원화에서 누락된133/135/136/137 사랑이를 최초 역사 자세의 방향과 새 손에 복원. 정본85의20texel/8px총열을 90도 강체 변환, 손가림만 적용.138 위로 든 총 유지.',
      'effect_policy':'136/137 역사 흰선46px씩 원위치 유지.134 새133+역사 구체,131 새133 알파13+역사 에너지.130은 새133 실루엣과 원반복shell의 투명칸 포함 가림.139는 수용 Nana 정책인138의 y-1이며 원US 동일그림 주장이 아님.141은 각폼 idle0+역사 먼지12px.',
      'shared_stream_policy':'131/132 원공유만 저장 스트림 분리.132 원18tile decodedraw·count·모든 조립·표시는 보존. 원 효과132/140은 새 원화로 집계하지 않음.',
      'limits':['실제 등장 이벤트/캡슐/차지 연결은 아직 게임 미검증.','원표2/95/96와 수동연결1종,114canvas 기계재생이며60호출/초 가정. 사람의 실시간 게임 관찰과 구분.','독립320목표RGBA와 제작자7296RGBA는 별도 범위.','승리204..207 및 다른 미완료 모션은 다음 묶음. 전체 나나 미술 통일/사용자 최종수용 아님.'],
      'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'files':len(files)}))
if __name__=='__main__':main()
