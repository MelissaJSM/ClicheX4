"""Ultimate사격8 동결과 체이서 첫8원화 진행을 분리한 장부."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    need(not(H/'fullform_ledger34.json').exists(),'새 장부 필요');q=json.loads((H/'fullform_ledger33.json').read_text('utf8'));d=H/'prepared_standing_fire_ultimate01'
    f=json.loads((d/'FROZEN.json').read_text('utf8'));p=d/'PL02_U.ARC';need(f['frozen']and sha(p.read_bytes())==f['candidate_sha256'],'동결 확인')
    q['current_candidates']['PL02_U.ARC']={**ev(p),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen':True,'integrated':False,'integration_planned_by_root':'BR25','gameplay_verified':False}
    q['ultimate_standing_fire8_prepared_scope'].update(frozen=True,frozen_record=ev(d/'FROZEN.json'),independent_pending=False,root_final_pending=False,status='8참조40층 독립/원MIPS8/원표23/루트10판/재현3·거부17 후 동결. BR25통합 대기, 실기별도.')
    q['next_generation']={'forms':['base','fourth'],'in_progress_refs':[162,166,170,174],'derived_scope':list(range(162,175)),
        'sources':[ev(H/f'chaser_base_inputs{i:02}/generation_receipt.json')for i in(1,2)],'native':[ev(H/f'chaser_base_native{i:02}/report.json')for i in(1,2)],
        'relations':ev(H/'chaser_sources01/report.json'),'common_layers':ev(H/'chaser_layers_final02/report.json'),
        'status':'4고유자세8표시 원화/고정등록·새공통머리/손·부분20층 후보. 외곽6셀 새원화 인접등록,170 홍채 의미팔레트1셀.13파생/패킹/원순서·독립·실기 미완료.',
        'all_forms_done':False,'frozen':False,'arc_written':False,'unchanged_blocked':'Ultimate135 거부 편집은 재시도하지 않고 부모 유지'}
    arcs={'base':Archive((ROOT/q['current_candidates']['PL00_U.ARC']['path']).read_bytes()),'ultimate':Archive(p.read_bytes())};unique={};empty=[]
    for r in q['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];a=arcs['ultimate'if form.startswith('ultimate')else'base'];mask=r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0)
        pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
        if 85<=n<=92 and form.startswith('ultimate'):
            r.update(status='new_art_frozen_for_integration',decision='새7고유자세14원화와88원효과 파생40층을 동결1f271a.원MIPS8/독립/원표/루트10판 통과,BR25통합대기/실기별도.',changed_from_reviewed_parent=True);r.pop('in_progress_unapplied_art',None)
        if 162<=n<=174 and form in('base','fourth'):r['in_progress_unapplied_art']=q['next_generation']
        if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes())
        b=unique.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});b['refs'].append(n);b['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);b['status_by_ref'][str(n)]=r['status'];b['groups'].add(r['group'])
    status=Counter(r['status']for r in q['references']);q['counts']['status_counts']=dict(status);q['counts']['new_frozen_form_images']=status['new_art_frozen_for_integration']
    for g in q['groups']:g['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==g['form']and r['ref']in g['refs']))
    q['full_art_unification_complete']=False;write(H/'fullform_ledger34.json',q);keys=[];pending=defaultdict(list)
    for(form,k),b in sorted(unique.items()):
        b['groups']=sorted(b['groups']);ss=set(b['status_by_ref'].values());b['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';b['refs'].sort();keys.append(b)
        if 'art_rework_group_pending'in ss:
            for g in b['groups']:pending[(form,g)].extend(b['refs'])
    report={'scope':'동결PL004fe717/PL021f271a 네폼의 고유 표시키. BR25통합 전 후보/고유원화장수/완료율 구분.',
        'definition':'같은폼 불투명bbox크기와RGBA가 같은 평행이동만한키.부분/UI제외.','source_ledger':ev(H/'fullform_ledger34.json'),'candidates':q['current_candidates'],
        'counts':{'visible_unique_keys':len(keys),'unique_key_status_counts':dict(Counter(k['status']for k in keys)),'reference_status_counts':dict(status),'empty_decoded_slots':empty},
        'forms':{f:{'native_reference_slots':len([r for r in q['references']if r['form']==f]),'unique_visible_art_keys':len([k for k in keys if k['form']==f]),'unique_key_status_counts':dict(Counter(k['status']for k in keys if k['form']==f))}for f in('base','fourth','ultimate_before','ultimate_after')},
        'keys':keys,'pending_motion_groups':[{'form':f,'group':g,'refs':sorted(set(refs))}for(f,g),refs in sorted(pending.items())],
        'full_art_unification_complete':False,'no_percent_estimated':True,'integration':q['active_integration'],'next_unfrozen_art':q['next_generation'],'selection_copy_candidate':q['selection_standing8_prepared']}
    write(H/'unique_art_keys34.json',report);print(json.dumps({'ledger':ev(H/'fullform_ledger34.json'),'keys':ev(H/'unique_art_keys34.json'),'counts':report['counts']['unique_key_status_counts']}))
if __name__=='__main__':main()
