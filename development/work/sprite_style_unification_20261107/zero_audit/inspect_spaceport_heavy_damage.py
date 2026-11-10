"""Read US body/shot damage initializers; do not execute AI or gameplay."""
from pathlib import Path
import hashlib, json, struct, sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
assets, _ = read_disc(ROOT/'MegaMan X4.bin', ('SLUS_005.61',))
exe = assets['SLUS_005.61']; base = struct.unpack_from('<I',exe,24)[0]
cs = Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
ranges = [('train_soldier',0x800684f8,0x8006a50c), ('dash_gunner',0x800586f0,0x80059d00),
          ('wheel_charger',0x8005ec58,0x8005f480), ('colonel',0x80085f08,0x80089400),
          ('enemy_bullet',0x8009b67c,0x8009bba0)]
rows=[]
for name,start,end in ranges:
    ins=[{'pc':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str}
         for i in cs.disasm(exe[start-base+2048:end-base+2048],start)]
    hits=[]
    for k,i in enumerate(ins):
        if i['mnemonic'] in ('sb','sh','sw') and any(x in i['operands'] for x in ('0x60(', '0x62(')):
            hits.append({'store':i,'nearby':ins[max(0,k-7):k+2]})
    rows.append({'name':name,'start':hex(start),'end':hex(end),'stores':hits})
O=Path(__file__).parent/'nana_hurt_triggers01/heavy_native_read.json'
O.write_text(json.dumps({'scope':'원US 정적 명령 읽기. 동작 실행 없음.','exe_sha256':hashlib.sha256(exe).hexdigest(),'rows':rows},ensure_ascii=False,indent=2)+'\n','utf8')
for r in rows:
    print(r['name'])
    for h in r['stores']:
        print(' | '.join(i['pc']+' '+i['mnemonic']+' '+i['operands'] for i in h['nearby']))
