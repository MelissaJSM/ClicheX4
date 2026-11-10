"""메모리카드 읽기 전용 목록. 카드/게임/활성 저장에는 쓰지 않는다."""
import hashlib,json,sys
from pathlib import Path
from functools import reduce
from operator import xor
ROOT=Path(__file__).resolve().parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def inspect(path):
 raw=path.read_bytes();row={'path':path.relative_to(ROOT).as_posix(),'sha256':sha(raw),'size':len(raw),'files':[]}
 if len(raw)!=131072 or raw[:2]!=b'MC':return {**row,'valid':False,'reason':'format'}
 row['directory_xor_valid']=all(reduce(xor,raw[i*128:i*128+127],0)==raw[i*128+127] for i in range(16))
 for block in range(1,16):
  rec=raw[block*128:(block+1)*128];name=rec[10:30].split(b'\0')[0].decode('ascii',errors='replace')
  if rec[0]!=0x51 or not name.startswith('BASLUS-00561'):continue
  size=int.from_bytes(rec[4:8],'little');base=block*8192;slots=[]
  for n in range(3):
   off=base+512+n*42;s=raw[off:off+42];character=s[0];special=s[41];armor=s[3]
   kind=('empty' if character==255 else 'ultimate_pre' if character==0 and special and not armor else 'ultimate_post' if character==0 and special and armor else 'x_fourth_or_base' if character==0 else 'black_zero' if character==1 and special else 'zero' if character==1 else 'unknown')
   slots.append({'DATA':n+1,'offset':off,'character':character,'max_hp':s[1],'arm_type':s[2],'armor':armor,'boss_palette_flags':s[4],'special_flag':special,'kind':kind,'raw':s.hex()})
  row['files'].append({'directory_block':block,'name':name,'size':size,'next_block':int.from_bytes(rec[8:10],'little'),'header_hex':raw[base:base+4].hex(),'slots':slots})
 row['valid']=row['directory_xor_valid'] and all(f['size']==8192 and f['next_block']==65535 and f['header_hex']=='73631301' for f in row['files'])
 return row
def main():
 paths=sorted(p for mode in ('ver_buki_riko','ver_rin_nana') for p in (ROOT/'work'/mode).rglob('*.mcr'))
 rows=[inspect(p) for p in paths]
 after={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in paths}
 changed=[r['path'] for r in rows if r['sha256']!=after[r['path']]]
 report={'scope':'read-only existing memory-card files; no emulation or card mutation','cards_read':len(rows),'contents_stable_during_audit':not changed,'changed_during_read':changed,'rows':rows}
 out=Path(__file__).parent/'card_inventory.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 selected=[]
 for row in rows:
  p=row['path']
  if ('/emulator/memcards/' in p or '/preultimate_cards/' in p or '/test_cards_v1/' in p or '/test_save/' in p) and '/original_backup/' not in p:selected.append({'path':p,'sha256':row['sha256'],'valid':row['valid'],'slots':[s for f in row['files'] for s in f['slots']]})
 print(json.dumps({'cards_read':len(rows),'stable':not changed,'selected':selected},ensure_ascii=False))
if __name__=='__main__':main()
