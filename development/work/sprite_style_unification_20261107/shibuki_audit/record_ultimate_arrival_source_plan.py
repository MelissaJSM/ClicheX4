"""현재 PL02 독립 읽기 결과와 새 원화 정책을 구분해 작업 범위를 고정한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    p=H/'ultimate_arrival_source_plan01.json';need(not p.exists(),'Fresh plan')
    a=H.parent/'zero_audit/shibuki_ultimate_arrival_relations01';need(sha((a/'report.json').read_bytes())=='3a7bee18e7625a72dc9e7f76731698b878d1c31ce730822c1f709ec7bea5e96a','Read-only source changed')
    write(p,{'parent':ev(H/'prepared_ultimate_hurt02/PL02_U.ARC'),'parent_frozen':ev(H/'prepared_ultimate_hurt02/FROZEN.json'),'independent_relation':ev(a/'report.json'),'independent_conclusions':ev(a/'conclusions.json'),'author_actually_viewed_relation_sheets':[ev(a/n)for n in('current_02.png','current_03.png')],'generated_body_keys':[133,135],'generated_status':'첫4는등록만.135후폼팔교정출력거부로미완료.이편집을다른도구/프롬프트로재시도하지않음.','blocked_local_edit_record':ev(H/'ultimate_arrival135_arms01/generation_failure.json'),'ready_other_body_inputs':[ev(H/'ultimate_arrival_inputs01/page02/input.json')],'rules':[{'refs':[126,127,128,129,132],'action':'그대로보존.132는131과동일raw소유이므로각각표시/소비타일 exact검사.'},{'refs':[130,131,134],'action':'새133몸체에따라원래각효과식으로연동.130의기존바깥3셀보정(-1..1,23)은보존.134는실제색몸체+원구체이며PL00밝기리맵을이식하지않음.'},{'refs':[135,136],'action':'136은135 y-1과동일하지않다.136의기존별도몸체를새의상/세부기준으로따로제작.단순alias로모션삭제하지않음.'},{'refs':[136,137],'action':'원번개46셀씩을아트입력에서분리하고게임후합성시좌표/flip/원색보존.현재이미지에구워진tile7이므로현재조립tile7을일괄제거하지않음.'},{'refs':[138,139],'action':'before139=before138 y-1 exact이나after는몸통/의상135px차이.두폼공통alias로단정하지않고after139를별도검토/제작한다.원표95/96소비도보호.'},{'refs':[140,141,142],'action':'현수용idle실루엣+46번개,폼별idle+12먼지,폼별idle exact관계를유지.새등장몸으로대체하지않음.'}],'shared_part_owners_to_preserve':[0,87,92,97,119,156,206],'generation_inputs_only_existing_mod_art':True,'source_game_original_not_uploaded':True,'arc_changed':False,'all_art_complete':False})
    print(sha(p.read_bytes()))
if __name__=='__main__':main()
