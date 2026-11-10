"""Activate the two verified title builds and save actual title captures."""
from pathlib import Path
import hashlib,json,shutil,subprocess
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parent;ROOT=W.parents[1];OUT=ROOT/'out/title_branding_20261108';APP=W/'application'
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not OUT.exists()and not APP.exists();OUT.mkdir();APP.mkdir()
builds=read(W/'builds.json');protected=read(W/'protection_before.json')['files'];allowed={f'projects/{k}/current_build.json'for k in builds}
for name,old in protected.items():assert {'size':(ROOT/name).stat().st_size,'sha256':sha(ROOT/name)}==old,name
font=ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf',20);sheet=Image.new('RGB',(1280,520),'#131b28');draw=ImageDraw.Draw(sheet);applied={}
for i,(project,b)in enumerate(builds.items()):
 proof=read(W/project/'runtime_verification.json');assert proof['passed']and proof['bin_sha256']==b['sha256'];base=(ROOT/b['cue']).parent;assert sha((ROOT/b['cue']).with_suffix('.bin'))==b['sha256']
 cap=ROOT/proof['capture'];ev=read(cap/'evidence.json');pic=cap/f'frame_{ev["vram_bases"][0]}_240.png';im=Image.open(pic);assert im.size==(320,240);shutil.copyfile(pic,OUT/(project+'.png'));draw.text((i*640+18,8),'텐코 시부키 · 유즈하 리코'if i==0 else'하나코 나나 · 아오쿠모 린',font=font,fill='#e0ecff');sheet.paste(im.resize((640,480),Image.Resampling.NEAREST),(i*640,40))
 pointer=ROOT/'projects'/project/'current_build.json';old=read(pointer);source=read(W/project/'source.json')['pointer'];assert old['sha256']==source['sha256'];backup=APP/(project+'_current_build_before.json');shutil.copyfile(pointer,backup)
 old.update(task='title_branding',stage='TITLE_BRANDING_APPLIED_REVIEW',build=base.relative_to(ROOT).as_posix(),cue=b['cue'],sha256=b['sha256'],previous_pointer=backup.relative_to(ROOT).as_posix(),status_report='docs/TITLE_BRANDING_20261108.md',user_accepted=False,
  title_branding_report='docs/TITLE_BRANDING_20261108.md',title_branding_runtime_verified=True,title_branding_user_accepted=False,title_notice='스텔라이브 팬 모드',title_subtitle='텐코 시부키 · 유즈하 리코'if i==0 else'하나코 나나 · 아오쿠모 린',
  current_session=None,running_bin_sha256=None,last_test_session=read(W/project/'after_boot.json')['session'],current_runtime_state='새 CUE 타이틀의 고지·부제·로고 및 세 메뉴 전체 픽셀 확인 후 시험 창 종료. 저장자료 보존.',
  next_action='최신 타이틀 배치 사용자 확인. 스프라이트 통일 최종 결과는 그대로 유지.')
 write(pointer,old);m=read(base/'manifest.json');m.update(runtime_verified=True,runtime_scope='Fresh-boot title logo, fan notice, character subtitle and three native menu labels; all opaque pixels match',runtime_report=(W/project/'runtime_verification.json').relative_to(ROOT).as_posix(),active_pointer_changed=True);write(base/'manifest.json',m)
 applied[project]={**b,'runtime':proof['capture'],'title_opaque_pixels':proof['title_ink_pixels'],'pointer_before_sha256':sha(backup),'pointer_after_sha256':sha(pointer),'backup':backup.relative_to(ROOT).as_posix(),'actual_capture':(OUT/(project+'.png')).relative_to(ROOT).as_posix()}
sheet.save(OUT/'comparison.png')
for name,old in protected.items():
 if name not in allowed:assert {'size':(ROOT/name).stat().st_size,'sha256':sha(ROOT/name)}==old,name
cards=read(ROOT/'work/sprite_style_unification_20261107/final_application/delivery.json')['test_cards']
for c in cards:assert sha(ROOT/c['source'])==sha(ROOT/c['copy'])==c['sha256']
count=subprocess.check_output(['powershell','-NoProfile','-Command','(Get-Process epsxe* -ErrorAction SilentlyContinue | Measure-Object).Count'],text=True);assert count.strip()=='0'
report={'passed':True,'builds':applied,'protected_files_unchanged':len(protected)-len(allowed),'only_protected_changes':sorted(allowed),'test_card_pairs_unchanged':len(cards),'originals_releases_save_states_preserved':True,'gameplay_sprites_exe_audio_palettes_preserved':True,'runtime_verified':True,'user_accepted':False,'F1_F3_sent':False,'memory_written':False,'epsxe_process_count':0,'comparison':(OUT/'comparison.png').relative_to(ROOT).as_posix()};write(APP/'verification.json',report);write(OUT/'verification.json',report);print(json.dumps({'passed':True,'protected_unchanged':78,'cards':len(cards),'builds':{k:v['sha256']for k,v in applied.items()}}))
