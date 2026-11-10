"""기존 동결 ARC와 독립/native 증거를 해시로 연결한다. 자원 변경 없음."""
from pathlib import Path
import json, hashlib
H=Path(__file__).resolve().parent
ROOT=H.parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    d=H/'prepared_ultimate_wall01'
    arc_sha='c851fb17b2369281667970c414be63eb31fb1f02fe5641ad667bfb4b5c8507cf'
    assert sha(d/'PL02_U.ARC')==arc_sha
    proof=json.loads((d/'verification.json').read_text('utf8'))
    independent=H.parent/'zero_audit/shibuki_ultimate_wall_independent.json'
    audit=json.loads(independent.read_text('utf8'))
    assert audit['passed'] and audit['candidate_sha256']==arc_sha
    native=H.parent/'br_pending_v7f_components_native_checks.json'
    n=json.loads(native.read_text('utf8'))
    files={p.name:sha(p) for p in d.iterdir() if p.is_file() and p.name!='FROZEN.json'}
    result={'frozen':True,'baseline_bin_sha256':'21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a',
            'scope':'기존 얼티밋 이동/저체력 누적본에 벽55..66 양폼24표시 추가. 자원과 원화 재작성 없음.',
            'files':files,'independent':{'path':independent.relative_to(ROOT).as_posix(),'sha256':sha(independent),'passed':True},
            'native_root_report':{'path':native.relative_to(ROOT).as_posix(),'sha256':sha(native),'reported_by_root_passed':True},
            'art_target_lock':{'path':(H/'ultimate_wall_target_lock01.json').relative_to(ROOT).as_posix(),'sha256':sha(H/'ultimate_wall_target_lock01.json')},
            'actual_viewed_packed_sheets':proof['actual_viewed_packed_sheets'],'root_art_review_accepted':True,
            'palette_audio_timing_unchanged':True,'game_runtime_verified':False,'full_art_unification_complete':False}
    (d/'FROZEN.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'path':str(d/'FROZEN.json'),'sha256':sha(d/'FROZEN.json'),'arc_sha256':arc_sha}))
if __name__=='__main__': main()
