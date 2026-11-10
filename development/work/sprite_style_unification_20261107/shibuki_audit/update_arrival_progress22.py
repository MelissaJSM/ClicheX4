"""BR18의 동일 자원과 등장 미완료 원화를 구분한 장부22. 완료 수를 늘리지 않는다."""
from pathlib import Path
import sys,json,copy
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash

def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def main():
    out=H/'fullform_ledger22.json';need(not out.exists(),'Fresh ledger')
    binary=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v18/shibuki_riko.bin';bs='b0bc7e3105966fbca46bb28b6dd8e2ae5daf4b785cd1ffb203b0bdfde6bfcc88';need(file_hash(binary)==bs,'BR18 changed')
    resources,_=read_disc(binary,('PL00_U.ARC','PL02_U.ARC'));j=json.loads((H/'fullform_ledger21.json').read_text('utf8'));u=json.loads((H/'unique_art_keys21.json').read_text('utf8'))
    for name,c in j['current_candidates'].items():
        p=ROOT/c['path'];need(resources[name]==p.read_bytes(),'BR18 resource mismatch '+name);c.update(integrated=True,integrated_build='sprite_style_unification_20261107_v18',integrated_bin_sha256=bs,integration_readback_verified=True)
        u['candidates'][name]=copy.deepcopy(c)
    proof={'bin':{'path':binary.relative_to(ROOT).as_posix(),'sha256':bs},'resources':{name:sha(b)for name,b in resources.items()},'whole_resource_bytes_exact':True,'new_gameplay_performed':False,'source_pixel_inventory_reused_from21':True,'source_ledger':ev(H/'fullform_ledger21.json')}
    write(H/'br18_shibuki_source_identity.json',proof)
    j['active_integration']=ev(H/'br18_shibuki_source_identity.json');j['hurt13_new_scope']['base']=j['current_candidates']['PL00_U.ARC'];j['hurt13_new_scope']['ultimate']=j['current_candidates']['PL02_U.ARC']
    groups=[('ultimate_arrival_native01',(133,135),'ultimate_arrival_inputs01/page01'),('ultimate_arrival_native02',(137,138),'ultimate_arrival_inputs01/page02'),('ultimate_arrival_separate_native01',(136,139),'ultimate_arrival_separate_inputs02')]
    progress=[]
    for folder,refs,source in groups:
        for form in('before','after'):
            for ref in refs:
                state='registered_candidate_pending_common_layers';reason='固定셀 원화 등록. 공통관절/원효과/최종패킹은 별도.'
                if form=='after'and ref==135:state='blocked_local_edit_not_retried';reason='앞팔 관절 차이. 국소 생성이 출력 단계에서 거부되어 다른 프롬프트/도구로 재시도하지 않음.'
                elif form=='after'and ref in(138,139):state='rejected_sleeve_material';reason='수용 수영복형과 다르게 긴 흰 재킷 소매가 남음. 생성 원화부터 확인, 단순 피부색 치환으로 수용하지 않음.'
                elif ref==136:reason='실제136 자체 자세를 사용. 부모보다 발바닥1px 높음. 별도 접점/공통층 검토 전.'
                progress.append({'form':'ultimate_'+form,'ref':ref,'state':state,'reason':reason,'native':ev(H/folder/f'{form}_{ref:03}_indices.png'),'registration':ev(H/folder/'report.json'),'source':ev(H/source/'generated.png'),'arc_written':False,'frozen':False})
    j['next_generation']={'group':'Ultimate 등장','unique_body_keys':[133,135,136,137,138,139],'generated_form_images':12,'packed':False,'frozen':False,'status':'새12표시 고정 등록. after135 국소편집은 도구 거부로 미완료. after138/139는 흰 소매로 반려. 나머지도 공통층/효과/패킹 전이다.','per_form_progress':progress,'blocked_edit':ev(H/'ultimate_arrival135_arms01/generation_failure.json'),'relation':ev(H.parent/'zero_audit/shibuki_ultimate_arrival_relations01/report.json'),'page02_visual_review':ev(H/'ultimate_arrival_native02/author_visual_review.json'),'preserved_refs':[0,115,116,117,118,119,126,127,128,129,132,140,141,142]}
    for r in j['references']:
        found=next((p for p in progress if p['form']==r['form']and p['ref']==r['ref']),None)
        if found:r['candidate_progress']=copy.deepcopy(found)
    j['counts_unchanged_from21']=True;j['unaccepted_generated_art_in_integrated_assets']=False
    write(out,j);u['source_ledger']=ev(out);u['active_integration']=proof;u['unfinished_arrival_progress']=j['next_generation'];u['counts_unchanged_from21']=True;write(H/'unique_art_keys22.json',u)
    print(json.dumps({'ledger':ev(out),'unique_keys':ev(H/'unique_art_keys22.json'),'new_unpacked_form_images':12,'existing_counts':u['counts']['unique_key_status_counts']},ensure_ascii=False))
if __name__=='__main__':main()
