"""Activate completed local HQ builds; retain accepted releases and user progress."""
import json,shutil
from pathlib import Path
from PIL import Image
from runtime import ROOT,H,sha
from src.psx_disc import file_hash
def load(p):return json.loads(p.read_text('utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
results=load(H/'builds.json');protected=load(H/'protection_before.json')['files'];updated=set();generation=[]
for n,q in protected.items():assert file_hash(ROOT/n)==q['sha256'],n
for result in results:
 mode=result['mode'];d=H/mode;out=(ROOT/result['cue']).parent;assert file_hash(out/Path(result['cue']).with_suffix('.bin').name)==result['sha256']
 cpu=load(d/'prepared/cpu_verification.json');assert cpu['passed']
 for n,digest in cpu['archive_sha256'].items():assert file_hash(d/'prepared'/n)==digest
 assert file_hash(d/'compiled/container.bin')==cpu['container_sha256']
 mf=load(out/'manifest.json');mf['native_cpu']=cpu;save(out/'manifest.json',mf)
 shutil.copyfile(d/'prepared/cpu_verification.json',out/'review/cpu_verification.json')
 for p in H.glob('*.py'):shutil.copyfile(p,out/'review/recipe'/p.name)
 for kind in ['force','ultimate','jacket']:
  p=d/f'{kind}_generated.png';prompt=d/f'{kind}_prompt.txt';assert p.exists() and prompt.exists();im=Image.open(p)
  generation.append({'mode':mode,'costume':kind,'asset':p.relative_to(ROOT).as_posix(),'sha256':file_hash(p),'size':im.size,'image_mode':im.mode,'prompt':prompt.relative_to(ROOT).as_posix(),'prompt_sha256':file_hash(prompt),'tool':'builtin image_gen','reference_art':f'character/{mode}/'+(('nana'if mode=='ver_rin_nana'else'buki')+('(4th armor).webp'if kind=='force'else'(ultimate armor).webp')),'pose_reference':(d/'pose_reference.png').relative_to(ROOT).as_posix(),'original_references_preserved':True})
 cp=ROOT/'projects'/mode/'current_build.json';pj=cp.with_name('project.json');old=load(cp);meta=load(pj);assert old==load(d/'pointer.json');save(d/'project_before.json',meta)
 new={**old,'task':'hq_armor_20261109','stage':'HQ_ARMOR_APPLIED_USER_REVIEW','build':out.relative_to(ROOT).as_posix(),'cue':result['cue'],'sha256':result['sha256'],'previous_pointer':(d/'pointer.json').relative_to(ROOT).as_posix(),'status_report':'docs/HQ_ARMOR_20261109.md','hunter_armor_report':'docs/HQ_ARMOR_20261109.md','hunter_armor_review':(out/'review/index.html').relative_to(ROOT).as_posix(),'x_hunter_armor_outfits_implemented':True,'hunter_armor_static_verified':True,'hunter_armor_runtime_verified':False,'hunter_armor_user_accepted':False,'current_session':None,'running_bin_sha256':None,'current_runtime_state':'아머별 HQ 전신 신규 CUE 적용. 실제 장면은 사용자 확인 대기. 자동 조작 없음.','runtime_verification_scope':'아머별 HQ는 MIPS 선택19·보호15, 실제 GPU 명령216그림/모드 및 전체 BIN 재추출 검사. 실제 게임 실행은 미실행.','next_action':'새 CUE로 게임 내 카드 저장을 불러와 HQ 아머·표정·손짓·출격과 주변 UI 확인.','user_accepted':False}
 save(cp,new);meta.update(active_task=new['task'],active_substage=new['stage'],latest_integrated_build=new['build'],latest_integrated_bin_sha256=new['sha256'],hunter_armor_report=new['status_report']);save(pj,meta);updated.update([cp.relative_to(ROOT).as_posix(),pj.relative_to(ROOT).as_posix()])
for n,q in protected.items():
 if n not in updated:assert file_hash(ROOT/n)==q['sha256'],n
save(H/'generation_receipt.json',{'skill':'<LOCAL_PATH>','tool':'built-in image_gen','CLI_or_paid_API_used':False,'assets':generation,'postprocessing':'원래 4bpp 팔레트·투명 인덱스·발 기준점에 등록하고 native 조립 및 GPU 출력 검증. 저알파 배경 프린지는 제외함.'})
save(H/'application.json',{'builds':results,'protected_files_unchanged':len(protected)-len(updated),'metadata_updates':[{'file':n,'before':protected[n]['sha256'],'after':file_hash(ROOT/n)}for n in sorted(updated)],'originals_references_accepted_releases_saves_preserved':True,'emulator_keys_sent':False,'F1_F3_used':False,'process_memory_written':False,'x_hunter_armor_outfits_implemented':True,'actual_gameplay_verified':False})
print('Activated both HQ builds; protected files:',len(protected)-len(updated))
