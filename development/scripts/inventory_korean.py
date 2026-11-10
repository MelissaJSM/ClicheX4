"""Read-only US localization inventory from the accepted character-mode build."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.discover_inputs import DiscReader,psx_arc,sha256
from scripts.prepare_riko_ui import entry
from src.psx_text import ALPHABET,message_ranges

PARENT=ROOT/'out/ver_buki_riko/cliche_logo_20261028T014549725868Z'
PARENT_HASH='b0c0fd75a83f488a5dff8f48964d102b09da57a29fbecfb64424c629518290e1'
SOURCE_HASH='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
D=ROOT/'work/ver_buki_riko/korean_v1'
PUNCT={0x80:'↑',0x81:'←',0x82:'→',0x83:'+',0x84:'-',0x85:',',0x86:'.',0x87:'!',0x88:'?',0x89:'“',0x8a:'”',0x8b:"'",0x8c:'·',0x8d:'…',0x1ff:' '}

def load():
    if digest(PARENT/'shibuki_riko.bin')!=PARENT_HASH or digest(ROOT/'MegaMan X4.bin')!=SOURCE_HASH:raise ValueError('Protected game input differs')
    inv=json.loads((ROOT/'work/ver_buki_riko/art_pilot/illustrations_v1/archive_inventory.json').read_text())
    rr={r['name'].split(';')[0]:r for r in inv};files={}
    with (PARENT/'shibuki_riko.bin').open('rb') as f:
        reader=DiscReader(f,(PARENT/'shibuki_riko.bin').stat().st_size)
        for name,r in rr.items():files[name]=reader.read(r['lba'],r['size'])
    return rr,files

def decode(w):
    g=w&511
    return ALPHABET[g-64] if 64<=g<64+len(ALPHABET) else PUNCT.get(g,f'<{g:03X}>')

def messages(data):
    out=[]
    for mi,(lo,hi) in enumerate(message_ranges(data)):
        words=list(struct.unpack('<'+'H'*((hi-lo)//2),data[lo:hi]));pages=[];page=[];line=[]
        for w in words:
            line.append(w)
            if w&0xe000:
                page.append({'text':''.join(decode(v) for v in line),'words':line});line=[]
            if w&0xa000:
                pages.append({'lines':page,'end_flags':w&0xe000});page=[]
        if line:page.append({'text':''.join(decode(v) for v in line),'words':line})
        out.append({'id':mi,'offset':lo,'end':hi,'pages':pages,'trailing':page,'word_count':len(words)})
    return out

def main():
    rr,files=load();out=D/'inventory';out.mkdir(parents=True,exist_ok=False);text={};resources={};font=[]
    for name,raw in files.items():
        if not name.endswith('.ARC'):continue
        try:entries=psx_arc(raw)
        except ValueError:continue
        resources[name]={'size':len(raw),'sha256':sha256(raw),'entries':entries}
        if name.startswith('PL') and any(e['type']=='0x15' for e in entries):
            text[name]=messages(entry(raw,0x15))
        if name.startswith(('LOAD','MOJI','PL')):
            for e in entries:
                if int(e['type'],16)>>16==1:font.append({'file':name,'type':e['type'],'size':e['size']})
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','LOAD_U.ARC','MOJIPAT.ARC','SLUS_005.61'):(out/name).write_bytes(files[name])
    (out/'dialogue.json').write_text(json.dumps(text,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[]
    for name,mm in text.items():
        lines.append('# '+name)
        for m in mm:
            lines.append(f"## message {m['id']}")
            for pi,p in enumerate(m['pages']):lines.append(f"[{pi}] "+' / '.join(x['text'] for x in p['lines']))
            if m['trailing']:lines.append('TRAILING '+str(m['trailing']))
    (out/'dialogue.txt').write_text('\n'.join(lines),encoding='utf-8')
    result={'parent':str(PARENT.relative_to(ROOT)),'parent_sha256':PARENT_HASH,'source_sha256':SOURCE_HASH,'dialogue':{n:{'messages':len(m),'pages':sum(len(x['pages']) for x in m),'words':sum(x['word_count'] for x in m)} for n,m in text.items()},'texture_candidates':font,'records':rr,'resources':resources}
    (out/'inventory.json').write_text(json.dumps(result,indent=2));print(json.dumps({'dialogue':result['dialogue'],'textures':font}))

if __name__=='__main__':main()
