"""기본/포스 대시20 동결과 Ultimate 대시 미완료를 별개로 기록한다."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def evidence(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    out=H/'fullform_ledger11.json';need(not out.exists(),'Fresh ledger');q=json.loads((H/'fullform_ledger10.json').read_text('utf8'));u=json.loads((H/'unique_art_keys10.json').read_text('utf8'));arcs={}
    for kind,name,folder in(('base','PL00_U.ARC','prepared_dash_base01'),('ultimate','PL02_U.ARC','prepared_ultimate_air01')):
        d=H/folder;lock=json.loads((d/'FROZEN.json').read_text('utf8'));data=(d/name).read_bytes();need(lock['frozen']and sha(data)==lock['files'][name],'Frozen resource changed');arcs[kind]=Archive(data);q['current_candidates'][name]={'path':(d/name).relative_to(ROOT).as_posix(),'sha256':sha(data),'frozen_record':evidence(d/'FROZEN.json'),'independent_and_full_native_pending':False,'new_dash20_gameplay_verified':False}
    groups={};pending=defaultdict(lambda:{'keys':set(),'refs':[]});empty=[];selected=set(range(67,85))|{93,94}
    for r in q['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];a=arcs['ultimate'if form.startswith('ultimate')else'base'];pix=np.array(a.composite(n,r['effective_render_mask'])[0]);r['current_rgba_sha256']=sha(pix.tobytes())
        if not form.startswith('ultimate')and n in selected:r.update({'status':'new_art_frozen_for_integration','decision':'대시10몸체+사격8+원속도선2 신규세밀화. 새머리/의상 원화·원34총열모듈/총구·원9속도선파츠/타일·32타일/부분640 검증. 독립reader/원MIPS·GPU/root14판 실제미술검토후동결. 새통합BIN실기·사용자최종수용은아직없음.','changed_from_reviewed_parent':True})
        yy,xx=np.nonzero(pix[:,:,3]);r['opaque_pixels']=len(xx)
        if not len(xx):empty.append({'form':form,'ref':n,'status':r['status']});continue
        cut=pix[yy.min():yy.max()+1,xx.min():xx.max()+1].copy();cut[cut[:,:,3]==0]=0;k=sha(struct.pack('<HH',cut.shape[1],cut.shape[0])+cut.tobytes());g=groups.setdefault((form,k),{'form':form,'normalized_rgba_sha256':k,'size':[cut.shape[1],cut.shape[0]],'refs':[],'status_by_ref':{},'groups':set()});g['refs'].append(n);g['status_by_ref'][str(n)]=r['status'];g['groups'].add(r['group'])
        if r['status']=='art_rework_group_pending':pending[form,r['group']]['keys'].add(k);pending[form,r['group']]['refs'].append(n)
    keys=[]
    for _,g in sorted(groups.items()):states=set(g['status_by_ref'].values());g['status']=next(iter(states))if len(states)==1 else'mixed_review_status';g['groups']=sorted(g['groups']);keys.append(g)
    states=Counter(r['status']for r in q['references']);q['counts']['status_counts']=dict(states);q['counts']['new_frozen_form_images']=states['new_art_frozen_for_integration'];q['counts']['new_prepared_form_images']=0
    for g in q['groups']:g['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==g['form']and r['ref']in g['refs']))
    q['unpacked_art_in_progress']={'group':'Ultimate 전후 대시20참조','body_keys':[67,69,71,75,77,79,81,83,93,94],'new_source_first_page_keys':[67,69,71],'new_source_form_images':6,'first_page_common_and_contacts':evidence(H/'ultimate_dash_contacts02/report.json'),'remaining_body_pages':3,'all8_firing_pairs_pending':True,'root_candidate_art_review_pending':True,'not_counted_as_frozen':True};q['full_art_unification_complete']=False;write(out,q)
    u.update({'source_ledger':evidence(out),'candidates':q['current_candidates'],'keys':keys,'counts':{'visible_unique_keys':len(keys),'unique_key_status_counts':dict(Counter(k['status']for k in keys)),'reference_status_counts':dict(states),'empty_decoded_slots':empty},'pending_motion_groups':[{'form':f,'group':g,'unique_keys':len(v['keys']),'refs':sorted(v['refs'])}for(f,g),v in sorted(pending.items())]})
    for form,r in u['forms'].items():kk=[k for k in keys if k['form']==form];r['unique_visible_art_keys']=len(kk);r['unique_key_status_counts']=dict(Counter(k['status']for k in kk));r['reference_status_counts']=dict(Counter(v['status']for v in q['references']if v['form']==form))
    write(H/'unique_art_keys11.json',u);print(json.dumps(u['counts'],ensure_ascii=False))
if __name__=='__main__':main()
