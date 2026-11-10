"""사다리14 동결과 최신 두 ARC의 실제 고유표시 키를 다시 집계한다."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    o=H/'fullform_ledger19.json';need(not o.exists(),'Fresh ledger');j=json.loads((H/'fullform_ledger18.json').read_text('utf8'));d=H/'prepared_ultimate_ladder01';fr=json.loads((d/'FROZEN.json').read_text('utf8'));need(fr['frozen'],'Not frozen')
    for n,h in fr['files'].items():need(sha((d/n).read_bytes())==h,'Frozen file changed')
    refs=set(fr['selected_visual_refs']);j['current_candidates']['PL02_U.ARC']={**ev(d/'PL02_U.ARC'),'frozen_record':ev(d/'FROZEN.json'),'independent_and_native_pending':False,'runtime_verified':False,'integrated':False};j.pop('pending_candidates',None)
    for r in j['references']:
        if r['form']in('ultimate_before','ultimate_after')and r['ref']in refs:r.update(status='new_art_frozen_for_integration',frozen_evidence=ev(d/'FROZEN.json'),decision='새사다리14의전후28표시 동결.원MIPS·독립·재현3/입력거부8·루트6재추출+4순서/끝점판 열람통과.155는수용기본형공통몸체정책이며발끝1~2px차이/실기가로대미검증은별도.',candidate_progress={'status':'통합용 동결','frozen':ev(d/'FROZEN.json'),'whole_project_complete':False})
    j['ladder14_prepared_scope'].update(frozen=ev(d/'FROZEN.json'),final_verification=ev(d/'final_verification.json'),native=ev(H/'ultimate_ladder_components_native_checks.json'),native_pending=False,independent_pending=False,integrated=False)
    j['next_generation'].update(status='피격106/110 기본·포스4 새원화/고정96셀 등록과실제2판열람완료.손발/부분층·효과파생은검사중.나머지233/234 및Ultimate미제작.',generated=True,native_report=ev(H/'hurt_native01/report.json'),source_art=ev(H/'hurt_inputs01/page01/generated.png'),source_receipt=ev(H/'hurt_inputs01/page01/generation_receipt.json'))
    j['new_root_review_evidence'].append(ev(ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint96.json'));arcs={name:Archive((ROOT/v['path']).read_bytes())for name,v in j['current_candidates'].items()if name in('PL00_U.ARC','PL02_U.ARC')};buckets={};empty=[]
    for r in j['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];a=arcs['PL02_U.ARC'if form.startswith('ultimate')else'PL00_U.ARC'];mask=r.get('effective_render_mask',15 if form in('fourth','ultimate_before')else 0);pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes());ys,xs=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xs))
        if not len(xs):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0;key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes());b=buckets.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()});b['refs'].append(n);b['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);b['status_by_ref'][str(n)]=r['status'];b['groups'].add(r['group'])
    unique=[];pending=defaultdict(list);forms={}
    for _,b in sorted(buckets.items()):
        b['groups']=sorted(b['groups']);ss=set(b['status_by_ref'].values());b['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';unique.append(b)
        if'art_rework_group_pending'in ss:
            for g in b['groups']:pending[(b['form'],g)].append(b)
    counts=Counter(r['status']for r in j['references']);j['counts']['status_counts']=dict(counts)
    for g in j['groups']:g['status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==g['form']and r['ref']in g['refs']))
    write(o,j)
    for form in('base','fourth','ultimate_before','ultimate_after'):
        rr=[r for r in j['references']if r['form']==form];kk=[k for k in unique if k['form']==form];forms[form]={'native_reference_slots':len(rr),'decoded_slots':sum(r['structural_decode']for r in rr),'unique_visible_art_keys':len(kk),'reference_status_counts':dict(Counter(r['status']for r in rr)),'unique_key_status_counts':dict(Counter(k['status']for k in kk))}
    u={'scope':'최신PL00381d/PL0203a675 실제다시디코드한네폼 고유표시.부분mask/선택저장사본은제외.','definition':'같은폼의불투명bbox크기와RGBA전체가같은평행이동별칭만한키.원화장수·제작완료율아님.','source_ledger':ev(o),'candidates':j['current_candidates'],'counts':{'visible_unique_keys':len(unique),'unique_key_status_counts':dict(Counter(k['status']for k in unique)),'reference_status_counts':dict(counts),'empty_decoded_slots':empty},'forms':forms,'keys':unique,'pending_motion_groups':[{'form':f,'group':g,'unique_keys':len(v),'refs':sorted(set(n for b in v for n in b['refs']))}for(f,g),v in sorted(pending.items())],'prior_count_note':'16~18은기존동형묶음에상태만갱신했으므로현재정확한별칭집계가아님.19부터최신두ARC를재복원해갱신.지난집계수치차이를신작원화장수로해석하지않음.','review_coverage':'기존64주요시트와후속실제원화/재추출검토.모든부분조합실기완료아님.','full_art_unification_complete':False,'no_percent_estimated':True};write(H/'unique_art_keys19.json',u);print(json.dumps(u['counts']))
if __name__=='__main__':main()
