"""별도 검사계획과 고정 제작입력 목록을 생성한다. 게임은 쓰지 않는다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_settle_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 v=read(P/'verification.json');assert v['passed'];assert sha(P/'PL00_U.ARC')==v['after']
 parent=ROOT/v['parent_path'];freeze=parent.parent/'FROZEN.json';assert sha(freeze)=='1c843a874dd7bc327e92ccad468953123eadf219c794935e674f5a5cc7f21b76';assert read(freeze)['candidate_sha256']==v['before']
 plan=read(ROOT/'work/sprite_style_unification_20261107/root_nana_standing/standing_components.json');plan['resources']['PL00_U.ARC'].update({'path':(P/'PL00_U.ARC').relative_to(ROOT).as_posix(),'after':v['after']});plan['scope']='현재 원실행코드의 MIPS 해독/GPU 격리검사. 활성 BIN·프로세스·저장 변경 없음.';write(D/'native_components_v1.json',plan)
 proposal=read(P/'proposal.json');proposal['files']['PL00_U.ARC']['before']=plan['resources']['PL00_U.ARC']['before'];write(P/'proposal.json',proposal)
 files=[]
 for folder in ('body_inputs_v1','body_v1','body_registered_v1','contacts_probe_v1','hair_inputs_v1','hair_v1','hair_registered_v1','joint_layers_probe_v3'):
  files.extend(sorted((D/folder).glob('*')))
 files.extend([parent,freeze,ROOT/read(D/'body_inputs_v1/manifest.json')['art_parent_arc'],ROOT/read(D/'contacts_probe_v1/manifest.json')['canonical_donor_path'],D/'register_body.py',D/'prepare_contacts.py',D/'register_hair.py',D/'prepare_joint_layers.py',D/'verify_sources.py',D/'pack_native.py',N/'base_run_repaint/register_page.py',D/'source_reconstruction_v2.json'])
 files=list(dict.fromkeys(p.resolve()for p in files if p.is_file()));out=P/'INPUT_FROZEN.json';assert not out.exists(),'기존입력잠금 덮기거부'
 write(out,{'input_frozen':True,'candidate_sha256':v['after'],'parent_sha256':v['before'],'target_manifest_sha256':v['targets_manifest_sha256'],'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],'runtime_verified':False,'scope':'새 전신2셀 및 머릿결2셀·정본권총·공통손/다리 실제표본·10목표층과 제작코드 고정. 최종동결/독립수용과 구분.'})
 print(json.dumps({'candidate':v['after'],'inputs':len(files),'input_lock_sha256':sha(out)}))
if __name__=='__main__':main()
