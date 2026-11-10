"""Adapt the established lossless resource checks to four native riding groups."""
from pathlib import Path
D=Path(__file__).resolve().parent
s=(D.parent/'root_nana_return/pack_return.py').read_text('utf8')
s=s.replace('90c614a7996d65ff71381ccc1f673cbfa13b84eccafec83c2e919010310b9239','6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9')
s=s.replace("refs==(156,157,158)","refs==tuple(range(162,175))")
start=s.index(' common_pin,common_proof=common_tall_head')
end=s.index(' nc=a.c;slack={}',start)
s=s[:start]+''' common_proof={'method':'four native shared streams; exact translated composition records, no resampling'}
 for q in m['frames']:groups.setdefault(q['source_key'],[]).append(q['ref'])
 translations={q['ref']:q['translation'][1] for q in m['frames']}
 for key,ns in groups.items():
  order=[(key,pb)for pb in PBS if targets[key,pb].any()]
  nr,rr,method=pack_pinned(bytes(4096),[targets[k][80:240,80:240]for k in order],set(range(1,32))-{16})
  for n in ns:
   dy=translations[n];raws[n]=nr
   for pb in PBS:changes[pb][n]=struct.pack('<BBbb',0,0,-8,-8)
   for (_,pb),parts in zip(order,rr):
    changes[pb][n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80+dy)for t,x,y,fl in parts)
    need(np.array_equal(targets[n,pb],np.roll(targets[key,pb],dy,0)),'Exact native alias')
  atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256);need(not atlas[:,0].any(),'U boundary')
  for n in ns:
   for pb in PBS:
    need(len(changes[pb][n])//4<=24,'Parts overflow')
    for fl,t,x,y in struct.iter_unpack('<BBbb',changes[pb][n]):
     if fl&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),'V boundary')
  reports.append({'refs':ns,'method':method,'parts':{f'{n}/{pb}':len(changes[pb][n])//4 for n in ns for pb in PBS}});print(json.dumps(reports[-1]),flush=True)
''' +s[end:]
s=s.replace("default='packed_return01'","default='packed_vehicle01'").replace("default='joint_targets02'","default='joint_targets03'")
s=s.replace("f'return {n}'","f'ride {n}'")
(D/'pack_vehicle.py').write_text(s,'utf8')
