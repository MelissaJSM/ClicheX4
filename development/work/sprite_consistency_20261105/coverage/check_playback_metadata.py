"""플레이백 메타데이터의 실제 EXE 포인터/스텝/시간/은행을 독립 대조."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.audit_sprite_consistency_coverage import read_assets,file_sha,sha,write
P=ROOT/'work/sprite_consistency_20261105/playback/manifest.json';before=file_sha(P)
assert before=='8b188cb7a3a8628c596c481e2499498966eacd1260c14c1f2cca6615a9fc5fd6'
q=json.loads(P.read_text('utf8'));exes={};counts={};nulls=0;unique=set();steps=0
def at(exe,addr,size):
 pos=addr-0x80010000+2048;assert 2048<=pos<=len(exe)-size;return exe[pos:pos+size]
for character,rec in q['characters'].items():
 source=rec['source'];mode=rec['project']
 if mode not in exes:
  path=ROOT/source['bin'];assert file_sha(path)==source['bin_sha256']
  assets,_=read_assets(path,['SLUS_005.61']);exe=assets['SLUS_005.61'];assert sha(exe)==source['assets']['SLUS_005.61'];exes[mode]=exe
 exe=exes[mode];selector=at(exe,0x8011af60,144);nseq=0
 for form,formdata in rec['forms'].items():
  capsule=form.startswith('capsule_')
  for animation in formdata['animations']:
   aid=animation['native_animation_id'];table=int(animation['table_address'],16)
   expectedtable=0x8011bf40 if capsule else 0x80119df0 if rec['family']=='x'else 0x8011aff0
   assert table==expectedtable
   pointer=at(exe,table+4*aid,4);address=struct.unpack('<I',pointer)[0]
   assert pointer.hex()==animation['pointer_bytes'] and address==int(animation['address'],16)
   pos=0;seen=[];calls=[]
   for step in animation['steps']:
    assert pos not in seen;seen.append(pos);raw=at(exe,address+pos*4,4)
    duration,event,relative,ref=struct.unpack('<bbbB',raw);ticks=duration if duration>0 else duration+256
    assert step['position']==pos and int(step['address'],16)==address+pos*4 and step['bytes']==raw.hex()
    assert (step['duration_signed'],step['event'],step['relative_step'],step['frame_ref'])==(duration,event,relative,ref)
    assert step['duration_calls']==ticks>0 and step['event_bits']==(event&255) and step['origin']==[160,160]
    bank=animation['graphics_bank'];parts=animation['composition_bank']
    if capsule:
     assert aid in(37,38)and bank in(10,11,12,13)and parts==bank+8;key=f'{form}_{bank}_{ref}'
    elif rec['family']=='zero':
     assert bank==selector[aid] and parts==(5 if bank else 0);key=f'{form}:b{bank}_{ref:03d}'
    else:
     assert bank==parts==0;key=f'{form}_{ref:03d}'
    assert step['expected_frame_id']==key
    if step['frame_id']is None:assert step['reason'];nulls+=1
    else:assert step['frame_id']==key
    calls.append(ticks);pos+=relative;steps+=1
   assert pos in seen;loop=seen.index(pos)
   assert animation['loop_to_position']==pos and animation['loop_start_index']==loop
   terminal=animation['steps'][-1]['relative_step']==0
   assert animation['terminal_position']==(pos if terminal else None)
   assert animation['exact_table_loop']==(not terminal)
   assert animation['prefix_calls']==sum(calls[:loop]) and animation['loop_calls']==sum(calls[loop:])and animation['sequence_calls']==sum(calls)
   assert animation['simulation_only']and not animation['runtime_verified']
   unique.add(address);nseq+=1
 counts[character]=nseq
contract=q['playback_contract']
assert contract['default_calls_per_second']==60 and contract['calls_per_second_is_assumption']
assert contract['duration_unit']=='uninterrupted animate_object calls'
assert 'never skip'in contract['missing_step_handling'] and 'indefinitely'in contract['terminal_handling']
assert nulls==q['coverage']['timed_unrendered_steps']==132 and steps==q['coverage']['steps']==14668
assert file_sha(P)==before
report={'passed':True,'manifest_sha256':before,'animation_forms':counts,'native_unique_sequence_addresses':len(unique),'step_records_checked':steps,
 'timed_missing_steps_retained':nulls,'all_pointer_step_event_relative_jump_bytes_match_current_discs':True,'zero_bank_selector_matches_current_exe':True,
 'capsule37_38_banks10through13_parts18through21_checked':True,'duration0_is256_negative1_is255':True,
 '60_calls_per_second_explicitly_assumed':True,'terminal_hold_is_review_policy_not_game_exit':True,
 'labels_not_globally_revalidated':True,'game_runtime_simulated':False,'source_originals_modified':False}
write(Path(__file__).with_name('playback_metadata_independent.json'),report)
print(json.dumps({'passed':True,'steps':steps,'missing':nulls,'sequences':sum(counts.values()),'unique_addresses':len(unique)}))
