"""Publish verified local pointers and review artifacts; user performs scene checks."""
from pathlib import Path
import sys,json,shutil,html,struct
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from src.psx_disc import file_hash
def load(p):return json.loads(p.read_text('utf8'))
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
builds=load(H/'builds.json');protected=load(H/'protection_before.json')['files']
authorized={f'projects/{m}/{n}.json'for m in builds for n in ['current_build','project']}
for n,q in protected.items():assert file_hash(ROOT/n)==q['sha256'],n
assert load(H/'static_verification.json')['passed']
assert load(H/'cpu_verification.json')['cases']==96
session=ROOT/'work/ver_rin_nana/emulator_sessions/20261108T120550218574Z'
assert load(session/'close.local.json')['exited']
capture=ROOT/'work/ver_rin_nana/korean_runtime/20261108T120658337970Z'
evidence=load(capture/'evidence.json');ram=(capture/f"ram_{evidence['ram_bases'][0]}.bin").read_bytes()
assert ram[0x22954:0x229a0]==(H/'selector_new.bin').read_bytes()
assert ram[0x172203]==0 and ram[0x172207]==15 and ram[0x1721f7]==0
runtime={'project':'ver_rin_nana','session':session.relative_to(ROOT).as_posix(),'bin_sha256':builds['ver_rin_nana']['sha256'],'fresh_boot':True,'normal_memory_card_load':True,'loaded_armor':15,'loaded_ultimate_flag':0,'actual_RAM_selector_exact':True,'dialogue_portrait_observed':False,'complete_scene_check':False,'handoff':'사용자가 대화 장면 확인을 맡겠다고 제안하여 자동 조작 종료','F1_F3_used':False,'process_memory_written':False,'test_emulator_closed':True,'evidence':(capture/'evidence.json').relative_to(ROOT).as_posix()}
write(H/'runtime_verification.json',runtime)
cards={}
for m in builds:
 for name,src in [('after','work/ver_buki_riko/ultimate_wrist_20261108/cards/after.mcr'),('fourth','work/ver_rin_nana/sprite_style_checkpoint49/cards/fourth.mcr'),('before','work/ver_buki_riko/ultimate_wrist_20261108/cards/before.mcr')]:
  path=ROOT/f'work/{m}/armor_dialogue_20261108/cards/{name}.mcr';assert file_hash(path)==file_hash(ROOT/src);cards[path.relative_to(ROOT).as_posix()]=file_hash(path)
labels=['기본형','포스 머리 파츠','포스 몸 파츠','포스 머리＋몸','얼티밋 캡슐 전 · 재킷','얼티밋 획득 후 · 수영복']
pairs=[(0,4),(1,5),(2,6),(3,7),(8,10),(9,11)]
generation=[]
for m,b in builds.items():
 h=H/m;out=ROOT/Path(b['cue']).parent;review=out/'review';name='텐코 시부키'if m=='ver_buki_riko'else'하나코 나나'
 assert file_hash(ROOT/Path(b['cue']).with_suffix('.bin'))==b['sha256']
 current=ROOT/f'projects/{m}/current_build.json';project=ROOT/f'projects/{m}/project.json';old=load(current);meta=load(project)
 assert old==load(h/'audit.json')['pointer']
 for i,((closed,opened),label)in enumerate(zip(pairs,labels)):
  frames=[]
  for n in [closed,opened,closed]:
   im=Image.open(review/f'{n:02}.png').convert('RGBA');bg=Image.new('RGB',im.size,(32,40,55));bg.paste(im,mask=im.getchannel('A'));frames.append(bg.resize((336,288),Image.Resampling.NEAREST))
  frames[0].save(review/f'variant_{i}.gif',save_all=True,append_images=frames[1:],duration=[1100,240,300],loop=0,optimize=False)
 receipts=[]
 mapping=[('ultimate_prompt.txt','ultimate_generated.png')]
 if m=='ver_rin_nana':mapping.insert(0,('force_prompt.txt','force_generated.png'))
 else:mapping.extend([('fill_prompt.txt','ultimate_filled.png'),('right_fill_prompt.txt','after_filled.png')])
 for prompt,img in mapping:
  receipts.append({'mode':'built_in_image_gen','prompt':(h/prompt).relative_to(ROOT).as_posix(),'prompt_sha256':file_hash(h/prompt),'generated':(h/img).relative_to(ROOT).as_posix(),'generated_sha256':file_hash(h/img),'size':list(Image.open(h/img).size)})
  shutil.copyfile(h/prompt,review/prompt)
 generation.extend(receipts);write(review/'generation_receipt.json',{'mode':'built_in_image_gen','CLI_used':False,'palette_and_registration':'accepted face / existing palette / closed-open mouth deltas retained','images':receipts})
 intro='기존 기본형과 포스아머 8그림은 픽셀 그대로 보존하고 얼티밋 4그림을 추가했습니다.'if m=='ver_buki_riko'else'기본형 얼굴을 보존하고 포스아머 머리·몸 조합과 얼티밋 캡슐 전·후 의상을 추가했습니다.'
 page=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>{name} 아머별 대화 초상화</title><style>body{{background:#182231;color:#eef2fa;font:17px/1.65 sans-serif;margin:28px;max-width:1500px}}a{{color:#aadeff}}img{{max-width:100%;image-rendering:pixelated}}.grid{{display:flex;gap:22px;flex-wrap:wrap}}figure{{margin:0}}pre{{white-space:pre-wrap}}details{{margin:24px 0}}</style><h1>{name} · 아머별 대화 초상화</h1><p>{intro}</p><p>아래 GIF는 입 모양 비교용 합성 미리보기입니다. GIF의 속도는 게임의 대화 시간표가 아닙니다. 게임의 입 움직임 시간표는 유지했습니다.</p><p><a href="../{Path(b['cue']).name}">새 CUE</a> · <a href="../../../../docs/ARMOR_DIALOGUE_20261108.md">검증·미확인 범위</a></p><p>대화창의 얼굴·상반신 그림만 대상으로 합니다. 헌터베이스 전신 그림은 이번 수정에 포함되지 않습니다. 실제 대화 장면 확인은 사용자에게 넘겼습니다.</p><div class="grid">'''
 for i,label in enumerate(labels):page+=f'<figure><figcaption>{label}</figcaption><img src="variant_{i}.gif" width="336" height="288"></figure>'
 page+='</div><details><summary>모든 12그림</summary><img src="all12.png"></details><details><summary>수정 이전 8그림</summary><img src="previous8.png"></details><details><summary>제작 프롬프트 · 내장 image_gen 사용</summary>'
 for prompt,_ in mapping:page+=f'<h3>{prompt}</h3><pre>{html.escape((h/prompt).read_text("utf8"))}</pre>'
 page+='</details></html>';(review/'index.html').write_text(page,'utf8')
 for n in ['audit.py','prepare.py','verify_cpu.py','build.py','native_nana.py','native_shibuki.py']:
  dest=review/'recipe';dest.mkdir(exist_ok=True);shutil.copyfile(H/n,dest/n)
 shutil.copyfile(H/'static_verification.json',review/'static_verification.json')
 scope='96상태 MIPS 선택 코드·12그림×9텍스처 복사본·비대상 바이트 보존 검증. 실제 대화 그림/입 움직임 관찰은 사용자 확인 대기.'
 if m=='ver_rin_nana':scope+=' 새 CUE 부팅·포스아머 정상 카드 불러오기·실제 RAM 선택 코드 일치 확인.'
 manifest=load(out/'manifest.json');manifest.update(review='review/index.html',runtime_verified=False,portrait_scene_runtime_verified=False,runtime_scope=scope,boot_verified=(m=='ver_rin_nana'),user_accepted=False);write(out/'manifest.json',manifest)
 write(h/'current_build_before.json',old);write(h/'project_before.json',meta)
 new={**old,'task':'armor_dialogue_20261108','stage':'ARMOR_DIALOGUE_APPLIED_USER_REVIEW','build':out.relative_to(ROOT).as_posix(),'cue':b['cue'],'sha256':b['sha256'],'previous_pointer':(h/'current_build_before.json').relative_to(ROOT).as_posix(),'status_report':'docs/ARMOR_DIALOGUE_20261108.md','armor_dialogue_report':'docs/ARMOR_DIALOGUE_20261108.md','armor_dialogue_review':(review/'index.html').relative_to(ROOT).as_posix(),'armor_dialogue_runtime_verified':False,'current_session':None,'running_bin_sha256':None,'current_runtime_state':'시험 창 종료. 새 CUE와 게임 내 카드로 대화 장면 사용자 확인 대기.','runtime_verification_scope':scope,'next_action':'나나 포스아머·두 캐릭터 얼티밋 캡슐 전/후 대화 그림과 입 움직임 사용자 확인. 헌터베이스 전신 자산은 별도 범위.','user_accepted':False}
 if m=='ver_rin_nana':new['last_test_session']=runtime['session']
 write(current,new);meta.update(active_task=new['task'],active_substage=new['stage'],latest_integrated_build=new['build'],latest_integrated_bin_sha256=new['sha256'],armor_dialogue_report=new['armor_dialogue_report']);write(project,meta)
write(H/'generation_receipt.json',{'mode':'built_in_image_gen','CLI_used':False,'images':generation})
for n,q in protected.items():
 if n not in authorized:assert file_hash(ROOT/n)==q['sha256'],n
write(H/'application.json',{'builds':builds,'protected_files_unchanged':len(protected)-len(authorized),'authorized_metadata_updates':[{'path':n,'before':protected[n]['sha256'],'after':file_hash(ROOT/n)}for n in sorted(authorized)],'test_cards_unchanged':cards,'original_and_final_releases_preserved':True,'user_scene_check_pending':True,'test_emulator_closed':True,'F1_F3_used':False,'process_memory_written':False})
print(json.dumps({'applied':builds,'protected_files_unchanged':len(protected)-len(authorized),'scene_verification':'user_pending'}))
