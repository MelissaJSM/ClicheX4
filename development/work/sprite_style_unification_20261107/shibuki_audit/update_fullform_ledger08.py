"""새 동결/보류 해제를 반영하되 미완료 미술을 완료율로 계산하지 않는다."""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write
def main():
    out=H/'fullform_ledger08.json';need(not out.exists(),'Fresh ledger required');q=json.loads((H/'fullform_ledger06.json').read_text('utf8'));arcs={}
    for kind,name,folder in[('base','PL00_U.ARC','prepared_rising_fire_base02'),('ultimate','PL02_U.ARC','prepared_rising_fire_ultimate01')]:
        d=H/folder;prop=json.loads((d/'proposal.json').read_text('utf8'));data=(d/name).read_bytes();need(sha(data)==prop['files'][name]['after'],'Wrong candidate');arcs[kind]=Archive(data);frozen=d/'FROZEN.json'
        q['current_candidates'][name]={'path':(d/name).relative_to(ROOT).as_posix(),'sha256':sha(data),'input_frozen_record':(d/'INPUT_FROZEN.json').relative_to(ROOT).as_posix(),'frozen_record':frozen.relative_to(ROOT).as_posix()if frozen.exists()else None,'independent_and_full_native_pending':not frozen.exists()}
    grouped={};empty=[]
    for row in q['references']:
        if not row['structural_decode']:continue
        f=row['form'];n=row['ref'];typ='ultimate'if f.startswith('ultimate')else'base';a=arcs[typ];mask=row.get('effective_render_mask',15 if f in('fourth','ultimate_before')else 0);pix=np.array(a.composite(n,mask)[0]);row['current_rgba_sha256']=sha(pix.tobytes())
        if n in(100,101,102,103,104,231,232):
            row['status']='new_art_frozen_for_integration';row['decision']='새 라이징파이어 전체 원화·35층 등록 완료. '+('독립 감사 및 원MIPS/GPU·루트 실제10시트 열람으로 동결. 실제 플레이/사용자 수용 별도.'if typ=='ultimate'else'포스103 소매58px 국소 교정 v2의 독립 감사·원MIPS/GPU·루트 국소 비교 열람으로 동결. v1 반려본은 불변 보존. 실제 플레이/사용자 수용 별도.')
        yy,xx=np.nonzero(pix[:,:,3]);row['opaque_pixels']=int(len(xx))
        if not len(xx):empty.append({'form':f,'ref':n,'status':row['status']});continue
        crop=pix[yy.min():yy.max()+1,xx.min():xx.max()+1].copy();crop[crop[:,:,3]==0]=0;k=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes());b=grouped.setdefault((f,k),{'form':f,'normalized_rgba_sha256':k,'size':[crop.shape[1],crop.shape[0]],'refs':[],'status_by_ref':{},'groups':set()});b['refs'].append(n);b['status_by_ref'][str(n)]=row['status'];b['groups'].add(row['group'])
    unique=[]
    for k,b in sorted(grouped.items()):
        s=set(b['status_by_ref'].values());b['status']=next(iter(s))if len(s)==1 else'mixed_review_status';b['groups']=sorted(b['groups']);unique.append(b)
    q['counts']['status_counts']=dict(Counter(r['status']for r in q['references']));q['counts']['new_prepared_form_images']=0
    for g in q['groups']:g['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==g['form']and r['ref']in g['refs']))
    q['review_basis']['local103_v2_actual_viewed']=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in sorted((H/'rising_base_pack_probe02').glob('*_readback_*.png'))]+[{'path':(H/'rising_base_pack_probe02/103_partial.png').relative_to(ROOT).as_posix(),'sha256':sha((H/'rising_base_pack_probe02/103_partial.png').read_bytes())}]
    q['priority_next'][0]={'group':'Ultimate air33..54','refs':list(range(33,55)),'why':'현재 머리/재킷이 큰 단색면이며 선글라스/칼라와 손발 재질도 대기와 밀도 차이. 새 기본 공중 관절을 의상 편집의 기준으로 삼되 Ultimate 대기 정체성·동일 총구·폼 전후 공통 머리/다리 보존.'};q['full_art_unification_complete']=False;write(out,q)
    old=json.loads((H/'unique_art_keys06.json').read_text('utf8'));old['source_ledger']={'path':out.relative_to(ROOT).as_posix(),'sha256':sha(out.read_bytes())};old['candidates']=q['current_candidates'];old['keys']=unique;old['counts']={'visible_unique_keys':len(unique),'unique_key_status_counts':dict(Counter(k['status']for k in unique)),'reference_status_counts':q['counts']['status_counts'],'empty_decoded_slots':empty}
    for f,v in old['forms'].items():v['reference_status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==f));v['unique_key_status_counts']=dict(Counter(k['status']for k in unique if k['form']==f))
    write(H/'unique_art_keys08.json',old);print(json.dumps(old['counts'],ensure_ascii=False))
if __name__=='__main__':main()
