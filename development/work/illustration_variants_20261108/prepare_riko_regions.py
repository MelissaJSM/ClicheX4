"""Authenticate every Riko dialogue copy and preserve all non-target resources."""
import struct,json,sys
from pathlib import Path
import numpy as np
from black_ui import H,ROOT,sha,words
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.discover_inputs import DiscReader,psx_arc
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
from src.psx_ui_render import render_static_rgba

D=H/'ver_buki_riko'; REG=D/'regions_v2'; OUT=D/'prepared_assets_v2';OUT.mkdir(exist_ok=False)
info=json.loads((D/'source.json').read_text('utf8')); src=ROOT/Path(info['pointer']['cue']).with_suffix('.bin')
old={};records={}
with src.open('rb') as f:
    reader=DiscReader(f,src.stat().st_size)
    for rec in reader.inspect()['files']:
        name=rec['name'].split(';')[0]
        if rec['path'].startswith('/ARC/') and name.endswith('.ARC'):
            old[name]=reader.read(rec['lba'],rec['size']); records[name]=rec
new=dict(old); main=old['ST00_00.ARC']; dg=entry(main,0x10102)[217088:223232]; dp=entry(main,10)
ds=struct.unpack_from('<I',dp,13*4)[0]; db=dp[ds:]
normal=words('ver_buki_riko')[0]; rn=json.loads((REG/'report.json').read_text('utf8')); normal_new=rn['normal_palette']
pal_before=struct.pack('<16H',*normal);pal_after=struct.pack('<16H',*normal_new)
graphics=[];compositions=[];palettes=[]
for name,raw in old.items():
    try: layout=psx_arc(raw)
    except ValueError:continue
    for e in layout:
        typ=int(e['type'],16);part=entry(new[name],typ)
        if typ>>16==1 and dg in part:
            assert part.count(dg)==1
            pos=part.index(dg);sub=(REG/'dialogue_texture.bin').read_bytes();assert len(sub)==len(dg)
            new[name]=replace_entry(new[name],typ,part[:pos]+sub+part[pos+len(dg):]);graphics.append({'file':name,'type':typ,'offset':pos,'size':len(dg)})
        if typ==10 and db in part:
            assert part.count(db)==1
            pos=part.index(db);sub=(REG/'dialogue_parts.bin').read_bytes();assert len(sub)==len(db)
            new[name]=replace_entry(new[name],typ,part[:pos]+sub+part[pos+len(db):]);compositions.append({'file':name,'offset':pos,'size':len(db)})
        if typ==5 and name.startswith(('COL00_','COL0A_','COL0B_','COL0C_','COL0D_')):
            hits=[i for i in range(len(part)//32)if part[32*i:32*i+32]==pal_before]
            changed=bytearray(part)
            for row in hits:changed[row*32:row*32+32]=pal_after
            if hits:new[name]=replace_entry(new[name],typ,changed);palettes.append({'file':name,'rows':hits})
assert len(graphics)==6 and len(compositions)==6 and len(palettes)==11,(graphics,compositions,palettes)
hq=old['ST0D_0Z.ARC'];p=entry(hq,10);offsets=struct.unpack_from('<'+'I'*(struct.unpack_from('<I',p)[0]//4),p);start,end=offsets[2],offsets[3]
sub=(REG/'hq_parts.bin').read_bytes(); assert len(sub)==end-start
new['ST0D_0Z.ARC']=replace_entry(hq,10,p[:start]+sub+p[end:]);g=entry(hq,0x10102)
new['ST0D_0Z.ARC']=replace_entry(new['ST0D_0Z.ARC'],0x10102,g[:63488]+(REG/'hq_texture.bin').read_bytes()+g[81920:])
# Every source bit outside the explicitly owned resources must be exact.
checks=[]
for name,data in new.items():
    if data==old[name]:continue
    layout=psx_arc(old[name]);allowed=bytearray(len(data))
    def allow(typ,pos,size):
        e=next(e for e in layout if int(e['type'],16)==typ);assert 0<=pos and pos+size<=e['size'];allowed[e['offset']+pos:e['offset']+pos+size]=b'\xff'*size
    for q in graphics:
        if q['file']==name:allow(q['type'],q['offset'],q['size'])
    for q in compositions:
        if q['file']==name:allow(10,q['offset'],q['size'])
    for q in palettes:
        if q['file']==name:
            for row in q['rows']:allow(5,row*32,32)
    if name=='ST0D_0Z.ARC':allow(10,start,end-start);allow(0x10102,63488,18432)
    assert len(data)==len(old[name]),name
    assert [(e['type'],e['offset'],e['size'])for e in psx_arc(data)]==[(e['type'],e['offset'],e['size'])for e in layout],name
    assert all(a==b or allowed[i] for i,(a,b) in enumerate(zip(old[name],data))),name
    (OUT/name).write_bytes(data);checks.append({'file':name,'before':sha(old[name]),'after':sha(data),'record':records[name]})
# Restore all 17 indexed poses; their silhouettes and ordered part positions are
# unchanged. All non-Riko parts records and texture bytes were guarded above.
pixel_checks=[]
for group in ['hq','dialogue']:
    origtex=g[63488:81920] if group=='hq' else dg
    origpart=struct.pack('<I',4)+(p[start:end] if group=='hq' else db)
    targettex=(REG/f'{group}_texture.bin').read_bytes();targetpart=struct.pack('<I',4)+(REG/f'{group}_parts.bin').read_bytes()
    for n in range(aliased_composition(origpart,0,0)['bank_frame_count']):
        c=aliased_composition(origpart,0,n);nc=aliased_composition(targetpart,0,n)
        x,xsize,xbb,_=compose_static(origtex,local_composition(c));y,ysize,ybb,_=compose_static(targettex,local_composition(nc))
        assert (xsize,xbb)==(ysize,ybb) and all(bool(a)==bool(b)for a,b in zip(x,y))
        assert [(q['x'],q['y'],q['flags']&252) for q in c['parts']]==[(q['x'],q['y'],q['flags']&252) for q in nc['parts']]
        before,_=render_static_rgba(origtex,c,{0:normal});after,_=render_static_rgba(targettex,nc,{0:normal_new})
        diff=int(np.any(np.array(before)!=np.array(after),axis=2).sum())
        pixel_checks.append({'group':group,'frame':n,'normal_rgb_pixels_adjusted':diff,'pixels':sum(bool(a)for a in x),'shape_geometry_exact':True})
        for variant,pal in [('normal',normal_new),('black',rn['black_palette'])]:
            pic,_=render_static_rgba(targettex,nc,{0:pal});pic.save(OUT/f'{group}_{n:02}_{variant}.png')
for q in graphics:
    assert entry(new[q['file']],q['type'])[q['offset']:q['offset']+q['size']]==(REG/'dialogue_texture.bin').read_bytes()
for q in compositions:
    assert entry(new[q['file']],10)[q['offset']:q['offset']+q['size']]==(REG/'dialogue_parts.bin').read_bytes()
(OUT/'verification.json').write_text(json.dumps({'pointer':info['pointer'],'files':checks,'graphics':graphics,'compositions':compositions,'palettes':palettes,'poses':pixel_checks,'normal_rgb_exact':False,'normal_design_geometry_and_animation_preserved':True,'all_non_target_bytes_exact':True,'runtime_verified':False},indent=2)+'\n','utf8')
print('PASS',len(checks),'assets',sum(q['normal_rgb_pixels_adjusted']for q in pixel_checks),'normal pixels adjusted')
