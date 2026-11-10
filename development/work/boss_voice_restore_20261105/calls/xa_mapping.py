from pathlib import Path
import json,struct
H=Path(__file__).resolve().parent
def u32(b,a):return struct.unpack_from('<I',b,a-0x8000f800)[0]
def u16(b,a):return struct.unpack_from('<H',b,a-0x8000f800)[0]
NAMES=['Web Spider','Frost Walrus','Split Mushroom','Magma Dragoon','Jet Stingray','Cyber Peacock','Storm Owl','Slash Beast','Colonel','Iris','Double','General','Sigma']
def main():
 out={}
 for region,name,table,ptrtable in [('us','SLUS_005.61',0x80105fc8,0x800f19e0),('jp','SLPS_009.02',0x80106104,0x800f1b70)]:
  b=(H/name).read_bytes()
  rows=[]
  for boss in range(13):
   ids=list(b[table-0x8000f800+boss*3:table-0x8000f800+boss*3+3])
   clips=[]
   for track in ids:
    group=track>>3;selection=track&7;p=u32(b,ptrtable+group*4);orig=p;ch=0
    if not 0x80010000<=p<0x80130000: raise ValueError(f'{region} ptr {p:x} group {group}')
    for step in range(selection):
     if u16(b,p)&0x8000:ch+=1;p+=2
     p+=2
    start=u16(b,p)&0x7fff;end=u16(b,p+2)&0x7fff
    clips.append({'track':track,'track_hex':hex(track),'group':group,'selection':selection,'table_address':hex(orig),'entry_address':hex(p),'start_table':start,'end_table':end,'channel':ch,'raw_sector_start_relative':start*8+ch,'raw_sector_end_relative':end*8+ch,'selected_channel_sectors':end-start,'approx_seconds_37800_stereo':(end-start)*2016/37800,'archive': ('VOICE'+str(group-4)+('_U' if region=='us' else '')+'.XA') if 5<=group<=9 else ('BOSINT_U.XA' if region=='us' else 'BOSSINT.XA') if group==10 else 'OTHER'})
   rows.append({'boss_index':boss,'boss':NAMES[boss],'track_ids':ids,'clips':clips,'calls_enabled':region=='jp' or boss>=8})
  out[region]={'table_address':hex(table),'pointer_table_address':hex(ptrtable),'bosses':rows}
 (H/'xa_mapping.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
 for r,d in out.items():
  print(r)
  for row in d['bosses']:print(row['boss'],[(c['track_hex'],c['archive'],c['channel'],c['start_table'],c['end_table']) for c in row['clips']])
if __name__=='__main__':main()
