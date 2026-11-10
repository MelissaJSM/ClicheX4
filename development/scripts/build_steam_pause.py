"""Port the accepted PS1 pause art and preserve every prior Steam modification."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.steam_arc import SteamArc,pat_from_ps1
from src.steam_player import unpack_indices,tex_geometry
from src.steam_portraits import encode_banks
from src.steam_ui import pat_frames
W=ROOT/'work/steam_port_20261109'

def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n','utf8')
def find(arc,folder,magic):
    rows=[e for e in arc.entries if folder in e.name and e.payload[:4]==magic]
    if len(rows)!=1:raise ValueError((folder,magic,len(rows)))
    return rows[0]
def variants(pal):
    bank=pal[1024:1536];out=[]
    for i in range(6):
        count,loc=struct.unpack_from('<HH',bank,i*4)
        if count!=19 or loc<6 or (loc+count)*4>len(bank):raise ValueError('Variant bank bounds')
        out.append(bank[loc*4:(loc+count)*4])
    return out

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--version',choices=('v1','v2','v3'),default='v3');args=parser.parse_args()
    parents=json.loads((W/'dialogue_builds.json').read_text('utf8'))
    ultimate=json.loads((W/'ultimate_builds.json').read_text('utf8'))
    parentmap={r['target_arc']:r for r in parents+ultimate}
    exe=(W/'original/RXC1.exe').read_bytes()
    original_hashes={r['relative_path']:r['sha256'] for r in json.loads((W/'backup_manifest.json').read_text('utf8'))['originals']}
    origpath=ROOT/'MegaMan X4.bin'
    if digest(origpath)!='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b':raise ValueError('Original PS1 mismatch')
    names=['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','LOAD_U.ARC','SLUS_005.61']
    originals,_=read_disc(origpath,names);reports=[]
    for mode,suffix in [('ver_rin_nana',''),('ver_buki_riko','_eng')]:
        ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));source=(ROOT/ptr['cue']).with_suffix('.bin')
        if digest(source)!=ptr['sha256']:raise ValueError('PS1 source hash differs')
        assets,_=read_disc(source,names)
        loadinfo=parentmap['load'+suffix+'.arc'];load=SteamArc((ROOT/loadinfo['output']).read_bytes(),loadinfo['output_sha256'])
        savepat=find(load,'\\loading\\',b'PAT\0').payload
        if len(pat_frames(savepat)[0])!=54:raise ValueError('Latest save frames missing')
        # CTEX/TEX/COF names are cached across LOAD, PL00 and PL02.
        # Every copy must contain the same atlas and Y-offset table.
        xbase=assets['PL00_U.ARC'];xult=assets['PL02_U.ARC']
        xb=pat_frames(pat_from_ps1(struct.pack('<I',4)+entry(xbase,18)))[0]
        xu=pat_frames(pat_from_ps1(struct.pack('<I',4)+entry(xult,18)))[0]
        if xb!=xu or entry(xbase,17)[:1024]!=entry(xult,17)[:1024]:raise ValueError('X shared layout/palette differs')
        gp0=unpack_indices(entry(xbase,0x10007));gp2=unpack_indices(entry(xult,0x10007))
        for fi,frame in enumerate(xb):
            if fi==10:continue
            for flags,t,x,y in struct.iter_unpack('<BBbb',frame):
                tile=(flags&3)*256+t+96;xx=tile%16*16;yy=tile//16*16
                for dy in range(16):
                    lo=(yy+dy)*256+xx
                    if gp0[lo:lo+16]!=gp2[lo:lo+16]:raise ValueError('X shared widget pixels differ')
        shared_banks=[xb+variants(entry(xbase,17))[:4]+variants(entry(xult,17))[4:6]]
        common=bytearray(gp0)
        if args.version=='v3':
            # Save info uses icon PAT20 at virtual1DE0: physical WSX tiles224..246.
            # These overlap pause portraits in the PS1 player-specific atlas.
            # Keep the shared save-icon strip on page0 and place portraits on
            # pages1/2. Save-icon COF indices0..19 must stay at Y0.
            icon_pixels=unpack_indices(entry(assets['LOAD_U.ARC'],0x10007))
            for tile in range(224,247):
                xx=tile%16*16;yy=tile//16*16
                for dy in range(16):
                    lo=(yy+dy)*256+xx;common[lo:lo+16]=icon_pixels[lo:lo+16]
            for fi,frame in enumerate(xb):
                if fi==10:continue
                for flags,t,x,y in struct.iter_unpack('<BBbb',frame):
                    tile=96+(flags&3)*256+t
                    if 224<=tile<=246:raise ValueError('Save icon strip overlaps a non-portrait pause widget')
            for value in struct.unpack('<768H',entry(xbase,16)):
                if 224<=value&255<=246:raise ValueError('Save icon strip overlaps the pause background')
        def shared_texture(payload):
            height=1024 if args.version=='v3' else 512
            tex=bytearray(payload[:20]);struct.pack_into('<I',tex,8,1|(256<<6)|(height<<19))
            pixels=bytes(common)+gp0+gp2+bytes(65536) if args.version=='v3' else gp0+gp2
            return bytes(tex)+pixels
        def shared_cof(payload):
            cof=bytearray(payload);cp=17+cof[16]
            if len(cof)!=cp+4+1024:raise ValueError('Shared COF layout')
            offsets=[0]*256;offsets[42]=offsets[43]=256
            if args.version=='v3':offsets[38:44]=[256]*4+[512]*2
            struct.pack_into('<I',cof,cp,44);struct.pack_into('<256I',cof,cp+4,*offsets)
            return bytes(cof)
        def output(arc,updates,target,parent,**extra):
            result=arc.rebuild(updates);back=SteamArc(result);back.validate_stream_order()
            if list(back.by_key)!=list(arc.by_key):raise ValueError('Archive structure changed')
            for e in arc.entries:
                if back.by_key[e.key].payload!=updates.get(e.key,e.payload):raise ValueError('Unrelated entry changed')
            out=ROOT/'out'/mode/f'steam_pause_20261109_{args.version}/nativeDX10/X4/romPC'/target;out.parent.mkdir(parents=True,exist_ok=True)
            if out.exists() and out.read_bytes()!=result:raise ValueError('Output collision')
            out.write_bytes(result)
            reports.append({'mode':mode,'target_arc':target,'source_bin_sha256':ptr['sha256'],'output':out.relative_to(ROOT).as_posix(),'output_sha256':sha(result),'parent':parent['output'],'parent_sha256':parent['output_sha256'],'changed_entries':[list(k) for k in updates],'native_maps_and_widget_layout_preserved':True,'non_menu_resources_preserved':True,'ps1_helper_code_not_copied':True,'install_eligible':True,'runtime_verified':False,**extra})
        if args.version!='v1':
            lt=find(load,'\\wsel\\',b'TEX\0');lc=find(load,'\\wsel\\',b'COF\0')
            output(load,{lt.key:shared_texture(lt.payload),lc.key:shared_cof(lc.payload)},loadinfo['target_arc'],loadinfo,shared_x_pause_cache=True)
        for n in range(3):
            psname=f'PL{n:02}_U.ARC';target=f'pl{n:02}{suffix}.arc';sourcearc=assets[psname];oldps=originals[psname]
            parent=parentmap[target];arc=SteamArc((ROOT/parent['output']).read_bytes(),parent['output_sha256'])
            original=SteamArc((W/'original/nativeDX10/X4/romPC'/target).read_bytes(),original_hashes['nativeDX10/X4/romPC/'+target])
            texture=find(arc,'\\wsel\\',b'TEX\0');col=find(arc,'\\wsel\\',b'COL\0');pat=find(arc,'\\wsel\\',b'PAT\0')
            cof=find(arc,'\\wsel\\',b'COF\0')
            if tex_geometry(texture.payload)!=(256,256,20):raise ValueError('Pause texture geometry')
            native_pixels=original.by_key[texture.key].payload[20:];old_pixels=unpack_indices(entry(oldps,0x10007))
            # JP contains localized label tiles; both use the same background/parts.
            if (native_pixels if suffix else native_pixels[:96*256])!=(old_pixels if suffix else old_pixels[:96*256]):raise ValueError('Original pause pixels differ')
            if original.by_key[pat.key].payload!=pat_from_ps1(struct.pack('<I',4)+entry(oldps,18)):raise ValueError('Original pause parts differ')
            off=0xb5d518 if n==1 else 0xb5cf18
            if entry(sourcearc,16)!=entry(oldps,16) or exe[off:off+1536]!=entry(oldps,16):raise ValueError('Native pause map differs')
            if assets['SLUS_005.61'][0xe22d8:0xe22d8+312]!=exe[0xb5ccf0:0xb5ccf0+312]:raise ValueError('Native widget layout differs')
            pal=entry(sourcearc,17)
            if len(pal)!=2048 or len(col.payload)!=2060:raise ValueError('Pause palette length')
            banks=pat_frames(pat_from_ps1(struct.pack('<I',4)+entry(sourcearc,18)))
            if len(banks)!=1 or len(banks[0])!=38:raise ValueError('Pause frame count')
            banks[0].extend(variants(pal))
            # The native COF has a fixed 256-entry zero Y-offset table.
            cp=17+cof.payload[16]
            if len(cof.payload)!=cp+4+1024 or struct.unpack_from('<I',cof.payload,cp)[0]!=1 or any(cof.payload[cp+4:]):raise ValueError('Pause COF differs')
            updates={texture.key:texture.payload[:20]+unpack_indices(entry(sourcearc,0x10007)),
                     col.key:col.payload[:12]+pal[:1024]+col.payload[1036:],
                     pat.key:encode_banks(banks)}
            if args.version!='v1' and n!=1:
                updates[texture.key]=shared_texture(texture.payload)
                updates[cof.key]=shared_cof(cof.payload)
                updates[pat.key]=encode_banks(shared_banks)
            # PL re-loads its own loading PAT after stage entry; keep frame53 there too.
            updates[find(arc,'\\loading\\',b'PAT\0').key]=savepat
            output(arc,updates,target,parent,pause_frames=44,save_frames=54,shared_x_pause_cache=args.version!='v1' and n!=1,save_icon_strip_preserved=args.version=='v3' and n!=1)
    if args.version=='v2' and (W/'pause_builds.json').exists() and not (W/'pause_v1_builds.json').exists():
        (W/'pause_v1_builds.json').write_bytes((W/'pause_builds.json').read_bytes())
    if args.version=='v3' and (W/'pause_builds.json').exists() and not (W/'pause_v2_builds.json').exists():
        (W/'pause_v2_builds.json').write_bytes((W/'pause_builds.json').read_bytes())
    write(W/'pause_builds.json',reports)
    write(W/'menu_outfits_runtime.json',{'installed_requirements':{'nativeDX10/X4/romPC/'+r['target_arc']:r['output_sha256'] for r in reports}})
    print({'archives':len(reports),'pause_frames_each':44,'save_frames_each':54})
if __name__=='__main__':main()
