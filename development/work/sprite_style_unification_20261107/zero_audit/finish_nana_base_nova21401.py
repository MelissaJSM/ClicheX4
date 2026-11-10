"""214 원US 내부효과와 역사 외부124픽셀 정책을 분리해 기록."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;O=D/'nana_base_nova214_relations01';sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def save(name,obj):
 p=O/name;assert not p.exists();p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf8');return {'path':rel(p),'sha256':sha(p)}
r=json.loads((O/'report.json').read_text('utf8'));assert sha(O/'report.json')=='5eae26bfb81cd7acb5bacdc6cf4ad35fa9da94090ad84891d43e7e89c2f03d0f'
us=Archive(read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC',))[0]['PL00_U.ARC']);a,b=us.layer(213,0)[0],us.layer(214,0)[0];diff=a!=b;outside=(a==0)&(b>0);inside=diff&(a>0)
assert int(diff.sum())==143 and int(outside.sum())==124 and int(inside.sum())==19 and np.all(np.isin(b[diff],[8,9]))
xy=lambda mask:[{'x':int(x-160),'y':int(y-160),'index213':int(a[y,x]),'index214':int(b[y,x])}for y,x in zip(*np.nonzero(mask))]
views=[{'path':z['path'],'sha256':z['sha256'],'actually_viewed':True}for z in r['sheets']]
v=save('visual_review.json',{'actually_viewed':views,'observations':['原US213→214에서 몸/손은같은축을유지하고머리앞·뒤에회색호형효과가추가된다. Nana팔레트에서는이두호가분홍으로보인다. 얼굴앞분홍형태를새손으로해석하면안된다.','현재214의얼굴/허벅지등몸체는현재213을바탕으로같은외부효과124셀을덮은모습이다. 새별도214포즈원화가필수라는근거가아니다.'],'new_runtime_or_MIPS':False})
c=save('conclusions.json',{'scope':'기본/포스Nana214만의원US효과·역사124셀정책','technical_report_sha256':sha(O/'report.json'),'visual_review':v,'historical_source':{'script':'scripts/overhaul_ui_nova_pack.py','lines':[70,71,72,73],'parent':'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL00_U.ARC','output':'work/overhaul_20261105/ui/nana_fourth_nova_v1/PL00_U.ARC','all_10_parent_layers_original_US_exact':True,'all_10_current_layers_C04_output_exact':True},'current214_formula':{'body':'copy current213 then overlay originalUS214 at originalUS213alpha0 and214alpha1','original_effect_samples':124,'indices':[8,9],'current_body_changed':119,'same_index_already_present':5,'overwritten_current_body_cells':44,'added_alpha':80,'armor_layers':'layers5/6/7 unchanged;layer8 equals213layer8 with the124mask cleared','layer8_removed_cells':34,'body_pose_newly_different':False},'original_effect_footprint':{'all_213_to214_changed_cells':143,'new_values_only_8_9':True,'external_to_original213':124,'inside_original213_not_used_in_C04':19,'external_samples':xy(outside),'internal_samples':xy(inside),'source_parts':[{'record_index':0,'tile':7,'external_cells':60},{'record_index':2,'tile':8,'external_cells':10},{'record_index':3,'tile':9,'external_cells':54}],'whole_tile_caution':'각tile7/8/9는원X몸체도함께저장한다. 전체타일256nibble을순수효과로복사하지않는다.'},'recommended_scope':['새213 몸체를214에도쓰고입증된동일좌표124효과를연동하는것은현재수용구조와맞는다. 새214고유몸체원화를자동추가할필요는없다.','143전체를복원하는선택은현재C04외부124정책과다르다. 내부19는원X몸가림속효과표본이므로새몸에붙이는경우새정책/가림검토로분리한다.','새몸과효과겹침은현재44였다는사실만보존하며,새몸에서다시실제순서/색/부분아머를검토한다. 무조건새몸알파로외부효과를자르지않는다.'],'supersedes_provisional_wording':'nana_remaining_after_hover_read01의213/214別그림후보는구조상차이만의잠정분류였다. 이번직접출처확인으로214는213몸+역사효과파생으로세분화;기존보고불변.','candidate_or_original_modified':False,'producer_functions_called':False,'new_MIPS_or_game_run':False})
inputs=dict(r['inputs'])
for p in [Path(__file__),D/'read_nana_base_nova21401.py',O/'report.json',O/'visual_review.json',O/'conclusions.json']:inputs[rel(p)]=sha(p)
for row in views:inputs[row['path']]=row['sha256']
for p,h in inputs.items():assert sha(ROOT/p)==h,p
l=save('READER_LOCK.json',{'input_count':len(inputs),'inputs':inputs});print(json.dumps({'conclusions':c,'visual':v,'lock':l}))
