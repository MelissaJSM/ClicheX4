"""원화/층 변경 없이 기존 head5 조립기록으로 새층을 수납할 수 있는지 읽는다."""
from pack_candidate import *
def choices(a,z):
 seen=set();rows=[]
 for n in range(237):
  rr=list(struct.iter_unpack('<BBbb',records(a.c,5,n)))
  for length in range(1,min(8,len(rr))+1):
   sub=rr[-length:];key=tuple(sub)
   if key in seen:continue
   seen.add(key)
   if any(fl or t in(0,16)or t>=32 for fl,t,x,y in sub)or len({t for fl,t,x,y in sub})!=len(sub):continue
   rem=z.copy()
   for fl,t,x,y in sub:
    if not(-80<=x<=64 and -80<=y<=64):break
    rem[y+160:y+176,x+160:x+176]=0
   else:
    if not rem.any():rows.append({'source_ref':n,'records':sub,'hex':b''.join(struct.pack('<BBbb',*r)for r in sub).hex()})
 return sorted(rows,key=lambda r:(len(r['records']),r['source_ref'],r['hex']))
if __name__=='__main__':
 a=Archive(PARENT.read_bytes());t,_=targets();out=D/'head_templates_probe_v2';out.mkdir(exist_ok=False);r={str(n):choices(a,t[n,5])for n in REFS};write(out/'choices.json',r)
 for n,q in r.items():print(json.dumps({'ref':n,'count':len(q),'first':q[:2]}))
