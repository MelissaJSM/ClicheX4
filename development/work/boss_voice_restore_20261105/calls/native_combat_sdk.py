"""Independent actual US dispatcher and unmocked PSYQ SPU SDK audit.

Loads only an isolated 2 MB RAM copy; does not alter emulator or save files.
"""
from pathlib import Path
import sys,json,struct,gzip,hashlib
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.inventory_riko_voice import parse_bank
from scripts.overhaul_audio_verify_cpu import banks
from scripts.overhaul_nana_progress_refresh import loaded_vab_header
from scripts.discover_inputs import DiscReader
from src.psx_spu_audio import decode_spu
SOURCE_STATE=ROOT/'work/overhaul_20261105/audio/nana_user_progress_candidate04_final_v1/SLUS_005.61.000'
STATE_HASH='57977106f9bf2a8fae08834c94225fdcdf477d895e82256510e7a745f5259440'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PREP=H.parent/'assets/prepared_combat_v1'
BUF=0x1d0000;SPU_START=0x50000
def sdk(ram,bank,command):
 h,b,q=bank;slot=2;raw=bytearray(ram);trans=loaded_vab_header(h,b,SPU_START)
 assert BUF+len(h)<0x1fef00
 raw[BUF:BUF+len(h)]=trans
 def ptr(at,val):struct.pack_into('<I',raw,at,val)
 vo=q['vab_offset'];vaddr=0x80000000|BUF+vo
 ptr(0x141f38,SPU_START);ptr(0x141f58,0x80000000|BUF+8);ptr(0x141ef0,vaddr)
 raw[0x13e19a]=2;raw[0x166d5a]=1
 ptr(0x141848,vaddr);ptr(0x1406c0,vaddr+32);ptr(0x141890,vaddr+32+128*16)
 raw[0x139234:0x139234+24]=bytes([255])*24
 raw[0x166d90:0x166d90+24*16]=bytes(24*16)
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f801000,0x1000);u.mem_write(0,bytes(raw))
 args=[]
 def observe(mu,pc,size,_):
  sp=mu.reg_read(m.UC_MIPS_REG_SP)&0x1fffffff
  args.append({'voice':mu.reg_read(m.UC_MIPS_REG_A0),'bank':mu.reg_read(m.UC_MIPS_REG_A1),'program':mu.reg_read(m.UC_MIPS_REG_A2),'tone':mu.reg_read(m.UC_MIPS_REG_A3),'note_fine_left_right':list(struct.unpack('<4I',mu.mem_read(sp+16,16)))})
 u.hook_add(UC_HOOK_CODE,observe,begin=0x800dfcfc,end=0x800dfcfc)
 for reg,val in ((m.UC_MIPS_REG_A0,2),(m.UC_MIPS_REG_A1,command),(m.UC_MIPS_REG_A2,0),(m.UC_MIPS_REG_SP,0x801ff000),(m.UC_MIPS_REG_RA,0x80008000)):u.reg_write(reg,val)
 u.emu_start(0x8001540c,0x80008000)
 assert u.reg_read(m.UC_MIPS_REG_PC)==0x80008000 and args,('SDK no note-on',command)
 rows=[]
 for a in args:
  assert a['bank']==2
  tpos=vo+32+128*16+(a['program']*16+a['tone'])*32;t=h[tpos:tpos+32]
  wid=struct.unpack_from('<H',t,22)[0]
  regs=struct.unpack('<8H',u.mem_read(0x166d90+a['voice']*16,16))
  if wid==0:
   assert regs==(0,)*8,('Unused tone modified cache',command,a,regs)
   rows.append({**a,'pitch':0,'wave':0,'wave_raw_sha256':None,'volume_left':0,'volume_right':0,'start_register':0,'adsr1':0,'adsr2':0,'decoded_samples':0,'duration_seconds':None,'unused_tone_no_voice_started':True})
   continue
  assert 1<=wid<=q['wave_count'],(command,a,wid)
  w=q['waves'][wid-1];sample=b[w['body_offset']:w['body_offset']+w['bytes']]
  assert regs[3]==(SPU_START+w['body_offset'])//8,(command,a,regs,w)
  assert regs[4:6]==struct.unpack_from('<HH',t,16)
  rows.append({**a,'pitch':regs[2],'wave':wid,'wave_raw_sha256':SHA(sample),'volume_left':regs[0],'volume_right':regs[1],'start_register':regs[3],'adsr1':regs[4],'adsr2':regs[5],'decoded_samples':len(decode_spu(sample).pcm),'duration_seconds':len(decode_spu(sample).pcm)/(regs[2]*44100/4096) if regs[2] else None})
 return rows
def main():
 state=SOURCE_STATE.read_bytes();assert SHA(state)==STATE_HASH;ram=gzip.decompress(state)[442:442+0x200000]
 exe=(H/'SLUS_005.61').read_bytes()
 assert SHA(exe)=='dae43d44a9f3176208830ddbba0607bb627ebcd7faf9b36fc03dd0ffda34d2e8'
 # All executed dispatcher/SDK code must match the supplied original US code.
 for start,end in ((0x1540c,0x15a50),(0xdfac0,0xe0000),(0xe0500,0xe6000)):
  assert ram[start:end]==exe[start-0x10000+2048:end-0x10000+2048],hex(start)
 jp_disc=ROOT/'Rockman X4.bin'
 assert SHA(jp_disc.read_bytes())=='a8fcc59d1d934c8601389bccc26f7a110b74f8fc025f1c73ebe63a46c547c9a1'
 jinv=json.loads((H.parent/'assets/jp_inventory.json').read_text());source_jp={}
 with (ROOT/'Rockman X4.bin').open('rb') as f:
  d=DiscReader(f,(ROOT/'Rockman X4.bin').stat().st_size)
  for row in jinv['banks']:
   if row['bank']['slot']==2 and row['path'].split('/')[-1].split(';')[0] in json.loads((PREP/'ver_buki_riko/proposal.json').read_text())['files']:
    a=d.read(row['record']['lba'],row['record']['size']);source_jp[row['path'].split('/')[-1].split(';')[0]]=banks(a)[2]
 results=[];mode_hashes={};regressions=[]
 for mode in ('ver_buki_riko','ver_rin_nana'):
  proposal=json.loads((PREP/mode/'proposal.json').read_text());verification=json.loads((PREP/mode/'verification.json').read_text())
  mode_hashes[mode]={}
  original_banks={}
  if mode=='ver_buki_riko':
   parent=ROOT/proposal['baseline'];assert SHA(parent.read_bytes())==proposal['baseline_sha256']
   with parent.open('rb') as f:
    d=DiscReader(f,parent.stat().st_size)
    for name,rec in proposal['files'].items():
     old=d.read(rec['record']['lba'],rec['record']['size']);assert SHA(old)==rec['before']
     original_banks[name]=banks(old)[2]
  for name,rec in proposal['files'].items():
   raw=(ROOT/rec['path']).read_bytes();assert SHA(raw)==rec['after'];mode_hashes[mode][name]=SHA(raw)
   if mode=='ver_rin_nana':continue
   bank=banks(raw)[2];h,b,q=bank;changes={t['packed_tone']:t for t in verification[name]['tones']}
   commands=[]
   for command in range(q['command_count']):
    c=h[8+command*4:12+command*4]
    if (c[0]&63)!=2:continue
    tones=[(c[1]&127)*16+(c[2]>>4)+n for n in range(((c[3]>>5)&3)+1)]
    if any(t in changes for t in tones):commands.append(command)
   for command in commands:
    target=sdk(ram,bank,command);source=sdk(ram,source_jp[name],command)
    assert len(source)==len(target)
    for s,t in zip(source,target):
     packed=t['program']*16+t['tone']
     if packed not in changes:continue
     ch=changes[packed]
     assert s['pitch']==ch['source_pitch'] and t['pitch']==ch['target_pitch_formula']
     assert (s['adsr1'],s['adsr2'])==(t['adsr1'],t['adsr2'])
     # Stereo composite voices can deliberately pan one tone fully left/right.
     assert t['volume_left']+t['volume_right']>0,(name,command,s,t)
     assert (s['volume_left'],s['volume_right'])==(t['volume_left'],t['volume_right'])
     assert abs(s['duration_seconds']-t['duration_seconds'])<0.004,(name,command,s,t)
    results.append({'file':name,'command':command,'source_jp_resource_via_us_sdk':source,'prepared_resource_via_us_sdk':target})
   # Execute every local bank2 note-on, including unaffected SFX whose addresses
   # can move when another waveform's byte allocation changes.
   oldbank=original_banks[name];oh,ob,oq=oldbank
   wave_rows=[]
   for number,w in enumerate(q['waves']):
    ow=oq['waves'][number]
    new_sample=b[w['body_offset']:w['body_offset']+w['bytes']]
    old_sample=ob[ow['body_offset']:ow['body_offset']+ow['bytes']]
    wave_rows.append({'wave':len(wave_rows)+1,'raw_unchanged':new_sample==old_sample,'old_offset':ow['body_offset'],'new_offset':w['body_offset']})
   for command in range(q['command_count']):
    c=h[8+command*4:12+command*4]
    if c[0]!=0x82:continue
    after=sdk(ram,bank,command);before=sdk(ram,oldbank,command)
    assert len(before)==len(after),(name,command)
    protected=[]
    for old,new in zip(before,after):
     packed=new['program']*16+new['tone']
     if packed in changes:continue
     for key in ('voice','bank','program','tone','note_fine_left_right','pitch','wave','volume_left','volume_right','adsr1','adsr2'):
      assert old[key]==new[key],(name,command,key,old,new)
     silent=old['volume_left']==old['volume_right']==new['volume_left']==new['volume_right']==0
     raw_same=old['wave_raw_sha256']==new['wave_raw_sha256']
     if not silent:
      for key in ('wave_raw_sha256','decoded_samples','duration_seconds'):
       assert old[key]==new[key],(name,command,key,old,new)
     protected.append({'tone':packed,'wave':new['wave'],'old_start':old['start_register'],'new_start':new['start_register'],'silent':silent,'raw_unchanged':raw_same,'silent_shared_replaced_wave':silent and not raw_same,'source_raw_sha256':old['wave_raw_sha256'],'target_raw_sha256':new['wave_raw_sha256']})
    regressions.append({'file':name,'command':command,'unmodified_note_checks':protected,'target_note_on_count':len(after)})
   # Every wave participates in the loaded VAB address table, whether or not a
   # boss AI path references that sample; verify its independent cumulative sum.
   trans=loaded_vab_header(h,b,SPU_START);table=q['vab_offset']+32
   for number,w in enumerate(q['waves'],1):
    addr=struct.unpack_from('<H',trans,table+(number//2)*16+12+(number%2)*2)[0]
    assert addr==(SPU_START+w['body_offset']+w['bytes'])//8,(name,number,addr,w)
   regressions.append({'file':name,'all_wave_addresses_checked':len(q['waves']),'waves':wave_rows})
 assert mode_hashes['ver_buki_riko']==mode_hashes['ver_rin_nana']
 assert SHA(SOURCE_STATE.read_bytes())==STATE_HASH
 report={'passed':True,'scope':'실제 미국판 dispatcher + SsUtGetVagAtr/SsUtKeyOnV/note2pitch2/음량/ADSR/SPU주소 생성 코드 무모킹; JP VAB와 준비 VAB를 동일한 SDK/초기조건에서 비교','source_note2pitch_jp_evidence':'../assets/asr_native_manifest.json','native_sdk_mocked':False,'hardware_spu_mix_emulated':False,'real_game_audio_recorded':False,'source_state_unchanged':True,'source_state_sha256':STATE_HASH,'calls':len(results),'target_note_ons':sum(len(r['prepared_resource_via_us_sdk']) for r in results),'same_resources_both_modes':True,'resource_sha256':mode_hashes,'cases':results}
 report['all_bank2_regression_commands']=sum('command' in r for r in regressions)
 report['unmodified_note_checks']=sum(len(r.get('unmodified_note_checks',[])) for r in regressions)
 report['all_wave_addresses_checked']=sum(r.get('all_wave_addresses_checked',0) for r in regressions)
 report['audible_unmodified_note_checks']=sum(not x['silent'] for r in regressions for x in r.get('unmodified_note_checks',[]))
 report['silent_shared_replaced_wave_checks']=sum(x['silent_shared_replaced_wave'] for r in regressions for x in r.get('unmodified_note_checks',[]))
 report['original_us_exe_sha256']=SHA(exe)
 report['original_jp_bin_sha256']='a8fcc59d1d934c8601389bccc26f7a110b74f8fc025f1c73ebe63a46c547c9a1'
 report['unchanged_native_code_ranges']=[{'start':hex(start),'end_exclusive':hex(end),'sha256':SHA(ram[start:end])} for start,end in ((0x1540c,0x15a50),(0xdfac0,0xe0000),(0xe0500,0xe6000))]
 report['native_keyon_entry']='0x800DFCFC'
 report['regression_scope']='원래 무음 슬롯도 그대로 유지. 비수정 가청 톤은 pitch/volume/ADSR/raw/길이를 보존하고, 재배치된 주소는 새 파형 시작점과 일치한다. 무음 슬롯 일부는 교체 파형을 공유하지만 좌우 볼륨 0으로 유지된다.'
 report['regressions']=regressions
 (H/'native_combat_sdk.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k not in ('cases','resource_sha256','regressions')},ensure_ascii=False))
if __name__=='__main__':main()
