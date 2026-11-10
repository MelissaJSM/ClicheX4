"""BR28 실제자원과준비4 동결/새217 후보를 분리한 전폼 장부."""
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
    need(not(H/'fullform_ledger38.json').exists(),'새장부');q=json.loads((H/'fullform_ledger37.json').read_text('utf8'));b=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v28/shibuki_riko.bin';digest=hashlib.sha256()
    with b.open('rb')as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):digest.update(block)
    need(digest.hexdigest()=='13d52f8be48ef29962dd78fc94f236897d216ef6c56f39406bb2bb67bbea5c77','BR28 변경')
    expected={'PL00_U.ARC':'619032d0b81ffc50e5f5664ff1e3d0c077f226a7d5a8ccfac081be6a2126c6c5','PL02_U.ARC':'687fb27b10b9a7c13dd6d0c9fd6976dbb04f88f9b3b775f3d33482ebb7efb86f','ST0E_U1.ARC':'47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'}
    actual=read_disc(b,tuple(expected))[0];need({n:sha(v)for n,v in actual.items()}==expected,'BR28 재추출');write(H/'br28_readback01.json',{'bin':ev(b),'resources':expected,'actual_disc_readback':True,'new_gameplay_execution_here':False})
    q['active_integration']={'project':'ver_buki_riko','build':'sprite_style_unification_20261107_v28','bin_sha256':digest.hexdigest(),'PL00_sha256':expected['PL00_U.ARC'],'PL02_sha256':expected['PL02_U.ARC'],'ST0E_sha256':expected['ST0E_U1.ARC'],'proof':ev(H/'br28_readback01.json'),'new_independent_bin_readback_here':True,'unaccepted_generated_art_included':False,'new_gameplay_execution_here':False}
    frozen={}
    for kind,name in(('base','PL00_U.ARC'),('ultimate','PL02_U.ARC')):
        d=H/f'prepared_nova_{kind}01';fr=json.loads((d/'FROZEN.json').read_text('utf8'));need(fr['frozen']and fr['candidate_sha256']==expected[name],'준비4동결');need(sha((d/name).read_bytes())==expected[name],'후보변경')
        for p,h in fr['files'].items():need(sha((d/p).read_bytes())==h,'동결근거변경')
        q['current_candidates'][name]={**ev(d/name),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen':True,'integrated':True,'integrated_build':'BR28','gameplay_verified':False}
        frozen[kind]={'refs':[213,214,215,216],'target_layers':20,'candidate':ev(d/name),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'integrated_build':'BR28','root_actual_gameplay':ev(H.parent/'runtime/br28_nova_summary.json')if kind=='ultimate'else None,'gameplay_limit':'루트 획득후Ultimate 양방향112캡처/6판만.기본/포스·획득전·60Hz전수·참조별RAM검사는아님.','status':'새준비2자세×2의상/현재동일짝4참조를동결통합.217이후새몸제작은별도.'}
    q.pop('nova_preparation_pending',None);q['nova_preparation_frozen_scope']=frozen
    d=H/'prepared_nova_strike_base01';base_pending={'candidate':ev(d/'PL00_U.ARC'),'proposal':ev(d/'proposal.json'),'input_lock':ev(d/'INPUT_LOCK.json'),'verification':ev(d/'verification.json'),'native':ev(H/'nova_strike_base_components_native_checks.json'),'sequence':ev(H/'nova_strike_base_sequence01/report.json'),'browser':ev(H/'nova_strike_base_sequence01/browser_verification.json'),'refs':[217,220],'target_layers':10,'frozen':False,'integrated':False,'native_renderer_and_independent_pending':True,'status':'새몸10층+원220전체18효과타일/24기록.새31+7파트검사는독립대기.기존6참조는역순열저장만.'}
    ult_pending={'input':ev(H/'nova_strike_ultimate_inputs01/input.json'),'generation':ev(H/'nova_strike_ultimate_inputs01/generation.json'),'registration':ev(H/'nova_strike_ultimate_native01/registration.json'),'refs':[217],'candidate_ARC':None,'frozen':False,'integrated':False,'status':'강제mask15용after의상 새몸1셀 고정등록.눈/위아래높이유지·끝샌들폭1px차이검토중.218/219/220효과파생은미제작.'}
    q['nova_strike_pending']={'base':base_pending,'ultimate':ult_pending};q['next_generation']={'scope':'217..220 현재새돌진몸/효과 마감후221..230호버10의 실제원총구·추진15위상·강제mask15 소유를기준으로제작한다.','relations':ev(H.parent/'zero_audit/shibuki_nova_hover_relations01/report.json'),'blocked_unchanged':'Ultimate135 거부된팔편집은재시도하지않고부모보존.184..203머리장식조건부/198빈참조도별도유지.','all_forms_done':False}
    arcs={'base':Archive(actual['PL00_U.ARC']),'ultimate':Archive(actual['PL02_U.ARC'])};unique={};empty=[]
    for r in q['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];kind='ultimate'if form.startswith('ultimate')else'base';a=arcs[kind];mask=r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0);pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
        if n in(213,214,215,216):r.update(status='new_art_frozen_for_integration',decision='준비4 새20층을해당폼619032/687fb 동결후BR28통합.실기범위는루트획득후Ultimate만.',changed_from_reviewed_parent=True);r.pop('in_progress_unapplied_art',None)
        if n in(217,220)and kind=='base':r['in_progress_unapplied_art']=base_pending
        if n==217 and kind=='ultimate':r['in_progress_unapplied_art']=ult_pending
        if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes());v=unique.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});v['refs'].append(n);v['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);v['status_by_ref'][str(n)]=r['status'];v['groups'].add(r['group'])
    status=Counter(r['status']for r in q['references']);q['counts']['status_counts']=dict(status);q['counts']['new_frozen_form_images']=status['new_art_frozen_for_integration'];q['counts']['new_prepared_form_images']=4
    for g in q['groups']:g['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==g['form']and r['ref']in g['refs']))
    q['full_art_unification_complete']=False;write(H/'fullform_ledger38.json',q);keys=[];remaining=defaultdict(list)
    for(form,key),v in sorted(unique.items()):
        v['groups']=sorted(v['groups']);ss=set(v['status_by_ref'].values());v['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';v['refs'].sort();keys.append(v)
        if 'art_rework_group_pending'in ss:
            for g in v['groups']:remaining[(form,g)].extend(v['refs'])
    report={'scope':'BR28 실제PL00619032/PL02687fb 준비4동결자료의폼별고유표시.새돌진36d4와Ultimate217원화는미통합별도.품질완료율아님.','definition':'같은폼·불투명bbox크기와RGBA가같은평행이동만합침.부분/UI제외.','source_ledger':ev(H/'fullform_ledger38.json'),'candidates':q['current_candidates'],'counts':{'visible_unique_keys':len(keys),'unique_key_status_counts':dict(Counter(k['status']for k in keys)),'reference_status_counts':dict(status),'empty_decoded_slots':empty},'keys':keys,'pending_motion_groups':[{'form':f,'group':g,'refs':sorted(set(refs))}for(f,g),refs in sorted(remaining.items())],'full_art_unification_complete':False,'no_percent_estimated':True,'integration':q['active_integration'],'pending_art':q['nova_strike_pending']};write(H/'unique_art_keys38.json',report);print(json.dumps({'ledger':ev(H/'fullform_ledger38.json'),'keys':ev(H/'unique_art_keys38.json'),'counts':report['counts']['unique_key_status_counts']}))
if __name__=='__main__':main()
