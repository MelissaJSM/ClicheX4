"""현재 린 BIN의 제로 대화 자원 복사본을 읽기 전용으로 확인한다."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.discover_inputs import DiscReader,psx_arc,sha256
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition
from src.psx_ui_render import render_static_rgba
from PIL import Image,ImageDraw

PARENT=ROOT/'out/ver_rin_nana/rin_hunter_20261029T021951953590Z'
PARENT_SHA='055ccf1244a687aa8b73cfc9938952e848dad04b285bbbf152f8bf883468dfd5'
ART=ROOT/'work/ver_rin_nana/illustrations/dialogue_v1'

def read_sources():
    if digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Accepted Rin parent differs')
    records={};raw={}
    with (PARENT/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size)
        for r in d.inspect()['files']:
            if not r['path'].startswith('/ARC/') or not r['path'].endswith('.ARC;1'):continue
            name=r['name'].split(';')[0];data=d.read(r['lba'],r['size']);records[name]={**r,'sha256':sha256(data)};raw[name]=data
    return records,raw

def locate(records,raw):
    head=entry(raw['ST00_00.ARC'],0x10102)[217088:223232];parts=entry(raw['ST00_00.ARC'],10)
    off=struct.unpack_from('<I',parts,13*4)[0];bank=parts[off:]
    palette=entry(raw['COL00_0Z.ARC'],5)[63*32:64*32]
    graphics=[];compositions=[];palettes=[];other_formats=[]
    for name,data in raw.items():
        try:entries=psx_arc(data)
        except ValueError:
            if head in data or bank in data or palette in data:raise ValueError('Target pattern in unsupported ARC: '+name)
            other_formats.append(name);continue
        for e in entries:
            sub=data[e['offset']:e['offset']+e['size']];kind=int(e['type'],16)
            if kind>>16==1:
                pos=sub.find(head)
                if pos>=0:
                    if sub.count(head)!=1:raise ValueError('Ambiguous portrait graphics')
                    graphics.append({'file':name,'type':kind,'offset':pos,'size':len(head)})
            if kind==10:
                pos=sub.find(bank)
                if pos>=0:
                    if sub.count(bank)!=1:raise ValueError('Ambiguous portrait composition')
                    compositions.append({'file':name,'type':kind,'offset':pos,'size':len(bank)})
            if kind==5:
                rows=[n for n in range(len(sub)//32) if sub[n*32:(n+1)*32]==palette]
                if rows:palettes.append({'file':name,'type':5,'rows':rows})
    if (len(graphics),len(compositions),len(palettes),sum(len(q['rows']) for q in palettes))!=(6,6,10,14):raise ValueError('Unexpected dialogue duplicate count')
    return {'graphics':graphics,'compositions':compositions,'palettes':palettes,'other_formats_without_target_patterns':other_formats,'graphics_sha256':sha256(head),'parts_sha256':sha256(bank),'palette_sha256':sha256(palette)}

def main():
    records,raw=read_sources();inv=locate(records,raw);ART.mkdir(parents=True,exist_ok=True)
    needed=sorted({q['file'] for k in ('graphics','compositions','palettes') for q in inv[k]})
    original=ART/'originals';original.mkdir(exist_ok=False)
    for name in needed:(original/name).write_bytes(raw[name])
    inv.update(parent=PARENT.relative_to(ROOT).as_posix(),parent_sha256=PARENT_SHA,records={n:records[n] for n in needed})
    (ART/'inventory.json').write_text(json.dumps(inv,indent=2)+'\n','utf8')
    g=entry(raw['ST00_00.ARC'],0x10102)[217088:223232];p=entry(raw['ST00_00.ARC'],10);col=entry(raw['COL00_0Z.ARC'],5)
    pals={n:struct.unpack('<16H',col[(63+n)*32:(64+n)*32]) for n in range(min(4,len(col)//32-63))}
    sheet=Image.new('RGB',(3*448,420),(45,45,60));dr=ImageDraw.Draw(sheet)
    for n in range(3):
        c=aliased_composition(p,13,n);im,b=render_static_rgba(g,c,pals);im.save(ART/f'original_{n}.png');big=im.resize((448,384),Image.Resampling.NEAREST);big.save(ART/f'original_{n}_4x.png');sheet.paste(big,(n*448,30),big);dr.text((n*448+5,5),f'{n}: {b}, parts {len(c["parts"])}',fill='white')
    sheet.save(ART/'original_sheet.png');print(json.dumps({'resources':len(needed),'graphics':inv['graphics'],'compositions':inv['compositions'],'palettes':inv['palettes']}))

if __name__=='__main__':main()
