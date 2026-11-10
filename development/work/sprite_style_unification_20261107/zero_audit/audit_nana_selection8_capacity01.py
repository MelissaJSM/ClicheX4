"""나나 선택8의 고정 atlas 전체 소비와 원 US 코드 읽기. 자원 쓰기 없음."""
from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
import capstone
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from scripts.c01_audio_build import read_disc
from src.psx_ui_atlas import aliased_composition,tile_pixels
O=D/'nana_selection8_capacity01';O.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
P=W/'nana_selection_sync34_03/ST0E_U1.ARC';ui=P.read_bytes()
assert sha(ui)=='a577566919c4dad695950347151ce3a57af8c3247172b04c1f36c5ec6f7101b5'
g,p=entry(ui,0x10102),entry(ui,10);starts=struct.unpack('<3I',entry(ui,12));assert starts==(0,40960,90112)
used=collections.defaultdict(list);records=[];banks=[];targets=set();other=set()
for bank,start in enumerate(starts):
 count=aliased_composition(p,bank,0)['bank_frame_count'];ts=set();rr=[]
 for n in range(count):
  c=aliased_composition(p,bank,n)
  for q in c['parts']:
   t=q['page']*256+q['tile'];assert not q['unknown_flags'];ts.add(t)
   # Full consumed tile, including transparent and covered texels.
   addrs=[start+(t//16*16+y)*128+t%16*8+x for y in range(16)for x in range(8)]
   assert max(addrs)<len(g)
   desc={'bank':bank,'ref':n,'record':q['record_offset'],'local_tile':t}
   for a in addrs:used[a].append(desc)
   rr.append({**desc,'flags':q['flags'],'xy':[q['x'],q['y']]})
   if bank==2:(targets if n in range(1,9)else other).add(t)
 records.extend(rr);banks.append({'bank':bank,'texture_start':start,'nominal_end':starts[bank+1]if bank<2 else len(g),'frames':count,'record_occurrences':len(rr),'local_tiles':sorted(ts),'max_consumed_byte':max(start+(t//16*16+15)*128+t%16*8+7 for t in ts)})
capacity=(len(g)-starts[2])//128;unconsumed=[];rows=[]
for t in range(capacity):
 addrs=[starts[2]+(t//16*16+y)*128+t%16*8+x for y in range(16)for x in range(8)]
 consumers={(c['bank'],c['ref'])for a in addrs for c in used[a]}
 if not consumers:unconsumed.append(t)
 z=tile_pixels(g[starts[2]:],t)
 rows.append({'tile':t,'opaque_texels':sum(v!=0 for v in z),'consumers':[list(v)for v in sorted(consumers)],'safe_without_U0_V0_padding':t%16!=0 and t%256>=16,'sha256':sha(z)})
cross=[{'bank':b['bank'],'max_consumed_byte':b['max_consumed_byte']}for b in banks if b['bank']!=2 and b['max_consumed_byte']>=90112]
og,_=read_disc(ROOT/'MegaMan X4.bin',['SLUS_005.61']);plan=json.loads((W/'staging_rn_v37.json').read_text('utf8'));ng,_=read_disc(ROOT/plan['source_bin'],['SLUS_005.61']);oe,ne=og['SLUS_005.61'],ng['SLUS_005.61'];off=lambda a:a-0x80010000+2048
cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN);code=[]
for name,lo,hi in [('select_init',0x800cca34,0x800ccca0),('select_all',0x800cca34,0x800cd78c),('archive_loader',0x80013014,0x80013424),('menu_resolver',0x8002938c,0x80029420)]:
 ob,nb=oe[off(lo):off(hi)],ne[off(lo):off(hi)];assert ob==nb
 f=O/(name+'_mips.txt');f.write_text('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}'for i in cs.disasm(nb,lo))+'\n','utf8');code.append({'name':name,'addresses':[hex(lo),hex(hi)],'original_current_exact':True,'sha256':sha(nb),'disassembly':rel(f)})
(O/'select_tables.bin').write_bytes(ne[off(0x8010e968):off(0x8010ebdc)])
r={'scope':'Nana 선택 1..8 고정 ST0E atlas 소비 조사. 후보 생성/적용 없음.','input':{'path':rel(P),'sha256':sha(ui)},'texture_bytes':len(g),'texture_directory':list(starts),'entries':psx_arc(ui),'banks':banks,'X_tail_tiles':capacity,'target_tiles':sorted(targets),'non_target_X_tiles':sorted(other),'shared_target_tiles':sorted(targets&other),'exclusive_target_tiles':sorted(targets-other),'all_banks_unconsumed_X_tiles':unconsumed,'unconsumed_unrestricted_UV_tiles':[t for t in unconsumed if t%16!=0 and t%256>=16],'cross_bank_access_into_X_tail':cross,'all_tile_rows':rows,'all_record_occurrences':records,'original_current_code':code,'original_EXE_sha256':sha(oe),'current_EXE_sha256':sha(ne),'source_BIN':plan['source_bin'],'native_access_review_pending':True,'candidate_written':False,'new_MIPS_executed':False,'runtime_verified':False}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'texture_bytes':len(g),'capacity':capacity,'banks':[{k:v for k,v in b.items()if k!='local_tiles'}for b in banks],'target':len(targets),'exclusive':len(targets-other),'shared':sorted(targets&other),'unconsumed':unconsumed,'unrestricted':r['unconsumed_unrestricted_UV_tiles'],'cross':cross,'sha256':sha((O/'report.json').read_bytes())}))
