from pathlib import Path
D=Path(__file__).resolve().parent;S=D.parent/'root_nana_arrival'
s=(S/'pack_arrival.py').read_text('utf8')
for a,b in [
 ('new arrival-pose','new victory-pose'),
 ('ef69d0a13ad11ede874f2642bd9df719cbb2d864798801867b6738f728df6df4','9599ca5fc21828df5ef4d865eafab4d27aa06a7b2391873a063c887120e70f91'),
 ('(135,136,137)','(204,205,206,207)'),
 ('across135/136/137','across204/205/206/207'),
 ('(130,131,133,134,135,136,137)','(204,205,206,207)'),
 ('records(a.c,5,51)if n in(133,134)else common_pin','common_pin'),
 ('packed_arrival01','packed_victory01'),
 ("f'arrival {n}'","f'victory {n}'")
]:
 assert a in s,a;s=s.replace(a,b)
start=s.index(' # 131 originally shares a stream')
end=s.index(' ng,packing=',start)
s=s[:start]+' counts={n:32 for n in refs}\n'+s[end:]
p=D/'pack_victory.py';assert not p.exists();p.write_text(s,'utf8')
print('victory packer prepared; parent and exact four references pinned')
