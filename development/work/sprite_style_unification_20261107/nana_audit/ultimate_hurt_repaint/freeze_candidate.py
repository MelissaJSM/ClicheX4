"""Ultimate 피격13의 실제 완료 근거를 해시로 결합한다."""
from pathlib import Path
import json,hashlib,argparse
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=D/'packed_hurt_candidate_v1'
FINAL='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
PARENT='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--timeline-checkpoint',required=True);ap.add_argument('--timeline-sha256',required=True);args=ap.parse_args()
    out=P/'FROZEN.json';assert not out.exists(),'동결 덮어쓰기 거부';assert sha(P/'PL02_U.ARC')==FINAL
    proposal=read(P/'proposal.json');assert proposal['files']['PL02_U.ARC']['after']==FINAL and proposal['parent_arc_sha256']==PARENT
    independent=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_hurt13_independent01/report.json';assert sha(independent)=='bb57d92bb2abbbef3c86ff65d8ffeac772b76a4faa4842d2fac687ed7f74b3cf'
    iv=independent.parent/'visual_review.json';assert sha(iv)=='1cd0b4bf7b2c53d995b7747a5725050aa8470342311d68cf2cfbb9abcb6bb78d'
    ij=read(independent);assert ij['passed'] and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
    lockpath=P/'INPUT_FROZEN.json';assert sha(lockpath)==ij['input_frozen_sha256'];lock=read(lockpath);assert lock['candidate_sha256']==FINAL
    for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
    target=D/'final_targets_v1/manifest.json';assert sha(target)==ij['target_manifest_sha256']
    checkpoints=[];viewed=[]
    digests={88:'c2fa9ea96f3830b55b211385f912a22dc5baaf438fa598030d77551447f50335',90:'a8cdcbd67c1d73178a4bbe7a70d20dfb404c004b49335b5a937eea1917ff1643',95:'1db38e57c7b02b1acc139021c308fe97723e5e25d427370ebfbb54696300e978',97:'4261c5759c0c1bde2bcdb6dd4db7df03a5ee7761974f2b2d5af851d75aea11ac'}
    refs=[(ROOT/f'work/sprite_style_unification_20261107/root_review_checkpoint{k}.json',v)for k,v in digests.items()]+[(ROOT/args.timeline_checkpoint,args.timeline_sha256)]
    for p,expected in refs:
        assert sha(p)==expected;checkpoints.append(p)
        for q in read(p)['root_actually_viewed']:
            if '/nana_audit/ultimate_hurt_repaint/'in q['path']:
                f=ROOT/q['path'];assert sha(f)==q['sha256'];viewed.append(f)
    proofs=[P/'verification.json',P/'source_reconstruction.json',P/'reproduction.json',D/'native_components_v1_native_checks.json',D/'native_cycle_v1/verification.json',independent]
    for p in proofs:assert read(p)['passed'],rel(p)
    assert read(P/'reproduction.json')['candidate_sha256']==FINAL
    assert read(D/'native_components_v1_native_checks.json')['resources']['PL02_U.ARC']['candidate_sha256']==FINAL
    assert read(D/'native_cycle_v1/verification.json')['candidate_arc_sha256']==FINAL
    files=[P/'PL02_U.ARC',P/'proposal.json',lockpath,target,*proofs,iv,*checkpoints,*viewed,D/'native_components_v1.json',D/'native_cycle_v1/manifest.json',D/'native_cycle_v1/REVIEW.html',D/'verify_production.py',D/'make_native_cycle.py',D/'verify_native_cycle.py',Path(__file__).resolve()]
    files=list(dict.fromkeys(files))
    result={'frozen':True,'status':'나나 Ultimate 피격13 준비본 동결. 새게임 통합/실기는 별도.','character':'nana','forms':['ultimate_before','ultimate_after','partial_masks_arm1_arm2'],
      'refs':list(range(106,115))+[233,234,235,236],'new_authored_body_keys':[106,110,233,234],'derived_body_effect_refs':[107,108,109,111,112,113,114,235,236],
      'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL02_U.ARC']['before'],
      'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':len(lock['files']),'independent_counts':ij['counts'],'root_art_review_checkpoints':[rel(p)for p in checkpoints],
      'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,
      'reproduction':'동일 부모/입력 메모리 재제작 byte-exact,8잘못된입력 거부. 별도 새 출력 재제작은 미실행.',
      'body_provenance':'새 원화2장→8고정셀,새 의상 의미영역·234신발-1y/110전완-1x-1y 출처링크·실제원화 경계2셀을 재구성. 옛몸/머리 덮기와 단색채움 없음.',
      'effect_policy':'107/108 기존재킷층에서 분리되는 원FX99/76px의 전체타일/파트를 새양폼에 공통 적용하는 신규정책.111의 고유10파트188px 유지.109 양폼각106알파;112..114는 기존과동일한 재킷110 공통CLUT2 규칙.',
      'aura_provenance':'235/236 현재재킷234바깥 확실한66/135px,각12개의8연결성분을 색/형상/픽셀 보존하여 국소평행정합. 새몸겹침0,최대거리5/7px. 숨겨진 모든효과 복구주장 없음. PL00의85/172px와구별.',
      'limits':['실제 게임 피격/점멸/이벤트복귀/CLUT 시간변화는 아직 미검증.','오프라인60호출/초 검토가정이며 실제시간의 인간게임관찰과 다르다.','제작자7296RGBA와 독립416대상RGBA+비대상층 보존을 구별한다.','이 동결은 Ultimate 피격만이며 저체력/등장승리/사다리/차량 등 전체모션 완료가 아니다.'],
      'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'files':len(files)}))
if __name__=='__main__':main()
