"""Fix native dash garment registration and ownership; reuse existing approved artwork."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_armor import entries
from scripts.discover_inputs import sha256
from scripts.prepare_riko_ui import replace_entry
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_armor_remaining import pack_many
from scripts.prepare_shibuki_hover_alignment import replace_reserved_slot
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets
from src.psx_sprite_batch import canvas_from_parts

PARENT=ROOT/'out/ver_buki_riko/shibuki_ui_20261027T052213672376Z'
PARENT_SHA='0d8a4db1d4aea17133c72afc74a359d5b16fb8ff7dc94c4fdbc9a1c8765245d6'
SOURCE=ROOT/'work/ver_buki_riko/shibuki_art/fourth_armor_remaining_v1/layers06/master_071.png'
FRAMES=list(range(71,77))

def polygon(points):
    im=Image.new('1',(160,160));ImageDraw.Draw(im).polygon(points,fill=1)
    return np.array(im,dtype=bool)

def transfer(source, source_mask, target_mask):
    """Register existing garment pixels to a measured native body region."""
    sy,sx=np.nonzero(source_mask & (source>0));ty,tx=np.nonzero(target_mask)
    if not len(sy) or not len(ty):raise ValueError('Empty garment region')
    qx=sx.min()+(tx-tx.min())*(sx.max()-sx.min())/max(1,tx.max()-tx.min())
    qy=sy.min()+(ty-ty.min())*(sy.max()-sy.min())/max(1,ty.max()-ty.min())
    out=np.zeros_like(source)
    for y,x,a,b in zip(ty,tx,qy,qx):
        k=np.argmin((sy-a)**2+(sx-b)**2);out[y,x]=source[sy[k],sx[k]]
    return out

def corrected_layers(base,original,source,frame):
    # Coordinates are native 160x160 canvas landmarks, origin (80,80).
    # The old generic neck+12 hip plane was y=103, below both bent legs.
    yy,xx=np.indices(base.shape)
    leg_front=polygon([(67,95),(70,95),(74,98),(79,98),(80,102),(72,103),(65,100)])
    leg_back=polygon([(80,94),(85,94),(90,95),(96,98),(96,103),(88,103),(84,100),(79,99)])
    cape=polygon([(71,85),(90,85),(92,91),(89,95),(80,95),(76,92),(69,91)])
    skirt=polygon([(66,91),(75,91),(83,94),(79,99),(71,99),(66,95)])
    front_sleeve=polygon([(59,91),(64,91),(64,96),(62,99),(58,99),(56,95)])
    # The two base dash drawings differ slightly; keep the original silhouette,
    # face, hair, bare hands, buster and speed-line tile unchanged.
    solid=base>0
    leg_front &= solid;leg_back &= solid & ~leg_front
    body=(cape|skirt)&solid&~leg_front&~leg_back
    arm=front_sleeve&solid&~np.isin(base,[12,13])
    if frame%2==0:
        # Register the extended sleeve independently; keep the barrel (x<49),
        # face and hand pixels from the base body.
        arm=polygon([(50,83),(56,84),(60,88),(57,92),(54,94),(49,93),(49,89)])&solid&~np.isin(base,[12,13])
        arm &= ~((xx>=57)&(yy<=87))
    result={5:original[5].copy(),6:np.zeros_like(base),7:np.zeros_like(base),8:np.zeros_like(base)}
    src_front=polygon([(65,95),(72,95),(74,96),(79,96),(80,100),(65,100)])
    src_back=polygon([(78,94),(85,94),(91,96),(96,99),(96,103),(87,103),(83,99),(78,98)])
    src_cape=polygon([(71,85),(88,85),(90,89),(88,93),(79,93),(75,91),(70,91)])
    src_skirt=polygon([(68,91),(75,91),(78,94),(78,96),(72,95),(66,94)])
    src_arm=polygon([(59,90),(63,90),(63,93),(61,95),(58,95),(56,92)])
    for mask,sm,b in [(leg_front,src_front,8),(leg_back,src_back,8),(body&cape,src_cape,6),(body&~cape,src_skirt,6)]:
        mapped=transfer(source,sm,mask);result[b][mask]=mapped[mask]
    result[7]=transfer(source,src_arm,arm)
    if np.count_nonzero(result[8])<100 or np.count_nonzero(result[6])<200 or np.count_nonzero(result[7])<25:raise ValueError('Missing bent-dash garment')
    return result,{'leg_front':leg_front,'leg_back':leg_back,'torso':body,'sleeve':arm}

def prepare(out):
    if out.exists() or not out.resolve().is_relative_to(ROOT/'work'):raise ValueError('Fresh workspace output required')
    arc=(PARENT/'modified.arc').read_bytes()
    if sha256(arc)!=PARENT_SHA:raise ValueError('Changed UI parent')
    es=entries(arc);g,c,pal=es[2],es[3],es[9];bank=graphics_bank(g,0,allow_bank_aliases=True)
    source=np.array(Image.open(SOURCE));out.mkdir(parents=True)
    targets={};originals={};details=[];expected_streams={};ng=g;nc=bytearray(c);allowed={}
    for n in FRAMES:
        f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        orig={b:canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,n)) for b in [0,5,6,7,8]};originals[n]=orig
        if n in [73,74]:layers,masks=targets[n-2]
        else:layers,masks=corrected_layers(orig[0],orig,source,n)
        targets[n]=(layers,masks)
        for b,v in layers.items():save_image(v.tobytes(),(160,160),struct.unpack_from('<16H',pal,32),out/f'bank{b}_{n:03}.png')
    for n,aliases in [(71,[71,72,73,74]),(75,[75,76])]:
        f=bank['frames'][n]
        if [q['index'] for q in bank['frames'] if q['offset']==f['offset']]!=aliases:raise ValueError('Unexpected stream sharing')
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        fixed={q['tile'] for k in aliases for b in [0,5] for q in composition_frame(c,b,k)['parts']}
        free=set(range(f['tile_count']))-fixed
        allocation=[]
        for b in [6,8,7]:
            comps=[composition_frame(c,b,k) for k in aliases];images=[targets[k][0][b] for k in aliases]
            raw,rr=pack_many(raw,f['tile_count'],images,free,[len(cp['parts']) for cp in comps]);used={v[0] for records in rr for v in records};free-=used
            for k,cp,records in zip(aliases,comps,rr):
                for i,q in enumerate(cp['parts']):
                    if q['page'] or q['clut'] or q['unknown_flags']:raise ValueError('Unsupported flags')
                    t,x,y,flag=records[min(i,len(records)-1)];value=struct.pack('<BBbb',flag,t,x-80,y-80);pos=q['record_offset']
                    if pos in allowed and allowed[pos]!=value:raise ValueError('Conflicting shared part')
                    allowed[pos]=value;nc[pos:pos+4]=value
            allocation.append({'bank':b,'tiles':sorted(used),'records':rr})
        for k in aliases:
            expected_streams[k]=raw
            for b in [0,5,6,7,8]:
                want=targets[k][0][b] if b in [6,7,8] else originals[k][b]
                if not np.array_equal(want,canvas_from_parts(raw,f['tile_count'],composition_frame(nc,b,k))):raise ValueError(f'Layer mismatch {k}/{b}')
        ng,compression=replace_reserved_slot(ng,f,raw);details.append({'frames':aliases,'allocation':allocation,'compression':compression})
    bitmap_checks=0;untouched=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        oldbank=graphics_bank(g,bi,allow_bank_aliases=True);newbank=graphics_bank(ng,bi,allow_bank_aliases=True)
        if oldbank!=newbank:raise ValueError('Graphics descriptor changed')
        for f in oldbank['frames']:
            a=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;b=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data
            if b!=(expected_streams.get(f['index'],a) if bi==0 else a):raise ValueError('Non-target bitmap changed')
            bitmap_checks+=1
    for bi,off in enumerate(bank_offsets(c)):
        for n in range(struct.unpack_from('<I',c,off)[0]>>16):
            if bi in [6,7,8] and n in FRAMES:continue
            if composition_frame(c,bi,n)!=composition_frame(nc,bi,n):raise ValueError('Non-target parts changed')
            untouched+=1
    result=replace_entry(replace_entry(arc,2,ng),3,bytes(nc));(out/'modified.arc').write_bytes(result)
    # Native 1x and nearest-neighbor review from stored layers.
    sheet=Image.new('RGB',(6*240,6*180),'#253546');draw=ImageDraw.Draw(sheet)
    for i,n in enumerate(FRAMES):
        for j,mask in enumerate([0,2,4,8,15,15]):
            after=j!=4;layers=targets[n][0] if after else originals[n]
            pic=save_image(originals[n][0].tobytes(),(160,160),struct.unpack_from('<16H',pal),out/f'base_{n:03}.png').convert('RGBA')
            for bit,b in [(8,8),(1,5),(4,7),(2,6)]:
                if mask&bit:
                    tmp=save_image(layers[b].tobytes(),(160,160),struct.unpack_from('<16H',pal,32),out/'scratch.png').convert('RGBA');pic.alpha_composite(tmp)
            pic.save(out/f'{"after" if after else "before"}_{n}_mask{mask}.png');pic=pic.crop((48,64,108,104)).resize((240,160),Image.Resampling.NEAREST)
            sheet.paste(pic,(i*240,j*180+20),pic);draw.text((i*240+4,j*180+2),f'{n} mask {mask} {"after" if after else "before"}',fill='white')
    sheet.save(out/'review.png')
    report={'parent':str(PARENT.relative_to(ROOT)),'parent_arc_sha256':PARENT_SHA,'output_sha256':sha256(result),'source_art':str(SOURCE.relative_to(ROOT)),'source_art_sha256':sha256(SOURCE.read_bytes()),'frames':FRAMES,'changed_banks':[6,7,8],'streams':details,'bitmap_references_checked':bitmap_checks,'untouched_compositions_checked':untouched,'base_head_effects_palettes_preserved':True,'resources_relocated':False,'runtime_verified':False,'layer_pixels':{str(n):{str(b):[int(np.count_nonzero(originals[n][b])),int(np.count_nonzero(targets[n][0][b]))] for b in [5,6,7,8]} for n in FRAMES}}
    (out/'recipe.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'output':str(out),'sha256':sha256(result),'streams':details}))
    return result,report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.output.resolve())
