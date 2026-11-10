"""PL00 등장섬광과 분신소멸의 실제 원 caller/renderer 참여를 읽는다."""
from pathlib import Path
import collections,hashlib,json,struct,sys
import numpy as np
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;sys.path[:0]=[str(R),str(D)]
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,animation_map
from src.psx_player import composition_frame,decode_stream
def parts(ar,pb,n):return composition_frame(ar.c,pb,n)['parts']
def raw(ar,gb,n):
 f=ar.banks[gb]['frames'][n];return decode_stream(ar.g,f['offset'],f['limit'],f['tile_count']*128).data
O=D/'nana_base_effect_callers01';assert not O.exists();tracked={};sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(R).as_posix()
def read(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
def digest(p):
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 tracked[rel(p)]=h;return h
src=R/'out/ver_rin_nana/sprite_style_unification_20261107_v41/rin_nana.bin';assert digest(src)=='e765577ac65cff3348a76ab0d2719ea96471b2c7895a35ac5a3c428db87385b3'
original=R/'MegaMan X4.bin';assert digest(original)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
e=read_disc(src,('SLUS_005.61',))[0]['SLUS_005.61'];od=read_disc(original,('SLUS_005.61','PL00_U.ARC'))[0];u=od['SLUS_005.61'];us=Archive(od['PL00_U.ARC']);base=struct.unpack_from('<I',e,24)[0]
cp=W/'root_nana_hover/packed_hover_final01/PL00_U.ARC';a=Archive(read(cp));assert sha(a.data)=='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c'
def code(ex,lo,hi):return ex[lo-base+2048:hi-base+2048]
cs=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN);O.mkdir(exist_ok=False);ranges=[]
for name,lo,hi in [('player_update',0x800311ec,0x800312b0),('beam_in',0x80031410,0x80031540),('draw_player_and_clone',0x80023e70,0x80023ed0),('armor_wrapper',0x800257bc,0x8002588c),('set_animation',0x800350a4,0x8003516c),('clone_init',0x800355c0,0x80035694),('clone_cast_wait_advance',0x80039120,0x80039328),('clone_vanish',0x80039328,0x80039378),('clone_update',0x80094f74,0x800951c0)]:
 b=code(e,lo,hi);orig=code(u,lo,hi);p=O/f'{name}_mips.txt';p.write_text('\n'.join(f'{i.address:08x} {bytes(i.bytes).hex()} {i.mnemonic} {i.op_str}'for i in cs.disasm(b,lo))+'\n',encoding='utf8');read(p)
 if name!='armor_wrapper':assert b==orig,name
 ranges.append({'name':name,'start':hex(lo),'end':hex(hi),'sha256':sha(b),'US_exact':b==orig,'original_sha256':sha(orig),'path':rel(p)})
an,refs=animation_map(e);un,ur=animation_map(u);sequences=[]
for aid in(2,98):
 aa=next(x for x in an if x['id']==aid);uu=next(x for x in un if x['id']==aid);assert aa==uu;sequences.append(aa)
inventory=[]
for tag,arc in [('US_PL00',us),('current_PL00',a)]:
 for n in(140,208,209,210,211,212):
  f=arc.banks[0]['frames'][n];layers=[]
  for pb in(0,5,6,7,8):
   z=arc.layer(n,pb)[0];ps=parts(arc,pb,n);q=composition_frame(arc.c,pb,n);locs={p['record_offset']for p in ps};aliases=[]
   if locs:
    for k in range(q['bank_frame_count']):
     if k!=n and locs&{p['record_offset']for p in parts(arc,pb,k)}:aliases.append(k)
   layers.append({'bank':pb,'count':len(ps),'opaque':int((z>0).sum()),'nonzero_indices':sorted(map(int,np.unique(z[z>0]))),'tiles':sorted({p['tile']+p['page']*256 for p in ps}),'records':[{'offset':p['record_offset'],'flags':p['flags'],'tile':p['tile'],'x':p['x'],'y':p['y']}for p in ps],'same_bank_shared_record_refs':aliases})
  inventory.append({'source':tag,'ref':n,'tile_count':f['tile_count'],'decoded_bytes':len(raw(arc,0,n)),'raw_same_stream_refs':[q['index']for q in arc.banks[0]['frames']if q['offset']==f['offset']],'layers':layers})
flash=a.layer(140,0)[0];idle=a.layer(0,0)[0]>0;fx=(flash>0)&~idle;assert int(idle.sum())==603 and int(fx.sum())==46 and np.all(flash[flash>0]==13)
extras={pb:(a.layer(0,pb)[0]>0)&~idle for pb in(5,6,7,8)};maskrows=[]
for mask in range(16):
 goal=np.array(a.composite(0,mask)[0])[:,:,3]>0;theory=flash>0
 for bit,pb in((1,5),(2,6),(4,7),(8,8)):
  if mask&bit:theory=theory|extras[pb]
 assert np.array_equal(theory,goal|fx)
 now=np.array(a.composite(140,mask)[0])[:,:,3]>0;old=np.array(us.composite(140,mask)[0])[:,:,3]>0
 assert np.array_equal(now,flash>0)and np.array_equal(old,us.layer(140,0)[0]>0)
 maskrows.append({'mask':mask,'current140_opaque':int(now.sum()),'current_idle_opaque':int(goal.sum()),'missing_idle_alpha':int((goal&~now).sum()),'base_alpha_removed_by_current_idle':int((idle&~goal).sum()),'theoretical_selected_overlay_plus_original46_exact':True,'originalUS140_same_alpha_across_masks':True})
palette_matches={str(s):[i for i in range(1,16)if a.words[s+i]==a.words[13]]for s in(16,32)};assert palette_matches=={'16':[13],'32':[13]}
for path in ('scripts/prepare_nana_air_clone_art.py','work/research/decomp/src/main/player.c','work/research/decomp/src/main/player_common.c','work/research/decomp/src/main/player_special.c','work/research/decomp/src/main/player_weapon.c','work/research/decomp/src/main/player_animations.c','work/research/decomp/src/main/14A60.c','work/research/decomp/config/symbols.us.txt','work/sprite_style_unification_20261107/root_nana_base_effect_audit01/report.json','work/sprite_style_unification_20261107/root_nana_clone210_source01/report.json'):
 read(R/path)
read(Path(__file__))
report={'scope':'Nana PL00 140/208..212 실제caller·렌더러/원US정책 읽기. 새원화·ARC·EXE 변경 및 MIPS실행 없음.','candidate':rel(cp),'candidate_sha256':sha(a.data),'source_bin':rel(src),'RN41_EXE_sha256':sha(e),'US_EXE_sha256':sha(u),'original_US_PL00_sha256':sha(us.data),'code_ranges':ranges,'original_US_tables_exact':sequences,'actual_resource_inventory':inventory,'flash140_masks':maskrows,'flash140_overlay_possible_alpha_only':{'source':'현재 수용idle0 부분층의 base알파 밖 표본만 사용한 읽기 계산','extra_alpha_by_layer':{str(pb):int(z.sum())for pb,z in extras.items()},'all16_union_reproduces_corresponding_idle_plus_old46':True,'palette0_index13_word':hex(a.words[13]),'same_palette_values':palette_matches,'prospective_art_or_ARC_written':False,'fit_or_native_candidate_verified':False},'inputs':tracked,'actual_runtime':False,'new_MIPS_executed':False,'resource_or_source_modified':False}
p=O/'report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'report':sha(p.read_bytes()),'ranges':[{k:x[k]for k in('name','US_exact')}for x in ranges],'mask15':maskrows[-1],'extra_by_layer':report['flash140_overlay_possible_alpha_only']['extra_alpha_by_layer']}))
