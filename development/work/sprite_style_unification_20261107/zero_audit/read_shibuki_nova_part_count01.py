"""24파트 제작기 가드와 원US 조립count/렌더러를 읽기만 대조."""
from pathlib import Path
import collections,hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit';sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame,bank_offsets
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
O=D/'shibuki_nova_part_count_read01';assert not O.exists()
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();inputs={}
def read(p):
 b=p.read_bytes();inputs[rel(p)]=sha(b);return b
orig=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61','PL00_U.ARC','PL02_U.ARC'))[0]
disc=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v27/shibuki_riko.bin'
current=read_disc(disc,('SLUS_005.61',))[0]['SLUS_005.61'];exe=orig['SLUS_005.61'];base=struct.unpack_from('<I',exe,24)[0]
def code(e,lo,hi):return e[lo-base+2048:hi-base+2048]
cs=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN);O.mkdir(exist_ok=False);ranges=[]
for name,lo,hi in [('base_sprite',0x80024334,0x80024920),('partial_sprite',0x8002588c,0x80025cdc),('object_dispatch',0x80023db8,0x800241e8),('frame_allocators',0x80025cdc,0x80025da0)]:
 b=code(exe,lo,hi);now=code(current,lo,hi);ins=[{'address':hex(i.address),'mnemonic':i.mnemonic,'operands':i.op_str,'bytes':bytes(i.bytes).hex()}for i in cs.disasm(b,lo)]
 p=O/f'{name}_mips.txt';p.write_text('\n'.join(f'{int(i["address"],16):08x} {i["mnemonic"]} {i["operands"]}'for i in ins)+'\n','utf8')
 ranges.append({'name':name,'lo':hex(lo),'hi':hex(hi),'original_sha256':sha(b),'BR27_same_as_original_US':b==now,'BR27_sha256':sha(now),'disassembly_path':rel(p),'disassembly_sha256':sha(p.read_bytes())})
inventory=[]
for tag,data in [('US_PL00',orig['PL00_U.ARC']),('US_PL02',orig['PL02_U.ARC']),('Shibuki619032',read(H/'prepared_nova_base01/PL00_U.ARC'))]:
 a=Archive(data);rows=[]
 for pb in (0,5,6,7,8):
  values=[]
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   q=composition_frame(a.c,pb,n);values.append(len(q['parts']))
  rows.append({'bank':pb,'max_count':max(values),'count_distribution':dict(collections.Counter(values)),'over24':[{ 'ref':n,'count':v}for n,v in enumerate(values)if v>24]})
 nova=[]
 for n in range(217,221):
  counts={str(pb):len(composition_frame(a.c,pb,n)['parts'])for pb in(0,5,6,7,8)};nova.append({'ref':n,'counts':counts,'mask15_all_layers_count':sum(counts.values())})
 inventory.append({'source':tag,'sha256':sha(data),'banks':rows,'nova':nova})
sources=['work/sprite_style_unification_20261107/shibuki_audit/native_pose_pack.py','scripts/prepare_shibuki_ultimate_production.py','src/psx_player.py','work/research/decomp/src/main/14A60.c','work/research/decomp/include/obj.h','work/research/decomp/include/scratchpad.h','work/sprite_style_unification_20261107/shibuki_audit/prepare_nova_strike_base_targets.py','work/sprite_style_unification_20261107/shibuki_audit/nova_strike_base_targets01/effect220_prefix.bin','work/sprite_style_unification_20261107/shibuki_audit/nova_strike_base_targets01/manifest.json']
for path in sources:read(ROOT/path)
r={'scope':'Shibuki Nova220 후보31 base파트/전체38 요청에 대한 원코드/원자원 읽기. 후보쓰기·실행 없는 초기근거.','US_exe_sha256':sha(exe),'BR27_exe_sha256':sha(current),'code_ranges':ranges,'count_inventory':inventory,'packer_guard':'native_pose_pack.py lossless_pack/packing는24를 명시적 제한으로 전달/검사하며 메시지 자체가 Native part limit requires investigation이다. 실제원US상한을인용하지않는다.','format':'조립header 하위16bit count, 상위16bit*4 상대record시작. repack_parts는4byte레코드 개수 저장. readonly composition_frame의256상한도 도구의검사이며 원US최대성능보장 아님.','native_or_runtime_executed':False,'candidate_or_source_changed':False,'inputs':inputs}
p=O/'read_data.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report':sha(p.read_bytes()),'count_summary':[{'source':q['source'],'nova':q['nova'],'over24':q['banks'][0]['over24']}for q in inventory],'ranges':ranges}))
