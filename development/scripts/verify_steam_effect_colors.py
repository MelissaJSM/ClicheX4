"""Execute native death palette setter/getter and compare all 54 PS1 orb frames."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from src.steam_effect_colors import TEXT_BASE,START,SIZE,ADDRESS,signatures
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from src.psx_player import composition_frame
from src.psx_ui_atlas import tile_pixels
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
W=ROOT/'work/steam_port_20261109';D=W/'get_boss_completion'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n','utf8')

def main():
 code=(W/'runtime/code/text.bin').read_bytes();old,new=signatures(code)
 assert [i for i,(a,b) in enumerate(zip(old,new)) if a!=b]==[ADDRESS-START]
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x3000000);u.mem_write(TEXT_BASE,code)
 obj,actor,sp,stop=0x2700000,0x2800000,0x2901000,0x2801000
 u.mem_write(obj+0x38,struct.pack('<I',actor));writes=[]
 u.hook_add(UC_HOOK_MEM_WRITE,lambda m,k,a,n,v,d:writes.append((a,n)))
 setter_cases=0;renderer_cases=0
 for operand in (2,0):
  u.mem_write(ADDRESS,bytes([operand]));u.ctl_remove_cache(START,START+SIZE)
  for seed in (0,0x55,0xff):
   initial=bytes([seed])*512;u.mem_write(actor,initial);u.mem_write(sp,struct.pack('<I',stop))
   u.reg_write(UC_X86_REG_ESI,obj);u.reg_write(UC_X86_REG_ESP,sp)
   for r in (UC_X86_REG_EBX,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_EDX):u.reg_write(r,0x12345678)
   writes.clear();u.emu_start(0xA7860E,0xA7861E,count=100)
   expected=bytearray(initial);struct.pack_into('<H',expected,0x5E,operand)
   assert bytes(u.mem_read(actor,512))==bytes(expected)
   assert u.reg_read(UC_X86_REG_ESP)==sp and u.reg_read(UC_X86_REG_ESI)==obj
   assert all(u.reg_read(r)==0x12345678 for r in (UC_X86_REG_EBX,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_EDX))
   assert all((sp-12<=a and a+n<=sp) or (a==actor+0x5E and n==2) for a,n in writes),writes
   # The actual renderer calls 98E020, not the adjacent geometry getter.
   u.reg_write(UC_X86_REG_ECX,actor);u.emu_start(0x98E020,stop,count=100)
   assert u.reg_read(UC_X86_REG_EAX)&0xffff==operand and u.reg_read(UC_X86_REG_ESP)==sp+4
   setter_cases+=1
  for flags in range(256):
   u.reg_write(UC_X86_REG_EBX,flags);u.reg_write(UC_X86_REG_ESP,sp);u.mem_write(sp+0x34,struct.pack('<I',operand))
   u.emu_start(0xAA30E2,0xAA30EF,count=10)
   assert u.reg_read(UC_X86_REG_ESI)==operand+(flags>>2&3);renderer_cases+=1
 # Compare both players and Ultimate COM/PAT data with the accepted PS1 build.
 # Tokens carry palette-row AND pixel-index; transparency and flips are included.
 builds=[r for r in json.loads((W/'pause_builds.json').read_text('utf8')) if r['target_arc'].startswith('pl')]
 assert len(builds)==6
 total=0;resources=[]
 for mode in ('ver_rin_nana','ver_buki_riko'):
  ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));p=(ROOT/ptr['cue']).with_suffix('.bin')
  with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==ptr['sha256']
  ps,_=read_disc(p,['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','SLUS_005.61'])
  assert ps['SLUS_005.61'][0xBB67C:0xBB680]==bytes.fromhex('00780224')
  for r in [x for x in builds if x['mode']==mode]:
   pl=int(r['target_arc'][2:4]);source=ps[f'PL{pl:02}_U.ARC'];raw=(ROOT/r['output']).read_bytes();assert sha(raw)==r['output_sha256'];a=SteamArc(raw)
   pat=pat_frames(next(e.payload for e in a.entries if e.payload[:4]==b'PAT\0' and '\\pat\\pl\\' in e.name))
   tex=next(e.payload for e in a.entries if e.payload[:4]==b'TEX\0' and '\\chr\\com\\' in e.name);atlas=np.frombuffer(tex[20:],np.uint8).reshape(-1,256)
   palette_rows=set()
   for frame in range(105,114):
    got=np.zeros((256,256),np.uint16);expected=got.copy()
    for flags,tile,x,y in struct.iter_unpack('<BBbb',pat[1][frame]):
     tile+=(flags&3)*256;pix=atlas[(tile//16)*16:(tile//16+1)*16,(tile%16)*16:(tile%16+1)*16]
     if flags&64:pix=pix[:,::-1]
     if flags&128:pix=pix[::-1]
     row=flags>>2&3;palette_rows.add(row);yy,xx=np.nonzero(pix);got[y+128+yy,x+128+xx]=pix[yy,xx].astype(np.uint16)|(row<<8)
    comp=composition_frame(entry(source,3),1,frame)
    for q in comp['parts']:
     pix=np.frombuffer(tile_pixels(entry(source,0x10206),q['page']*256+q['tile']),np.uint8).reshape(16,16)
     if q['flip_x']:pix=pix[:,::-1]
     if q['flip_y']:pix=pix[::-1]
     yy,xx=np.nonzero(pix);expected[q['y']+128+yy,q['x']+128+xx]=pix[yy,xx].astype(np.uint16)|(q['clut']<<8)
    assert np.array_equal(got,expected);total+=1
   assert palette_rows==({3} if pl==1 else {0})
   resources.append({'mode':mode,'target_arc':r['target_arc'],'palette_rows':sorted(palette_rows),'frames':9,'source_bin_sha256':ptr['sha256']})
 result={'passed':True,'native_setter_getter_cases':setter_cases,'native_renderer_flag_cases':renderer_cases,'ps1_death_frames_equal':total,'only_actor_palette_and_stack_written':True,'native_callees_mocked':False,'single_byte_palette_operand':hex(ADDRESS),'original_value':2,'patched_value':0,'source_ps1_instruction':'00780224','resources':resources,'actual_death_scene_verified':False}
 proof=D/'death_cpu_verification.json';save(proof,result)
 save(W/'effect_colors_runtime.json',{'address':ADDRESS,'before_hex':'02','after_hex':'00','proof_sha256':sha(proof.read_bytes()),'installed_requirements':{r['relative_path']:r['output_sha256']for r in builds},'source':'PS1 accepted death palette base, native uMset11 initializer'})
 print({k:v for k,v in result.items() if k!='resources'})
if __name__=='__main__':main()
