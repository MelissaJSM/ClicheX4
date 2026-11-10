"""귀환 동결과 BR20 승리 통합을 별도 상태로 기록한다."""
from pathlib import Path
from collections import Counter,defaultdict
import json,sys,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
 o=H/'fullform_ledger27.json';need(not o.exists(),'Fresh snapshot');j=json.loads((H/'fullform_ledger26.json').read_text('utf8'));d=H/'prepared_ultimate_return01';fr=json.loads((d/'FROZEN.json').read_text('utf8'))
 for n,h in fr['files'].items():need(sha((d/n).read_bytes())==h,'Frozen changed '+n)
 br=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v20/shibuki_riko.bin';need(sha(br.read_bytes())=='9bfd915f5e717781dd433eb291daa1aac1bad424734ad7decad69498d521598b','BR20 changed')
 j['current_candidates']['PL02_U.ARC']={**ev(d/'PL02_U.ARC'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'frozen':True,'integrated':False,'gameplay_verified':False}
 for r in j['references']:
  if r['form'].startswith('ultimate')and r['ref']in(204,205,206,207):r['candidate_progress']['integrated']=True;r['integration_evidence']=ev(br)
  if r['form'].startswith('ultimate')and r['ref']in(156,157,158):r.update(status='new_art_frozen_for_integration',frozen_evidence=ev(d/'FROZEN.json'),decision='귀환 새156 및157 새윤곽/158 역사빛 파생 동결. 독립·원MIPS·루트9판·원표164canvas 통과. 실기와 전체수용은 별도.',candidate_progress={'frozen':True,'integrated':False,'candidate':j['current_candidates']['PL02_U.ARC']})
 j['victory4_frozen_scope'].update(integrated=True,integration_evidence=ev(br));j['return3_frozen_scope']={'refs':[156,157,158],'frozen':True,'integrated':False,'final_evidence':ev(d/'final_verification.json')};j['new_root_review_evidence'].append(ev(H.parent/'root_review_checkpoint122.json'))
 old=H/'standing_special_sources02/visual_review.json';v=json.loads(old.read_text('utf8'));v['supersedes_text_only_record']=ev(old);v['text_correction_reason']='이전 기록의 한국어 관찰문이 물음표로 저장되어 새 파일에 복구했다. 이미지 및 열람 범위는 불변.'
 v['observations']=[{'refs':[85,86,87,92],'forms':'all','finding':'대기보다 큰 단색 머리 면과 단순한 소매/가슴 명암이 남는다. 85/86은 실제 서로 다른 그림이므로 별칭으로 덮지 않는다.'},{'refs':[88,89,90,91],'forms':'all','finding':'머리/흰 소매의 큰 면을 상세화해야 한다. 88의 별도 효과는 몸체와 분리해 보존한다.'},{'refs':[89,90],'forms':'ultimate_after','finding':'올린 팔에 흰 재킷 소매가 남아 수용 맨팔 의상과 다르다.'},{'refs':[95,96],'forms':'all','finding':'새138/139와 연결되는 옛 큰 단색 머리 및 평면 의상이다. 원작/현재의 평행이동 관계는 폼별로 구분한다.'},{'refs':[97],'forms':'fourth/ultimate_before/ultimate_after','finding':'포스의 흰 소매와 Ultimate 뒤다리의 검은 덩어리가 대기 재질과 다르며 구체적 수정 대상이다.'}];v['next_work']='95/97 두 자세의 기본/포스 새 그림부터 준비하고 원US 순서/손발·효과 관계를 별도 대조한다.';write(H/'standing_special_sources02/visual_review02.json',v)
 j['next_generation']={'group':'정지사격/특수85..92·95..97 네폼','review':ev(H/'standing_special_sources02/visual_review02.json'),'first_page':[95,97],'first_forms':['base','fourth'],'status':'현재44표시/12판 실제 열람. 첫95/97 새원화 입력 준비, 원US 파생/접점은 별도 읽기 중.','frozen':False,'packed':False};arcs={n:Archive((ROOT/q['path']).read_bytes())for n,q in j['current_candidates'].items()};buckets={};empty=[]
 for r in j['references']:
  if not r['structural_decode']:continue
  f,n=r['form'],r['ref'];a=arcs['PL02_U.ARC'if f.startswith('ultimate')else'PL00_U.ARC'];pix=np.array(a.composite(n,r.get('effective_render_mask',15 if f in('fourth','ultimate_before')else 0))[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
  if not len(xs):empty.append({'form':f,'ref':n,'status':r['status']});continue
  cut=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();cut[cut[:,:,3]==0]=0;k=sha(struct.pack('<HH',cut.shape[1],cut.shape[0])+cut.tobytes());b=buckets.setdefault((f,k),{'form':f,'normalized_rgba_sha256':k,'size':[cut.shape[1],cut.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});b['refs'].append(n);b['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);b['status_by_ref'][str(n)]=r['status'];b['groups'].add(r['group'])
 unique=[];pending=defaultdict(list)
 for _,b in sorted(buckets.items()):
  b['groups']=sorted(b['groups']);ss=set(b['status_by_ref'].values());b['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';unique.append(b)
  if'art_rework_group_pending'in ss:
   for g in b['groups']:pending[(b['form'],g)].append(b)
 counts=Counter(r['status']for r in j['references']);j['counts'].update(status_counts=dict(counts),new_frozen_form_images=counts['new_art_frozen_for_integration'],new_prepared_form_images=0)
 for g in j['groups']:g['status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==g['form']and r['ref']in g['refs']))
 write(o,j);forms={}
 for f in('base','fourth','ultimate_before','ultimate_after'):
  rr=[r for r in j['references']if r['form']==f];kk=[r for r in unique if r['form']==f];forms[f]={'native_reference_slots':len(rr),'decoded_slots':sum(r['structural_decode']for r in rr),'unique_visible_art_keys':len(kk),'reference_status_counts':dict(Counter(r['status']for r in rr)),'unique_key_status_counts':dict(Counter(r['status']for r in kk))}
 u={'scope':'현재 동결 PL0087e7/PL02f40f 실제 네폼 표시키. 원화 장수/품질 완료율 아님.','definition':'같은폼 불투명bbox크기와RGBA가 같은 평행이동만 한키. 부분마스크/UI 제외.','source_ledger':ev(o),'candidates':j['current_candidates'],'counts':{'visible_unique_keys':len(unique),'unique_key_status_counts':dict(Counter(r['status']for r in unique)),'reference_status_counts':dict(counts),'empty_decoded_slots':empty},'forms':forms,'keys':unique,'pending_motion_groups':[{'form':f,'group':g,'unique_keys':len(v),'refs':sorted(set(n for b in v for n in b['refs']))}for(f,g),v in sorted(pending.items())],'full_art_unification_complete':False,'no_percent_estimated':True,'integration':'승리4 BR20 통합. 새 귀환3은 동결·통합 대기이며 실기 없음.','unfinished_arrival135':'부모보존/국소편집미완료','next_unfrozen_art':j['next_generation']};write(H/'unique_art_keys27.json',u);print(json.dumps({'ledger':ev(o),'unique':ev(H/'unique_art_keys27.json'),'counts':u['counts']['unique_key_status_counts'],'keys':len(unique)}))
if __name__=='__main__':main()
