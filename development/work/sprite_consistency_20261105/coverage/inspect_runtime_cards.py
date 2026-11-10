"""실기 경로 준비용 기존 카드/공통 로더 읽기 감사. 카드 출력·수정 없음."""
import json,struct,sys
from functools import reduce
from operator import xor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.audit_sprite_consistency_coverage import file_sha,sha,read_assets,write
from scripts.observe_sprite_consistency_runtime import EXPECTED

selected=[
 ('shibuki_riko_current','work/ver_buki_riko/baseline/20261023T054951214649Z/emulator/memcards/epsxe000.mcr'),
 ('shibuki_riko_current','work/ver_buki_riko/baseline/20261023T054951214649Z/emulator/memcards/epsxe001.mcr'),
 ('nana_rin_current','work/ver_rin_nana/emulator/memcards/epsxe000.mcr'),
 ('nana_rin_current','work/ver_rin_nana/emulator/memcards/epsxe001.mcr'),
 ('existing_nana_rin_test_copy','work/ver_rin_nana/test_cards/idle_v1/epsxe000.mcr'),
 ('existing_nana_rin_test_copy','work/ver_rin_nana/test_cards/idle_v1/epsxe001.mcr'),
 ('existing_historical_ultimate_test_copy','work/ver_buki_riko/shibuki_art/ultimate_v1/test_save/card2_ultimate.mcr'),
 ('existing_historical_ultimate_test_copy','work/ver_rin_nana/nana_ultimate_armor/test_cards_v1/card2_ultimate.mcr'),
 ('historical_derived_preultimate_test_copy','work/ver_buki_riko/overhaul_runtime/preultimate_cards/card2_preultimate.mcr'),
 ('historical_derived_preultimate_test_copy','work/ver_rin_nana/overhaul_runtime/preultimate_cards/card2_preultimate.mcr')]

def inspect(label,path):
 p=ROOT/path;data=p.read_bytes();initial=sha(data);assert len(data)==131072 and data[:2]==b'MC'
 checks=[reduce(xor,data[n*128:n*128+127],0)==data[n*128+127]for n in range(16)]
 assert all(checks),f'Card header/directory checksum failed {path}'
 saves=[]
 for block in range(1,16):
  directory=data[block*128:(block+1)*128];name=directory[10:30].split(b'\0')[0]
  if directory[0]!=0x51 or name!=b'BASLUS-00561':continue
  assert int.from_bytes(directory[4:8],'little')==8192 and directory[8:10]==b'\xff\xff'
  assert data[block*8192:block*8192+4]==b'sc\x13\x01'
  for slot in range(3):
   offset=block*8192+512+slot*42;r=data[offset:offset+42];character=r[0]
   saves.append({'data_slot':slot+1,'card_file_block':block,'record_offset':offset,'raw_hex':r.hex(),
    'character':character,'empty':character==255,'max_hp':r[1],'arm_type':r[2],'armor_mask':r[3],
    'boss_palette_flags':r[4],'all8_boss_flag':r[4]==255,'progress_byte5':r[5],
    'upgrade_flags':struct.unpack_from('<H',r,6)[0],'native_progress_words':list(struct.unpack_from('<16H',r,8)),
    'ultimate_if_X_or_black_if_Zero':r[41]})
 assert file_sha(p)==initial
 return {'kind':label,'path':path,'sha256':initial,'size':len(data),'directory_xor16_passed':True,'x4_slots':saves,'unchanged_after_read':True}

cards=[inspect(*row)for row in selected];exes={};builds={}
for mode,expected in EXPECTED.items():
 pointer=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));stem='shibuki_riko'if mode=='ver_buki_riko'else'rin_nana'
 path=ROOT/pointer['build']/f'{stem}.bin';assert file_sha(path)==expected
 assets,_=read_assets(path,['SLUS_005.61']);exes[mode]=assets['SLUS_005.61'];builds[mode]={'bin':path.relative_to(ROOT).as_posix(),'sha256':expected,'exe_sha256':sha(exes[mode])}
assert exes['ver_buki_riko']==exes['ver_rin_nana']
exe=exes['ver_buki_riko'];lo=0x8001c210-0x80010000+2048;hi=0x8001c4b4-0x80010000+2048
proof={'passed':True,'cards':cards,'builds':builds,'current_mode_executables_byte_identical':True,
 'common_native_loader_range':['0x8001C210','0x8001C4B4'],'loader_sha256':sha(exe[lo:hi]),
 'loader_source':'work/research/decomp/src/main/menu.c:1141..1209 and include/obj.h MemcardSaveSlot size42',
 'cross_mode_scope':'동일 US 저장 구조/동일 현재 EXE. 같은 캐릭터 ID·아머·보스/무기 진행을 다른 모드의 외형으로 시험 가능. 다른 모드에서 실제로 플레이해 얻은 진행이라는 주장은 하지 않음.',
 'cards_written':False,'active_F1_used':False,'limitations':['이전 F3는 자산 캐시를 포함하므로 새 BIN 로딩 증거로 사용하지 않는다.','카드 기록은 stage checkpoint를 저장하지 않아 메뉴에서 스테이지에 새로 진입해야 한다.','역사적 테스트 카드의 Ultimate 변경은 사용자 실제 캡슐 획득과 구분한다.']}
write(Path(__file__).with_name('runtime_card_inventory.json'),proof)
print(json.dumps({'passed':True,'cards':len(cards),'same_exe_sha256':sha(exe)}))
