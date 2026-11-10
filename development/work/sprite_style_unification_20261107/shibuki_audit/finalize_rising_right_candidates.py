"""오른손 발사점 교정 두 자원을 재현/거부검사 후 별도 통합 제안으로 동결한다."""
from pathlib import Path
import sys,json,subprocess,importlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
    configs=[('base','PL00_U.ARC','prepared_rising_fire_base02','rising_right_base_pack02','rising_right_base_reproduction02','rising_right_base_layers02','pack_rising_right_base02','prepared_rising_right_base01','13a29023365419d32475cf5a6551adc4658116c8f03622d962d5b8071744e8b8'),('ultimate','PL02_U.ARC','prepared_rising_fire_ultimate01','rising_right_ultimate_pack01','rising_right_ultimate_reproduction01','rising_right_ultimate_shared02','pack_rising_right_ultimate01','prepared_rising_right_ultimate01','d636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d')]
    contact=H/'rising_right_packed_contact01/report.json';need(json.loads(contact.read_text('utf8'))['passed'],'Contact not passed');summary=[]
    for form,name,parentdir,artifactdir,reprodir,locked,producer,outdir,expected in configs:
        parent=H/parentdir;artifact=H/artifactdir;d=H/locked;out=H/outdir;need(not out.exists(),'Fresh prepared only')
        data=(artifact/name).read_bytes();baseline=(parent/name).read_bytes();need(sha(data)==expected,'Candidate changed');need(data==(H/reprodir/name).read_bytes(),'Reproduction differs')
        mod=importlib.import_module(producer);mod.validate_inputs(baseline,d);rejects=[]
        bad=bytearray(baseline);bad[-1]^=1
        try:mod.validate_inputs(bytes(bad),d)
        except ValueError as e:rejects.append({'case':'wrong_parent','reason':str(e)})
        else:raise ValueError('Wrong parent accepted')
        lock=json.loads((d/'LOCK.json').read_text('utf8'));target=d/next(iter(lock['files']));source=H/next(name for name in lock['source_files']if name.endswith('generated.png'))
        for label,path in [('wrong_lock',d/'LOCK.json'),('changed_native',target),('changed_generation',source)]:
            def read(p):
                raw=p.read_bytes();return bytes([raw[0]^1])+raw[1:]if p==path else raw
            try:mod.validate_inputs(baseline,d,read)
            except ValueError as e:rejects.append({'case':label,'reason':str(e)})
            else:raise ValueError('Modified source accepted')
        for label,path in [('output_escape','../outside_not_written'),('existing_output',artifactdir)]:
            result=subprocess.run([sys.executable,'-B',str(H/(producer+'.py')),'--out',path],cwd=ROOT,capture_output=True,text=True)
            need(result.returncode!=0 and'ValueError'in result.stderr,'Bad destination accepted');rejects.append({'case':label,'reason':result.stderr.splitlines()[-1]})
        prop=json.loads((parent/'proposal.json').read_text('utf8'));prop['files'][name]['path']=rel(out/name);prop['files'][name]['after']=expected
        prop['replaces']=rel(parent/'proposal.json');prop['supersedes']=parentdir;prop['selected_visual_refs']=[103,104];prop['parent_arc_sha256']=sha(baseline);prop['sequential_parent']={'path':rel(parent/name),'sha256':sha(baseline)}
        prop['source_art_manifest']=rel(d/'LOCK.json');prop['source_art_manifest_sha256']=mod.LOCK_SHA
        prop['scope']='원US 공중 일반 라이징파이어의 오른쪽 발사손에 맞춰103 준비→104 상승 자세를 교정. 기존 세밀한 머리/의상 방향 유지. 전신반전·효과이동·시간표·게임로직 변경 없음. 100..102/231/232 및 기타 모든 참조 보존.'
        prop['runtime_bug_evidence']={'path':rel(H/'rising_runtime_followup01/report.json'),'sha256':sha((H/'rising_runtime_followup01/report.json').read_bytes())}
        prop['static_review_passed']=True;prop['native_cpu_pending']=True;prop['independent_review_pending']=True;prop['actual_gameplay_pending']=True
        prop.pop('supersedes_rejected_candidate',None)
        images=sorted(artifact.glob('*_readback_*.png'))+sorted(artifact.glob('*_partial.png'))
        proof={'passed':True,'candidate_sha256':expected,'parent_sha256':sha(baseline),'reproduction_exact':True,'input_rejections':rejects,'source_lock_sha256':mod.LOCK_SHA,'producer':json.loads((artifact/'report.json').read_text('utf8')),'contact_evidence':{'path':rel(contact),'sha256':sha(contact.read_bytes())},'source_art_changes':{'wrong_raised_hand_side_fixed':True,'new_right_hand_native_height':[-30,-26],'whole_body_mirror_or_scale':False,'old_coarse_art_copied':False,'base_alpha224_unique_body_not_alpha240':form=='base','alpha240_intermediate_rejected':form=='base','ultimate103_whole_pose_translation':[0,1]if form=='ultimate'else[0,0]},'source_alpha_check':{'path':rel(H/'rising_right_hand_native05/report.json'),'sha256':sha((H/'rising_right_hand_native05/report.json').read_bytes())},'author_actual_readback_review':[{'path':rel(p),'sha256':sha(p.read_bytes())}for p in images],'independent_pending':True,'native_full_draw_mips_pending':True,'native_effect_initializer_checked':True,'root_final_readback_pending':True,'emulator_gameplay_verified':False,'user_accepted':False,'previous_test_limitation':'이전 v10 접점 감사는 구형 시부키의 반대쪽 손을 기준으로 삼았다. 이번은 원US 발원점/발사손 의미를 별도로 대조함.'}
        out.mkdir();(out/name).write_bytes(data);write(out/'proposal.json',prop);write(out/'verification.json',proof)
        write(out/'INPUT_FROZEN.json',{'candidate_and_source_frozen':True,'files':{p:sha((out/p).read_bytes())for p in(name,'proposal.json','verification.json')},'source_lock_sha256':mod.LOCK_SHA,'producer_scripts':{producer+'.py':sha((H/(producer+'.py')).read_bytes()),'finalize_rising_right_candidates.py':sha(Path(__file__).read_bytes())},'user_accepted':False,'actual_gameplay_verified':False,'independent_review_pending':True,'full_draw_mips_pending':True})
        summary.append({'proposal':rel(out/'proposal.json'),'candidate_sha256':expected,'rejects':len(rejects)})
    print(json.dumps(summary))
if __name__=='__main__':main()
