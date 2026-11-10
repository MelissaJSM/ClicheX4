"""Back up the working emulator state, then validate a newly made F1 locally."""
from pathlib import Path
import json,sys,shutil,gzip,struct
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,digest
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank
D=Path(__file__).parent
EM=ROOT/'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator'
B=Path(json.loads((D/'builds.json').read_text())['build']['output'])
if sys.argv[1]=='prepare':
 out=new_run(ROOT,'ver_buki_riko','current_build_saves');before=out/'before_new_f1';before.mkdir()
 for name in ('SLUS_005.61.000','SLUS_005.61.000.pic'):
  src=EM/'sstates'/name
  if src.exists():shutil.copyfile(src,before/name)
 record={'output':str(out),'build':str(B),'previous_working_state_sha256':digest(before/'SLUS_005.61.000')}
 write_json(D/'checkpoint_preparation.json',record);print(json.dumps(record))
else:
 prep=json.loads((D/'checkpoint_preparation.json').read_text());out=Path(prep['output']);src=EM/'sstates/SLUS_005.61.000'
 if digest(src)==prep['previous_working_state_sha256']:raise ValueError('No new F1 written')
 data=gzip.decompress(src.read_bytes());ram=data[442:442+2097152]
 profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text());exe=(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z/original.exe').read_bytes()
 address=profile['zero_animation_table_address'];offset=address-profile['executable']['load_address']+2048
 assert ram[address&0x1fffff:(address&0x1fffff)+576]==exe[offset:offset+576]
 p=ram[0x1418c8:0x1418c8+0xe4];e=ram[0x1721c0:0x1721c0+0x64];ptr=struct.unpack_from('<I',p,0x38)[0]&0x1fffff
 arc=(B/'modified.arc').read_bytes();entry=next(e for e in psx_arc(arc) if e['type']=='0x2');gfx=arc[entry['offset']:entry['offset']+entry['size']];bank=graphics_bank(gfx,0)
 assert ram[ptr:ptr+bank['end']-bank['base']]==gfx[bank['base']:bank['end']]
 assert p[2]==1 and p[0xb9]==255 and e[0x59]==255
 for name in ('SLUS_005.61.000','SLUS_005.61.000.pic'):
  source=EM/'sstates'/name
  if source.exists():shutil.copyfile(source,out/name)
 result={'session':str(ROOT/sys.argv[2]),'build':str(B),'bin_sha256':json.loads((B/'manifest.json').read_text())['modified_bin']['sha256'],
  'state_sha256':digest(src),'ram_offset':442,'full_current_bank0_equal':True,'character':p[2],'boss_flags':p[0xb9],'hp':p[0x5c],
  'x':struct.unpack_from('<i',p,8)[0]/65536,'y':struct.unpack_from('<i',p,12)[0]/65536,
  'source_memory_card_sha256':digest(EM/'memcards/epsxe000.mcr'),'source':'Fresh BIN -> CONTINUE -> memory card slot1/data1 -> stage -> pause -> F1',
  'source_f1_loaded':False,'saved_in_pause_menu':True,'original_user_files_overwritten':False}
 write_json(out/'manifest.local.json',result);print(json.dumps({'output':str(out),**result}))
