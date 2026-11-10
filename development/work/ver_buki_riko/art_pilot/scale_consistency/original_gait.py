from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
from src.psx_player import compose_indices
from scripts.discover_inputs import psx_arc
e=next(e for e in psx_arc(arc) if e['type']=='0x9');original_words=struct.unpack('<16H',arc[e['offset']:e['offset']+32])
board=Image.new('RGBA',(7*256,2*304),(42,45,54,255));d=ImageDraw.Draw(board);Q=P/'stride_revision';Q.mkdir(exist_ok=True)
for k,n in enumerate(range(7,21)):
 f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;indices,size,b,extra=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n));im=save_image(indices,size,original_words,Q/f'original_{n:03d}.png');tile=Image.new('RGBA',(64,72));tile.alpha_composite(im.convert('RGBA'),(b[0]+32,b[1]+40));board.alpha_composite(tile.resize((256,288),Image.Resampling.NEAREST),(k%7*256,k//7*304+16));d.text((k%7*256+3,k//7*304),str(n),fill='white')
board.save(Q/'original_local_only.png')
