"""Ultimate 호버10 동결과 아직 미통합인 새 원화 범위를 분리한 장부."""
from pathlib import Path
from collections import Counter,defaultdict
import json,sys,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    need(not(H/'fullform_ledger40.json').exists(),'새 장부 보호');q=json.loads((H/'fullform_ledger39.json').read_text('utf8'));d=H/'prepared_hover_ultimate01';fr=json.loads((d/'FROZEN.json').read_text('utf8'))
    need(fr['frozen'] and fr['candidate_sha256']=='3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba','동결 후보')
    for name,h in fr['files'].items():need(sha((d/name).read_bytes())==h,'동결 파일 변경 '+name)
    q['previous_ledger']=ev(H/'fullform_ledger39.json');q['current_candidates']['PL02_U.ARC']={**ev(d/'PL02_U.ARC'),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen':True,'integrated':False,'planned_build':'BR30','gameplay_verified':False}
    q['hover_frozen_ultimate']={'refs':list(range(221,231)),'unique_bodies':5,'firing_arms':5,'target_layers':50,'candidate':ev(d/'PL02_U.ARC'),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'native_changed_refs':10,'partial_RGBA':320,'actual_engine_mask':15,'integrated':False,'gameplay_verified':False,'status':'독립 원화13고정셀 재구성/50층/보존·원코드10·Root159 최종11판·3재현18거부·원표3000canvas를 결속한 별도 동결. BR30 통합은 Root 담당이며 이 장부에서 실제 통합으로 세지 않음.'}
    pending={'forms':['base','fourth'],'refs':list(range(221,231)),'owner':'Root','root_owns_base_fourth':True,'packed':False,'integrated':False,'status':'Root 새5몸 양의상 등록·공통층/사격팔 제작 중. Ultimate 동결 근거를 기본/포스에 확대하지 않음.'};q['hover_pending']=pending
    q['tiny_vehicle_head_pending']={'refs':[n for n in range(184,204) if n!=198],'empty_preserved':[198],'normalized_existing_heads':4,'new_art_target_forms':['ultimate_before','ultimate_after'],'read':ev(H/'vehicle_head_accessory_read01/report.json'),'conclusions':ev(H/'vehicle_head_accessory_read01/conclusions.json'),'input':ev(H/'vehicle_head_ultimate_inputs01/input_manifest.json'),'generated':False,'status':'13×15 머리144픽셀의 동일그림 위치별칭. 기본/포스는 조건부 보존, Ultimate 고글·내부머릿결 보완 입력 준비. 머리 전체 확대 금지.'}
    q['next_generation']={'scope':'Ultimate 작은 탑승머리의 현재13×15 외곽/눈높이를 보존한 내부 고글·머릿결 편집. Root 기본/포스 호버 사격 반환 이후 순차 호출.','blocked_unchanged':'Ultimate135 거부 팔은 재시도하지 않고 부모 보존.','all_forms_done':False}
    arcs={'base':Archive((H/'prepared_nova_strike_base01/PL00_U.ARC').read_bytes()),'ultimate':Archive((d/'PL02_U.ARC').read_bytes())};unique={};empty=[]
    for r in q['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];kind='ultimate' if form.startswith('ultimate') else 'base';a=arcs[kind];mask=r.get('effective_render_mask',15 if form in ('fourth','ultimate_before') else 0);pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
        if 221<=n<=230:
            if kind=='ultimate':r.update(status='new_art_frozen_for_integration',decision='새5몸/5사격팔의10참조를3f168로동결. 실제엔진강제mask15이며전후양식진단과원화수는별도.',changed_from_reviewed_parent=True);r.pop('in_progress_unapplied_art',None)
            else:r['in_progress_unapplied_art']=pending
        if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes());v=unique.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});v['refs'].append(n);v['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);v['status_by_ref'][str(n)]=r['status'];v['groups'].add(r['group'])
    status=Counter(r['status'] for r in q['references']);q['counts']['status_counts']=dict(status);q['counts']['new_frozen_form_images']=status['new_art_frozen_for_integration'];q['counts']['new_prepared_form_images']=0
    for g in q['groups']:g['status_counts']=dict(Counter(r['status'] for r in q['references'] if r['form']==g['form'] and r['ref'] in g['refs']))
    q['full_art_unification_complete']=False;write(H/'fullform_ledger40.json',q);keys=[];remaining=defaultdict(list)
    for (form,key),v in sorted(unique.items()):
        v['groups']=sorted(v['groups']);ss=set(v['status_by_ref'].values());v['status']=next(iter(ss)) if len(ss)==1 else 'mixed_review_status';v['refs'].sort();keys.append(v)
        if 'art_rework_group_pending' in ss:
            for g in v['groups']:remaining[(form,g)].extend(v['refs'])
    report={'scope':'기본36d4·Ultimate3f168 최신 동결 기준. 마지막 직접BIN재추출은BR29이며새호버10은BR30미통합후보로분리.품질완료율아님.','definition':'같은폼·불투명bbox크기와RGBA가 같은 평행이동만 합침.부분/UI 제외.','source_ledger':ev(H/'fullform_ledger40.json'),'candidates':q['current_candidates'],'counts':{'visible_unique_keys':len(keys),'unique_key_status_counts':dict(Counter(k['status'] for k in keys)),'reference_status_counts':dict(status),'empty_decoded_slots':empty},'keys':keys,'pending_motion_groups':[{'form':f,'group':g,'refs':sorted(set(refs))} for(f,g),refs in sorted(remaining.items())],'full_art_unification_complete':False,'no_percent_estimated':True,'integration':q['active_integration'],'pending_art':pending,'tiny_heads':q['tiny_vehicle_head_pending']};write(H/'unique_art_keys40.json',report);print(json.dumps({'ledger':ev(H/'fullform_ledger40.json'),'keys':ev(H/'unique_art_keys40.json'),'counts':report['counts']['unique_key_status_counts']}))
if __name__=='__main__':main()
