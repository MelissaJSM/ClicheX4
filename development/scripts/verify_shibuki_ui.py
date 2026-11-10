"""Offline UI regression checks; deliberately does not operate the emulator."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_shibuki_ui import load,D,background,sheet
from scripts.prepare_shibuki_ui import entry,actual,save,WORDS
from scripts.discover_inputs import sha256,psx_arc
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
from src.psx_shibuki_text import rename_shibuki,char,NAME
from src.psx_text import message_ranges

def records(parts,b,n):
    c=aliased_composition(parts,b,n)
    return b''.join(parts[p['record_offset']:p['record_offset']+4] for p in c['parts'])

def verify(folder):
    source,original,parent=load();recipe=json.loads((folder/'recipe.json').read_text('utf8'));current=dict(parent)
    for item in recipe['files']:
        data=(folder/item['file']).read_bytes()
        if sha256(data)!=item['sha256'] or len(data)!=item['source']['size']:raise ValueError('Prepared resource differs')
        current[item['file']]=data
    checked_parts=0;checked_entries=0
    for name in ('PL00_U.ARC','PL02_U.ARC'):
        a,b=parent[name],current[name]
        for e in psx_arc(a):
            kind=int(e['type'],16)
            if kind not in (3,0x10206,0x10007,0x11):
                if entry(a,kind)!=entry(b,kind):raise ValueError('Gameplay resource changed')
                checked_entries+=1
        p,q=entry(a,3),entry(b,3)
        for bank in range(struct.unpack_from('<I',p)[0]//4):
            for n in range(aliased_composition(p,bank,0)['bank_frame_count']):
                if bank==1 and (69<=n<=77 or 105<=n<=113):continue
                if records(p,bank,n)!=records(q,bank,n):raise ValueError('Protected player composition changed')
                checked_parts+=1
    if current['PL01_U.ARC']!=parent['PL01_U.ARC']:raise ValueError('Riko player changed')
    rikopal=entry(original['COL00_0Z.ARC'],5)[63*32:64*32];checked_riko_palettes=0
    for name,raw in original.items():
        if not name.startswith('COL'):continue
        a=entry(raw,5);b=entry(parent[name],5);z=entry(current[name],5)
        for pos in range(0,len(a),32):
            if a[pos:pos+32]==rikopal:
                if b[pos:pos+32]!=z[pos:pos+32]:raise ValueError('Riko dialogue palette changed')
                checked_riko_palettes+=1
    a,b=parent['ST0E_U1.ARC'],current['ST0E_U1.ARC']
    if entry(a,0x10102)[:40960]!=entry(b,0x10102)[:40960]:raise ValueError('Riko selection graphics changed')
    for n in (1,4,7,8,9,10,11,12,13):
        old=compose_static(entry(a,0x10102)[40960:90112],local_composition(aliased_composition(entry(a,10),1,n)))[:3]
        new=compose_static(entry(b,0x10102)[40960:90112],local_composition(aliased_composition(entry(b,10),1,n)))[:3]
        if old!=new:raise ValueError('Protected selection frame changed')
    for row in (0,1,2,3,4,5,6,17,64,65,66,67,68):
        pa=entry(parent['COL0E_U1.ARC'],5);pb=entry(current['COL0E_U1.ARC'],5)
        if pa[row*32:(row+1)*32]!=pb[row*32:(row+1)*32]:raise ValueError('Protected selection palette changed')
    # Native selection object uses CLUT 0x7840, not COL row64.
    clut=0x7840;row=((clut>>6)-480)*16+(clut&63)
    if row!=16 or pb[row*32:(row+1)*32]!=entry(current['PL00_U.ARC'],9)[:32]:
        raise ValueError('Selection player CLUT differs from accepted gameplay palette')
    # Other screens in the same tile atlases must remain pixel exact after repacking.
    checked_screens=0;screen_previews=[]
    for name,palname,changed in [('ST0E_U1.ARC','COL0E_U1.ARC',None),('ST0E_U0.ARC','COL0E_U0.ARC',6),('ST0F_UX.ARC','COL0F_U0.ARC',5),('ST0F_UZ.ARC','COL0F_U0.ARC',5)]:
        for n in range(len(entry(parent[name],0))//512):
            a=background(parent[name],entry(parent[palname],5),n);b=background(current[name],entry(current[palname],5),n)
            if n!=changed:
                if a.tobytes()!=b.tobytes():raise ValueError(f'Protected background changed: {name}/{n}')
                checked_screens+=1
            else:
                screen_previews.append((name+' new',b))
                if b.getbbox() is None:raise ValueError('Empty new illustration')
    sheet(screen_previews,folder/'backgrounds.png',3,(270,290))
    # Save icon layers compose exactly like their accepted gameplay counterparts.
    saved=[];menu=current['MOJIPAT.ARC'];g=entry(current['LOAD_U.ARC'],0x10008);player=current['PL00_U.ARC']
    for n,bank in [(44,0),(45,5),(46,6),(47,7),(48,8)]:
        got=compose_static(g,local_composition(aliased_composition(menu,2,n)))[:3];want=actual(player,0,bank)
        if got!=want:raise ValueError('Save layer differs from accepted player')
    for mask in range(16):
        canvas=np.zeros((160,160),dtype='uint8')
        for bit,n,bank in [(0,44,0),(1,45,5),(2,46,6),(4,47,7),(8,48,8)]:
            if bit and not mask&bit:continue
            px,sz,bb=compose_static(g,local_composition(aliased_composition(menu,2,n)))[:3];a=np.frombuffer(px,dtype='uint8').reshape(sz[1],sz[0]);region=canvas[bb[1]+80:bb[3]+80,bb[0]+80:bb[2]+80];region[a>0]=a[a>0]+(16 if bit else 0)
        pal=struct.unpack('<32H',entry(player,9)[:64]);im=save(canvas,folder/f'save_combo_{mask:02}.png',pal);bbox=im.getbbox();im=im.convert('RGBA').crop(bbox);im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);saved.append((f'parts {mask:02X}',im))
    sheet(saved,folder/'save_combinations.png',8,(140,165))
    idle=[np.array(Image.open(folder/f'hq_{n:02}.png')) for n in range(3)]
    for n in (1,2):
        changed=idle[n]!=idle[0];allowed=np.zeros(changed.shape,bool);allowed[24:27,35:40]=True
        if np.any(changed&~allowed):raise ValueError('Idle blink changed pixels outside eyes')
    for n in range(4):
        a=np.array(Image.open(folder/f'dialogue_{n}.png'));b=np.array(Image.open(folder/f'dialogue_{n+4}.png'))
        allowed=np.zeros(a.shape,bool);allowed[57:63,64:71]=True
        if np.any((a!=b)&~allowed):raise ValueError('Portrait speech changed outside mouth')
    # Text changes are reviewed separately and have not entered this graphics candidate.
    texts={}
    for name in ('PL00_U.ARC','PL02_U.ARC','PL01_U.ARC'):
        old=entry(parent[name],0x15);renamed,report=rename_shibuki(old)
        if rename_shibuki(renamed)[0]!=renamed or rename_shibuki(renamed)[1]['name_count']:raise ValueError('Name replacement is not idempotent')
        if entry(current[name],0x15)!=old:raise ValueError('Unapproved text relocation entered graphics build')
        original_flags=[];new_flags=[];widths=[]
        for data,flags in [(old,original_flags),(renamed,new_flags)]:
            for start,end in message_ranges(data):
                words=struct.unpack('<'+'H'*((end-start)//2),data[start:end]);flags.append([w&0xa000 for w in words if w&0xa000])
                if data is renamed:
                    line=''
                    for w in words:
                        line+=char(w)
                        if w&0xe000:
                            if NAME.search(line):raise ValueError('Old character name remains')
                            widths.append(len(line));line=''
        if original_flags!=new_flags:raise ValueError('Dialogue page termination changed')
        texts[name]={k:v for k,v in report.items() if k!='changes'};texts[name]['max_native_line_width']=max(widths)
    result={'kind':'offline_only','resource_count':len(recipe['files']),'protected_player_entries':checked_entries,'protected_player_compositions':checked_parts,
        'protected_background_screens':checked_screens,'save_equipment_combinations':16,'text_proposals':texts,'riko_player_exact':True,
        'selection_riko_exact':True,'riko_dialogue_palette_copies_preserved':checked_riko_palettes,'runtime_verified':False,'text_applied':False,'all_checks_passed':True}
    (folder/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();verify(a.candidate.resolve())
