"""8참조 동결 후 실제 네폼 표시 키를 재집계.135와 다음승리 후보는 미완료."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
 o=H/'fullform_ledger24.json';need(not o.exists(),'Fresh ledger');j=json.loads((H/'fullform_ledger23.json').read_text('utf8'));d=H/'prepared_ultimate_arrival_partial01';f=d/'FROZEN.json';fr=json.loads(f.read_text('utf8'))
 for n,h in fr['files'].items():need(sha((d/n).read_bytes())==h,'Frozen asset changed')
 refs=set(fr['selected_visual_refs']);j['current_candidates']['PL02_U.ARC']={**ev(d/'PL02_U.ARC'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen_record':ev(f),'final_verification':ev(d/'final_verification.json'),'frozen':True,'integrated':False,'gameplay_verified':False}
 for r in j['references']:
  if r['form'].startswith('ultimate')and r['ref']in refs:r.update(status='new_art_frozen_for_integration',frozen_evidence=ev(f),decision='별도 새5몸체와 원효과 포함8참조 동결.135 부모/132공유/0·141·142 보존.독립/원MIPS/root16판/원표406canvas 통과,실기와 사용자 전체수용은 별도.',candidate_progress={'frozen':True,'integrated':False,'candidate':j['current_candidates']['PL02_U.ARC']})
  elif r['form'].startswith('ultimate')and r['ref']==135:r.update(decision='국소 편집 도구 거부 후 재시도하지 않았으며 부모 그림 그대로 보존한 미완료 참조.',status='art_rework_group_pending')
 j['arrival8_frozen_scope']={**j['next_generation'],'frozen':True,'integrated':False,'final_evidence':ev(d/'final_verification.json')};j['new_root_review_evidence'].append(ev(H.parent/'root_review_checkpoint116.json'));j['next_generation']={'group':'Ultimate 승리204..207·정면귀환156..158','first_page':ev(H/'ultimate_victory_inputs01/page01/generated.png'),'first_registration':ev(H/'ultimate_victory_native01/report.json'),'local204_bent_arm':ev(H/'ultimate_victory204_arm01/generated.png'),'status':'첫204/205×전후4 고정등록.후폼204 앞팔 국소 새 원화까지 저장,공통머리/사지·등록·패킹 전.206/207과귀환은 미생성.','frozen':False,'packed':False}
 arcs={n:Archive((ROOT/q['path']).read_bytes())for n,q in j['current_candidates'].items()};buckets={};empty=[]
 for r in j['references']:
  if not r['structural_decode']:continue
  form,n=r['form'],r['ref'];a=arcs['PL02_U.ARC'if form.startswith('ultimate')else'PL00_U.ARC'];pix=np.array(a.composite(n,r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0))[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
  if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
  crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes());b=buckets.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});b['refs'].append(n);b['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);b['status_by_ref'][str(n)]=r['status'];b['groups'].add(r['group'])
 unique=[];pending=defaultdict(list);forms={}
 for _,b in sorted(buckets.items()):
  b['groups']=sorted(b['groups']);ss=set(b['status_by_ref'].values());b['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';unique.append(b)
  if'art_rework_group_pending'in ss:
   for g in b['groups']:pending[(b['form'],g)].append(b)
 counts=Counter(r['status']for r in j['references']);j['counts'].update(status_counts=dict(counts),new_frozen_form_images=counts['new_art_frozen_for_integration'],new_prepared_form_images=0)
 for g in j['groups']:g['status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==g['form']and r['ref']in g['refs']))
 j.pop('counts_unchanged_from21',None);j.pop('counts_unchanged_from22',None);write(o,j)
 for form in('base','fourth','ultimate_before','ultimate_after'):
  rr=[r for r in j['references']if r['form']==form];kk=[k for k in unique if k['form']==form];forms[form]={'native_reference_slots':len(rr),'decoded_slots':sum(r['structural_decode']for r in rr),'unique_visible_art_keys':len(kk),'reference_status_counts':dict(Counter(r['status']for r in rr)),'unique_key_status_counts':dict(Counter(k['status']for k in kk))}
 u={'scope':'현재 동결PL0087e7/PL023e55 실제 네폼 표시 키.원화장수/품질완료율 아님.','definition':'같은폼의 불투명bbox크기와RGBA가 같은 평행이동만 한키.부분마스크/UI사본 제외.','source_ledger':ev(o),'candidates':j['current_candidates'],'counts':{'visible_unique_keys':len(unique),'unique_key_status_counts':dict(Counter(k['status']for k in unique)),'reference_status_counts':dict(counts),'empty_decoded_slots':empty},'forms':forms,'keys':unique,'pending_motion_groups':[{'form':form,'group':g,'unique_keys':len(v),'refs':sorted(set(n for b in v for n in b['refs']))}for(form,g),v in sorted(pending.items())],'full_art_unification_complete':False,'no_percent_estimated':True,'integration':'현재BR18실제자원과별개로PL02등장8은BR19통합대기','unfinished_arrival135':'부모보존/국소편집미완료','next_unfrozen_art':j['next_generation']};write(H/'unique_art_keys24.json',u);print(json.dumps({'ledger':ev(o),'unique':ev(H/'unique_art_keys24.json'),'counts':u['counts']['unique_key_status_counts'],'visible_unique_keys':len(unique)}))
if __name__=='__main__':main()
