"""포스103 소매 수정본을 별도 재현/거부 검사와 함께 준비한다."""
from pathlib import Path
import sys,json,subprocess
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from src.psx_player import decode_stream
import pack_rising_base_v2 as mod
TARGET='008eb1df4809fe6f8e7002604f98abbe58c885265cfa63a688105f9acf4d29ce'
def rel(p):return p.relative_to(ROOT).as_posix()
def main():
    d=H/'rising_common_layers02';artifact=H/'rising_base_pack_probe02';out=H/'prepared_rising_fire_base02';need(not out.exists(),'Fresh candidate required')
    data=(artifact/'PL00_U.ARC').read_bytes();need(sha(data)==TARGET,'Wrong v2 candidate');need(data==(H/'rising_base_reproduction02/PL00_U.ARC').read_bytes(),'Reproduction mismatch')
    parent=(H/'prepared_double_cyclone_base01/PL00_U.ARC').read_bytes();mod.validate_inputs(parent,d)
    first=H/'prepared_rising_fire_base01';old=Archive((first/'PL00_U.ARC').read_bytes());new=Archive(data);need(old.c==new.c,'Local correction altered composition');need(old.p==new.p,'Palette changed')
    allowed=np.array(Image.open(H/'rising103_sleeve_native03/allowed_sleeve_mask.png'))>0;layers=rawcount=conditions=0
    for gb,bb in enumerate(old.banks):
        for f,g in zip(bb['frames'],new.banks[gb]['frames']):
            if gb==0 and f['index']==103:continue
            a=decode_stream(old.g,f['offset'],f['limit'],f['tile_count']*128).data;b=decode_stream(new.g,g['offset'],g['limit'],g['tile_count']*128).data
            need(a==b,'Other raw changed relative to v1');rawcount+=1
    for ref in range(237):
        if ref in{105,*range(175,183)}:continue
        for bank in(0,5,6,7,8):
            a=old.layer(ref,bank)[0];b=new.layer(ref,bank)[0]
            if(ref,bank)==(103,7):need(np.array_equal(a[~allowed],b[~allowed]),'Outside sleeve changed');need(np.array_equal(a>0,b>0),'Alpha changed')
            else:need(np.array_equal(a,b),'Another visible layer changed');layers+=1
    for mask in range(16):
        for arm in(1,2):
            a=np.array(old.composite(103,mask,arm)[0]);b=np.array(new.composite(103,mask,arm)[0]);delta=np.any(a!=b,2)
            need(not np.any(delta&~allowed),'Partial alpha/color outside sleeve changed');need(np.array_equal(a[:,:,3],b[:,:,3]),'Partial alpha changed')
            need(int(delta.sum())==(58 if mask&4 else 0),'Wrong mask sleeve visibility');conditions+=1
    rejects=[];bad=bytearray(parent);bad[-1]^=1
    try:mod.validate_inputs(bytes(bad),d)
    except ValueError as e:rejects.append({'case':'wrong_parent','reason':str(e)})
    else:raise ValueError('Wrong parent accepted')
    for label,path in [('wrong_lock',d/'LOCK.json'),('changed_native',d/'103_bank7_indices.png'),('changed_generation',H/'rising103_sleeve_edit01/generated.png')]:
        def read(p):
            v=p.read_bytes();return bytes([v[0]^1])+v[1:] if p==path else v
        try:mod.validate_inputs(parent,d,read)
        except ValueError as e:rejects.append({'case':label,'reason':str(e)})
        else:raise ValueError('Mutated source accepted')
    for label,path in[('output_escape','../outside_not_written'),('existing_output','rising_base_pack_probe02')]:
        r=subprocess.run([sys.executable,'-B',str(H/'pack_rising_base_v2.py'),'--out',path],cwd=ROOT,capture_output=True,text=True);need(r.returncode!=0 and'ValueError'in r.stderr,'Invalid output accepted');rejects.append({'case':label,'reason':r.stderr.splitlines()[-1]})
    prop=json.loads((first/'proposal.json').read_text('utf8'));prop['files']['PL00_U.ARC']['path']=rel(out/'PL00_U.ARC');prop['files']['PL00_U.ARC']['after']=TARGET;prop['source_art_manifest']=rel(d/'LOCK.json');prop['source_art_manifest_sha256']=mod.LOCK_SHA
    prop['supersedes_rejected_candidate']=rel(first/'proposal.json');prop['scope']+=' 포스103의 들린 소매만 새 검정/보라 주름으로 교정; 기본형/나머지 자세/원래 실루엣/손끝 동일.'
    contact=json.loads((H/'rising_packed_contact02/report.json').read_text('utf8'));need(contact['passed'],'Previous contact failed')
    # Only ref103 arm color changes. The verified normal initial emitter refs
    # 104/232 and spatial charged diagnostic refs100/101 are byte-exact above.
    proof={'passed':True,'candidate_sha256':TARGET,'parent_sha256':sha(parent),'reproduction_exact':True,'source_lock_sha256':mod.LOCK_SHA,'input_rejections':rejects,'producer':json.loads((artifact/'report.json').read_text('utf8')),'v1_to_v2_local_correction':{'old_candidate':sha(old.data),'raw_non103_exact':rawcount,'other_layers_exact':layers,'all_composition_bytes_exact':True,'changed_layer':[103,7],'changed_display_pixels':58,'partial_checks':conditions,'alpha_all_masks_exact':True,'fist_head_body_legs_exact':True,'source_registration_report':rel(H/'rising103_sleeve_native03/report.json'),'source_registration_sha256':sha((H/'rising103_sleeve_native03/report.json').read_bytes())},'native_effect_evidence':{'report':rel(H/'rising_packed_contact02/report.json'),'sha256':sha((H/'rising_packed_contact02/report.json').read_bytes()),'verified_refs_100_101_104_232_byte_exact_vs_previous':True,'effect_graphics_parts_exact':True,'new103_hand_alpha_exact':True,'normal_initializer_contact_preserved':True,'charged_phase_simulation':False},'author_actual_readback_review':[{'path':rel(p),'sha256':sha(p.read_bytes())}for p in sorted(artifact.glob('*_readback_*.png'))],'independent_pending':True,'native_cpu_pending':True,'root_visual_pending':True,'emulator_gameplay_test':False,'user_accepted':False}
    out.mkdir();(out/'PL00_U.ARC').write_bytes(data);write(out/'proposal.json',prop);write(out/'verification.json',proof)
    producers=['pack_rising_base_v2.py','prepare_rising_base_v2.py','register_rising103_sleeve.py','finalize_rising_base_v2.py']
    write(out/'INPUT_FROZEN.json',{'candidate_and_source_frozen':True,'files':{p:sha((out/p).read_bytes())for p in('PL00_U.ARC','proposal.json','verification.json')},'source_lock_sha256':mod.LOCK_SHA,'producer_scripts':{p:sha((H/p).read_bytes())for p in producers},'user_accepted':False,'actual_gameplay_verified':False,'independent_review_pending':True,'full_draw_mips_pending':True})
    print(json.dumps({'proposal':rel(out/'proposal.json'),'candidate_sha256':TARGET,'local_raw_checks':rawcount,'local_layers':layers,'partial_checks':conditions,'rejections':len(rejects)}))
if __name__=='__main__':main()
