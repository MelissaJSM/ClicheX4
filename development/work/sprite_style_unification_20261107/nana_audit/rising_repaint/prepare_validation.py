"""라이징 후보의 입력 고정/원MIPS 계획/권총·효과 보존 검증."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,need,write
from scripts.c01_audio_build import read_disc
FINAL='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42'

def main():
 out=D/'packed_base_candidate_v1';candidate=Archive((out/'PL00_U.ARC').read_bytes());need(sha(candidate.data)==FINAL,'Candidate')
 parent=Archive((N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC').read_bytes());src=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';expected='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720';need(digest(src)==expected,'Baseline BIN')
 assets,_=read_disc(src,('PL00_U.ARC','SLUS_005.61'));original=sha(assets['PL00_U.ARC'])
 plan={'project':'ver_rin_nana','source_bin':src.relative_to(ROOT).as_posix(),'source_sha256':expected,'resources':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':original,'after':FINAL}},'checkpoint_only':True,'scope':'원MIPS 격리검사 계획. 실제 게임/포인터 쓰기 없음.'};write(D/'native_components.json',plan)
 prop=json.loads((out/'proposal.json').read_text('utf8'));prop['baseline_sha256']=expected;prop['files']['PL00_U.ARC']['before']=original;prop['working_parent_arc_sha256']=sha(parent.data);write(out/'proposal.json',prop)
 weapons=[];p=D/'canonical_weapon_probe_v2'
 for n in(100,101,102,103,104,231,232):
  source=231 if n==232 else n;base=np.array(Image.open(p/f'base_{source:03}_indices.png'));fourth=np.array(Image.open(p/f'fourth_{source:03}_indices.png'));case=np.array(Image.open(p/f'base_{source:03}_case.png'));fixed=(case>0)&(base==fourth)
  for form,mask in(('base',0),('fourth',15)):
   body=np.array(Image.open(p/f'{form}_{source:03}_indices.png'));expected_rgba=np.array(candidate.rgba(body,16 if mask else 0));real=np.array(candidate.composite(n,mask)[0]);need(np.array_equal(expected_rgba[case>0],real[case>0]),f'Canonical case/new fingers {n}/{form}')
  for mask in range(16):
   for arm in(1,2):
    real=np.array(candidate.composite(n,mask,arm)[0]);need(np.array_equal(real[fixed],np.array(candidate.rgba(base))[fixed]),f'Common exposed gun {n}/{mask}/{arm}')
  weapons.append({'ref':n,'case_source_ref':85,'module_texels':20,'native_extent':8,'common_unoccluded_texels':int(fixed.sum()),'native_case_sha256':sha(case.tobytes()),'canonical_window_source_sha256':digest(p/f'base_{source:03}_case.png'),'base_and_fourth_case_plus_fingers_exact':True,'all32_partial_cases_exact':True})
 effect=[]
 for gb in range(1,len(parent.banks)):
  need(parent.banks[gb]['base']==candidate.banks[gb]['base']and parent.banks[gb]['end']==candidate.banks[gb]['end'],'Aux boundary');lo,hi=parent.banks[gb]['base'],parent.banks[gb]['end'];need(parent.g[lo:hi]==candidate.g[lo:hi],'Aux graphics bytes');effect.append({'bank':gb,'sha256':sha(parent.g[lo:hi]),'byte_exact':True})
 # All non-player composition records and every non-graphics/non-composition
 # ARC entry are separately byte-checked by the complete packer audit.
 need(parent.p==candidate.p,'Palette exact')
 write(out/'weapon_effect_verification.json',{'passed':True,'candidate_sha256':FINAL,'parent_sha256':sha(parent.data),'weapons':weapons,'canonical_visible_window_checks':14,'partial_weapon_checks':224,'effect_auxiliary_graphics':effect,'native_initializer_evidence':(D/'native_contacts_v1/manifest.json').relative_to(ROOT).as_posix(),'native_initializer_sha256':digest(D/'native_contacts_v1/manifest.json'),'scope':'정본권총20셀+새손 가림 보존 및 기본/포스+부분32조합. 효과 그래픽·배치 은행 원형 보존. 실제 발사/불꽃 시간표 재생/게임은 별도.','runtime_verified':False})
 folders=('air_v1','air_registered_v1','charge_v1','charge_registered_v1','recovery_ground_v1','recovery_ground_registered_v1','leg_edges_v1','leg_edges_registered_v1','canonical_weapon_probe_v2','body_contacts_probe_v1','common_legs_probe_v2','common_legs_probe_v3','joint_layers_probe_v2','native_contacts_v1')
 files=list(D.glob('*.py'))
 for folder in folders:files.extend(p for p in(D/folder).rglob('*')if p.is_file()and p.suffix in('.png','.json','.txt'))
 frozen=[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in sorted(set(files))]
 write(out/'INPUT_FROZEN.json',{'candidate_sha256':FINAL,'input_fixed':True,'files':frozen,'scope':'이 기본/포스7 후보의 등록원화·출처·목표35층·제작코드 고정. 독립감사/미술 최종수용 전이므로 FROZEN 아님.'})
 print(json.dumps({'candidate':FINAL,'baseline_arc':original,'input_files':len(frozen),'partial_weapon_checks':224}))
if __name__=='__main__':main()
