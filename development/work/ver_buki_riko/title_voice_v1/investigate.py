import sys,json,struct,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader
from src.psx_spu_audio import decode_spu
D=Path(__file__).parent
inv=json.loads((ROOT/'work/ver_buki_riko/voice_discovery/20261026T002411833185Z/inventory.local.json').read_text('utf-8'))
with (ROOT/'out/ver_buki_riko/shibuki_voice_mute_20261028T064914983985Z/shibuki_riko.bin').open('rb') as f:
    reader=DiscReader(f,592217136)
    a=next(a for a in inv['archives'] if 'ST0E_U0' in a['path']); raw=reader.read(a['lba'],a['size']); b=a['banks'][0]
    h=b['header_entry'];head=raw[h['offset']:h['offset']+h['size']]
    print('commands', [head[8+i*4:12+i*4].hex() for i in range(b['command_count'])])
    tone_base=b['vab_offset']+32+128*16
    for p in range(b['program_count']):
        print('tones',p,[head[tone_base+(p*16+t)*32:tone_base+(p*16+t+1)*32].hex() for t in range(16)])
    e=b['body_entry'];body=raw[e['offset']:e['offset']+e['size']]
    for w in b['waves']:
        data=body[w['body_offset']:w['body_offset']+w['bytes']];pcm=decode_spu(data).pcm
        with wave.open(str(D/f"system_{w['wave_id']:02}.wav"),'wb') as out:
            out.setparams((1,2,22050,0,'NONE',''));out.writeframes(struct.pack('<'+'h'*len(pcm),*pcm))
    # Raw XA clips: keep original sector framing for independent ffmpeg decoding.
    for s in inv['streams']:
        if 'BGM' not in s['path']:continue
        f.seek(s['lba']*2352);raw=f.read(min(s['raw_sectors'],2400)*2352)
        (D/(s['path'].split('/')[-1].split(';')[0])).write_bytes(raw)
print('done')
