"""호버10 원화·실제총구·원효과·독립/native/원순서 근거를 동결한다."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_hover_candidate_v1'
FINAL='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff';PARENT='94326933d0dd62ccd7a5904019cae9fd36fc068a6acde8941d6bf8ff363666ca'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));rel=lambda p:p.relative_to(ROOT).as_posix()
def main():
 out=P/'FROZEN.json';assert not out.exists();assert sha(P/'PL02_U.ARC')==FINAL;proposal=read(P/'proposal.json');assert proposal['parent_arc_sha256']==PARENT and proposal['files']['PL02_U.ARC']['after']==FINAL
 ip=N.parent/'zero_audit/nana_ultimate_hover10_independent01/report.json';iv=ip.parent/'visual_review.json';assert sha(ip)=='d88f6713a8007e5065909d2ca3b3a22200fccbfaea6a01e9d1e07d61b7795665';assert sha(iv)=='4032b507ff0b30736c3e758a551481883f6e9599f60afb8a537431e37ee73896';ij=read(ip);assert ij['passed']and ij['candidate_sha256']==FINAL and ij['parent_sha256']==PARENT
 lockp=P/'INPUT_FROZEN.json';assert sha(lockp)==ij['input_frozen_sha256'];lock=read(lockp)
 for q in lock['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
 roots=[]
 for num,h in((142,'fd126b2be30f208586c607b97532f31884da0cd086eb568cbef95baa8ae5895e'),(143,'a4d15e747e93211355053deb4b3d608f1a6578a262736d8614c4ee405f46caab')):
  cp=N.parent/f'root_review_checkpoint{num}.json';assert sha(cp)==h;cj=read(cp);assert cj['candidate_sha256']==FINAL
  for q in cj['actually_viewed_files']:assert sha(ROOT/q['path'])==q['sha256']and q['actually_viewed']
  roots.append(cp)
 proofs=[P/'verification.json',P/'reproduction.json',D/'targets_preview_v3/source_reconstruction.json',D/'native_components_v1_native_checks.json',D/'native_cycle_v1/verification.json',D/'packed_contacts_v1/report.json',ip]
 for p in proofs:assert read(p)['passed'],rel(p)
 assert read(P/'verification.json')['after']==FINAL and read(P/'reproduction.json')['candidate_sha256']==FINAL;assert read(D/'native_components_v1_native_checks.json')['resources']['PL02_U.ARC']['candidate_sha256']==FINAL and read(D/'native_cycle_v1/verification.json')['candidate_arc_sha256']==FINAL and read(D/'packed_contacts_v1/report.json')['candidate_sha256']==FINAL
 jetbind=[]
 for n in(221,223,225,227,229):
  old=np.array(Image.open(D/f'canonical_cases_probe_v3/body_{n:03}_indices.png'));new=np.array(Image.open(D/f'canonical_cases_probe_v4/body_{n:03}_indices.png'));assert np.array_equal(old>0,new>0);diff=[[int(x-160),int(y-160),int(old[y,x]),int(new[y,x])]for y,x in np.argwhere(old!=new)];assert len(diff)==(3 if n==229 else 0);jetbind.append({'ref':n,'prior_root_jet_board_alpha_exact_to_final':True,'changed_actual_RGB_semantic_cells':diff})
 sheets=[P/f'readback_{i}.png'for i in range(1,6)]+[D/f'native_cycle_v1/timeline_{i}.png'for i in[*range(21,27),*range(133,139)]]+[D/f'packed_contacts_v1/jets_{i}.png'for i in(221,223,225,227,229)]+[D/f'packed_contacts_v1/muzzle_{i}.png'for i in(1,2,3)]
 files=list(dict.fromkeys([P/'PL02_U.ARC',P/'proposal.json',lockp,D/'targets_preview_v3/manifest.json',*proofs,iv,*roots,*sheets,P/'producer_visual_review.json',D/'native_components_v1.json',D/'native_cycle_v1/manifest.json',D/'native_cycle_v1/REVIEW.html',D/'verify_reproduction.py',D/'make_native_cycle.py',D/'verify_native_cycle.py',D/'verify_packed_contacts.py',D/'record_review.py',Path(__file__).resolve()]))
 r={'frozen':True,'status':'나나 Ultimate 호버10 새상세·원발사점 팔/권총 검증 동결. 전체미술완료는 아니다.','character':'nana','forms':['ultimate_before','ultimate_after'],'actual_visual_policy':'원코드217..230은 engine ownership과 무관하게 mask15. 두 별개의 의상 원화를 제작한 것이 아니라 같은 실제표시이며 캡슐전 실제도달성은 별도다.','refs':list(range(221,231)),'new_authored_body_keys':[221,223,225,227,229],'new_authored_firing_arms':[222,224,226,228,230],'new_authored_source_cells':10,'derived_effect_refs':[],'asset_sha256':FINAL,'parent_asset_sha256':PARENT,'original_active_asset_sha256':proposal['files']['PL02_U.ARC']['before'],'files':[{'path':rel(p),'sha256':sha(p)}for p in files],'input_files_verified_unchanged':len(lock['files']),'independent_counts':ij['counts'],'root_art_review_checkpoints':[rel(p)for p in roots],'root_static_art_direction_accepted':True,'original_MIPS_decode_and_GPU_upload_checked':True,'offline_canvas_play_pause_checked':True,'root_prior_jet_final_body_binding':jetbind,'source_provenance':'제작자 생성10고정셀 재양자화→실제홍채9/하체RGB20/정본85권총/원발사표 팔→50층 재구성 exact. 독립reader는 등록후출처부터50층·원효과를 별도로 재구성했으며 생성10셀 자체재양자화를 수행한 것으로 확대하지 않는다.','muzzle_policy':'실제US/RN36 8011B230 signedXY:222(-27,-9),224(-29,-8),226(-20,-10),228(-17,-10),230(-24,-11). 정본85의20셀을 X=원점+1/총열Y=원점−1,0에 배치하고 새피부손으로2/1/1/1/1셀만가림. 원8열창 고정 진단안은미채택. 총/손/팔만 새원화 정합했고 원코드·효과·몸체전체원점은불변.','packing_policy':'원5사격공유stream/각32tile·은행/항목경계·비대상502raw/1090층/1741조립·팔레트보존. upper0/lower5/empty6·7·8,사격짝하체exact. 116GPU끝단 안전.','effect_policy':'원15추진위상/6전체타일504..509와 원7탄환프레임은 독립exact. 첫188px점유 및15추진위상은 원점의 중립색정적판으로검토. 실제CLUT/블렌딩/그리기순서/물리/발사시점은미실행.','reproduction':'최초7296전체RGBA, 별도프로세스동일바이트재현1회·8거부·320타깃RGBA. 직접목표32마스크×2팔×10=640과패킹/독립16×2×10=320을구분. 최종경로는통과동일ARC복사이며 그복사를전체검사재실행이라고하지않는다.','limits':['원표21..26/133..138의14참조84canvas·12재생/정지와정적원순서검토. 실제게임 입력/물리·인간실시간관측은별도다.','다음노바213..220 및전체잔여는계속제작한다.','보류사다리148/149/150/151/152/153/155는무변경·미완료로유지했다.'],'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False,'game_BIN_pointer_save_written':False}
 out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'asset':FINAL,'frozen_sha256':sha(out),'files':len(files)}))
if __name__=='__main__':main()
