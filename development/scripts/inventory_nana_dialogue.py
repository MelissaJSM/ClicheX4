"""현재 나나 누적본의 X 대화 얼굴 복사본을 읽기 전용으로 조사한다."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_rin_dialogue import read_sources as _read
import scripts.inventory_rin_dialogue as shared
from scripts.discover_inputs import psx_arc,sha256
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition
from src.psx_ui_render import render_static_rgba
from PIL import Image,ImageDraw
PARENT=ROOT/'out/ver_rin_nana/nana_hunter_20261030T023706695526Z'
PARENT_SHA='17d9bcfd2ecb80bae3a101464e42dff9c0863c1e352d92f610c72739439e17c1'
ART=ROOT/'work/ver_rin_nana/illustrations/nana_dialogue_v1'
def read_sources():
    old=(shared.PARENT,shared.PARENT_SHA)
    try:
        shared.PARENT,shared.PARENT_SHA=PARENT,PARENT_SHA
        return _read()
    finally:shared.PARENT,shared.PARENT_SHA=old
def locate(records,raw):
    head=entry(raw['ST00_00.ARC'],0x10102)[204800:217088]
    p=entry(raw['ST00_00.ARC'],10);start=struct.unpack_from('<I',p,44)[0];end=struct.unpack_from('<I',p,52)[0];bank=p[start:end]
    palette=entry(raw['COL00_0X.ARC'],5)[62*32:63*32]
    inv={'graphics':[],'compositions':[],'palettes':[]}
    for name,data in raw.items():
        try:entries=psx_arc(data)
        except ValueError:
            if head in data or bank in data or palette in data:raise ValueError('Target in unsupported ARC '+name)
            continue
        for e in entries:
            sub=data[e['offset']:e['offset']+e['size']];kind=int(e['type'],16)
            for key,payload,match in [('graphics',head,kind>>16==1),('compositions',bank,kind==10)]:
                if match and payload in sub:
                    if sub.count(payload)!=1:raise ValueError('Ambiguous target')
                    inv[key].append({'file':name,'type':kind,'offset':sub.index(payload),'size':len(payload)})
            if kind==5:
                rows=[n for n in range(len(sub)//32)if sub[n*32:(n+1)*32]==palette]
                if rows:inv['palettes'].append({'file':name,'type':5,'rows':rows})
    inv.update(graphics_sha256=sha256(head),parts_sha256=sha256(bank),palette_sha256=sha256(palette))
    return inv
def main():
    records,raw=read_sources();inv=locate(records,raw);ART.mkdir(parents=True,exist_ok=True)
    original=ART/'originals';original.mkdir(exist_ok=False)
    names=sorted({q['file']for k in('graphics','compositions','palettes')for q in inv[k]})
    for n in names:(original/n).write_bytes(raw[n])
    (ART/'inventory.json').write_text(json.dumps({**inv,'parent_sha256':PARENT_SHA,'records':{n:records[n]for n in names}},indent=2)+'\n','utf8')
    p=entry(raw['ST00_00.ARC'],10);g=entry(raw['ST00_00.ARC'],0x10102)[204800:217088];col=entry(raw['COL00_0X.ARC'],5)
    pals={n:struct.unpack('<16H',col[(62+n)*32:(63+n)*32])for n in range(2)}
    sheet=Image.new('RGB',(4*336,2*312),(45,45,60));d=ImageDraw.Draw(sheet);meta=[]
    for n in range(8):
        c=aliased_composition(p,11,n);im,b=render_static_rgba(g,c,pals);im.save(ART/f'original_{n}.png');big=im.resize((336,288),Image.Resampling.NEAREST)
        sheet.paste(big,(n%4*336,n//4*312+24),big);d.text((n%4*336,n//4*312),str(n),fill='white');meta.append({'frame':n,'bounds':b,'parts':len(c['parts']),'cluts':sorted({q['clut']for q in c['parts']})})
    sheet.save(ART/'original_sheet.png');print(json.dumps({'files':len(names),'inventory':inv,'frames':meta,'offsets':struct.unpack_from('<14I',p)}))
if __name__=='__main__':main()
