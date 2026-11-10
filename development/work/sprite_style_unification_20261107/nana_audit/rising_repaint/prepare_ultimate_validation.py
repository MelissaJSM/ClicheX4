"""Ultimate 라이징7 후보의 입력 잠금 및 정본 권총/효과 보존 읽기 검사."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
FINAL='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
PARENT='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'

def main():
    out=D/'packed_ultimate_candidate_v1';need(not(out/'INPUT_FROZEN.json').exists(),'기존 입력잠금 보존')
    p=N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());b=Archive((out/'PL02_U.ARC').read_bytes())
    need(sha(a.data)==PARENT and sha(b.data)==FINAL,'대상 해시')
    cm=json.loads((D/'canonical_weapon_probe_v2/manifest.json').read_text('utf8'))
    canonical=a.layer(85)[0]
    for x,y,v in cm['canonical_source_texels']:need(int(canonical[y+160,x+160])==v,'원85 실제 정본')
    weapons=[]
    for n in(100,101,102,103,104,231,232):
        ref=231 if n==232 else n;folder=D/'ultimate_weapon_probe_v1'
        before=np.array(Image.open(folder/f'before_{ref:03}_indices.png'));case=np.array(Image.open(folder/f'before_{ref:03}_case.png'))
        hand=np.array(Image.open(folder/f'before_{ref:03}_hand_mask.png'))>0
        mask=(case>0)|hand;expected=np.array(a.rgba(before))
        for arm in(1,2):
            for bits in range(16):need(np.array_equal(np.array(b.composite(n,bits,arm)[0])[mask],expected[mask]),f'권총과 손 {n}/{bits}/{arm}')
        weapons.append({'ref':n,'case_texels':int((case>0).sum()),'native_extent':8,'before_hand_texels':int(hand.sum()),'common_case_plus_hand_rgba_all32':True,'case_file':(folder/f'before_{ref:03}_case.png').relative_to(ROOT).as_posix(),'case_file_sha256':digest(folder/f'before_{ref:03}_case.png'),'visible_case_texels':int(((case>0)&~hand).sum())})
    effects=[]
    for gb in range(1,len(a.banks)):
        lo,hi=a.banks[gb]['base'],a.banks[gb]['end'];need((lo,hi)==(b.banks[gb]['base'],b.banks[gb]['end']),'효과 은행 경계')
        need(a.g[lo:hi]==b.g[lo:hi],'효과 은행 bytes');effects.append({'bank':gb,'sha256':sha(a.g[lo:hi]),'byte_exact':True})
    write(out/'weapon_effect_verification.json',{'passed':True,'candidate_sha256':FINAL,'parent_sha256':PARENT,'weapons':weapons,'partial_weapon_checks':224,'effect_auxiliary_graphics':effects,'native_initializer_evidence':(D/'native_contacts_v1/manifest.json').relative_to(ROOT).as_posix(),'native_initializer_sha256':digest(D/'native_contacts_v1/manifest.json'),'scope':'정본85의 20색인 권총 모듈과 신규 before손 가림을 32합성마다 검사. 원 효과 은행 보존. 원 초기 효과 좌표와 최종권총 공간 비교·게임 시간표는 별도.','runtime_verified':False})
    write(D/'ultimate_native_components.json',{'project':'ver_rin_nana','source_bin':'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin','source_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','resources':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','after':FINAL}},'checkpoint_only':True,'scope':'원MIPS 격리검사. 게임/포인터/세이브 접근 없음.'})
    folders=('ultimate_inputs_v1','ultimate_air_v1','ultimate_air_registered_v1','ultimate_charge_v1','ultimate_charge_registered_v3','ultimate_recovery_v1','ultimate_recovery_registered_v1','ultimate_weapon_probe_v1','ultimate_boundary_audit_v2','ultimate_neck_audit_v1','ultimate_costume_pair_probe_v4','ultimate_costume_pair_probe_v6','ultimate_ground_feet_probe_v1','ultimate_layers_probe_v2','canonical_weapon_probe_v2','native_contacts_v1')
    names=('register_ultimate_page.py','register_ultimate_weapon.py','audit_ultimate_boundary.py','audit_ultimate_neck.py','register_ultimate_costume_pair.py','register_ultimate_ground_feet.py','prepare_ultimate_layers.py','pack_ultimate.py','pack_native.py')
    files=[D/n for n in names]
    for folder in folders:files.extend(p for p in(D/folder).rglob('*')if p.is_file()and p.suffix in('.png','.json','.txt'))
    lock=[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in sorted(set(files))]
    write(out/'INPUT_FROZEN.json',{'candidate_sha256':FINAL,'input_fixed':True,'files':lock,'scope':'Ultimate 라이징7 원화/의미등록/목표35층/제작코드 고정. 기술·루트 미술·독립 완료 후 별도 FROZEN.'})
    print(json.dumps({'candidate':FINAL,'input_files':len(lock),'partial_weapon_checks':224}))
if __name__=='__main__':main()
