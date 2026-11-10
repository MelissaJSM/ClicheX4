"""기본85..92 동결과 Ultimate 국소 진행을 실제 최신 표시로 재집계."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    need(not(H/'fullform_ledger31.json').exists(),'새 장부 필요');q=json.loads((H/'fullform_ledger30.json').read_text('utf8'));d=H/'prepared_standing_fire_base01';f=json.loads((d/'FROZEN.json').read_text('utf8'));p=d/'PL00_U.ARC';need(f['frozen']and sha(p.read_bytes())==f['candidate_sha256'],'동결 확인')
    q['current_candidates']['PL00_U.ARC']={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'frozen':True,'integrated':False,'integration_planned_by_root':'BR23','gameplay_verified':False}
    arcs={'base':Archive(p.read_bytes()),'ultimate':Archive((ROOT/q['current_candidates']['PL02_U.ARC']['path']).read_bytes())}
    q['standing_fire8_frozen_scope']={'refs':list(range(85,93)),'display_refs_twoforms':16,'target_layers':40,'storage_only_refs':f['storage_only_refs'],'root_review':ev(H.parent/'root_review_checkpoint135.json'),'root_actual_plates':12,'independent':ev(H.parent/'zero_audit/shibuki_standing_fire8_independent01/report.json'),'native_directory':ev(H.parent/'zero_audit/shibuki_standing_fire_directory_native01/report.json'),'all_graphics_bank_boundaries_preserved':True,'no_art_reduced':True,'selection1_8_sync_pending':True,'integration':False,'runtime':False}
    q['next_generation']={'in_progress_refs':[85,89],'forms':['ultimate_before','ultimate_after'],'generated_form_images':4,'current_native':ev(H/'ultimate_standing_fire_native02/report.json'),'source_evidence':[ev(H/p)for p in ['ultimate_standing_fire_inputs01/generation_receipt.json','ultimate_standing_fire_sleeves01/generation_receipt.json','ultimate_standing89_arm02/generation_receipt.json']],'status':'첫85/89 전후4 원화와 국소팔 등록.89 흰세로소매를 피부팔로 교정하고85접힌팔도 새donor.공통머리/사지·정본총·나머지86/87/90/91/92 및패킹 미완료.','unaccepted_local_edit':'sleeves01의89는 윗소매잔존/팔하강으로 미사용;별도arm02 새그림만 등록.','unchanged_blocked':'Ultimate135 거부 편집은 재요청하지 않고 부모 유지','frozen':False,'arc_written':False}
    q['priority_next'][0].update(forms=['ultimate_before','ultimate_after'],why='기본/포스85..92는동결4fe717. Ultimate85/89 공통정합 뒤86/87/90/91/92 별도 의상원화와 전체8 패킹. 양쪽선택1..8 futurev4 동기화 필수.')
    q['full_art_unification_complete']=False;unique={};empty=[]
    for r in q['references']:
        if not r['structural_decode']:continue
        form=r['form'];n=r['ref'];a=arcs['ultimate'if form.startswith('ultimate')else'base'];mask=r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0)
        pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
        if n in range(85,93)and form in('base','fourth'):
            r.update(status='new_art_frozen_for_integration',decision='새85..92 상세원화40층·18기존참조순열보존/독립/508원MIPS/부분/원순서/루트12판 후 동결4fe717. BR23통합예정, UI1..8/실기 별도.',changed_from_reviewed_parent=True);r.pop('in_progress_unapplied_art',None)
        if n in(85,89)and form.startswith('ultimate'):r['in_progress_unapplied_art']=q['next_generation']
        if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes())
        b=unique.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});b['refs'].append(n);b['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);b['status_by_ref'][str(n)]=r['status'];b['groups'].add(r['group'])
    statuses=Counter(r['status']for r in q['references']);q['counts']['status_counts']=dict(statuses);q['counts']['new_frozen_form_images']=statuses['new_art_frozen_for_integration']
    for g in q['groups']:g['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==g['form']and r['ref']in g['refs']))
    write(H/'fullform_ledger31.json',q);keys=[];pending=defaultdict(list)
    for (form,key),b in sorted(unique.items()):
        b['groups']=sorted(b['groups']);s=set(b['status_by_ref'].values());b['status']=next(iter(s))if len(s)==1 else'mixed_review_status';b['refs'].sort();keys.append(b)
        if 'art_rework_group_pending'in s:
            for g in b['groups']:pending[(form,g)].extend(b['refs'])
    forms={f:{'native_reference_slots':len([r for r in q['references']if r['form']==f]),'unique_visible_art_keys':len([k for k in keys if k['form']==f]),'unique_key_status_counts':dict(Counter(k['status']for k in keys if k['form']==f))}for f in('base','fourth','ultimate_before','ultimate_after')}
    report={'scope':'동결 PL004fe717/PL0226fd 네폼 표시키. 아직통합BR22와구분;원화장수/품질완료율아님.','definition':'같은폼 불투명bbox크기와RGBA가 같은 평행이동만 한키. 부분마스크/UI 제외.','source_ledger':ev(H/'fullform_ledger31.json'),'candidates':q['current_candidates'],'counts':{'visible_unique_keys':len(keys),'unique_key_status_counts':dict(Counter(k['status']for k in keys)),'reference_status_counts':dict(statuses),'empty_decoded_slots':empty},'forms':forms,'keys':keys,'pending_motion_groups':[{'form':f,'group':g,'refs':sorted(set(refs))}for(f,g),refs in sorted(pending.items())],'full_art_unification_complete':False,'no_percent_estimated':True,'integration':q['active_integration'],'next_unfrozen_art':q['next_generation']}
    write(H/'unique_art_keys31.json',report);print(json.dumps({'ledger':ev(H/'fullform_ledger31.json'),'keys':ev(H/'unique_art_keys31.json'),'counts':report['counts']['unique_key_status_counts'],'unique':len(keys)}))
if __name__=='__main__':main()
