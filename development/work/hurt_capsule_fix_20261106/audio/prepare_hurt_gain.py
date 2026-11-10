"""Only raise bank3 tone0 gain. Outputs are resource proposals, never game discs."""
from pathlib import Path
import gzip,hashlib,json,math,struct,sys,wave
import numpy as np
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.overhaul_audio_verify_cpu import banks
from scripts.overhaul_nana_progress_refresh import loaded_vab_header
from src.psx_spu_audio import decode_spu
OUT=Path(__file__).parent;DEST=OUT/'prepared_v1'
NAMES=('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC')
SOURCES={'ver_buki_riko':('shibuki_riko','ef2fcec562f02f6ba6b372e26b021924ea595abe4d654a9fc4e632a529804bb7'),
 'ver_rin_nana':('rin_nana','c84dcda554ae6320c9808fc55088731a7f90dc9bda391d5c0674645315b56b31')}
STATE='work/overhaul_20261105/audio/nana_user_progress_candidate04_final_v1/SLUS_005.61.000'
STATE_SHA='57977106f9bf2a8fae08834c94225fdcdf477d895e82256510e7a745f5259440'
HURT_SHA='3849f73da2ec664732118255463da30fcd8438fc29ef37db4b0b18c1b8c51029'
DEATH_SHA='bca9ec5b6b47b1247ec483f6b95cb8de3d94c58e03132255c63df5f434e4cfbc'
TARGET=104
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(c,msg):
 if not c:raise ValueError(msg)
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
def load(mode):
 stem,expected=SOURCES[mode];p=ROOT/'out'/mode/'boss_voice_restored_20261105_v2'/(stem+'.bin');require(digest(p)==expected,'Parent BIN SHA changed')
 with p.open('rb')as f:
  d=DiscReader(f,p.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']if not r['directory']}
  return p,{n:d.read(rs[n]['lba'],rs[n]['size'])for n in NAMES+('SLUS_005.61',)},rs
def header_entry(arc,header):
 es=psx_arc(arc);found=[e for e in es if e['size']==len(header)and arc[e['offset']:e['offset']+e['size']]==header]
 require(len(found)==1,'Ambiguous sound header');return found[0]
def patch(arc,expected,new_volume=TARGET):
 require(sha(arc)==expected,'Unsupported ARC hash');require(isinstance(new_volume,int)and 90<new_volume<=127,'Invalid gain')
 h,b,q=banks(arc)[3];tb=q['vab_offset']+32+128*16;t=h[tb:tb+32]
 require(t.hex()=='00005a4053003b3b000000000000b1b2ff80c01f00000100c000c100c200c300','Unexpected hurt tone')
 require(h[8:16]==bytes.fromhex('8300001483000014')and h[56:60]==bytes.fromhex('83001014'),'Unexpected player sound commands')
 require(q['waves'][0]['sha256']==HURT_SHA and q['waves'][1]['sha256']==DEATH_SHA,'X6 sample changed')
 he=header_entry(arc,h);off=he['offset']+tb+2;out=bytearray(arc);out[off]=new_volume
 require([i for i,(a,b)in enumerate(zip(arc,out))if a!=b]==[off],'Not a single tone-volume byte change')
 nh,nb,nq=banks(out)[3];require(nb==b and nq['waves']==q['waves'],'Sample/offset changed')
 require(h[:tb+2]+h[tb+3:]==nh[:tb+2]+nh[tb+3:],'Unrelated sound header changed')
 require(all(banks(arc)[k]==banks(out)[k]for k in(0,1)),'Common SFX bank changed')
 return bytes(out),{'offset':off,'header_entry':he,'bank':3,'program':0,'tone':0,'volume_before':90,'volume_after':new_volume,
      'body_bytes_identical':True,'all_wave_addresses_identical':True,'all_other_arc_bytes_identical':True,'changed_bytes':1}
def sdk(ram,asset_banks,slot,command):
 raw=bytearray(ram);loaded={};nextbuf=0x1d0000;spu=0x1010
 for k,(h,b,q)in sorted(asset_banks.items()):
  start=spu;spu+=len(b);require(spu<0x80000,'SPU address overflow');buf=nextbuf;nextbuf+=(len(h)+255)//256*256
  require(nextbuf<0x1f0000,'Temporary header RAM overflow');raw[buf:buf+len(h)]=loaded_vab_header(h,b,start);vaddr=0x80000000|buf+q['vab_offset']
  for base,value in((0x141f30,start),(0x141f50,0x80000000|buf+8),(0x141ee8,vaddr),(0x141840,vaddr),(0x1406b8,vaddr+32),(0x141888,vaddr+32+128*16)):
   struct.pack_into('<I',raw,base+k*4,value)
  raw[0x13e198+k]=k;raw[0x166d58+k]=1;loaded[k]={'start':start,'h':h,'b':b,'q':q}
 raw[0x139234:0x139234+24]=bytes([255])*24;raw[0x166d90:0x166d90+24*16]=bytes(24*16)
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f801000,0x1000);u.mem_write(0,bytes(raw));calls=[]
 def observe(cpu,pc,size,_):
  sp=cpu.reg_read(m.UC_MIPS_REG_SP)&0x1fffffff
  calls.append({'voice':cpu.reg_read(m.UC_MIPS_REG_A0),'bank':cpu.reg_read(m.UC_MIPS_REG_A1),'program':cpu.reg_read(m.UC_MIPS_REG_A2),'tone':cpu.reg_read(m.UC_MIPS_REG_A3),
     'note_fine_left_right':list(struct.unpack('<4I',cpu.mem_read(sp+16,16)))})
 u.hook_add(UC_HOOK_CODE,observe,begin=0x800dfcfc,end=0x800dfcfc)
 for reg,value in((m.UC_MIPS_REG_A0,slot),(m.UC_MIPS_REG_A1,command),(m.UC_MIPS_REG_A2,0),(m.UC_MIPS_REG_SP,0x801ff000),(m.UC_MIPS_REG_RA,0x80008000)):u.reg_write(reg,value)
 u.emu_start(0x8001540c,0x80008000,count=300000);require(u.reg_read(m.UC_MIPS_REG_PC)==0x80008000 and calls,'Native SDK did not return/note-on')
 rows=[]
 for c in calls:
  data=loaded[c['bank']];h,b,q=data['h'],data['b'],data['q'];pos=q['vab_offset']+32+128*16+(c['program']*16+c['tone'])*32;t=h[pos:pos+32];wi=struct.unpack_from('<H',t,22)[0]
  w=q['waves'][wi-1];raw_wave=b[w['body_offset']:w['body_offset']+w['bytes']];pcm=np.asarray(decode_spu(raw_wave).pcm,dtype=np.int32)
  regs=struct.unpack('<8H',u.mem_read(0x166d90+c['voice']*16,16));require(regs[3]==(data['start']+w['body_offset'])//8,'Wrong actual SDK start')
  rows.append({**c,'pitch':regs[2],'volume_left':regs[0],'volume_right':regs[1],'start_register':regs[3],'adsr1':regs[4],'adsr2':regs[5],
    'wave_id':wi,'wave_sha256':sha(raw_wave),'decoded_samples':len(pcm),'pcm_peak':int(max(abs(pcm))),
    'solo_peak_bound_at_full_ADSR':int(max(abs(pcm)))*max(regs[:2])/16384,
    'duration_seconds':len(pcm)/(regs[2]*44100/4096)if regs[2]else None,'native_SDK_unmocked':True})
 return rows
def main():
 require(not DEST.exists(),'Output already exists');state=(ROOT/STATE).read_bytes();require(sha(state)==STATE_SHA,'Protected state changed');ram=gzip.decompress(state)[442:442+0x200000]
 products={};reports={};candidate_rows=[]
 for mode in SOURCES:
  source,assets,records=load(mode);exe=assets['SLUS_005.61'];executed=[]
  for start,end in((0x1540c,0x15a50),(0xdfac0,0xe0000),(0xe0500,0xe6000)):
   require(ram[start:end]==exe[start-0x10000+2048:end-0x10000+2048],'Actual parent native code mismatch');executed.append({'start':hex(start),'end':hex(end),'sha256':sha(ram[start:end])})
  mode_products={};files={};checks={}
  for name in NAMES:
   old=assets[name];new,report=patch(old,sha(old));beforebanks=banks(old);afterbanks=banks(new);mode_products[name]=new
   compare=[]
   for command in range(13):
    before=sdk(ram,beforebanks,3,command);after=sdk(ram,afterbanks,3,command)
    if command in(0,1):
     require(len(before)==len(after)==1,'Hurt must be single channel');a,b=before[0],after[0]
     for key in a:
      if key not in('volume_left','volume_right','note_fine_left_right','solo_peak_bound_at_full_ADSR'):require(a[key]==b[key],'Hurt changed '+key)
     gain=b['volume_left']/a['volume_left'];db=20*math.log10(gain)
     require(3<=db<=6 and b['volume_left']==b['volume_right']and b['solo_peak_bound_at_full_ADSR']<32767,'Invalid volume gain/headroom')
    else:require(before==after,'Other player command changed')
    compare.append({'command':command,'before':before,'after':after,'identical':before==after})
   require(patch(old,sha(old))[0]==new,'Nonreproducible single-byte patch')
   refusals=0
   for data,expected,value in((old,'0'*64,TARGET),(old[:-1],sha(old),TARGET),(new,sha(new),TARGET),(old,sha(old),128),(old,sha(old),90)):
    try:patch(data,expected,value)
    except ValueError:refusals+=1
   require(refusals==5,'Invalid input accepted')
   report.update(native_cases=compare,negative_inputs_rejected=refusals)
   offset=report['offset'];files[name]={'path':(DEST/mode/name).relative_to(ROOT).as_posix(),'before':sha(old),'after':sha(new),'size':len(new),'record':records[name],
         'changes':[{'offset':offset,'before':90,'after':TARGET}],'allowed_entries':[report['header_entry']]};checks[name]=report
   if mode=='ver_buki_riko'and name=='PL00_U.ARC':
    baseline=sdk(ram,beforebanks,3,0)[0]
    for v in(90,100,101,102,103,104,105,106,107,108,110,120,127):
     variant=old if v==90 else patch(old,sha(old),v)[0];x=sdk(ram,banks(variant),3,0)[0]
     candidate_rows.append({'tone_volume':v,'actual_spu':x,'linear_gain':x['volume_left']/baseline['volume_left'],'gain_db':20*math.log10(x['volume_left']/baseline['volume_left'])})
  products[mode]=mode_products;reports[mode]={'proposal':{'project':mode,'baseline':source.relative_to(ROOT).as_posix(),'baseline_sha256':SOURCES[mode][1],'files':files,
    'scope':'Only bank3 tone0 volume90->104; X6 hurt commands0/1. All other bytes exact.','real_runtime_verified':False,'human_listening_verified':False},
    'verification':{'passed':True,'source_state':STATE,'source_state_sha256':STATE_SHA,'unchanged_native_code':executed,'checks':checks,'hardware_spu_mix_emulated':False,'save_or_process_memory_written':False}}
 # Both projects share audio; their graphic ARC contents are intentionally separate.
 require(all(banks(products['ver_buki_riko'][n])[3]==banks(products['ver_rin_nana'][n])[3]for n in NAMES),'Mode sound banks differ')
 require(sha((ROOT/STATE).read_bytes())==STATE_SHA,'State source modified')
 DEST.mkdir(parents=True)
 for mode in products:
  directory=DEST/mode;directory.mkdir()
  for name,data in products[mode].items():(directory/name).write_bytes(data)
  write(directory/'proposal.json',reports[mode]['proposal']);write(directory/'verification.json',reports[mode]['verification'])
 write(DEST/'gain_candidates.json',{'selected_tone_volume':TARGET,'candidates':candidate_rows,'scope':'Actual isolated native SDK volume registers; full game mix and perceptual loudness are not measured.'})
 gain=next(x for x in candidate_rows if x['tone_volume']==TARGET)
 write(DEST/'summary.json',{'passed':True,'resources':6,'changed_bytes_total':6,'native_calls_before_after':6*13*2,'new_volume':TARGET,'gain_db':gain['gain_db'],
    'same_bank3_audio_both_modes':True,'different_graphics_resources_preserved':True,'original_X6_raw_pitch_duration_preserved':True,
    'boss_C06_death_Rakuhouha_mute_preserved':True,'real_mixed_audio_or_user_acceptance_verified':False})
 print(json.dumps({'prepared':True,'gain_db':gain['gain_db'],'resources':6,'spu_volume':gain['actual_spu']['volume_left'],'solo_peak_bound':gain['actual_spu']['solo_peak_bound_at_full_ADSR']}),flush=True)
if __name__=='__main__':main()
