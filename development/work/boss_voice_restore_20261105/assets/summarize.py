"""Reconcile complete resource inventory, native-used commands and prepared changes."""
from pathlib import Path
import json,sys
OUT=Path(__file__).parent;ROOT=OUT.parents[2]
NAMES={1:('Web Spider','spider'),2:('Frost Walrus','walrus'),3:('Split Mushroom','mushroom'),4:('Magma Dragoon','dragoon'),
       5:('Jet Stingray','stingray'),6:('Cyber Peacock','peacock'),7:('Storm Owl','owl'),8:('Slash Beast','slash_beast')}
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
    inv={k:json.loads((OUT/(k+'_inventory.json')).read_text('utf8'))for k in('us','jp','ver_buki_riko','ver_rin_nana')}
    comparison=json.loads((OUT/'comparison.json').read_text('utf8'));calls=json.loads((OUT.parent/'calls/boss_ai_calls.json').read_text('utf8'))
    prepared=json.loads((OUT/'prepared_combat_v1/ver_buki_riko/verification.json').read_text('utf8'));rows=[];bankclassification=[]
    lookup={k:{(x['path'],x['bank']['slot']):x for x in v['banks']}for k,v in inv.items()}
    for p in comparison['pairs']:
        us=lookup['us'][p['us'],p['slot']];nonadjacent=us['body_entry']!=us['header_entry']+1
        same=p['headers_equal']and p['bodies_equal'];name=Path(p['us']).name.split(';')[0]
        category='region_bytes_identical'if same else('eight_boss_combat_localization'if name in prepared else'preserved_region_difference_outside_selected_combat_lines')
        bankclassification.append({'us':p['us'],'jp':p['jp'],'slot':p['slot'],'header_entry':us['header_entry'],'body_entry':us['body_entry'],
           'old_adjacent_only_scan_missed':nonadjacent,'header_equal':p['headers_equal'],'body_equal':p['bodies_equal'],'category':category,
           'command_differences':[x['id']for x in p['command_differences']],'muted_tones':[{'program':t['program'],'tone':t['tone']}for t in p['tone_or_mapped_wave_differences']if'US_tone_volume_zero'in t['tags']]})
    for stage,(boss,key)in NAMES.items():
        path=f'/ARC/ST{stage}_1_1.ARC;1';a=lookup['us'][path,2];b=lookup['jp'][path,2];proof=prepared.get(f'ST{stage}_1_1.ARC')
        actual=[{'section':r['section'],**c}for r in calls if key in r['section']for c in r['calls']['us']if c['api']=='play_sound'and c['arguments'].get('$a0')==2 and isinstance(c['arguments'].get('$a1'),int)]
        targets=[]
        for w in proof['waves']if proof else[]:
            tones={t['packed_tone']for t in proof['tones']if t['source_wave']==w['source_wave']}
            mapped=[]
            for call in actual:
                command=call['arguments']['$a1'];cmd=b['bank']['commands'][command]
                selected={t['program']*16+t['tone']for t in cmd['local_tones']}
                if tones&selected:mapped.append({'command':command,'call':call['address'],'section':call['section'],'jp_command':cmd['hex'],'us_command':a['bank']['commands'][command]['hex']})
            assert mapped,(boss,w['source_wave'])
            targets.append({'source_jp_wave':w['source_wave'],'target_us_wave':w['target_wave'],'packed_tones':sorted(tones),
                 'source_raw_sha256':w['source_raw_sha256'],'native_call_mappings':mapped,'reencoded':w.get('reencoded',False),'center_note_delta':w.get('center_note_increase',0)})
        rows.append({'stage':stage,'boss':boss,'normal_archive':f'ST{stage}_1_1.ARC','rematch_archive':f'ONPARE{stage}.ARC',
            'source_bank2_header_body_equal':a['header_sha256']==b['header_sha256']and a['body_sha256']==b['body_sha256'],
            'additional_sample_count':len(targets),'targets':targets,'human_listening_completed':False})
    report={'bank_classification':bankclassification,'bosses':rows,'source_input_unchanged':all(x['input_unchanged_after_read']for x in inv.values()),
       'new_nonadjacent_banks':sum(x['old_adjacent_only_scan_missed']for x in bankclassification),
       'new_nonadjacent_with_any_region_difference':sum(x['old_adjacent_only_scan_missed']and not(x['header_equal']and x['body_equal'])for x in bankclassification),
       'additional_restored_combat_samples':sum(x['additional_sample_count']for x in rows),'scope':'Native call-to-bank/tone mapping and ASR-supported JP line restoration. Text transcription is auxiliary; not a human listening result.'}
    write(OUT/'coverage_classification.json',report)
    print(json.dumps({k:report[k]for k in('new_nonadjacent_banks','new_nonadjacent_with_any_region_difference','additional_restored_combat_samples')}))
if __name__=='__main__':main()
