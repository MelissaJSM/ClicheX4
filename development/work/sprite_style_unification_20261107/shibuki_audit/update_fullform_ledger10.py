"""Ultimate 공중22 동결을 고유 표시 키 장부에 반영. 대시는 미완료 유지."""
from pathlib import Path
from collections import Counter,defaultdict
import json,struct,sys
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def evidence(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    out=H/'fullform_ledger10.json';need(not out.exists(),'Fresh ledger required');q=json.loads((H/'fullform_ledger09.json').read_text('utf8'));u=json.loads((H/'unique_art_keys09.json').read_text('utf8'));arcs={}
    for kind,name,folder in(('base','PL00_U.ARC','prepared_rising_right_base01'),('ultimate','PL02_U.ARC','prepared_ultimate_air01')):
        d=H/folder;frozen=json.loads((d/'FROZEN.json').read_text('utf8'));data=(d/name).read_bytes();need(frozen['frozen']and sha(data)==frozen['files'][name],'Changed frozen resource');arcs[kind]=Archive(data)
        q['current_candidates'][name]={'path':(d/name).relative_to(ROOT).as_posix(),'sha256':sha(data),'frozen_record':evidence(d/'FROZEN.json'),'independent_and_full_native_pending':False,'new_air22_gameplay_verified':False}
    groups={};empty=[];pending=defaultdict(lambda:{'keys':set(),'refs':[]})
    for r in q['references']:
        if not r['structural_decode']:continue
        form,n=r['form'],r['ref'];a=arcs['ultimate'if form.startswith('ultimate')else'base'];mask=r['effective_render_mask'];pix=np.array(a.composite(n,mask)[0]);r['current_rgba_sha256']=sha(pix.tobytes())
        if form.startswith('ultimate')and 33<=n<=54:
            r['status']='new_art_frozen_for_integration';r['decision']='새공중11몸체/11사격짝44표시. 새원화전체의미영역·원총구34총열모듈·공통머리/다리·32타일. 제작/독립/원MIPS·GPU/최종8판루트미술검수후동결. 아직새통합BIN실기·사용자최종수용없음.';r['changed_from_reviewed_parent']=True
        yy,xx=np.nonzero(pix[:,:,3]);r['opaque_pixels']=int(len(xx))
        if not len(xx):empty.append({'form':form,'ref':n,'status':r['status']});continue
        crop=pix[yy.min():yy.max()+1,xx.min():xx.max()+1].copy();crop[crop[:,:,3]==0]=0;k=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes())
        g=groups.setdefault((form,k),{'form':form,'normalized_rgba_sha256':k,'size':[crop.shape[1],crop.shape[0]],'refs':[],'status_by_ref':{},'groups':set()});g['refs'].append(n);g['status_by_ref'][str(n)]=r['status'];g['groups'].add(r['group'])
        if r['status']=='art_rework_group_pending':pending[(form,r['group'])]['keys'].add(k);pending[(form,r['group'])]['refs'].append(n)
    keys=[]
    for _,g in sorted(groups.items()):
        states=set(g['status_by_ref'].values());g['status']=next(iter(states))if len(states)==1 else'mixed_review_status';g['groups']=sorted(g['groups']);keys.append(g)
    states=Counter(r['status']for r in q['references']);q['counts']['status_counts']=dict(states);q['counts']['new_frozen_form_images']=states['new_art_frozen_for_integration'];q['counts']['new_prepared_form_images']=0
    for g in q['groups']:g['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==g['form']and r['ref']in g['refs']))
    q['unpacked_art_in_progress']={'group':'기본/포스 대시·공중대시67..84/93/94','body_keys':[67,69,71,75,77,79,81,83,93,94],'source_body_form_images':20,'generated_body_pages':4,'reviewed_native_comparison_sheets':8,'pending_local_repaint':[81,83],'registered_first12':evidence(H/'dash_detail_contacts01/report.json'),'shooting_and_partial_packing_pending':True,'ultimate_dash_all20_pending':True,'not_counted_as_frozen':True}
    q['right_hand_followup']['new_gameplay_verified']=True;q['right_hand_followup']['new_gameplay_scope']='루트BR11 actual352창·28고유참조/12판에서Ultimate후폼103/104양방향관측. 다른세의상실기까지확대하지않음.'
    q['full_art_unification_complete']=False;write(out,q)
    u.update({'source_ledger':evidence(out),'candidates':q['current_candidates'],'keys':keys,'counts':{'visible_unique_keys':len(keys),'unique_key_status_counts':dict(Counter(g['status']for g in keys)),'reference_status_counts':dict(states),'empty_decoded_slots':empty},'pending_motion_groups':[{'form':f,'group':g,'unique_keys':len(v['keys']),'refs':sorted(v['refs'])}for(f,g),v in sorted(pending.items())]})
    for form,row in u['forms'].items():
        selected=[g for g in keys if g['form']==form];row['unique_visible_art_keys']=len(selected);row['reference_status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==form));row['unique_key_status_counts']=dict(Counter(g['status']for g in selected))
    write(H/'unique_art_keys10.json',u);print(json.dumps(u['counts'],ensure_ascii=False))
if __name__=='__main__':main()
