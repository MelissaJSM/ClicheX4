"""보존된 탑승 상태를 읽기만 하여 실제 조종석 비교 자료를 추출한다."""
from pathlib import Path
import gzip,hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from src.epsxe_state import framebuffer
D=Path(__file__).parent/'rin_extension'/'ride_cockpit_review01';D.mkdir(exist_ok=True)
P=ROOT/'work/ver_rin_nana/checkpoints/ride_armor_accepted_20261029T005856936087Z/accepted_ride_armor/SLUS_005.61.000'
b=P.read_bytes();sha=hashlib.sha256(b).hexdigest();assert sha=='a07e488ce7ed48a69af7d5175e7f16794e2c2a196810d395ab71a5ac78fdbf46'
s=gzip.decompress(b);assert s.startswith(b'ePSXe\x06\x00SLUS_005.61') and len(s)==4254418
ram=s[442:442+0x200000];player=ram[0x1418c8:0x1418c8+0xe4]
for p in (0,240):framebuffer(s,2569183,p).save(D/f'original_framebuffer_{p}.png')
r={'source':str(P.relative_to(ROOT)),'source_sha256':sha,'state_bytes':len(s),'ram_offset':442,'vram_offset':2569183,'player':{'raw_hex':player.hex(),'frame':player[0x47],'animation':player[0x48],'ride_animation':player[0xd4],'facing':player[0x15],'world':[struct.unpack_from('<i',player,o)[0]/65536 for o in (8,12)],'resource':[hex(struct.unpack_from('<I',player,o)[0])for o in(0x34,0x3c)],'clut':hex(struct.unpack_from('<H',player,0x42)[0])},'scope':'예전 사용자 수용 탑승 상태를 읽은 비교 입력이며 현재 수정본 실행 증거가 아닙니다. 원본 상태/에뮬레이터를 수정하지 않습니다.'}
r['mech_objects']=[]
for table in (0x800f9428,0x800f965c):
 cursor=0
 while (cursor:=ram.find(struct.pack('<I',table),cursor))>=0:
  pos=cursor-0x2c;cursor+=1
  if not 0x140000<=pos<0x160000:continue
  o=ram[pos:pos+0xb0]
  r['mech_objects'].append({'address':hex(pos+0x80000000),'raw_hex':o.hex(),'active':o[0],'id':o[1],'state':o[4],'frame':o[0x47],'facing':o[0x15],'world':[struct.unpack_from('<i',o,k)[0]/65536 for k in(8,12)],'parts_address':hex(struct.unpack_from('<I',o,0x3c)[0]),'tpage':hex(struct.unpack_from('<H',o,0x40)[0]),'clut':hex(struct.unpack_from('<H',o,0x42)[0])})
(D/'source.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(r))
