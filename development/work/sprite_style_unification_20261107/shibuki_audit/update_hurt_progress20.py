"""현재 두 ARC에서 전폼 고유표시를 다시 세고 동결/후보/실기 범위를 구분한다."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}

def main():
    o=H/'fullform_ledger20.json';need(not o.exists(),'Fresh ledger')
    j=json.loads((H/'fullform_ledger19.json').read_text('utf8'));refs=set(range(106,115))|set(range(233,237));cand={}
    for arc,folder in(('PL00_U.ARC','prepared_hurt_base01'),('PL02_U.ARC','prepared_ultimate_hurt02')):
        d=H/folder;f=d/'FROZEN.json';frozen=f.exists();r={**ev(d/arc),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen':frozen,'new_hurt_runtime_verified':False}
        lk=json.loads((d/'PREPARED_LOCK.json').read_text('utf8'))
        for n,h in lk['files'].items():need(sha((d/n).read_bytes())==h,'Prepared changed')
        if frozen:r['frozen_record']=ev(f)
        if arc=='PL00_U.ARC':r.update(integrated_build='sprite_style_unification_20261107_v17',integrated_bin_sha256='963ccbd41c71819bec1c594b0314683273972c08d85db3925a75b9599f060ea1',integration_reported_by='root',runtime_evidence=ev(H.parent/'runtime/shibuki_fourth_hurt17_summary.json'),runtime_scope='포스233..236 실제관측. 기본/106..114/모든방향/전체부분조합은 미확인.')
        else:r.update(integrated=False,native=ev(H/'ultimate_hurt_v2_components_native_checks.json'),independent=ev(H.parent/'zero_audit/shibuki_ultimate_hurt13_independent01/report.json'),sequence=ev(H/'ultimate_hurt_sequence01/report.json'),browser=ev(H/'ultimate_hurt_sequence01/browser_verification.json'))
        cand[arc]=r
    j['current_candidates']=cand
    for r in j['references']:
        arc='PL02_U.ARC'if r['form'].startswith('ultimate')else'PL00_U.ARC'
        if r['ref']in refs:
            frozen=cand[arc]['frozen'];r.update(status='new_art_frozen_for_integration'if frozen else'new_art_prepared_pending_final_review',candidate_progress={'frozen':frozen,'candidate':cand[arc],'whole_project_complete':False},decision='새4몸체와 실제부모별 효과 파생13. 원화·공통층·효과 출처/원순서/실기 근거를 별도 기록한다.')
            if frozen:r['frozen_evidence']=cand[arc]['frozen_record']
    j['ladder14_prepared_scope']['integrated']=True;j['ladder14_prepared_scope']['integrated_build']='sprite_style_unification_20261107_v16'
    j['next_generation']={'group':'Ultimate 등장','unique_body_keys':[133,135,137,138],'input_pages':[ev(H/f'ultimate_arrival_inputs01/page{i:02}/input.json')for i in(1,2)],'status':'새 기본형 수용포즈의 의상편집 입력 준비. 실제PL02 공유/효과 관계 독립조사 중. 생성 전.','generated':False,'packed':False,'preserved_refs':[0,115,116,117,118,119,141,142]}
    j['hurt13_new_scope']={'base':cand['PL00_U.ARC'],'ultimate':cand['PL02_U.ARC'],'intermediate_rejected_ultimate':'8c9a83077a6973b5ea2fff46ee3273ae281bf0d0d2190db4f67dbc792ee3e3c3','correction':'원 효과tile16을빈31로복제해111 layer5 신규U경계만제거.그림동일.','full_art_unification_complete':False}
    for name in('root_review_checkpoint103.json','root_review_checkpoint104.json','root_review_checkpoint106.json','root_review_checkpoint108.json'):j['new_root_review_evidence'].append(ev(H.parent/name))
    arcs={name:Archive((ROOT/v['path']).read_bytes())for name,v in cand.items()};buckets={};empty=[]
    for r in j['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];a=arcs['PL02_U.ARC'if form.startswith('ultimate')else'PL00_U.ARC'];mask=r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0);pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
        if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes());b=buckets.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});b['refs'].append(n);b['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);b['status_by_ref'][str(n)]=r['status'];b['groups'].add(r['group'])
    unique=[];pending=defaultdict(list);forms={}
    for _,b in sorted(buckets.items()):
        b['groups']=sorted(b['groups']);ss=set(b['status_by_ref'].values());b['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';unique.append(b)
        if ss&{'art_rework_group_pending','new_art_prepared_pending_final_review'}:
            for g in b['groups']:pending[(b['form'],g)].append(b)
    counts=Counter(r['status']for r in j['references']);j['counts']['status_counts']=dict(counts);j['counts']['new_frozen_form_images']=counts['new_art_frozen_for_integration'];j['counts']['new_prepared_form_images']=counts['new_art_prepared_pending_final_review']
    for g in j['groups']:
        g['status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==g['form']and r['ref']in g['refs']))
        g['observation_is_historical_baseline']=True;g['current_status_uses_per_reference_evidence']=True
    write(o,j)
    for form in('base','fourth','ultimate_before','ultimate_after'):
        rr=[r for r in j['references']if r['form']==form];kk=[k for k in unique if k['form']==form];forms[form]={'native_reference_slots':len(rr),'decoded_slots':sum(r['structural_decode']for r in rr),'unique_visible_art_keys':len(kk),'reference_status_counts':dict(Counter(r['status']for r in rr)),'unique_key_status_counts':dict(Counter(k['status']for k in kk))}
    u={'scope':'최신 PL0087e7/PL02b43e 실제복원한 네폼 표시 고유키. 의상/색상과 순수효과도 별도로 존재하므로 원화장수·완료율 아님.','definition':'같은폼의 불투명bbox크기와RGBA가 같은 평행이동별칭만 한키. 부분mask/선택저장사본 제외.','source_ledger':ev(o),'candidates':cand,'counts':{'visible_unique_keys':len(unique),'unique_key_status_counts':dict(Counter(k['status']for k in unique)),'reference_status_counts':dict(counts),'empty_decoded_slots':empty},'forms':forms,'keys':unique,'pending_motion_groups':[{'form':f,'group':g,'unique_keys':len(v),'refs':sorted(set(n for b in v for n in b['refs']))}for(f,g),v in sorted(pending.items())],'full_art_unification_complete':False,'no_percent_estimated':True};write(H/'unique_art_keys20.json',u);print(json.dumps(u['counts']))

if __name__=='__main__':main()
