"""새Ultimate대시 준비본과 실기에서 발견한 기존2/4 잔여를 구분한다."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    o=H/'fullform_ledger12.json';need(not o.exists(),'Fresh ledger only');j=json.loads((H/'fullform_ledger11.json').read_text('utf8'));u=json.loads((H/'unique_art_keys11.json').read_text('utf8'));p=H/'prepared_ultimate_dash01/PL02_U.ARC';need(sha(p.read_bytes())=='bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb','Candidate changed');arcs={'base':Archive((H/'prepared_dash_base01/PL00_U.ARC').read_bytes()),'ultimate':Archive(p.read_bytes())};selected=set(range(67,85))|{93,94};keys={};pending=defaultdict(lambda:{'keys':set(),'refs':[]});empty=[]
    for r in j['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];arc=arcs['ultimate'if form.startswith('ultimate')else'base'];pix=np.array(arc.composite(n,r['effective_render_mask'])[0]);r['current_rgba_sha256']=sha(pix.tobytes());yy,xx=np.nonzero(pix[:,:,3]);r['opaque_pixels']=len(xx)
        if form.startswith('ultimate')and n in selected:r.update(status='new_art_prepared_pending_independent',decision='신규10몸체·8사격팔·원작속도선2로양의상40표시를무손실패킹. 재현3회/거부8/100층·640부분·256총열·344GPU 통과. 제작자8실제재추출판열람. 독립reader/원MIPS·GPU/root최종미술/실기는별도대기.',changed_from_reviewed_parent=True,new_candidate=p.relative_to(ROOT).as_posix())
        if form=='fourth'and n in(2,4):r.update(status='art_rework_group_pending',decision='v13 실제 armor15고정2→4→68에서 가슴이밝아짐. 정적0/2/4/68대조에도 기존2·4의흰가슴·칼라면적이넓어명암/의상묘사통일잔여로확정. 파츠누락이라고단정하지않음. 서서사격2는이동3..32외별도포함.')
        if not form.startswith('ultimate')and n in selected:r['runtime_followup']={'source':'root actual v13 report','base':'기본18/18 실제관측','fourth':'포스19/20 후68별도재시도양방향4관측','all_motion_or_user_acceptance_claim':False}
        if not len(xx):empty.append({'form':form,'ref':n,'status':r['status']});continue
        cut=pix[yy.min():yy.max()+1,xx.min():xx.max()+1].copy();cut[cut[:,:,3]==0]=0;k=sha(struct.pack('<HH',cut.shape[1],cut.shape[0])+cut.tobytes());v=keys.setdefault((form,k),{'form':form,'normalized_rgba_sha256':k,'size':[cut.shape[1],cut.shape[0]],'refs':[],'status_by_ref':{},'groups':set()});v['refs'].append(n);v['status_by_ref'][str(n)]=r['status'];v['groups'].add(r['group'])
        if r['status']=='art_rework_group_pending':pending[form,r['group']]['refs'].append(n);pending[form,r['group']]['keys'].add(k)
    kk=[]
    for _,v in sorted(keys.items()):ss=set(v['status_by_ref'].values());v['status']=next(iter(ss))if len(ss)==1 else'mixed_review_status';v['groups']=sorted(v['groups']);kk.append(v)
    counts=Counter(r['status']for r in j['references']);j['counts']['status_counts']=dict(counts);j['counts']['new_frozen_form_images']=counts['new_art_frozen_for_integration'];j['counts']['new_prepared_form_images']=counts['new_art_prepared_pending_independent']
    for g in j['groups']:g['status_counts']=dict(Counter(r['status']for r in j['references']if r['form']==g['form']and r['ref']in g['refs']))
    j['current_candidates']['PL02_U.ARC']={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'prepared_lock':ev(p.parent/'PREPARED_LOCK.json'),'independent_and_native_pending':True,'runtime_verified':False};j['current_candidates']['PL00_U.ARC']['new_dash20_gameplay_verified']='root표본관측과68추가관측으로별도기록';j.pop('unpacked_art_in_progress',None)
    j['priority_next']=[{'rank':1,'forms':['base','fourth'],'refs':list(range(3,33)),'additional_standing_shot_ref':2,'why':'기존이동머리·소매·의상질감과대기차이. 포스2/4는새실기및정적흰가슴면적차이확인.0/2→4→68연결기준.'},{'rank':2,'forms':['ultimate_before','ultimate_after'],'refs':list(range(143,156))+[183],'why':'후면머리의큰단색면·재킷/맨팔분리및사다리접점'},{'rank':3,'forms':['ultimate_before','ultimate_after'],'refs':list(range(126,143))+list(range(156,162))+list(range(204,208)),'why':'등장/승리/귀환앞뒤세밀화,기존광선보호'},{'rank':4,'forms':['base','fourth','ultimate_before','ultimate_after'],'refs':[85,86,87,88,89,90,91,92,95,96,97,208,209,210,211,212]+list(range(213,231)),'why':'잔여특수/호버/노바본체를실제도달성·효과와구별하여검토'}]
    j['new_evidence']={'standing_shot_root_static':ev(ROOT/'work/sprite_style_unification_20261107/runtime/fourth_fire_transition13/manifest.json'),'standing_shot_comparison_actually_viewed_by_ui':ev(ROOT/'work/sprite_style_unification_20261107/runtime/fourth_fire_transition13/comparison.png'),'dash68_actual_root_capture_manifest':ev(ROOT/'work/sprite_style_unification_20261107/runtime/shibuki_fourth_dash13_retry_review/manifest.json'),'selection_frame23':'root읽기검사상원선택23복귀기둥에옛주황입자잔존.루트별도동기화대상이며이대시PL02와분리.'};j['full_art_unification_complete']=False;write(o,j)
    u.update(source_ledger=ev(o),candidates=j['current_candidates'],keys=kk,counts={'visible_unique_keys':len(kk),'unique_key_status_counts':dict(Counter(k['status']for k in kk)),'reference_status_counts':dict(counts),'empty_decoded_slots':empty},pending_motion_groups=[{'form':f,'group':g,'unique_keys':len(v['keys']),'refs':sorted(v['refs'])}for(f,g),v in sorted(pending.items())]);
    for form,r in u['forms'].items():v=[k for k in kk if k['form']==form];r.update(unique_visible_art_keys=len(v),unique_key_status_counts=dict(Counter(x['status']for x in v)),reference_status_counts=dict(Counter(x['status']for x in j['references']if x['form']==form)))
    write(H/'unique_art_keys12.json',u);print(json.dumps(u['counts'],ensure_ascii=False))
if __name__=='__main__':main()
