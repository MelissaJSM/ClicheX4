"""Compare native boss animation/dispatch data, normalizing mapped pointers only."""
from pathlib import Path
import json,struct,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from compare_calls import sections
IDS={8,43,45,47,54,56,57,60,61,64,65,66,68,69,73,74,75}
def main():
 sec={r:sections(r) for r in ('us','jp')}
 data={'us':(H/'SLUS_005.61').read_bytes(),'jp':(H/'SLPS_009.02').read_bytes()}
 def owner(region,value):
  off=value-0x8000f800
  for s in sec[region]:
   if s['offset']<=off<s['end']:return (s['kind'],s['name'],off-s['offset'])
  return None
 rows=[]
 for u in sec['us']:
  if u['kind'] not in ('.data','.rodata') or not u['name'].startswith('mains/main_'):continue
  if int(u['name'].split('main_')[1].split('_')[0]) not in IDS:continue
  js=[s for s in sec['jp'] if (s['name'],s['kind'])==(u['name'],u['kind'])]
  assert len(js)==1
  j=js[0];a=data['us'][u['offset']:u['end']];b=data['jp'][j['offset']:j['end']]
  row={'section':u['name'],'kind':u['kind'],'us_start':hex(u['offset']+0x8000f800),'jp_start':hex(j['offset']+0x8000f800),'same_size':len(a)==len(b),'us_size':len(a),'jp_size':len(b)}
  if len(a)!=len(b):rows.append(row);continue
  changed=[];pointers=[]
  for at in range(0,len(a),4):
   aa,bb=a[at:at+4],b[at:at+4]
   if aa==bb:continue
   if len(aa)==4:
    av,bv=struct.unpack('<I',aa)[0],struct.unpack('<I',bb)[0]
    ao,bo=owner('us',av),owner('jp',bv)
    if ao is not None and ao==bo:
     pointers.append({'offset':at,'us':hex(av),'jp':hex(bv),'target':ao});continue
   changed.append({'offset':at,'us':aa.hex(),'jp':bb.hex()})
  row.update(mapped_pointer_differences=pointers,other_differences=changed,all_nonpointer_bytes_equal=not changed)
  rows.append(row)
 report={'scope':'실제 EXE의 보스 애니메이션/상태표가 포함된 데이터 섹션 비교. 지역별 포인터가 동일한 섹션과 상대위치를 가리킬 때만 정규화한다. 초기 섹션 명칭은 디컴파일 설정을 참고하며 음성 이벤트라고 임의 분류하지 않는다.','sections':rows,'passed':all(r.get('all_nonpointer_bytes_equal',False) for r in rows)}
 (H/'boss_data_comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'passed':report['passed'],'sections':len(rows),'differences':[r for r in rows if not r.get('all_nonpointer_bytes_equal')]},ensure_ascii=False))
if __name__=='__main__':main()
