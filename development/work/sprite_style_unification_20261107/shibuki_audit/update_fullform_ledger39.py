"""BR29 실제 재추출과 돌진 동결, 별도 호버 미완료를 결속한다."""
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
    need(not(H/'fullform_ledger39.json').exists(),'새장부');q=json.loads((H/'fullform_ledger38.json').read_text('utf8'));b=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v29/shibuki_riko.bin';h=hashlib.sha256()
    with b.open('rb')as f:
        for block in iter(lambda:f.read(8388608),b''):h.update(block)
    need(h.hexdigest()=='753928a3cf2101caabf05cbe112217aa6d4b95b6320674632692831297a52252','BR29변경')
    expected={'PL00_U.ARC':'36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e','PL02_U.ARC':'01997c949968d5a1a12d89e09c5eb46448bbcf245009feb9953e3d9e9356efd7','ST0E_U1.ARC':'47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'}
    actual=read_disc(b,tuple(expected))[0];need({n:sha(v)for n,v in actual.items()}==expected,'BR29재추출');write(H/'br29_readback01.json',{'bin':ev(b),'resources':expected,'actual_disc_readback':True,'new_gameplay_execution_here':False})
    q['active_integration']={'project':'ver_buki_riko','build':'sprite_style_unification_20261107_v29','bin_sha256':h.hexdigest(),'PL00_sha256':expected['PL00_U.ARC'],'PL02_sha256':expected['PL02_U.ARC'],'ST0E_sha256':expected['ST0E_U1.ARC'],'proof':ev(H/'br29_readback01.json'),'new_independent_bin_readback_here':True,'unaccepted_generated_art_included':False,'new_gameplay_execution_here':False}
    frozen={}
    for kind,name,refs in(('base','PL00_U.ARC',[217,220]),('ultimate','PL02_U.ARC',[217,218,219,220])):
        d=H/f'prepared_nova_strike_{kind}01';fr=json.loads((d/'FROZEN.json').read_text('utf8'));need(fr['frozen']and fr['candidate_sha256']==expected[name],'돌진동결');need(sha((d/name).read_bytes())==expected[name],'후보변경')
        for p,v in fr['files'].items():need(sha((d/p).read_bytes())==v,'동결근거변경')
        q['current_candidates'][name]={**ev(d/name),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),'frozen':True,'integrated':True,'integrated_build':'BR29','gameplay_verified':False}
        frozen[kind]={'refs':refs,'target_layers':5*len(refs),'candidate':ev(d/name),'frozen_record':ev(d/'FROZEN.json'),'final_verification':ev(d/'final_verification.json'),'integrated_build':'BR29','gameplay_verified':False,'status':'기본 새몸2참조 및 Ultimate 새몸·효과4참조 동결/실제BIN재추출.실제게임검증은별도.','effect_policy':'기본218/219부모보존.원220전체효과타일/24기록보존.'if kind=='base'else'218현재3점보존·숨은발끝1점재도입없음,219새몸실루엣,220역사효과의새몸가림93셀정책.전체효과rawexact주장아님.'}
    q.pop('nova_strike_pending',None);q['nova_strike_frozen_scope']=frozen
    pending={'refs':list(range(221,231)),'root_owns_base_fourth':True,'ui_owns_ultimate':True,'ultimate_body_refs':[221,223,225,227,229],'first4_layers':ev(H/'hover_ultimate_body_layers01/manifest.json'),'last229':ev(H/'hover_ultimate_native02/registration.json'),'right_hand221':ev(H/'hover221_reach_native01/registration.json'),'firing5_unmade':True,'packed':False,'integrated':False,'status':'5새몸고정등록.221두손위국소교정잔여1px·229원바닥유지.원추진15위상·정본총구·50층·패킹검사미완료.'}
    q['hover_pending']=pending;q['next_generation']={'scope':'Ultimate호버사격222/224/226/228/230의앞팔을원발사점에맞추며새몸5를보존.기본/포스호버는Root별도제작.','relations':ev(H.parent/'zero_audit/shibuki_nova_hover_relations01/report.json'),'blocked_unchanged':'Ultimate135거부팔은재시도않음.184..203머리장식조건부/198빈참조보존.','all_forms_done':False}
    arcs={'base':Archive(actual['PL00_U.ARC']),'ultimate':Archive(actual['PL02_U.ARC'])};unique={};empty=[]
    for r in q['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];kind='ultimate'if form.startswith('ultimate')else'base';a=arcs[kind];mask=r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0);pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
        if n in frozen[kind]['refs']:
            r.update(status='new_art_frozen_for_integration',decision='돌진새몸/효과를해당폼36d4/01997c동결후BR29통합.효과파생과원화몸체수는별도.',changed_from_reviewed_parent=True);r.pop('in_progress_unapplied_art',None)
        if 221<=n<=230:r['in_progress_unapplied_art']=pending
        if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes());v=unique.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});v['refs'].append(n);v['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);v['status_by_ref'][str(n)]=r['status'];v['groups'].add(r['group'])
    status=Counter(r['status']for r in q['references']);q['counts']['status_counts']=dict(status);q['counts']['new_frozen_form_images']=status['new_art_frozen_for_integration'];q['counts']['new_prepared_form_images']=0
    for g in q['groups']:g['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==g['form']and r['ref']in g['refs']))
    q['full_art_unification_complete']=False;write(H/'fullform_ledger39.json',q);keys=[];remaining=defaultdict(list)
    for(form,key),v in sorted(unique.items()):
        v['groups']=sorted(v['groups']);ss=set(v['status_by_ref'].values());v['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';v['refs'].sort();keys.append(v)
        if 'art_rework_group_pending'in ss:
            for g in v['groups']:remaining[(form,g)].extend(v['refs'])
    report={'scope':'BR29실제PL0036d4/PL0201997c돌진동결자료의폼별고유표시.호버5원화/등록은미통합별도.품질완료율아님.','definition':'같은폼·불투명bbox크기와RGBA가같은평행이동만합침.부분/UI제외.','source_ledger':ev(H/'fullform_ledger39.json'),'candidates':q['current_candidates'],'counts':{'visible_unique_keys':len(keys),'unique_key_status_counts':dict(Counter(k['status']for k in keys)),'reference_status_counts':dict(status),'empty_decoded_slots':empty},'keys':keys,'pending_motion_groups':[{'form':f,'group':g,'refs':sorted(set(refs))}for(f,g),refs in sorted(remaining.items())],'full_art_unification_complete':False,'no_percent_estimated':True,'integration':q['active_integration'],'pending_art':pending};write(H/'unique_art_keys39.json',report);print(json.dumps({'ledger':ev(H/'fullform_ledger39.json'),'keys':ev(H/'unique_art_keys39.json'),'counts':report['counts']['unique_key_status_counts']}))
if __name__=='__main__':main()
