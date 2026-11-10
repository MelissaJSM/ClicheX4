"""최신 PL00 후보/PL02 동결과 기존 장부의 미지정 잔여만 읽기 분류."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;N=W/'nana_audit';sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
O=D/'nana_remaining_after_hover_read01';assert not O.exists();sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();inputs={}
def read(p):
 b=p.read_bytes();inputs[rel(p)]=sha(b);return b
def js(p):return json.loads(read(p))
old=js(N/'scope_summary_v5/manifest.json');latest=js(N/'scope_summary_v27/manifest.json');coverage=js(D/'full_scope_matrix11/coverage.json')
bp=W/'root_nana_hover/packed_hover_final01/PL00_U.ARC';up=N/'ultimate_nova_repaint/packed_nova_candidate_v1/PL02_U.ARC';a=Archive(read(bp));u=Archive(read(up));assert sha(a.data)=='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c';assert sha(u.data)=='1ec00de5164827c5dd5322b93b7060e11a1afbddd26bacb23f5b585e63715195'
hv=js(bp.parent/'verification.json');assert hv['after']==sha(a.data)and hv['refs']==list(range(221,231));nova=js(up.parent/'FROZEN.json')
us=Archive(read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC',))[0]['PL00_U.ARC']);assert sha(us.data)=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a'
additions=[]
for path in('root_nana_shot85/packed_shot01','root_nana_shot87/packed_settle01'):
 p=W/path/'FROZEN.json';j=js(p);assert j['frozen'];additions.append({'path':rel(p),'sha256':sha(p.read_bytes()),'refs':j['refs'],'candidate_sha256':j['candidate_sha256']})
states={};preserves=[];PBS=(0,5,6,7,8)
for form in('base','fourth','ultimate_before','ultimate_after'):
 ar=a if form in('base','fourth')else u;mask=0 if form in('base','ultimate_after')else 15;s={q['ref']:q['decision']for q in old['frames'][form]}
 for key,status in [('frozen_full_new_art_refs','new_art_reference_frozen'),('frozen_derived_effect_refs','effect_derived_frozen'),('frozen_mirrored_refs','mirror_frozen')]:
  for n in latest['summary'][form].get(key,[]):s[n]=status
 if form.startswith('ultimate'):
  for n in(214,216):s[n]='alias_frozen'
  for n in(148,149,150,151,152,153,155):s[n]='held_unmodified_tool_refusal_or_linked'
  for n in(140,208,209,210,211,212):s[n]='effect_preservation_review_pending_no_new_body'
 else:
  for g in additions:
   for n in g['refs']:s[n]='new_art_reference_frozen'
  for n in range(221,231):s[n]='new_hover_candidate_pending_final_independent_freeze'
  for n in(213,214,215,217):s[n]='distinct_existing_body_detail_review'
  s[216]='existing_same_body_alias_215'
  for n in(218,219):s[n]='separate_effect_not_new_body'
  s[220]='mixed_shifted217_plus_effect_needs_body_sync'
  for n in(140,208,209,210,211,212):s[n]='effect_preservation_review_pending_no_new_body'
 for q in old['frames'][form]:
  n=q['ref']
  if s[n]=='preserve_reviewed':
   act=sha(ar.composite(n,mask)[0].tobytes());preserves.append({'form':form,'ref':n,'old_review_path':q['reviewed'],'old_production_stage':q['production_stage'],'current_RGBA_exact_to_old_review':act==q['rgba_sha256'],'old_RGBA_sha256':q['rgba_sha256'],'current_RGBA_sha256':act})
 grouped=collections.defaultdict(list)
 for n,state in sorted(s.items()):grouped[state].append(n)
 assert sum(map(len,grouped.values()))==237;states[form]=dict(grouped)
def shift(z,dy):
 out=np.zeros_like(z);yy,xx=np.nonzero(z);out[yy+dy,xx]=z[yy,xx];return out
nova_rows=[]
for n in range(213,221):
 ls={pb:a.layer(n,pb)[0]for pb in PBS};uls={pb:us.layer(n,pb)[0]for pb in PBS};nova_rows.append({'ref':n,'layer_opaque':{str(pb):int((z>0).sum())for pb,z in ls.items()},'layer_indices':{str(pb):np.unique(z).tolist()for pb,z in ls.items()},'original_US_layer_alpha_exact':{str(pb):bool(np.array_equal(z>0,uls[pb]>0))for pb,z in ls.items()}})
pairs=[]
for n,k in[(214,213),(216,215)]:pairs.append({'ref':n,'source':k,'layer_different_cells':{str(pb):int((a.layer(n,pb)[0]!=a.layer(k,pb)[0]).sum())for pb in PBS},'original_US_different_cells':{str(pb):int((us.layer(n,pb)[0]!=us.layer(k,pb)[0]).sum())for pb in PBS}})
sync={}
for pb in PBS:
 z=shift(a.layer(217,pb)[0],1);target=a.layer(220,pb)[0];sync[str(pb)]={'shift':[0,1],'whole_layer_exact':bool(np.array_equal(z,target)),'difference_cells':int((z!=target).sum()),'opaque_body_cells_occluded':int(((z>0)&(z!=target)).sum()),'body_opaque':int((z>0).sum())}
preserve=js(N/'ultimate_remaining_classification01/conclusions_v2.json');base_effect=[]
for n in(140,208,209,210,211,212):
 im=a.composite(n,0)[0];base_effect.append({'ref':n,'opaque':int((np.array(im)[:,:,3]>0).sum()),'layer0_indices':np.unique(a.layer(n,0)[0]).tolist(),'same_five_layers_as_ultimate':all(np.array_equal(a.layer(n,pb)[0],u.layer(n,pb)[0])for pb in PBS),'new_body_not_auto_required':True})
O.mkdir(exist_ok=False);sheets=[]
for name,ns in [('preparation',[213,214,215,216]),('strike_effects',[217,218,219,220])]:
 for form,mask in(('base',0),('fourth',15)):
  box=(100,115,250,200);cw,ch=460,290;out=Image.new('RGB',(cw*4,ch),'#253044');dr=ImageDraw.Draw(out)
  for i,n in enumerate(ns):
   im=a.composite(n,mask)[0];bb=im.getbbox();assert box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3];dr.text((i*cw+4,4),f'PL00 {form} ref{n}',fill='white');v=im.crop(box).resize((450,255),Image.Resampling.NEAREST);out.paste(v,(i*cw+4,28),v)
  p=O/f'{form}_{name}.png';out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes())})
result={'scope':'최신 Nana 잔여 원화 후보 읽기 분류. 전체 네 캐릭터 범위표 대체/품질 완료율 아님.','base_candidate':{'path':rel(bp),'sha256':sha(a.data),'frozen_at_read_time':(bp.parent/'FROZEN.json').exists()},'ultimate_frozen':{'path':rel(up),'sha256':sha(u.data)},'sources':{'scope27':rel(N/'scope_summary_v27/manifest.json'),'detailed_v5':rel(N/'scope_summary_v5/manifest.json')},'late_root_additions_missing_from_scope27_base_lists':additions,'per_form_reference_status':states,'existing_preservation_current_comparison':preserves,'base_Nova':{'actual_layers':nova_rows,'preparation_pairs':pairs,'220_relation':sync,'body_candidates':[213,214,215,217],'existing_alias':[{'ref':216,'source':215,'all5_layers_exact':True}],'separate_effect_refs':[218,219],'mixed_body_effect_refs':[220],'source_count_policy':'현재 서로 다른 준비3/돌진1 구조를 분리할 뿐 신규4원화 제작이 확정된 뜻은 아님.214를213별칭으로 바꾸려면 새 제작정책임을 별도로 결정.218/219는Ultimate실루엣공식을 복사하지 않는다.','reachability':'기존 원코드 노바 발동은 body armor bit2/에너지0x30 등 조건이므로 무아머mask0 정적판의 존재를 실제 기본형 사용으로 보지 않는다. PL00는 player+A7 그대로이며 Ultimate217강제mask15정책과 다름.'},'base_effect_preservation_review':base_effect,'remaining_priority':[{'forms':['base','fourth'],'refs':list(range(213,221)),'action':'4현재고유몸체 후보/1별칭/2별도효과/1몸효과혼합의 원출처·사용조건과 기존세부를 분리한 후 제작범위 결정'},{'forms':['ultimate_before','ultimate_after'],'refs':[148,149,150,151,152,153,155],'action':'기존 도구 거부와 연결7은 부모보존 미완료. 재시도/우회하지 않음.149151153 새몸3과 반전/사격연동을 신규7원화로 세지 않음.'},{'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':[140,208,209,210,211,212],'action':'실루엣/전환/광선 보존검토. 새 인물원화로 세지 않음. Ultimate만 현재분류 근거가 자세하며 PL00까지동일복원이라고 확대하지 않음.'}], 'preservation_not_newly_completed':['기존보존0/115..119·작은차량머리184..203(198blank)·Ultimate120..125·85/86/87/92를 미재작화라는 이유로 결함/누락으로 환산하지 않음.','126..129/132/159..161은 별도효과,105/175..182는예약/빈참조로 기존분류유지.','UI/HQ/대사/잔기는 최신선택동기화/기존root보충판 검토를 연결하며 플레이어신규원화개수에더하지않음.'],'readback_sheets':sheets,'actually_viewed':False,'new_art_created':False,'new_native_or_runtime_tests':False,'producer_functions_called':False,'inputs':inputs,'all_nana_complete':False}
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'preserve_current_mismatch':[q for q in preserves if not q['current_RGBA_exact_to_old_review']],'pair':pairs,'220':sync}))
