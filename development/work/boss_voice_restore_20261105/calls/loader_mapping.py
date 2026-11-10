from pathlib import Path
import json,struct
H=Path(__file__).resolve().parent
def read(b,address,n):return b[address-0x8000f800:address-0x8000f800+n]
def main():
 out={}
 for r,n in [('us','SLUS_005.61'),('jp','SLPS_009.02')]:
  b=(H/n).read_bytes();pref=b'E:\\ROCKX4\\'+(b'USA' if r=='us' else b'JAPAN')+b'\\ARC\\CAPCOM.ARC'
  p=b.index(pref);paths={i:b[p+i*64:p+(i+1)*64].split(b'\0')[0].decode('ascii','replace').replace('\\','/').split('/')[-1] for i in range(170)}
  initial_pattern=bytes.fromhex('5455565758595a5b5c5d5e5f60616263646566006700')
  at=b.index(initial_pattern);common=b[at:at+32]
  loadtable=0x8010b434+(0 if r=='us' else 0x13c)
  rematch=at+0x8000f800-8
  rows=[]
  for stage in range(13):
   ids=list(common[stage*2:stage*2+2]);bossid=read(b,loadtable+stage,1)[0]
   rows.append({'stage':stage,'initial_common_ids':ids,'initial_common':[paths[i] if i else None for i in ids],'boss_bank_load_id':bossid,'boss_bank_archive':paths[bossid] if bossid else None})
  rem=read(b,rematch,8)
  out[r]={'archive_path_table':hex(p+0x8000f800),'path_stride':64,'initial_stage_table':hex(at+0x8000f800),'boss_load_table':hex(loadtable),'stage_common':rows,'stage11_area0_character_variants':[paths[i] for i in b[at+40:at+42]],'rematch_table_address':hex(rematch),'rematch_checkpoint_2_to_9':[{'checkpoint':i+2,'id':x,'archive':paths[x]} for i,x in enumerate(rem)],'sigma_final_secondary_load':{'call':hex(0x8008d51c+(0 if r=='us' else 0x5c)),'file_id':0x81 if r=='us' else 0x80,'archive':paths[0x81 if r=='us' else 0x80]},'path_id_map':paths}
 (H/'loader_mapping.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
 for r,d in out.items():
  print(r,d['initial_stage_table'],d['rematch_checkpoint_2_to_9']);[print(x) for x in d['stage_common']]
if __name__=='__main__':main()
