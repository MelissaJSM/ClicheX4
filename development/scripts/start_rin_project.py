"""첫 완성본 별도 보관과 두 번째 버전 시작 상태 기록. 원본/기존 완성본은 읽기 전용."""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,working_cue,load_project,inspect_references

def main():
    first=json.loads((ROOT/'projects/ver_buki_riko/final_release.json').read_text('utf-8'))
    source=ROOT/first['directory']/'game';expected=first['bin_sha256']
    if digest(source/'shibuki_riko.bin')!=expected:raise ValueError('Accepted release hash changed')
    if digest(ROOT/'MegaMan X4.bin')!=first['source_sha256']:raise ValueError('Original changed')
    target=ROOT/'completed/ver_buki_riko/v1.0.0'
    if not target.resolve().is_relative_to(ROOT/'completed'):raise ValueError('Backup outside completed area')
    target.mkdir(parents=True,exist_ok=False)
    name='ClicheX4_Shibuki_Riko_v1.0.0'
    shutil.copy2(source/'shibuki_riko.bin',target/(name+'.bin'))
    cue=working_cue((source/'shibuki_riko.cue').read_text('ascii'),name+'.bin')
    (target/(name+'.cue')).write_text(cue,'ascii')
    if digest(target/(name+'.bin'))!=expected:raise ValueError('Backup mismatch')
    record={'version':'1.0.0','source':str(source.relative_to(ROOT)).replace('\\','/'),'bin':name+'.bin','cue':name+'.cue','bin_sha256':expected,'cue_sha256':digest(target/(name+'.cue')),'bin_bytes':(target/(name+'.bin')).stat().st_size,'byte_identical_to_user_accepted_release':True,'purpose':'시부키 / 리코 완성형 별도 보관. 나나 / 린 제작 입력으로 덮어쓰지 않음.'}
    (target/'manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf-8')
    (target/'README.txt').write_text('시부키 / 리코 모드 완성본 v1.0.0\n이 폴더의 CUE를 ePSXe에서 엽니다. BIN과 CUE를 같은 폴더에 두세요.\n상세 제작 기록: docs/FINAL_RELEASE.md\n나나 / 린 작업은 work/ver_rin_nana 및 out/ver_rin_nana에 분리합니다.\n','utf-8')
    first['standalone_backup']=target.relative_to(ROOT).as_posix()
    (ROOT/'projects/ver_buki_riko/final_release.json').write_text(json.dumps(first,ensure_ascii=False,indent=2)+'\n','utf-8')
    project=load_project(ROOT,'ver_rin_nana');refs=inspect_references(ROOT,project)
    project.update(stage='EXPANSION',active_task='zero_rin',active_substage='ART_PILOT_IN_PROGRESS',task_order=['zero_rin','x_nana','fourth_armor_nana','ultimate_armor_nana'],start_approval={'date':'2026-10-28','quote':'그러면 시부키 / 리코모드 완성형 cue 및 bin 파일을 일단 따로 저장하고나서 나나 / 린 모드를 만들러 가보자','scope':'별도 완성본 보관 후 두 번째 버전 제작 시작; 린 기준안 우선'},weapons={'nana':{'kind':'dedicated_handgun','name_ko':'사랑이','sprite':'권총을 손에 쥐고 원작 X 발사점에 총구를 맞춤','menu_weapon_name':'사랑이','menu_icon':'사랑이 권총 모양','projectile_and_charge_shot_policy':'원작 탄환·차지샷 모양/크기/이펙트/타이밍/판정 유지'},'rin':{'kind':'mop','name_ko':'대걸레','identity':'대걸레를 사용하는 메이드','attack_policy':'대걸레를 쥔 손과 짧은 자루·검기 연결부 중심. 긴 자루/솔의 별도 궤적으로 원작 검기와 충돌하지 않기','original_saber_effect_and_timing_preserved':True}},full_name_decisions_pending=True,style_approved=False)
    (ROOT/'projects/ver_rin_nana/project.json').write_text(json.dumps(project,ensure_ascii=False,indent=2)+'\n','utf-8')
    work=ROOT/'work/ver_rin_nana/art_pilot/idle_v1';work.mkdir(parents=True,exist_ok=False)
    (work/'input_verification.json').write_text(json.dumps({'references':refs,'source_sha256':project['source_sha256'],'first_release_sha256':expected,'standalone_backup':record},ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'backup':target.relative_to(ROOT).as_posix(),'sha256':expected,'references_verified':len(refs),'active_task':'zero_rin'}))

if __name__=='__main__':main()
