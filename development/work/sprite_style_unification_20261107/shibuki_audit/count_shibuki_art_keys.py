"""폼별 중복 표시를 제거한 실제 그림 키와 남은 동작 장부를 집계한다.

제작 난이도/완료율을 추정하지 않는다. 색/자세가 완전히 같은 그림의 평행이동만 묶는다.
"""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write
NEW=(100,101,102,103,104,231,232)
def main():
    q=json.loads((H/'fullform_ledger05.json').read_text('utf8'));arcs={}
    for kind,name in(('base','PL00_U.ARC'),('ultimate','PL02_U.ARC')):
        folder=H/f'prepared_rising_fire_{kind}01';prop=json.loads((folder/'proposal.json').read_text('utf8'));data=(folder/name).read_bytes();need(sha(data)==prop['files'][name]['after'],'Prepared changed');arcs[kind]=Archive(data)
        q['current_candidates'][name]={'path':(folder/name).relative_to(ROOT).as_posix(),'sha256':sha(data),'input_frozen_record':(folder/'INPUT_FROZEN.json').relative_to(ROOT).as_posix(),'independent_and_full_native_pending':True}
    buckets={};empty=[]
    for row in q['references']:
        if not row['structural_decode']:continue
        form=row['form'];n=row['ref'];a=arcs['ultimate'if form.startswith('ultimate')else'base'];mask=15 if form in('fourth','ultimate_before')else 0
        # Ultimate213..230 may use the dedicated native effect layers. The
        # existing ledger supplies the effective mask used by this exporter.
        mask=row.get('effective_render_mask',mask)
        im=a.composite(n,mask)[0];pix=np.array(im);row['current_rgba_sha256']=sha(pix.tobytes())
        if n in NEW:row.update(status='new_art_prepared_awaiting_independent',changed_from_reviewed_parent=True,decision='새 라이징파이어7참조 입력동결/원화 exact/부분조합/기존효과접점 검사 완료. 루트 full-native·독립감사·실기·사용자수용 별도.')
        if form=='fourth'and n==103:row.update(status='art_local_material_correction_required',decision='루트 packed 재검토에서 들린 소매의 흰/붉은 재질을 확정 결함으로 판단. 새 원화 소매만 검정/보라로 국소 교정 예정. 첫 PL00 후보 보류.')
        ys,xs=np.nonzero(pix[:,:,3]);row['opaque_pixels']=int(len(xs))
        if not len(xs):empty.append({'form':form,'ref':n,'status':row['status']});continue
        crop=pix[ys.min():ys.max()+1,xs.min():xs.max()+1].copy();crop[crop[:,:,3]==0]=0
        key=sha(struct.pack('<HH',crop.shape[1],crop.shape[0])+crop.tobytes());bucket=buckets.setdefault((form,key),{'form':form,'normalized_rgba_sha256':key,'size':[crop.shape[1],crop.shape[0]],'refs':[],'origins':[],'status_by_ref':{},'groups':set()})
        bucket['refs'].append(n);bucket['origins'].append([n,int(xs.min())-160,int(ys.min())-160]);bucket['status_by_ref'][str(n)]=row['status'];bucket['groups'].add(row['group'])
    unique=[];performs={};pending_bygroup=defaultdict(list)
    for (form,key),b in sorted(buckets.items()):
        b['groups']=sorted(b['groups']);statuses=set(b['status_by_ref'].values());b['status']=next(iter(statuses))if len(statuses)==1 else'mixed_review_status';b['refs'].sort();unique.append(b)
        if'art_rework_group_pending'in statuses:
            for g in b['groups']:pending_bygroup[(form,g)].append({'key':key,'refs':b['refs']})
    for form in('base','fourth','ultimate_before','ultimate_after'):
        rr=[r for r in q['references']if r['form']==form];kk=[k for k in unique if k['form']==form]
        performs[form]={'native_reference_slots':len(rr),'decoded_slots':sum(r['structural_decode']for r in rr),'unique_visible_art_keys':len(kk),'reference_status_counts':dict(Counter(r['status']for r in rr)),'unique_key_status_counts':dict(Counter(k['status']for k in kk))}
    counts=Counter(r['status']for r in q['references']);q['counts']['status_counts']=dict(counts);q['counts']['new_prepared_form_images']=counts['new_art_prepared_awaiting_independent'];need(counts['new_art_prepared_awaiting_independent']+counts['art_local_material_correction_required']==28,'New coverage mismatch')
    q['current_candidates']['PL00_U.ARC']['held_for_fourth103_sleeve_correction']=True
    for group in q['groups']:group['status_counts']=dict(Counter(r['status']for r in q['references']if r['form']==group['form']and r['ref']in group['refs']))
    q['priority_next'][0]['why']='네 폼7참조 첫 패킹·접점 검증. 포스103 들린 소매의 흰/붉은 재질은 루트 확정 교정 대상으로 첫 PL00 후보 보류. Ultimate는 독립감사/full-native 대기.'
    actual=[]
    for folder,pattern in [('rising_base_pack_probe01','*_readback_*.png'),('rising_ultimate_pack_probe01','*_readback_*.png'),('rising_packed_contact02','*_spatial.png')]:
        actual.extend({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in sorted((H/folder).glob(pattern)))
    actual.extend({'path':(H/'rising_base_pack_probe01'/f'{n:03}_partial.png').relative_to(ROOT).as_posix(),'sha256':sha((H/'rising_base_pack_probe01'/f'{n:03}_partial.png').read_bytes())}for n in NEW)
    q['review_basis']['rising_fire_packed_and_partial_actual_viewed']=actual;q['review_basis']['rising_fire_effect_limitations']='원래 초기화MIPS16조건/일반 지상·공중 좌우16접점. 차지 위상·물리·실기 미검증.'
    q['full_art_unification_complete']=False;write(H/'fullform_ledger06.json',q)
    report={'scope':'시부키 네 폼 최신 준비자원 기준, 부분16mask/선택저장사본은 중복 집계에서 제외','definition':'같은 폼 안에서 불투명 bbox로 자른 RGBA가 크기와 모든 픽셀까지 같으면 평행이동 별칭을 하나의 그림 키로 계산. 다른색/눈깜박임/다른의상은 별도 키. 생성 원화 장수나 소요시간/완료율이 아님.','review_coverage':'기존 주요64시트 실제열람 + 후속 원화/재독출. 모든부분조합을 실기에서 봤다는 뜻 아님.','source_ledger':{'path':(H/'fullform_ledger06.json').relative_to(ROOT).as_posix(),'sha256':sha((H/'fullform_ledger06.json').read_bytes())},'candidates':q['current_candidates'],'counts':{'visible_unique_keys':len(unique),'unique_key_status_counts':dict(Counter(k['status']for k in unique)),'reference_status_counts':dict(counts),'empty_decoded_slots':empty},'forms':performs,'keys':unique,'pending_motion_groups':[{'form':form,'group':g,'unique_keys':len(v),'refs':sorted(set(n for x in v for n in x['refs']))}for(form,g),v in sorted(pending_bygroup.items())],'full_art_unification_complete':False,'no_percent_estimated':True}
    write(H/'unique_art_keys06.json',report)
    lines=['# 시부키 고유 표시 키 집계','',report['definition'],'','완료율로 환산하지 않는다. 동결은 통합용 미술/기술 검사 단계이며 사용자 전체 실기 수용과 다르다.','', '| 폼 | 참조 슬롯 | 디코딩 | 중복 제거 그림 키 |','| --- | ---: | ---: | ---: |']
    for f,v in performs.items():lines.append(f"| {f} | {v['native_reference_slots']} | {v['decoded_slots']} | {v['unique_visible_art_keys']} |")
    lines+=['','## 상태별 고유 그림 키','']+[f'- `{k}`: {v}'for k,v in report['counts']['unique_key_status_counts'].items()]
    lines+=['','## 남은 핵심 동작군','']+[f"- {r['form']} / {r['group']}: {r['unique_keys']}개 키, refs {','.join(map(str,r['refs']))}"for r in report['pending_motion_groups']]
    lines+=['','효과/탑승 머리와 일부 유사 준비자세는 재생성 확정과 추가 검토가 섞여 있다. 따라서 pending 전체를 새 원화 필요 장수라고 부르지 않는다.','Rising Fire28표시는 이번 준비본이며 현재 v9 적용범위와 구분한다.','포스103 소매의 흰/붉은 새 원화 재질은 루트 확정 교정 대상이다. 첫 PL00 제안은 보류하고 국소 수정본을 별도로 만든다.']
    (H/'UNIQUE_ART_KEYS.md').write_text('\n'.join(lines)+'\n','utf8');print(json.dumps({'counts':report['counts'],'forms':performs},ensure_ascii=False))
if __name__=='__main__':main()
