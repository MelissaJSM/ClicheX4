"""특수3 네폼 동결과 BR21 귀환 통합, 다음85/89 미완료를 별도 스냅샷에 기록."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    need(not(H/'fullform_ledger28.json').exists(),'Fresh snapshot')
    q=json.loads((H/'fullform_ledger27.json').read_text('utf8'));arcs={}
    for kind,name in [('base','PL00_U.ARC'),('ultimate','PL02_U.ARC')]:
        d=H/f'prepared_standing_special_{kind}01';f=json.loads((d/'FROZEN.json').read_text('utf8'));p=d/name
        need(f['frozen']and sha(p.read_bytes())==f['candidate_sha256'],'Candidate not frozen');arcs[kind]=Archive(p.read_bytes())
        q['current_candidates'][name]={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'frozen':True,'integrated':False,'integration_planned_by_root':'BR22','gameplay_verified':False}
    q['active_integration']={'project':'ver_buki_riko','build':'sprite_style_unification_20261107_v21','bin_sha256':'6d550cbcbcf06315c07aa17bbee75e07f64e4f0dc4efd6b2f381a3dc7a40db42','integration_reported_by':'root 및 현재 docs/STATUS.md','PL00_sha256':'87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b','PL02_sha256':'f40f33969d488af9db8c7d99b6bf4a78ad6e5542883bff63116fa26778de4cdc','includes_ultimate_return3':True,'new_special3_included':False,'new_independent_bin_readback_here':False}
    q['return3_frozen_scope']['integrated_in_BR21']=True
    q['standing_special3_frozen_scope']={'refs':[95,96,97],'fourform_display_refs':12,'root_review':ev(H.parent/'root_review_checkpoint127.json'),'native':ev(H/'standing_special_fourform_components_native_checks.json'),'directory_native':ev(H.parent/'zero_audit/shibuki_standing3_directory_native01/report.json'),'independent':[ev(H.parent/'zero_audit'/n/'report.json')for n in('shibuki_standing3_independent01','shibuki_ultimate_special3_independent01')],'offline_sequence':ev(H/'standing_special_sequence01/browser_verification.json'),'integration':False,'runtime':False,'base_relocation':'고정 entry2 186228B 안에서 bank0+280, bank1..12 상대이동, bank12 원decoder 미소비 후미280B 회수. bank13 절대위치/전체바이트 보존.'}
    q['priority_next']=[{'rank':1,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(85,93)),'why':'원사격/차지/복귀 자세별 머리·의상 재질 통일. 기본/포스85/89 첫원화 및 포스앞소매 국소 원화 등록 중. 기존0과 같다고 가정하지 않는다.'},{'rank':2,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(162,175)),'why':'체이서 머리 단색면과 소매 상세. 기존 원모션·탑승위치 보존.'},{'rank':3,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(213,231)),'why':'호버/노바 몸체·효과·전후 고정mask15의 의상표시를 분리 검토.'},{'rank':4,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':list(range(184,204)),'why':'차량 머리만 표시 및 빈198 구분. 장식 식별성 추가검토, 통째 높이 확대 금지.'}]
    q['next_generation']={'in_progress_refs':[85,89],'forms':['base','fourth'],'source':ev(H/'standing_fire_inputs01/generated.png'),'registration':ev(H/'standing_fire_native01/report.json'),'fourth_sleeve_correction_source':ev(H/'standing_fire_fourth_sleeves01/generated.png'),'status':'첫 원화 등록/포스 앞소매 재질 교정 중. 원총구/소유층·나머지6참조·패킹 미완료.','unchanged_blocked':'Ultimate135 과거 도구 거부 국소편집은 재요청하지 않으며 부모를 보존한다.'}
    q['full_art_unification_complete']=False;unique={};empty=[]
    for r in q['references']:
        if not r['structural_decode']:continue
        form=r['form'];n=r['ref'];a=arcs['ultimate'if form.startswith('ultimate')else'base'];mask=r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0)
        pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
        if n in (95,96,97):r.update(status='new_art_frozen_for_integration',decision='새95/97 상세원화와96 x+1 파생, 독립/원MIPS/부분/원표/루트16판 통과 후 동결. BR22 통합예정이며 실기·전체수용 별도.',changed_from_reviewed_parent=True)
        if n in (85,89)and form in('base','fourth'):r['in_progress_unapplied_art']=q['next_generation']
        if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes())
        b=unique.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});b['refs'].append(n);b['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);b['status_by_ref'][str(n)]=r['status'];b['groups'].add(r['group'])
    statuses=Counter(r['status']for r in q['references']);q['counts']['status_counts']=dict(statuses);q['counts']['new_frozen_form_images']=statuses['new_art_frozen_for_integration']
    for g in q['groups']:g['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==g['form']and r['ref']in g['refs']))
    write(H/'fullform_ledger28.json',q);keys=[];pending=defaultdict(list)
    for (form,key),b in sorted(unique.items()):
        b['groups']=sorted(b['groups']);s=set(b['status_by_ref'].values());b['status']=next(iter(s))if len(s)==1 else'mixed_review_status';b['refs'].sort();keys.append(b)
        if 'art_rework_group_pending'in s:
            for g in b['groups']:pending[(form,g)].extend(b['refs'])
    forms={f:{'native_reference_slots':len([r for r in q['references']if r['form']==f]),'unique_visible_art_keys':len([k for k in keys if k['form']==f]),'unique_key_status_counts':dict(Counter(k['status']for k in keys if k['form']==f))}for f in('base','fourth','ultimate_before','ultimate_after')}
    report={'scope':'현재 동결 PL00fdba/PL0226fd 네폼 표시키. 통합 BR21과 구분하며 원화 장수/품질 완료율 아님.','definition':'같은폼 불투명bbox크기와RGBA가 같은 평행이동만 한키. 부분마스크/UI 제외.','source_ledger':ev(H/'fullform_ledger28.json'),'candidates':q['current_candidates'],'counts':{'visible_unique_keys':len(keys),'unique_key_status_counts':dict(Counter(k['status']for k in keys)),'reference_status_counts':dict(statuses),'empty_decoded_slots':empty},'forms':forms,'keys':keys,'pending_motion_groups':[{'form':f,'group':g,'refs':sorted(set(refs))}for(f,g),refs in sorted(pending.items())],'full_art_unification_complete':False,'no_percent_estimated':True,'integration':q['active_integration'],'next_unfrozen_art':q['next_generation']}
    write(H/'unique_art_keys28.json',report);print(json.dumps({'ledger':ev(H/'fullform_ledger28.json'),'keys':ev(H/'unique_art_keys28.json'),'counts':report['counts']['unique_key_status_counts'],'unique':len(keys)}))
if __name__=='__main__':main()
