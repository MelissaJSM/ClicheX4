"""루트 새 부팅의 저장 RAM과 실제 최종 EXE, 카드 사본/원본 보존을 대조한다."""
from pathlib import Path
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import verify_final as v


def main():
    output=HERE/'runtime_preservation.json'
    v.require(not output.exists(),'Existing runtime audit')
    current=v.load(HERE/'final_independent.json')
    root=ROOT/'work/boss_voice_restore_20261105/runtime'
    cards=v.load(root/'test_cards_before.json')
    checked_cards=[]
    for row in cards:
        path=ROOT/row['path'];raw=path.read_bytes()
        v.require(len(raw)==131072 and v.sha(raw)==row['sha256'],'Fresh boot test card changed')
        checked_cards.append({**row,'unchanged':True})
    boots={}
    for project,meta in current['projects'].items():
        evidence=root/(project+'_boot.json');boot=v.load(evidence)
        v.require(boot['passed']and boot['bin_sha256']==meta['bin_sha256'],'Boot evidence targets different BIN')
        session=ROOT/boot['session'];info=v.load(session/'session.local.json');close=v.load(session/'close.local.json')
        v.require(info['bin_sha256']==meta['bin_sha256']and not info['save_state_loaded'],'Session did not fresh boot expected disc')
        v.require(close['exited'],'Test session not normally exited')
        v.require(not boot['F1_F3_used']and not boot['memory_written'],'Unexpected test mutation')
        override=list(info['memory_card_overrides'].values())
        for row in override:
            rel=Path(row['path']).relative_to(ROOT).as_posix()
            v.require(any(c['path']==rel and c['sha256']==row['sha256']for c in checked_cards),'Unlisted test card')
        capture=ROOT/boot['capture'];rams=list(capture.glob('ram_*.bin'))
        v.require(len(rams)==1,'Ambiguous captured RAM');ram=rams[0].read_bytes()
        v.require(v.sha(ram)==boot['RAM_sha256'],'Saved RAM SHA mismatch')
        disc,_,_=v.assets(ROOT/meta['bin'],{'SLUS_005.61'});exe=disc['SLUS_005.61']
        ranges=[]
        for row in boot['verified_code_and_tables']:
            at=int(row['address'],16)&0x1fffffff;n=row['size'];raw=ram[at:at+n]
            actual=exe[at-0x10000+2048:at-0x10000+2048+n]
            v.require(raw==actual and v.sha(raw)==row['sha256'],'Runtime native code/table differs')
            ranges.append({**row,'actual_disc_equals_captured_RAM':True})
        boots[project]={'bin_sha256':meta['bin_sha256'],'evidence':evidence.relative_to(ROOT).as_posix(),
            'evidence_sha256':v.digest(evidence),'RAM_sha256':v.sha(ram),'verified_ranges':ranges,
            'fresh_boot':True,'normal_exit_recorded':True,'cards_are_isolated_copies':True,
            'F1_F3_used':False,'process_memory_written':False,'actual_boss_intro_heard':False}
    protected=v.load(HERE/'protection_before.json')
    for rel,row in protected['files'].items():
        v.require(v.digest(ROOT/rel)==row['sha256'],'Protected file changed after live testing: '+rel)
    proc=subprocess.run(['powershell','-NoProfile','-Command',
        '@(Get-Process -Name ePSXe -ErrorAction SilentlyContinue | Select-Object Id,Path) | ConvertTo-Json -Compress'],
        capture_output=True,text=True,check=True)
    active=json.loads(proc.stdout.strip()or'[]')
    result={'passed':True,'projects':boots,'new_test_cards':checked_cards,'original_53_files_still_exact':True,
        'current_epsxe_processes':active,'audit_keys_sent':False,'audit_process_memory_written':False,
        'scope':'실제 새 부팅 저장 RAM의 코드/테이블 및 원본/카드 보존. 보스 개전 CD 완료/청취 증거 아님.'}
    with output.open('x',encoding='utf-8')as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'passed':True,'boot_sessions':len(boots),'ranges':sum(len(b['verified_ranges'])for b in boots.values()),'new_cards':len(cards),'running':active}))


if __name__=='__main__':main()
