"""변경 없는 후보에 독립·native·실제 이미지 열람 근거를 묶는다."""
from pathlib import Path
import json, hashlib
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
W = H.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok, msg):
    if not ok: raise ValueError(msg)
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def main():
    native_path = W/'br_pending_v9a_components_native_checks.json'
    visual_path = W/'root_review_checkpoint19.json'
    native, visual = read(native_path), read(visual_path)
    need(native['passed'], 'Native check not passed')
    for kind, arcname, parent in [('base','PL00_U.ARC','prepared_air01'),('ultimate','PL02_U.ARC','prepared_ultimate_wall01')]:
        folder = H/f'prepared_double_cyclone_{kind}01'
        need(not (folder/'FROZEN.json').exists(), 'Do not overwrite freeze record')
        locked = read(folder/'INPUT_FROZEN.json')
        for name, value in locked['files'].items(): need(sha(folder/name)==value,'Frozen input changed: '+name)
        for name, value in locked['producer_scripts'].items(): need(sha(H/name)==value,'Producer changed: '+name)
        expected = locked['files'][arcname]
        audit_path = W/f'zero_audit/checkpoint20_x_independent/shibuki_{kind}_cyclone.json'
        audit = read(audit_path)
        need(audit['passed'] and audit['candidate_sha256']==expected, 'Independent target mismatch')
        need(native['resources'][arcname]['candidate_sha256']==expected,'Native target mismatch')
        selected = [q for q in visual['art_review_images'] if 'shibuki_audit/double_cyclone_' in q['path']]
        for q in selected: need(q['root_actually_viewed'] and sha(ROOT/q['path'])==q['sha256'],'Visual source changed')
        evidence = {p.relative_to(ROOT).as_posix():sha(p) for p in (audit_path,native_path,visual_path)}
        result = {'frozen':True,'files':locked['files']|{'INPUT_FROZEN.json':sha(folder/'INPUT_FROZEN.json')},
            'baseline_bin_sha256':'21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a',
            'parent_arc_sha256':sha(H/parent/arcname),'target_art_lock_sha256':locked['lock_sha256'],
            'root_native_and_independent_evidence':evidence,'selected_visual_refs':[98,99],
            'cumulative_previous_proposal':parent+'/proposal.json',
            'source_art_method':'builtin imagegen 새 전신, 고정 1/8 배율·원CLUT 등록. 새 손/머리/다리를 통째로 평행 정합하며 옛 뭉개진 몸 복사나 전신 늘임 없음.',
            'readback_visual_review_passed':True,'native_mips_gpu_passed':True,
            'effect_contact_native_initializer_verified':True,'independent_counts':audit['counts'],
            'emulator_gameplay_test':False,'user_accepted':False,'full_style_unification_complete':False}
        (folder/'FROZEN.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(kind,sha(folder/'FROZEN.json'),expected)
if __name__=='__main__':main()
