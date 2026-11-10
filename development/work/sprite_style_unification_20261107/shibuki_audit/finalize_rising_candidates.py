"""원화와 자원 후보를 동결해 루트 통합/독립 감사용 제안서를 만든다."""
from pathlib import Path
import sys,json,subprocess,importlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from scripts.discover_inputs import psx_arc
from native_pose_pack import need,sha,write
REFS=[100,101,102,103,104,231,232]
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
    contactpath=H/'rising_packed_contact02/report.json';contact=json.loads(contactpath.read_text('utf8'));need(contact['passed'],'Final contact probe failed')
    rows=[]
    for typ,name,artifact,repro,native,packer,expected in[
      ('base','PL00_U.ARC','rising_base_pack_probe01','rising_base_reproduction01','rising_common_layers01','pack_rising_base_probe','5e6b8be38f59413938b8515c227b3142a06d4af4c9378645fb696ea145b47a3e'),
      ('ultimate','PL02_U.ARC','rising_ultimate_pack_probe01','rising_ultimate_reproduction01','rising_ultimate_shared02','pack_rising_ultimate_probe','71d02fe6d965c1fb42cc786766bad62372c792ccd8ecf6d5bc1e40dc8deb8597')]:
        out=H/f'prepared_rising_fire_{typ}01';need(not out.exists(),'Fresh proposal required');parentdir=H/f'prepared_double_cyclone_{typ}01';parent=(parentdir/name).read_bytes();candidate=(H/artifact/name).read_bytes();need(sha(candidate)==expected,'Wrong candidate');need(candidate==(H/repro/name).read_bytes(),'Reproduction differs')
        need(contact['sources'][typ]['candidate']==expected,'Wrong contact candidate');mod=importlib.import_module(packer);d=H/native;mod.validate_inputs(parent,d)
        allowed=np.zeros(len(parent),bool);changed_entries=[]
        for e in psx_arc(parent):
            if int(e['type'],16)in(2,3):allowed[e['offset']:e['offset']+e['size']]=True;changed_entries.append(e)
        need(len(parent)==len(candidate),'Archive size changed');delta=np.frombuffer(parent,np.uint8)!=np.frombuffer(candidate,np.uint8);need(not np.any(delta&~allowed),'Outside graphics/parts mutation')
        rejects=[];bad=bytearray(parent);bad[-1]^=1
        try:mod.validate_inputs(bytes(bad),d)
        except ValueError as e:rejects.append({'case':'wrong_parent','reason':str(e)})
        else:raise ValueError('Bad parent accepted')
        generation='rising_fire_inputs01/page01/generated.png'if typ=='base'else'rising_ultimate_costume01/page02/generated.png'
        for label,path in[('wrong_lock',d/'LOCK.json'),('changed_native',next(d.glob('*_indices.png'))),('changed_generation',H/generation)]:
            def read(p):
                v=p.read_bytes();return bytes([v[0]^1])+v[1:]if p==path else v
            try:mod.validate_inputs(parent,d,read)
            except ValueError as e:rejects.append({'case':label,'reason':str(e)})
            else:raise ValueError('Changed input accepted')
        for label,path in[('output_escape','../outside_not_written'),('existing_output',artifact)]:
            q=subprocess.run([sys.executable,'-B',str(H/(packer+'.py')),'--out',path],capture_output=True,text=True,cwd=ROOT);need(q.returncode!=0 and'ValueError'in q.stderr,'Invalid output accepted');rejects.append({'case':label,'reason':q.stderr.splitlines()[-1]})
        oldprop=json.loads((parentdir/'proposal.json').read_text('utf8'));prop={**oldprop};prop.pop('source_art',None)
        prop.update({'replaces':rel(parentdir/'proposal.json'),'selected_visual_refs':REFS,'source_art_manifest':rel(d/'LOCK.json'),'source_art_manifest_sha256':mod.LOCK_SHA,'parent_arc_sha256':sha(parent),'sequential_parent':{'path':rel(parentdir/name),'sha256':sha(parent)},'supersedes':parentdir.name,'scope':('기본/포스'if typ=='base'else'얼티밋 재킷/수영복')+' 라이징파이어100..104·231/232 새 머리/의상 세부묘사. 232는 현재 수용된231의 y+1 변환이며 원작 US 포즈 복원이라고 주장하지 않음. 효과·시간표·게임로직·팔레트 불변.','static_review_passed':True,'native_cpu_pending':True,'independent_review_pending':True,'actual_gameplay_pending':True})
        prop['files']={**oldprop['files'],name:{**oldprop['files'][name],'path':rel(out/name),'after':expected}}
        producer=json.loads((H/artifact/'report.json').read_text('utf8'));readbackfiles=sorted((H/artifact).glob('*_readback_*.png'))
        proof={'passed':True,'parent_sha256':sha(parent),'candidate_sha256':expected,'reproduction_exact':True,'input_rejections':rejects,'changed_bytes':int(delta.sum()),'outside_2_3_exact_bytes':int((~allowed).sum()),'changed_entries':changed_entries,'producer':producer,'native_effect_initializer_cases':len(contact['native_initializer_cases']),'native_effect_initializers_not_full_gameplay':True,'contact_report':rel(contactpath),'contact_report_sha256':sha(contactpath.read_bytes()),'normal_contact_preserved':True,'charged_contact_spatial_only':True,'author_actual_readback_review':[{'path':rel(p),'sha256':sha(p.read_bytes())}for p in readbackfiles],'limitations':contact['limitations'],'runtime_verified':False,'independent_pending':True,'root_review_pending':True,'full_draw_mips_pending':True}
        out.mkdir();(out/name).write_bytes(candidate);write(out/'proposal.json',prop);write(out/'verification.json',proof)
        scripts=[packer+'.py','finalize_rising_candidates.py','audit_rising_packed_contact.py']
        write(out/'INPUT_FROZEN.json',{'candidate_and_source_frozen':True,'files':{p:sha((out/p).read_bytes())for p in(name,'proposal.json','verification.json')},'source_lock_sha256':mod.LOCK_SHA,'producer_scripts':{p:sha((H/p).read_bytes())for p in scripts},'user_accepted':False,'actual_gameplay_verified':False,'independent_review_pending':True,'full_draw_mips_pending':True})
        rows.append({'type':typ,'path':rel(out/'proposal.json'),'sha256':expected,'rejections':len(rejects)})
    print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
