"""Activate the seam fix while leaving HQ/Black expansion explicitly pending."""
from pathlib import Path
import sys,json,shutil,html
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from src.psx_disc import file_hash
def load(p):return json.loads(p.read_text('utf8'))
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
b=load(H/'build.json');out=ROOT/Path(b['cue']).parent;assert file_hash(ROOT/Path(b['cue']).with_suffix('.bin'))==b['sha256']
protected=load(H/'protection_before.json')['files'];updates={'projects/ver_rin_nana/current_build.json','projects/ver_rin_nana/project.json'}
for n,q in protected.items():assert file_hash(ROOT/n)==q['sha256'],n
review=out/'review';review.mkdir(exist_ok=False)
for name in ['prompt.txt','all_forms_audit.json','shibuki_all_join_audit.png']:shutil.copyfile(H/name,review/name)
shutil.copyfile(H/'native_v2/review.png',review/'all12.png')
shutil.copyfile(ROOT/'work/armor_dialogue_20261108/ver_rin_nana/native_proposal/review.png',review/'previous12.png')
shutil.copyfile(ROOT/'work/armor_dialogue_20261108/ver_buki_riko/native_proposal/review.png',review/'shibuki_audited12.png')
shutil.copyfile(H/'packed_rn_v3/verification.json',review/'packing_verification.json')
for n in range(12):shutil.copyfile(H/f'native_v2/{n:02}.png',review/f'{n:02}.png')
generation={'mode':'built_in_image_gen','CLI_used':False,'edit_target':'work/nana_dialogue_hair_20261108/edit_target.png','prompt':'work/nana_dialogue_hair_20261108/prompt.txt','generated':'work/nana_dialogue_hair_20261108/generated.png','generated_sha256':file_hash(H/'generated.png'),'native_registration':'register_v2.py; common body repair; veil behind preserved foreground hair; unchanged base and Ultimate portraits'}
write(H/'generation_receipt.json',generation);write(review/'generation_receipt.json',generation)
labels=['기본형 보존','머리 파츠','몸 파츠','포스 완전 장착','얼티밋 캡슐 전 보존','얼티밋 획득 후 보존']
for i,(closed,opened)in enumerate([(0,4),(1,5),(2,6),(3,7),(8,10),(9,11)]):
 frames=[]
 for n in [closed,opened,closed]:
  im=Image.open(review/f'{n:02}.png').convert('RGBA');bg=Image.new('RGB',im.size,(32,40,55));bg.paste(im,mask=im.getchannel('A'));frames.append(bg.resize((336,288),0))
 frames[0].save(review/f'variant_{i}.gif',save_all=True,append_images=frames[1:],duration=[1000,240,300],loop=0,optimize=False)
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>나나 파츠 조합 연결 수정 · 시부키 전체 점검</title><style>body{background:#182231;color:#eef2fa;font:17px/1.65 sans-serif;margin:28px;max-width:1500px}a{color:#aadeff}img{max-width:100%;image-rendering:pixelated}.grid{display:flex;flex-wrap:wrap;gap:22px}figure{margin:0}pre{white-space:pre-wrap}</style><h1>나나 파츠 조합의 그림 연결 수정</h1><p>머리카락만이 아니라 얼굴 주변·목·어깨·옷깃 연결을 점검했습니다. 얼굴을 사각형으로 덮거나 목 높이에서 머리카락을 잘라 붙이지 않도록 조립을 수정했습니다. 기본형과 얼티밋 그림은 그대로 보존했습니다.</p><p>아래 GIF는 합성 비교용이며 실제 게임의 말하기 속도가 아닙니다. 새 그림의 실제 대화 장면은 사용자 확인 대기입니다.</p><p><a href="../rin_nana.cue">수정 CUE</a> · <a href="../../../../docs/ILLUSTRATION_ARMOR_BLACK_20261108.md">변경·검사·헌터베이스/블랙 후속 범위</a></p><div class="grid">'''
for i,label in enumerate(labels):page+=f'<figure><figcaption>{label}</figcaption><img src="variant_{i}.gif"></figure>'
page+='</div><h2>수정 이전</h2><img src="previous12.png"><h2>시부키 전체 점검</h2><p>12그림을 모두 복원했습니다. 기본형과 포스 완전 장착은 기존 전체 원화와 픽셀이 일치하며, 현재 정적 이미지에서 나나와 같은 사각 잘림은 확인하지 못했습니다. 실제 모든 장면의 무결함을 뜻하지 않습니다. 시부키 BIN은 이번 연결 수정에서 변경하지 않았습니다.</p><img src="shibuki_audited12.png"><details><summary>제작 프롬프트 · 내장 image_gen</summary><pre>'+html.escape((H/'prompt.txt').read_text('utf8'))+'</pre></details></html>'
(review/'index.html').write_text(page,'utf8')
cp=ROOT/'projects/ver_rin_nana/current_build.json';pj=ROOT/'projects/ver_rin_nana/project.json';old=load(cp);meta=load(pj);assert old==load(H/'packed_rn_v3/verification.json')['pointer']
write(H/'current_build_before.json',old);write(H/'project_before.json',meta)
new={**old,'task':'illustration_armor_black_20261108','stage':'DIALOGUE_SEAMS_APPLIED_HQ_BLACK_INVESTIGATION','build':out.relative_to(ROOT).as_posix(),'cue':b['cue'],'sha256':b['sha256'],'status_report':'docs/ILLUSTRATION_ARMOR_BLACK_20261108.md','previous_pointer':(H/'current_build_before.json').relative_to(ROOT).as_posix(),'armor_dialogue_seam_report':'docs/ILLUSTRATION_ARMOR_BLACK_20261108.md','armor_dialogue_seam_review':(review/'index.html').relative_to(ROOT).as_posix(),'armor_dialogue_runtime_verified':False,'current_session':None,'running_bin_sha256':None,'current_runtime_state':'ユーザー実機確認待ち','runtime_verification_scope':'나나 파츠 조합 6그림 수정.12그림×9텍스처와 NPC·대화창 정적 복원 통과. 이번 수정본의 실제 대화 장면은 사용자 확인 대기.','next_action':'나나 파츠 연결 사용자 확인. 두 캐릭터 헌터베이스 아머 의상과 블랙 린·리코의 HQ/대화 표시 분리 조사 계속.','user_accepted':False}
new['current_runtime_state']='사용자 실기 확인 대기. 자동 게임 조작 없음.'
write(cp,new);meta.update(active_task=new['task'],active_substage=new['stage'],latest_integrated_build=new['build'],latest_integrated_bin_sha256=new['sha256'],armor_dialogue_seam_report=new['status_report']);write(pj,meta)
manifest=load(out/'manifest.json');manifest.update(review='review/index.html',scene_verification='user_pending',shibuki_current_build_unchanged=True,hunter_base_changed=False,black_portraits_changed=False);write(out/'manifest.json',manifest)
for n,q in protected.items():
 if n not in updates:assert file_hash(ROOT/n)==q['sha256'],n
write(H/'application.json',{'build':b,'protected_files_unchanged':len(protected)-len(updates),'authorized_metadata_updates':[{'file':n,'before':protected[n]['sha256'],'after':file_hash(ROOT/n)}for n in sorted(updates)],'shibuki_riko_pointer_preserved':True,'F1_F3_used':False,'runtime_inputs_sent':False,'user_review_pending':True,'HQ_and_Black_expansion_pending':True})
print(json.dumps({'applied':b,'protected_files_unchanged':len(protected)-len(updates)}))
