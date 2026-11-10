"""BR27 실제 읽기·Ultimate 차량 동결과 노바 준비 후보를 분리한 전폼 장부."""
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
    need(not(H/'fullform_ledger37.json').exists(),'새 장부');q=json.loads((H/'fullform_ledger36.json').read_text('utf8'));base=H/'prepared_chaser_base01';ult=H/'prepared_chaser_ultimate01'
    b=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v27/shibuki_riko.bin';digest=hashlib.sha256()
    with b.open('rb')as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):digest.update(block)
    need(digest.hexdigest()=='73c2b28eb59739234351b59d9f18de6a1a9429bcf9d8e71327f3206dcb6d2cbb','BR27 변경')
    expected={'PL00_U.ARC':sha((base/'PL00_U.ARC').read_bytes()),'PL02_U.ARC':sha((ult/'PL02_U.ARC').read_bytes()),'ST0E_U1.ARC':'47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'}
    actual=read_disc(b,tuple(expected))[0];need({n:sha(v)for n,v in actual.items()}==expected,'BR27 재추출')
    write(H/'br27_readback01.json',{'bin':ev(b),'resources':expected,'actual_disc_readback':True,'new_gameplay_execution_here':False})
    q['active_integration']={'project':'ver_buki_riko','build':'sprite_style_unification_20261107_v27','bin_sha256':digest.hexdigest(),'PL00_sha256':expected['PL00_U.ARC'],'PL02_sha256':expected['PL02_U.ARC'],'ST0E_sha256':expected['ST0E_U1.ARC'],'proof':ev(H/'br27_readback01.json'),'new_independent_bin_readback_here':True,'unaccepted_generated_art_included':False,'new_gameplay_execution_here':False}
    for name,folder in [('PL00_U.ARC',base),('PL02_U.ARC',ult)]:q['current_candidates'][name]={**ev(folder/name),'frozen_record':ev(folder/'FROZEN.json'),'final_verification':ev(folder/'final_verification.json'),'prepared_lock':ev(folder/'PREPARED_LOCK.json'),'frozen':True,'integrated':True,'integrated_build':'BR27','gameplay_verified':False}
    q['chaser_ultimate13_frozen_scope']={'candidate':ev(ult/'PL02_U.ARC'),'frozen_record':ev(ult/'FROZEN.json'),'final_verification':ev(ult/'final_verification.json'),'root_art':ev(H.parent/'root_review_checkpoint145.json'),'candidate_frozen':True,'integrated':True,'integrated_build':'BR27','runtime_verified':False,'status':'새13참조/65층과 원US Y9별칭을 두의상으로 동결·통합. 실제차량 손잡이/발판은 미검증.'}
    pending={}
    for kind in('base','ultimate'):
        d=H/f'prepared_nova_{kind}01';pending[kind]={'candidate':ev(d/f'PL0{0 if kind=="base"else 2}_U.ARC'),'proposal':ev(d/'proposal.json'),'input_lock':ev(d/'INPUT_LOCK.json'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'verification':ev(d/'verification.json'),'native':ev(H/f'nova_{kind}_components_native_checks.json'),'sequence':ev(H/f'nova_{kind}_sequence01/report.json'),'browser':ev(H/f'nova_{kind}_sequence01/browser_verification.json'),'author_visual':ev(d/'author_visual_review.json'),'refs':[213,214,215,216],'new_body_keys':[213,215],'target_layers':20,'frozen':False,'integrated':False,'runtime_verified':False,'independent_pending':True,'status':'새준비2몸체/두의상과 현재동일짝을20층으로 패킹. 원US 별도짝 완전복원 아님.217~230은 아직 부모 보존.'}
    pending['base']['root_art']=ev(H.parent/'root_review_checkpoint147.json');pending['base']['root_final_art_pending']=False;pending['ultimate']['root_final_art_pending']=True
    q['nova_preparation_pending']=pending;q['next_generation']={'scope':'213~216 준비후보 두ARC는 잠금·독립대기. 다음217몸과218~220효과·221~230호버를 실제mask15/원총구/추진발에맞춰 별도제작.','relations':ev(H.parent/'zero_audit/shibuki_nova_hover_relations01/report.json'),'no_active_image_call':True,'blocked_unchanged':'Ultimate135 거부된 팔 편집은 재시도하지 않고 부모를 보존한다.','all_forms_done':False}
    arcs={'base':Archive(actual['PL00_U.ARC']),'ultimate':Archive(actual['PL02_U.ARC'])};unique={};empty=[]
    for r in q['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];kind='ultimate'if form.startswith('ultimate')else'base';a=arcs[kind];mask=r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0);pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
        if 162<=n<=174 and kind=='ultimate':r.update(status='new_art_frozen_for_integration',decision='새4키와원US Y9파생13참조를2b8faa/c9263564로동결하고BR27통합.실제차량접점은별도.',changed_from_reviewed_parent=True);r.pop('in_progress_unapplied_art',None)
        if n in(213,214,215,216):r['in_progress_unapplied_art']=pending[kind]
        if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes());bucket=unique.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});bucket['refs'].append(n);bucket['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);bucket['status_by_ref'][str(n)]=r['status'];bucket['groups'].add(r['group'])
    status=Counter(r['status']for r in q['references']);q['counts']['status_counts']=dict(status);q['counts']['new_frozen_form_images']=status['new_art_frozen_for_integration'];q['counts']['new_prepared_form_images']=16
    for g in q['groups']:g['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==g['form']and r['ref']in g['refs']))
    q['full_art_unification_complete']=False;write(H/'fullform_ledger37.json',q);keys=[];remaining=defaultdict(list)
    for(form,key),v in sorted(unique.items()):
        v['groups']=sorted(v['groups']);ss=set(v['status_by_ref'].values());v['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';v['refs'].sort();keys.append(v)
        if 'art_rework_group_pending'in ss:
            for g in v['groups']:remaining[(form,g)].extend(v['refs'])
    report={'scope':'BR27 실제PL003e11/PL022b8faa 동결자료의 폼별 고유표시. 노바준비619032/687fb 후보는 미통합·독립대기로 별도. 품질완료율 아님.','definition':'같은폼·불투명bbox크기와RGBA가같은평행이동만합침.부분/UI제외.','source_ledger':ev(H/'fullform_ledger37.json'),'candidates':q['current_candidates'],'counts':{'visible_unique_keys':len(keys),'unique_key_status_counts':dict(Counter(k['status']for k in keys)),'reference_status_counts':dict(status),'empty_decoded_slots':empty},'keys':keys,'pending_motion_groups':[{'form':f,'group':g,'refs':sorted(set(refs))}for(f,g),refs in sorted(remaining.items())],'full_art_unification_complete':False,'no_percent_estimated':True,'integration':q['active_integration'],'pending_art':pending};write(H/'unique_art_keys37.json',report);print(json.dumps({'ledger':ev(H/'fullform_ledger37.json'),'keys':ev(H/'unique_art_keys37.json'),'counts':report['counts']['unique_key_status_counts']}))
if __name__=='__main__':main()
