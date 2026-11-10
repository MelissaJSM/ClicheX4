"""Read-only inventory of native portraits and encoded English text."""
import json,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc,sha256
from scripts.prepare_riko_ui import entry
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

D=ROOT/'work/ver_buki_riko/art_pilot/illustrations_v1'
def read_sources():
    inventory=json.loads((D/'archive_inventory.json').read_text())
    with (ROOT/'MegaMan X4.bin').open('rb') as f:
        reader=DiscReader(f,(ROOT/'MegaMan X4.bin').stat().st_size)
        return [(r,reader.read(r['lba'],r['size'])) for r in inventory]

def main():
    sources=read_sources();byname={r['name'].split(';')[0]:b for r,b in sources}
    zero=entry(byname['ST00_00.ARC'],0x10102)[217088:223232]
    pal=entry(byname['COL00_0Z.ARC'],5)[63*32:64*32];words=struct.unpack('<16H',pal)
    records=[];previews=[];text=[];matches=[];palette_matches=[]
    for r,raw in sources:
        name=r['name'].split(';')[0]
        for e in r.get('entries',[]):
            data=raw[e['offset']:e['offset']+e['size']]
            if e['type']=='0x15':
                first=struct.unpack_from('<H',data)[0]
                alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                def decode(w):
                    i=w&511
                    if 64<=i<64+len(alphabet):return alphabet[i-64]
                    return {0x1ff:' ',0x84:'-',0x86:'.',0x87:',',0x85:'!',0x88:'?',0x8b:"'"}.get(i,'{%03x}'%i)
                offsets=struct.unpack_from('<'+'H'*(first//2),data) if first%2==0 and first<len(data) else []
                for n,start in enumerate(offsets):
                    end=offsets[n+1] if n+1<len(offsets) else len(data)
                    if end<start or end>len(data) or (end-start)%2:continue
                    vals=struct.unpack('<'+'H'*((end-start)//2),data[start:end])
                    text.append({'file':name,'entry':e['index'],'message':n,'offset':start,'text':''.join(map(decode,vals))})
            if e['type']=='0x5':
                found=[i for i in range(0,len(data),32) if data[i:i+32]==pal]
                if found:palette_matches.append({'file':name,'entry':e['index'],'rows':[i//32 for i in found]})
            if int(e['type'],16)>>16==1:
                start=0
                while (i:=data.find(zero,start))>=0:
                    matches.append({'file':name,'entry':e['index'],'offset':i});start=i+len(zero)
        if not name.startswith('ST') or not any(e['type']=='0xa' for e in r.get('entries',[])):continue
        try:g=entry(raw,0x10102);p=entry(raw,0xa);o=entry(raw,0xc);offs=struct.unpack('<'+'I'*(len(o)//4),o)
        except (StopIteration,ValueError):continue
        for b,start in enumerate(offs):
            end=min((v for v in offs if v>start),default=len(g))
            try:
                c=aliased_composition(p,b,0);count=c['bank_frame_count']
                if count>25:continue
                px,size,bounds,_=compose_static(g[start:end],local_composition(c))
                if size[0]<48 or size[1]<40:continue
                dest=D/'inventory_frames'/f'{name}_b{b}.png';dest.parent.mkdir(exist_ok=True)
                im=save_image(px,size,words,dest).convert('RGBA')
                previews.append((f'{name} b{b} n{count}',im))
                records.append({'file':name,'bank':b,'count':count,'graphics_start':start,'graphics_end':end,'size':size,'bounds':bounds,'graphics_sha256':sha256(g[start:end]),'zero_exact_block':g[start:end]==zero,'preview':str(dest.relative_to(ROOT))})
            except (ValueError,IndexError,struct.error):pass
    for name,items in [('portrait_inventory',records),('zero_dialogue_matches',matches),('zero_dialogue_palettes',palette_matches),('decoded_text_initial',text)]:
        (D/(name+'.json')).write_text(json.dumps(items,indent=2),encoding='utf8')
    for page in range(0,len(previews),30):
        sheet=Image.new('RGB',(5*260,6*210),(45,45,55));dr=ImageDraw.Draw(sheet)
        for j,(label,im) in enumerate(previews[page:page+30]):
            im.thumbnail((250,180),Image.Resampling.NEAREST);x=j%5*260;y=j//5*210
            sheet.paste(im,(x,y+24),im);dr.text((x+2,y+2),label,fill='white')
        sheet.save(D/f'inventory_sheet_{page//30:02d}.png')
    print(json.dumps({'portrait_banks':len(records),'dialogue_duplicates':matches,'palette_copies':palette_matches,'text_messages':len(text)}))
if __name__=='__main__':main()
