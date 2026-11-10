"""BR26 실제재독출·체이서 기본동결과 Ultimate 준비본을 구별한 전폼장부."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct,hashlib
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    need(not(H/'fullform_ledger36.json').exists(),'새장부');q=json.loads((H/'fullform_ledger35.json').read_text('utf8'));d=H/'prepared_chaser_base01';u=H/'prepared_chaser_ultimate01'
    b=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v26/shibuki_riko.bin';digest=hashlib.sha256()
    with b.open('rb')as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):digest.update(block)
    need(digest.hexdigest()=='b99860d4a87e8b152d2476ea65851583eb01d7978f9b97488a8d88ad7b536f27','BR26 변경')
    expected={'PL00_U.ARC':sha((d/'PL00_U.ARC').read_bytes()),'PL02_U.ARC':sha((H/'prepared_standing_fire_ultimate01/PL02_U.ARC').read_bytes()),'ST0E_U1.ARC':'47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'}
    need({n:sha(v)for n,v in read_disc(b,tuple(expected))[0].items()}==expected,'BR26 재독출');write(H/'br26_readback01.json',{'bin':{'path':b.relative_to(ROOT).as_posix(),'sha256':digest.hexdigest()},'resources':expected,'actual_disc_readback':True,'new_gameplay_execution_here':False})
    q['active_integration']={'project':'ver_buki_riko','build':'sprite_style_unification_20261107_v26','bin_sha256':digest.hexdigest(),'PL00_sha256':expected['PL00_U.ARC'],'PL02_sha256':expected['PL02_U.ARC'],'ST0E_sha256':expected['ST0E_U1.ARC'],'proof':ev(H/'br26_readback01.json'),'new_independent_bin_readback_here':True,'unaccepted_generated_art_included':False,'new_gameplay_execution_here':False}
    q['current_candidates']['PL00_U.ARC']={**ev(d/'PL00_U.ARC'),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen':True,'integrated':True,'integrated_build':'BR26','gameplay_verified':False}
    q['current_candidates']['PL02_U.ARC'].update(integrated=True,integrated_build='BR25',runtime_by_root=ev(H.parent/'runtime/br25_shot_summary.json'))
    q['ultimate_standing_fire8_prepared_scope'].update(integrated=True,integrated_build='BR25',runtime_by_root=ev(H.parent/'runtime/br25_shot_summary.json'))
    q['chaser_base13_prepared_scope'].update(candidate_frozen=True,frozen_record=ev(d/'FROZEN.json'),final_verification=ev(d/'final_verification.json'),independent_static_pending=False,root_final_art_pending=False,integrated=True,integrated_build='BR26',status='新13/65층과저장16순열동결654408. 독립508원loader/원화·부분/루트18판·원순서/재현3·거부16 통과. BR26 실제재독출일치,차량실기미확인.')
    q['chaser_base13_prepared_scope']['status']=q['chaser_base13_prepared_scope']['status'].replace('新13','새13')
    q['next_generation']={'forms':['ultimate_before','ultimate_after'],'in_progress_refs':[162,166,170,174],'derived_scope':list(range(162,175)),'candidate':ev(u/'PL02_U.ARC'),'proposal':ev(u/'proposal.json'),'input_lock':ev(u/'INPUT_LOCK.json'),'verification':ev(u/'verification.json'),'source_receipts':[ev(H/f'chaser_ultimate_inputs{i:02}/generation_receipt.json')for i in(1,2)],'common':ev(H/'chaser_ultimate_common02/report.json'),'targets':ev(H/'chaser_ultimate_targets01/manifest.json'),'native':ev(H/'chaser_ultimate_components_native_checks.json'),'sequence':ev(H/'chaser_ultimate_sequence01/report.json'),'browser':ev(H/'chaser_ultimate_sequence01/browser_verification.json'),'author_visual':ev(u/'author_visual_review.json'),'status':'新4키8원화→65층/13참조 준비2b8faa.512raw499보존/416부분/174GPU·원MIPS13·원표39/300폼·재현3/거부12 통과.독립/루트최종검토대기.','frozen':False,'arc_written':True,'integrated':False,'runtime_verified':False,'all_forms_done':False,'unchanged_blocked':'Ultimate135거부편집은 재시도하지않고부모유지'}
    q['next_generation']['status']=q['next_generation']['status'].replace('新4키','새4키');arcs={'base':Archive((d/'PL00_U.ARC').read_bytes()),'ultimate':Archive((H/'prepared_standing_fire_ultimate01/PL02_U.ARC').read_bytes())};unique={};empty=[]
    for r in q['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];a=arcs['ultimate'if form.startswith('ultimate')else'base'];mask=r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0);pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
        if 162<=n<=174 and form in('base','fourth'):r.update(status='new_art_frozen_for_integration',decision='새4키와원Y9파생13참조를3e11b7e6/654408로동결하고BR26통합.차량손발실기별도.',changed_from_reviewed_parent=True);r.pop('in_progress_unapplied_art',None)
        if 162<=n<=174 and form.startswith('ultimate'):r['in_progress_unapplied_art']=q['next_generation']
        if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes());bucket=unique.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});bucket['refs'].append(n);bucket['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);bucket['status_by_ref'][str(n)]=r['status'];bucket['groups'].add(r['group'])
    status=Counter(r['status']for r in q['references']);q['counts']['status_counts']=dict(status);q['counts']['new_frozen_form_images']=status['new_art_frozen_for_integration']
    for g in q['groups']:g['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==g['form']and r['ref']in g['refs']))
    q['full_art_unification_complete']=False;write(H/'fullform_ledger36.json',q);keys=[];pending=defaultdict(list)
    for(form,k),v in sorted(unique.items()):
        v['groups']=sorted(v['groups']);ss=set(v['status_by_ref'].values());v['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';v['refs'].sort();keys.append(v)
        if 'art_rework_group_pending'in ss:
            for g in v['groups']:pending[(form,g)].extend(v['refs'])
    report={'scope':'동결PL003e11/PL021f271의네폼고유표시키. BR26실제재독출과Ultimate준비2b8faa는분리.품질완료율아님.','definition':'같은폼 불투명bbox크기와RGBA가 같은평행이동만한키.부분/UI제외.','source_ledger':ev(H/'fullform_ledger36.json'),'candidates':q['current_candidates'],'counts':{'visible_unique_keys':len(keys),'unique_key_status_counts':dict(Counter(k['status']for k in keys)),'reference_status_counts':dict(status),'empty_decoded_slots':empty},'keys':keys,'pending_motion_groups':[{'form':f,'group':g,'refs':sorted(set(refs))}for(f,g),refs in sorted(pending.items())],'full_art_unification_complete':False,'no_percent_estimated':True,'integration':q['active_integration'],'next_unfrozen_art':q['next_generation']};write(H/'unique_art_keys36.json',report);print(json.dumps({'ledger':ev(H/'fullform_ledger36.json'),'keys':ev(H/'unique_art_keys36.json'),'counts':report['counts']['unique_key_status_counts']}))
if __name__=='__main__':main()
