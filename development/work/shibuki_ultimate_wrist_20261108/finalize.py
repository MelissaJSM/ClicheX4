from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from common import write,sha
from src.psx_disc import file_hash
from scripts.export_x_consistency import Archive
build=json.loads((H/'build.json').read_text('utf8'));out=ROOT/Path(build['cue']).parent;review=out/'review';a=Archive((H/'PL02_fixed.ARC').read_bytes())
j=json.loads((H/'pixel_matches.json').read_text('utf8'));occlusion=[];gd=ROOT/'work/sprite_style_unification_20261107/shibuki_audit/ultimate_dash_barrel_guard01'
for r in j['rows']:
 if not r['arm_matches']:continue
 n=r['ref'];mask=15 if r['form']=='before' else 0;src=np.array(a.composite(n,mask)[0]);allowed=np.array(Image.open(H/f'candidate/mask_{n:03}.png'))>0;arm=src.copy();arm[~allowed]=0;ab=Image.fromarray(arm).getbbox();bb=Image.fromarray(src).getbbox();f=r['arm_matches'][0];whole=src[bb[1]:bb[3],bb[0]:bb[2]]
 guard=np.array(Image.open(gd/f'{72 if n==74 else n:03}_mask.png'))>0;guard=guard[bb[1]:bb[3],bb[0]:bb[2]];dx=ab[0]-bb[0]
 if f['flip_x']:whole=whole[:,::-1];guard=guard[:,::-1];dx=bb[2]-ab[2]
 x=f['x']-dx;y=f['y']-(ab[1]-bb[1]);scene=np.array(Image.open(ROOT/f['file']).convert('RGB'));cut=scene[y:y+whole.shape[0],x:x+whole.shape[1]];diff=(whole[:,:,3]>0)&np.any(whole[:,:,:3]!=cut,axis=2);ys,xs=np.nonzero(diff)
 assert np.all(guard[diff]),'Difference outside original gun/effect boundary'
 occlusion.append({'form':r['form'],'ref':n,'file':f['file'],'body_origin':[x,y],'full_opaque':int((whole[:,:,3]>0).sum()),'matched_opaque':int((whole[:,:,3]>0).sum())-len(xs),'mismatches_in_muzzle_guard_only':len(xs),'arm_and_body_outside_gun_exact':True})
write(H/'muzzle_occlusion.json',occlusion)
for name in ['pixel_matches.json','muzzle_occlusion.json','pack.json']:shutil.copyfile(H/name,review/name)
for form in ('before','after'):
 shutil.copyfile(review/(form+'.gif'),review/('ver_buki_riko_ultimate_'+form+'.gif'))
html='''<!doctype html><meta charset="utf-8"><title>시부키 얼티밋 손목 수정 v3</title><style>body{background:#182231;color:#f0f2fa;font:17px sans-serif;margin:30px}img{max-width:100%;image-rendering:pixelated}section{margin:30px 0}</style><h1>시부키 얼티밋 대시 사격 — 손목 수정 v3</h1><p>PNG는 왼쪽 이전 수정본 / 오른쪽 이번 수정본입니다. before는 캡슐 전 재킷, after는 획득 후 의상을 뜻합니다.</p>'''
for form,title in [('before','캡슐 전 · 재킷'),('after','얼티밋 획득 후')]:
 html+=f'<section><h2>{title}</h2><img src="{form}.png"><p>수정 자세 연결 비교: 80ms 고정 간격 합성 재생이며 실제 플레이 녹화와 다릅니다.</p><img src="ver_buki_riko_ultimate_{form}.gif"><p>실제 게임에서 수정 팔 영역의 모든 불투명 픽셀이 일치한 표본</p><img src="actual_{form}.png"></section>'
(review/'index.html').write_text(html,'utf8')
runtime={}
for form in ('before','after'):
 r=json.loads((H/f'final_runtime_{form}/report.json').read_text('utf8'));assert r['bin_sha256']==build['sha256'] and r['visual_mask']==(15 if form=='before' else 0)
 runtime[form]={'session':r['session'],'engine_owned_armor':r['engine_owned_armor'],'visual_mask':r['visual_mask'],'verified_dash_shots':sorted({q['frame'] for q in r['frames'] if q['verified'] and q['frame'] in (68,70,72,74,76,78,80,84)}),'keys_only_no_state_or_memory_write':True}
manifest=json.loads((out/'manifest.json').read_text('utf8'));manifest.update(runtime_verified=True,runtime_scope='캡슐 전/후 실제 진입과 대표 대시 사격 RAM/VRAM 및 팔 픽셀 확인. 모든 프레임 실기 전수 검사는 아님.',runtime=runtime,review='review/index.html');write(out/'manifest.json',manifest)
p=ROOT/'projects/ver_buki_riko/current_build.json';old=json.loads(p.read_text('utf8'));source=json.loads((H/'source.json').read_text('utf8'));assert old['sha256']=='40630dbd3415245765e4bf39882f17a609bbe8bc9c94b518b35e38d976b65f80';write(H/'current_build_before_v3.json',old)
assert file_hash(ROOT/Path(build['cue']).with_suffix('.bin'))==build['sha256']
new={**old,'task':'shibuki_ultimate_wrist','stage':'ULTIMATE_WRIST_V3_APPLIED_REVIEW','build':out.relative_to(ROOT).as_posix(),'cue':build['cue'],'sha256':build['sha256'],'previous_pointer':(H/'current_build_before_v3.json').relative_to(ROOT).as_posix(),'status_report':'docs/SHIBUKI_ULTIMATE_WRIST_20261108.md','ultimate_wrist_report':'docs/SHIBUKI_ULTIMATE_WRIST_20261108.md','ultimate_wrist_review':(review/'index.html').relative_to(ROOT).as_posix(),'current_session':None,'running_bin_sha256':None,'current_runtime_state':'최신 CUE로 얼티밋 캡슐 전/후 정상 카드 로드 및 대시 사격 확인 후 시험 창 종료.','runtime_verification_scope':'이번 시부키 얼티밋 전/후의 대표 대시 사격 actual RAM/VRAM과 팔 영역 픽셀 확인. 모든 중간 프레임 실기 전수 검사 아님. 이전 기본형·린·나나 검사 이력은 기존 보고서에 유지.','next_action':'새 CUE와 수정 v3 비교 페이지에서 얼티밋 전/후 손·버스터 연결 사용자 확인.','user_accepted':False}
write(p,new)
project=ROOT/'projects/ver_buki_riko/project.json';meta=json.loads(project.read_text('utf8'));write(H/'project_before_v3.json',meta);meta.update(active_task='shibuki_ultimate_wrist',active_substage='ULTIMATE_WRIST_V3_APPLIED_REVIEW',latest_integrated_build=new['build'],latest_integrated_bin_sha256=new['sha256'],ultimate_wrist_report=new['ultimate_wrist_report']);write(project,meta)
protected=json.loads((H/'protection_before.json').read_text('utf8'))['files'];authorized={p.relative_to(ROOT).as_posix(),project.relative_to(ROOT).as_posix()};unchanged=0;updates=[]
for name,r in protected.items():
 now=file_hash(ROOT/name)
 if name in authorized:updates.append({'path':name,'before':r['sha256'],'after':now})
 else:assert now==r['sha256'],name;unchanged+=1
cards={}
for name,source in [('after','work/ver_rin_nana/sprite_style_checkpoint9/cards/nana_allboss.mcr'),('before','work/ver_rin_nana/sprite_style_checkpoint52/cards/preultimate.mcr')]:
 path=ROOT/f'work/ver_buki_riko/ultimate_wrist_20261108/cards/{name}.mcr';assert file_hash(path)==file_hash(ROOT/source);cards[name]=file_hash(path)
write(H/'application.json',{'new_build':build,'protected_files_unchanged':unchanged,'authorized_metadata_updates':updates,'test_cards_unchanged':cards,'runtime':runtime,'nana_rin_pointer_and_bin_preserved':True,'original_and_final_release_preserved':True})
older=ROOT/'out/motion_fixes_20261108_review/index.html';s=older.read_text('utf8');notice='<p><strong>시부키 얼티밋 두 의상의 대시 사격은 후속 수정 v3가 있습니다.</strong> <a href="../ver_buki_riko/ultimate_wrist_20261108_v3/review/index.html">최신 비교와 실제 화면 보기</a></p>'
if notice not in s:older.write_text(s.replace('<h1>',notice+'<h1>',1),'utf8')
print('applied; protected unchanged',unchanged,'metadata updates',len(updates),'muzzle-only differences',[(r['form'],r['ref'],r['mismatches_in_muzzle_guard_only']) for r in occlusion])
