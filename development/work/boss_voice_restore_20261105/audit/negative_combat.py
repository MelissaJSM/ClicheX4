"""감사 검증기의 비대상 그림·명령·톤·JP 출처 손상 거부. 메모리 사본만 변조."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import verify_final as v


def main():
    output=HERE/'negative_combat.json'
    v.require(not output.exists(),'Existing negative evidence')
    protected=v.load(HERE/'protection_before.json')
    folder=ROOT/'work/boss_voice_restore_20261105/assets/prepared_combat_v1'
    name='ST1_1_1.ARC'
    jp,_,_=v.assets(ROOT/'Rockman X4.bin',{name})
    rows=[]
    for project,spec in protected['projects'].items():
        source,_,_=v.assets(ROOT/spec['bin'],{name})
        before=source[name];after=(folder/project/name).read_bytes();proof=v.load(folder/project/'verification.json')[name]
        h,b,q,he,be=v.bank(after,2)
        excluded={he['index'],be['index']}
        other=next(e for e in v.psx_arc(after)if e['index']not in excluded and e['size']>0)
        base=he['offset'];tb=q['vab_offset']+32+128*16
        for label,offset in [('unrelated_graphic',other['offset']),('VAB_master',base+q['vab_offset']+24),
                             ('command',base+8),('target_wrong_wave',base+tb+3*32+22)]:
            bad=bytearray(after);bad[offset]^=1
            try:v.check_arc(before,bytes(bad),jp[name],1,proof)
            except ValueError as ex:rows.append({'project':project,'case':label,'rejected':True,'reason':str(ex)})
            else:raise ValueError('Corruption accepted '+label)
        jh,jb,jq,jhe,jbe=v.bank(jp[name],2)
        at=jbe['offset']+jq['waves'][2]['body_offset']+2
        wrong_jp=bytearray(jp[name]);wrong_jp[at]^=1
        try:v.check_arc(before,after,bytes(wrong_jp),1,proof)
        except ValueError as ex:rows.append({'project':project,'case':'JP_source_wave_corrupted','rejected':True,'reason':str(ex)})
        else:raise ValueError('Corrupt source accepted')
    result={'passed':True,'cases':rows,'game_or_prepared_files_modified':False,'mutations_memory_only':True}
    with output.open('x',encoding='utf-8')as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'passed':True,'rejections':len(rows)}))


if __name__=='__main__':main()
