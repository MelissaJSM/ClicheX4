"""실제 검토한 새 원화 등록안을 후보 입력으로 고정한다."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
from PIL import Image
D=Path(__file__).parent/'rin_extension';A=D/'ladder_dash01';O=D/'ladder_dash_registered_v1';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ROOT=Path(__file__).resolve().parents[3]
info=json.loads((A/'inputs.json').read_text('utf8'));probe=json.loads((A/'anchor_probe/registration.json').read_text('utf8'));body=json.loads((A/'body_probe/registration.json').read_text('utf8'));rows=[]
for f in info['frames']:
 key=f['key'];p=A/'body_probe'/(key+'_indices.png');old=np.array(Image.open(A/(key+'_before_indices.png')));z=np.array(Image.open(p));assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<=15;assert np.nonzero(z)[0].max()==np.nonzero(old)[0].max()
 row=next(q for q in probe['records']if q['key']==key).copy();br=next(q for q in body['records']if q['key']==key);row.update(br);row.update(bank=0,ref=f['ref'],output_sha256=sha(p),old_body_or_head_override=False,source_native=str((A/'native_fixed'/(key+'_indices.png')).relative_to(ROOT)),exact_alias_refs=f['exact_display_aliases'])
 shutil.copyfile(p,O/(key+'_indices.png'));mp=A/'body_probe'/(key+'_head_mask.png')
 if mp.exists():shutil.copyfile(mp,O/mp.name);row['head_mask_sha256']=sha(mp)
 rows.append(row)
for form in('normal','black'):shutil.copyfile(A/'body_probe'/(form+'_comparison.png'),O/(form+'_comparison.png'))
report={'source_arc':info['actual_input_arc'],'source_arc_sha256':info['archive_sha256'],'source_generated_sha256':sha(A/'generated.png'),'fixed_grid_registration':str((A/'native_fixed/registration.json').relative_to(ROOT)),'anchor_proof':str((A/'anchor_probe/registration.json').relative_to(ROOT)),'body_proof':str((A/'body_probe/registration.json').relative_to(ROOT)),'native_contact_proof':str((A/'contact_probe/report.json').relative_to(ROOT)),'records':rows,'scope':'사다리 베기199/202 정확사본7과 질풍아 준비155/156 새4원화9참조. 고정셀 양자화·실제cyan눈 표본 복원·전신 평행등록.199/202는 새 머리와 내부투명 보존 후 새몸체만 -2y로 목/발높이 정합. 원게임 원점/시간표 불변.','root_art_review':True,'root_review_scope':'normal/black body_probe 두 판 실제 열람 및 미술방향 수용. 후보이며 최종 사용자 수용/실기와 구분.','user_accepted':False,'runtime_verified':False,'wholebody_scale':False,'invented_pixel_art':False,'contact_limitations':'실제 표93/117·104/125 160 native호출로 짝 확인. 사다리 검기는 후속구간에서 원래 손과 떨어져 있으며 새 ROI거리차0~1px. 효과 이동/확대/손 강제 접착 없음. 피부 손끝 군집은 원표현과1~2px차이가 있어 실기 관찰을 별도 유지.'}
(O/'registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(O/'registration.json'))
