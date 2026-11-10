"""Translate eight boss introductions without moving files or changing actors."""
import argparse,json,runpy,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D,PARENT,PARENT_HASH
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_korean_ending import extract_screens,repack_screens
from scripts.inventory_shibuki_ui import background,sheet
from scripts.inventory_korean_ui import grey
from src.psx_ui_atlas import aliased_composition,local_composition,write_tile
from src.psx_static_effect import compose_static
from src.psx_korean_typography import render_mask,profile_manifest

PREFIXES=['웹','프로스트','스플릿','마그마','제트','사이버','스톰','슬래시']
SUFFIX_KEYS=['SPIDER','WALRUS','MUSHROOM','DRAGOON','STINGRAY','PEACOCK','OWL','BEAST']
LOWER_PAIRS=[(32,33),(34,35),(36,37),(38,39),(40,41),(42,11),(12,13),(14,15)]
DESCRIPTIONS=[
    '정글에 숨겨진\n비밀 병기를\n지키고 있다.',
    '스노 베이스에 숨겨진\n비밀 병기를\n지키고 있다.',
    '연구소를 점거하고\n찾아오는 자를\n닥치는 대로 공격한다.',
    '이레귤러 헌터를\n배신하고 화산 안에\n숨어들었다.',
    '도시를 파괴한 뒤\n바다로 달아났다.',
    '사이버 공간에 살며\n네트워크 시스템을\n파괴하려 한다.',
    '공중을 정복하려고\n공중 요새를 이끌고\n출격했다.',
    '물자 보급을 위해\n군용 열차를\n방어하고 있다.',
]

def mask_text(text,font_size):
    return render_mask(text,'display',font_size,slant=0).point(lambda v:255 if v>=112 else 0).convert('1')

def expand(mask,radius):
    return np.array(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(radius*2+1)))>0

def name_target(screens,pair,text,top):
    a,b=pair;old=np.concatenate([screens[a][0],screens[b][0]],1);rows=np.concatenate([screens[a][1],screens[b][1]],1)
    # The native name is a black cutout with a bright edge in a horizontal
    # gradient. Only erase the old letter silhouette, retaining surrounding
    # dither, band palette assignments and the moving background.
    base=old.copy();yy=18 if top else 162
    # Each band uses a repeating 16px horizontal dither. The leftmost tile of
    # WEB / SPIDER is clear and provides the native gradient for every row.
    sample=screens[16 if top else 32][0][:,:16];clean=np.tile(sample,(1,32))
    # Text includes black cutouts, dark nonzero pixels and antialiased edges.
    # A transparency-only mask leaves thin English remnants. Restore every
    # deviation from the native dither within the original 61px caption band.
    erase=np.zeros_like(old,bool);erase[yy:yy+61,:320]=old[yy:yy+61,:320]!=clean[yy:yy+61,:320]
    base[erase]=clean[erase]
    letter=mask_text(text,58)
    if letter.width>288 or letter.height>61:raise ValueError('Boss name exceeds native band')
    x=(320-letter.width)//2;y=yy+(61-letter.height)//2
    mask=np.zeros_like(old,bool);mask[y:y+letter.height,x:x+letter.width]=np.array(letter,bool)
    outline=expand(mask,1);shadow=np.zeros_like(mask);shadow[2:,2:]=outline[:-2,:-2]
    base[shadow]=1;base[outline]=14;base[mask]=0
    allowed=erase|outline|shadow
    if np.any((base!=old)&~allowed):raise ValueError('Pixels outside name silhouettes changed')
    targets={a:(base[:,:256],rows[:,:16]),b:(base[:,256:],rows[:,16:])}
    return targets,{'text':text,'screens':pair,'old_letter_pixels':int(erase.sum()),'preserved_outside_pixels':int((~allowed).sum()),'new_bounds':[x,y,x+letter.width,y+letter.height]}

def description(raw,text):
    g=entry(raw,0x10102);p=entry(raw,10);offs=struct.unpack('<2I',entry(raw,12));start=offs[1]
    c=local_composition(aliased_composition(p,1,0));px,size,bounds,_=compose_static(g[start:],c)
    if size!=(240,80) or bounds!=(-120,-40,120,40):raise ValueError('Boss description geometry differs')
    old=np.frombuffer(px,np.uint8).reshape(80,240);base=old.copy();pattern=old[:,-16:];clean=np.tile(pattern,(1,15))
    # All eight native cards share the same untouched rightmost 16px stripe.
    # Difference against that exact horizontal pattern includes the complete
    # multi-index English letter and shadow, rather than only white pixels.
    erase=old!=clean;base[erase]=clean[erase]
    lines=text.split('\n');mask=Image.new('1',(240,80))
    for n,line in enumerate(lines):
        glyphs=render_mask(line,'loading',16).point(lambda v:255 if v>=112 else 0).convert('1')
        if glyphs.width>232 or glyphs.height>19:raise ValueError('Boss description line too wide/tall')
        y=(80-len(lines)*20)//2+n*20
        mask.paste(glyphs,(4,y))
    letters=np.array(mask,bool);shadow=np.zeros_like(letters);shadow[1:,1:]=letters[:-1,:-1]
    base[shadow]=1;base[letters]=15;allowed=erase|letters|shadow
    if np.any((base!=old)&~allowed):raise ValueError('Description background changed')
    ng=bytearray(g);written={}
    for q in c['parts']:
        if q['flip_x'] or q['flip_y']:raise ValueError('Unexpected description flip')
        x=q['x']-bounds[0];y=q['y']-bounds[1];tile=q['page']*256+q['tile'];value=base[y:y+16,x:x+16].tobytes()
        if tile in written and written[tile]!=value:raise ValueError('Description tile alias conflict')
        written[tile]=value
    bank=bytearray(g[start:])
    for tile,value in written.items():write_tile(bank,tile,value)
    ng[start:]=bank
    if ng[:start]!=g[:start]:raise ValueError('Boss actor pixels changed')
    new=replace_entry(raw,0x10102,bytes(ng));after=compose_static(entry(new,0x10102)[start:],c)
    if after[:3]!=(base.tobytes(),size,bounds):raise ValueError('Description did not roundtrip')
    return new,{'text':text,'bank':1,'frame':0,'start':start,'size':size,'bounds':bounds,'actor_bank_bytes_preserved':start,'composition_bytes_preserved':len(p),'background_pixels_preserved':int((~allowed).sum())}

def main(output):
    output.mkdir(exist_ok=False);inv=json.loads((D/'inventory/inventory.json').read_text('utf-8'));files={};palettes={};game=PARENT/'shibuki_riko.bin'
    if digest(game)!=PARENT_HASH:raise ValueError('Accepted source hash differs')
    with game.open('rb') as f:
        reader=DiscReader(f,game.stat().st_size)
        for i in range(1,9):
            for name,cache in [(f'STD_1_{i}U.ARC',files),(f'COLD_1U{i}.ARC',palettes)]:
                rec=inv['records'][name];cache[name]=reader.read(rec['lba'],rec['size'])
                if sha256(cache[name])!=inv['resources'][name]['sha256']:raise ValueError('Resource hash differs')
    heads=runpy.run_path(str(D/'translation_ko.py'))['HEADERS'];suffixes=[heads[k] for k in SUFFIX_KEYS]
    description_stripes=[]
    for raw in files.values():
        start=struct.unpack('<2I',entry(raw,12))[1]
        px,size,_,_=compose_static(entry(raw,0x10102)[start:],local_composition(aliased_composition(entry(raw,10),1,0)))
        description_stripes.append(np.frombuffer(px,np.uint8).reshape(80,240)[:,-16:].tobytes())
    if len(set(description_stripes))!=1:raise ValueError('Description gradient reference is not shared')
    first=files['STD_1_1U.ARC'];screens=extract_screens(first);targets={};names=[]
    for i,(prefix,suffix) in enumerate(zip(PREFIXES,suffixes)):
        for pair,text,top in [((16+i*2,17+i*2),prefix,True),(LOWER_PAIRS[i],suffix,False)]:
            t,proof=name_target(screens,pair,text,top)
            if set(t)&set(targets):raise ValueError('Boss-name screen alias')
            targets.update(t);names.append(proof)
    patched,background_proof=repack_screens(first,targets);result={};checks={};items=[]
    for i in range(1,9):
        name=f'STD_1_{i}U.ARC';raw=files[name];new=raw
        for kind in (0x10000,0,1):
            if entry(raw,kind)!=entry(first,kind):raise ValueError('Boss background differs across sources')
            new=replace_entry(new,kind,entry(patched,kind))
        new,proof=description(new,DESCRIPTIONS[i-1]);before_entries=psx_arc(raw);after_entries=psx_arc(new)
        if [(e['type'],e['offset'],e['size']) for e in before_entries]!=[(e['type'],e['offset'],e['size']) for e in after_entries]:raise ValueError('ARC layout changed')
        for kind in (10,11,12):
            if entry(raw,kind)!=entry(new,kind):raise ValueError('Actor composition/layout changed')
        (output/name).write_bytes(new);result[name]={'before':sha256(raw),'after':sha256(new),'size':len(new)};checks[name]=proof
        pal=entry(palettes[f'COLD_1U{i}.ARC'],5)
        # Static native-resource preview only, not a runtime screenshot.
        im=Image.new('RGBA',(320,240));pairs=[(16+(i-1)*2,17+(i-1)*2),LOWER_PAIRS[i-1]]
        for pair in pairs:
            im.alpha_composite(background(new,pal,pair[0]));im.alpha_composite(background(new,pal,pair[1]),(256,0))
        im.save(output/f'name_{i}.png');items.append((f'BOSS {i} native name layers',im))
        start=struct.unpack('<2I',entry(new,12))[1];px,size,_,_=compose_static(entry(new,0x10102)[start:],local_composition(aliased_composition(entry(new,10),1,0)))
        grey(px,size).save(output/f'description_{i}.png')
    sheet(items,output/'names.png',4,(330,270));sheet([(f'BOSS {i}',Image.open(output/f'description_{i}.png')) for i in range(1,9)],output/'descriptions.png',2,(260,110))
    report={'kind':'korean_boss_intro_proposal','bin_applied':False,'source_parent':str(PARENT.relative_to(ROOT)),'source_parent_sha256':PARENT_HASH,'files':result,'checks':checks,'background':background_proof,'names':names,'palette_files_modified':False,'runtime_verified':False}
    (output/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'files':len(result),'names':len(names),'descriptions':len(checks),'background':background_proof}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();main(args.output)
