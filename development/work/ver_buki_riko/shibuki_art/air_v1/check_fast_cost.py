import json,sys,time,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from psx_compress_cost import encoded_cost
from src.psx_compress import encode_stream
from src.psx_player import graphics_bank,decode_stream
g=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/graphics_entry.bin').read_bytes();seen=set();cases=[]
for b in range(len(json.loads((ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json').read_text())['graphics_banks'])):
 for f in graphics_bank(g,b,allow_bank_aliases=True)['frames']:
  if f['offset'] in seen:continue
  seen.add(f['offset']);cases.append(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data)
rng=random.Random(82)
for i in range(50):cases.append(bytes(rng.choice((0,0,0,0,1,2,15,255)) for j in range(2*rng.randrange(1,1300))))
cases.extend((bytes(2560),bytes([0,1])*1280,bytes(range(256))*10))
for raw in cases:assert encoded_cost(raw)==len(encode_stream(raw)),len(raw)
start=time.perf_counter()
for i in range(100):encoded_cost(cases[20])
r={'original_unique_streams':len(seen),'random_and_boundary_cases':len(cases)-len(seen),'all_costs_identical':True,'seconds_per_100':time.perf_counter()-start,'purpose':'search_only; production still encodes and decodes with src.psx_compress'}
(Path(__file__).parent/'fast_cost_checks.json').write_text(json.dumps(r,indent=2));print(r)
