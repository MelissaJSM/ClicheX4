"""검증된 기존 실제 캡처를 복사하고 나란히 비교한다. 게임/자원 변경 없음."""
import hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'before_runtime'
OUT.mkdir(exist_ok=True)
items=[('ver_buki_riko','work/ver_buki_riko/emulator_sessions/20261105T004753040085Z_isolated_shibuki_hud/20261105T005028326206Z.png','92ab09adf0284c0581a6993c88f64b2348f4e2bdc886e4ca9df1e1bc8c2bdb50'),('ver_rin_nana','work/ver_buki_riko/emulator_sessions/20261105T005514192483Z_isolated_shibuki_hud/20261105T005831034386Z.png','8b70dbca936c2ad4d72eade207cf44f9095fb9ae05beb4e2e4943a7ba6e19768')]
report=[]
comparison=Image.new('RGB',(1600,626),(25,28,36));draw=ImageDraw.Draw(comparison)
for i,(name,source,game_sha) in enumerate(items):
    p=ROOT/source; data=p.read_bytes(); target=OUT/(name+'.png');shutil.copyfile(p,target)
    assert target.read_bytes()==data
    im=Image.open(target).convert('RGB');assert im.size==(800,600)
    comparison.paste(im,(i*800,26));draw.text((i*800+8,7),name+' | actual game capture | before',fill='white')
    session=json.loads((p.parent/'session.local.json').read_text('utf8'));assert session['bin_sha256']==game_sha
    report.append({'project':name,'source_capture':source,'capture':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'mounted_bin_sha256':game_sha,'selected_character':'left','cursor_state':'green','native_client_size':[800,600],'pixels_modified':False})
comparison.save(OUT/'both_modes.png')
(OUT/'captures.json').write_text(json.dumps({'scope':'실제 선택 화면을 무변경 복사. 비교 PNG는 라벨 영역을 덧붙여 가로로 배치한 것. 새 통일본 적용 전 화면.','captures':report,'comparison':(OUT/'both_modes.png').relative_to(ROOT).as_posix()},ensure_ascii=False,indent=2)+'\n','utf8')
runtime=ROOT/'work/hud_frame_fix_20261105/rin_optical_v9/runtime.json'
audit=json.loads((runtime.parent/'runtime_session/preservation_after.json').read_text('utf8'))
runtime.write_text(json.dumps({'passed':False,'status':'HUD_runtime_not_verified','mounted_bin_sha256':items[1][2],'capture':items[1][1],'scope':'격리된 새 부팅과 캐릭터 선택 화면까지만 실제 확인. 방향키가 선택 캐릭터 변경에 반영되지 않아 Rin HUD 표시/광학중심 실기는 미검증. 정적 검증의 성공과 구별한다.','isolated_session':'work/ver_buki_riko/emulator_sessions/20261105T005924587100Z_isolated_rin_hud','F1_or_F3_sent':False,'source_state_card_files_unchanged':audit['passed'],'protected_original_file_count':audit['protected_original_files'],'current_nana_restarted':False,'remaining_test':'후속 선택 화면 통일본에서 실제 Rin 선택 및 HUD 화면 확인'},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'comparison':str(OUT/'both_modes.png'),'runtime_report':str(runtime),'protected_files':audit['protected_original_files']}))
