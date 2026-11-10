"""검사한 동일 ARC를 최종 후보 경로에 보존하고 잘못된 설명만 바로잡는다."""
from pathlib import Path
import json,hashlib,shutil
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=D/'packed_hover_diagnostic_v2';out=D/'packed_hover_candidate_v1';assert not out.exists()
 final='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff';assert sha(src/'PL02_U.ARC')==final
 v=json.loads((src/'verification.json').read_text('utf8'));assert v['passed'] and v['after']==final and v['rgba_combinations']==7296 and v['target_layers_exact']==50
 assert v['targets_manifest_sha256']==sha(D/'targets_preview_v3/manifest.json')
 out.mkdir()
 for p in [src/'PL02_U.ARC',*[src/f'readback_{i}.png'for i in range(1,6)]]:shutil.copyfile(p,out/p.name);assert sha(p)==sha(out/p.name)
 v['inherited_full_verification']={'path':(src/'verification.json').relative_to(ROOT).as_posix(),'sha256':sha(src/'verification.json'),'all_counts_from_same_exact_arc':True,'reexecuted_for_path_copy':False}
 v['scope']='새5몸체+원발사점 국소팔5의 호버10/50층. 원5공유32타일·상체0/하체5·빈6/7/8 보존. 기존 보고의 차량/Y별칭 설명은 복사 오류였으며 검사 대상과 ARC는 처음부터 이 호버10이었다. 현재 검증을 재실행했다고 주장하지 않는다.'
 (out/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
 p=json.loads((src/'proposal.json').read_text('utf8'));p['files']['PL02_U.ARC']['path']=(out/'PL02_U.ARC').relative_to(ROOT).as_posix();(out/'proposal.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'candidate_sha256':final,'copied_byte_exact':True}))
if __name__=='__main__':main()
