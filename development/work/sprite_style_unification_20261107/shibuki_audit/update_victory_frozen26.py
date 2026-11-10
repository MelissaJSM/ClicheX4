"""승리4 동결 범위와 별도미완료 귀환 후보를 실제 고유표시 장부에 기록."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
 o=H/'fullform_ledger26.json';need(not o.exists(),'Fresh ledger');j=json.loads((H/'fullform_ledger25.json').read_text('utf8'));d=H/'prepared_ultimate_victory01';fr=json.loads((d/'FROZEN.json').read_text('utf8'))
 for n,h in fr['files'].items():need(sha((d/n).read_bytes())==h,'Frozen changed')
 j['current_candidates']['PL02_U.ARC']={**ev(d/'PL02_U.ARC'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'frozen':True,'integrated':False,'gameplay_verified':False}
 for r in j['references']:
  if r['form'].startswith('ultimate')and r['ref']in(204,205,206,207):r.update(status='new_art_frozen_for_integration',frozen_evidence=ev(d/'FROZEN.json'),decision='새승리4 동결.원화/20층/독립/원MIPS/루트10판/원표202canvas 통과.실기/전체수용은별도.',candidate_progress={'frozen':True,'integrated':False,'candidate':j['current_candidates']['PL02_U.ARC']})
 j['victory4_frozen_scope']=j['next_generation'];j['victory4_frozen_scope'].update(frozen=True,integrated=False,final_evidence=ev(d/'final_verification.json'));j['new_root_review_evidence'].append(ev(H.parent/'root_review_checkpoint118.json'));j['next_generation']={'group':'Ultimate 정면귀환156..158','source_art':ev(H/'ultimate_return_inputs01/generated.png'),'first_native':ev(H/'ultimate_return_native01/report.json'),'pose_inspection':ev(H/'ultimate_return_pose_inspection01/report.json'),'relations':ev(H.parent/'zero_audit/shibuki_ultimate_return_relations01/report.json'),'status':'156양폼 첫새원화/고정등록.손끝 안쪽약3px·아래1px,발 앞뒤높이 차이가 없어 팔다리 국소재작화필요.현재미수용·미패킹.157옛가림을새몸에복사하지않고새윤곽정책,158역사빛식으로후속예정.','frozen':False,'packed':False}
 arcs={n:Archive((ROOT/q['path']).read_bytes())for n,q in j['current_candidates'].items()};buckets={};empty=[]
 for r in j['references']:
  if not r['structural_decode']:continue
  form,n=r['form'],r['ref'];a=arcs['PL02_U.ARC'if form.startswith('ultimate')else'PL00_U.ARC'];pix=np.array(a.composite(n,r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0))[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
  if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
  cut=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();cut[cut[:,:,3]==0]=0;key=sha(struct.pack('<HH',cut.shape[1],cut.shape[0])+cut.tobytes());b=buckets.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[cut.shape[1],cut.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});b['refs'].append(n);b['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);b['status_by_ref'][str(n)]=r['status'];b['groups'].add(r['group'])
 unique=[];pending=defaultdict(list)
 for _,b in sorted(buckets.items()):
  b['groups']=sorted(b['groups']);ss=set(b['status_by_ref'].values());b['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';unique.append(b)
  if'art_rework_group_pending'in ss:
   for g in b['groups']:pending[(b['form'],g)].append(b)
 counts=Counter(r['status']for r in j['references']);j['counts'].update(status_counts=dict(counts),new_frozen_form_images=counts['new_art_frozen_for_integration'],new_prepared_form_images=0)
 for g in j['groups']:g['status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==g['form']and r['ref']in g['refs']))
 j.pop('counts_unchanged_from24',None);j.pop('frozen_counts_note',None);write(o,j);forms={}
 for form in('base','fourth','ultimate_before','ultimate_after'):
  rr=[r for r in j['references']if r['form']==form];kk=[r for r in unique if r['form']==form];forms[form]={'native_reference_slots':len(rr),'decoded_slots':sum(r['structural_decode']for r in rr),'unique_visible_art_keys':len(kk),'reference_status_counts':dict(Counter(r['status']for r in rr)),'unique_key_status_counts':dict(Counter(r['status']for r in kk))}
 u={'scope':'현재동결PL0087e7/PL02ec7a 실제 네폼 표시키.원화장수/품질완료율 아님.','definition':'같은폼의 불투명bbox크기와RGBA가같은 평행이동만 한키.부분마스크/UI사본 제외.','source_ledger':ev(o),'candidates':j['current_candidates'],'counts':{'visible_unique_keys':len(unique),'unique_key_status_counts':dict(Counter(r['status']for r in unique)),'reference_status_counts':dict(counts),'empty_decoded_slots':empty},'forms':forms,'keys':unique,'pending_motion_groups':[{'form':form,'group':g,'unique_keys':len(v),'refs':sorted(set(n for b in v for n in b['refs']))}for(form,g),v in sorted(pending.items())],'full_art_unification_complete':False,'no_percent_estimated':True,'integration':'승리4는BR20통합대기.통합/실기 확인 전 상태를구분.','unfinished_arrival135':'부모보존/국소편집미완료','next_unfrozen_art':j['next_generation']};write(H/'unique_art_keys26.json',u);print(json.dumps({'ledger':ev(o),'unique':ev(H/'unique_art_keys26.json'),'counts':u['counts']['unique_key_status_counts'],'keys':len(unique)}))
if __name__=='__main__':main()
