"""Port the accepted normal/Force dialogue portraits and base HQ animations."""
import json,struct,sys,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.inspect_steam_portraits import frames
from scripts.build_steam_selection import render_frame
from src.psx_player import decode_stream
from src.psx_ui_atlas import write_tile
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from src.steam_player import unpack_indices
from src.steam_portraits import pack,encode_banks
W=ROOT/'work/steam_port_20261109';ORIG=W/'original/nativeDX10/X4/romPC'
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')

def main():
    if digest(ROOT/'MegaMan X4.bin')!='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b':raise ValueError('US reference hash')
    names=['ST00_00.ARC','COL00_0X.ARC','COL00_0Z.ARC','ST0D_0X.ARC','ST0D_0Z.ARC','COL0D_0X.ARC','COL0D_0Z.ARC']
    orig,_=read_disc(ROOT/'MegaMan X4.bin',names)
    base=orig['ST00_00.ARC'];original_frames=frames(entry(base,10));original_g=entry(base,0x10102)
    refs={'x':unpack_indices(original_g[204800:217088]),'z':unpack_indices(original_g[217088:223232])}
    colors={'x':entry(orig['COL00_0X.ARC'],5)[62*32:63*32],'z':entry(orig['COL00_0Z.ARC'],5)[63*32:64*32]}
    sourcebanks={'x':original_frames[11],'z':original_frames[13]}
    correspondence=json.loads((W/'portraits_research/correspondence.json').read_text())
    candidates=[]
    for q in correspondence:
        if q['arc'].endswith('_eng.arc'):continue
        a=SteamArc((ORIG/q['arc']).read_bytes())
        relevant=any(e.payload[:4]==b'TEX\0' and '\\chr\\' in e.name and any(e.payload[20:20+len(r)]==r for r in refs.values()) for e in a.entries)
        relevant|=any(e.payload[:4]==b'PAT\0' and any(b in sourcebanks.values() for b in pat_frames(e.payload)) for e in a.entries)
        if relevant or q['arc'] in ['st0d_0x.arc','st0d_0z.arc']:candidates.append(q['arc'])
    reports=[];routes=[];reviews=[]
    for mode in ['ver_rin_nana','ver_buki_riko']:
        ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));game=(ROOT/ptr['cue']).with_suffix('.bin')
        if digest(game)!=ptr['sha256']:raise ValueError('PS1 current hash')
        raw,_=read_disc(game,names);st=raw['ST00_00.ARC'];p=entry(st,10);g=entry(st,0x10102)
        source={}
        for kind,b in [('x',11),('z',13)]:
            start=struct.unpack_from('<I',entry(st,12),b*4)[0]
            source[kind]=(frames(p)[b],unpack_indices(g[start:]),entry(raw['COL00_0X.ARC' if kind=='x' else 'COL00_0Z.ARC'],5)[(62 if kind=='x' else 63)*32:(63 if kind=='x' else 64)*32])
        outdir=ROOT/'out'/mode/'steam_portraits_20261109_v1';review=outdir/'review';review.mkdir(parents=True,exist_ok=True)
        prepared={}
        for arcname in candidates:
            eng=arcname.replace('.arc','_eng.arc');shared=not (ORIG/eng).exists()
            native=arcname if mode=='ver_rin_nana' or shared else eng
            target=('cliche_br_'+arcname) if mode=='ver_buki_riko' and shared else native
            a=SteamArc((ORIG/native).read_bytes());updates={};checks=[];hqn=arcname in ['st0d_0x.arc','st0d_0z.arc']
            if hqn:
                psname='ST0D_0X.ARC' if arcname=='st0d_0x.arc' else 'ST0D_0Z.ARC';h=raw[psname]
                pe=next(e for e in a.entries if e.payload[:4]==b'PAT\0');banks=pat_frames(pe.payload)
                tex=next(e for e in a.entries if e.payload[:4]==b'TEX\0' and e.name.endswith('_002'))
                if psname=='ST0D_0X.ARC':
                    blob=entry(h,13)[96:];chunks=[]
                    if blob[:4]!=struct.pack('<I',0x52415148):raise ValueError('HQ container signature')
                    for n in range(struct.unpack_from('<I',blob,4)[0]):
                        kind,start,offset,size=struct.unpack_from('<4I',blob,16+n*16);chunks.append((kind,start,decode_stream(blob,offset,len(blob),size).data))
                    states=next(v for k,s,v in chunks if k==0);dictionary=b''.join(v for k,s,v in chunks if k==1);state=states[:1412];atlas=bytearray(176*128)
                    for t,k in enumerate(struct.unpack('<176H',state[:352])):
                        if k!=65535:write_tile(atlas,t,unpack_indices(dictionary[k*128:k*128+128]))
                    fr=frames(struct.pack('<I',4)+state[352:])[0];px=unpack_indices(atlas)
                else:
                    fr=frames(entry(h,10))[2];start=struct.unpack_from('<I',entry(h,12),8)[0];px=unpack_indices(entry(h,0x10102)[start:])
                converted,banks[2]=pack(tex.payload,fr,px);updates[tex.key]=converted;updates[pe.key]=encode_banks(banks)
                pal=entry(raw[psname.replace('ST','COL',1)],5)[35*32:36*32]
                for e in a.entries:
                    if e.payload[:4]==b'COL\0' and '\\stage\\col\\' in e.name:
                        value=bytearray(e.payload);value[12+35*32:12+36*32]=pal;updates[e.key]=bytes(value)
                for f,rec in enumerate(banks[2]):
                    im=render_frame(converted,rec,pal,0);im.save(review/f'{arcname[:-4]}_{f:02}.png')
                checks.append({'category':'hq','frames':len(fr),'state':'base','all_parts_exact':True})
            else:
                packed={}
                for kind in source:
                    template=next(e.payload for e in SteamArc((ORIG/'st00_00.arc').read_bytes()).entries if e.payload[:4]==b'TEX\0' and e.payload[20:20+len(refs[kind])]==refs[kind])
                    packed[kind]=pack(template,source[kind][0],source[kind][1])
                for e in a.entries:
                    if e.payload[:4]==b'TEX\0' and '\\chr\\' in e.name:
                        for kind,r in refs.items():
                            if e.payload[20:20+len(r)]==r:updates[e.key]=e.payload[:8]+packed[kind][0][8:]
                    elif e.payload[:4]==b'PAT\0':
                        banks=pat_frames(e.payload);changed=[]
                        for b,bank in enumerate(banks):
                            for kind,old in sourcebanks.items():
                                if bank==old:banks[b]=packed[kind][1];changed.append([b,kind,len(bank)])
                        if changed:updates[e.key]=encode_banks(banks);checks.append({'category':'dialogue','banks':changed})
                    elif e.payload[:4]==b'COL\0' and '\\stage\\col\\' in e.name:
                        value=bytearray(e.payload);changed=[]
                        for row in range((len(value)-12)//32):
                            for kind,old in colors.items():
                                lo=12+row*32
                                if e.payload[lo:lo+32]==old:value[lo:lo+32]=source[kind][2];changed.append([row,kind])
                        if changed:updates[e.key]=bytes(value);checks.append({'category':'palette','name':e.name,'rows':changed})
                if arcname=='st00_00.arc':
                    for kind,(tex,fr) in packed.items():
                        for f,rec in enumerate(fr):render_frame(tex,rec,source[kind][2],0).save(review/f'dialogue_{kind}_{f:02}.png')
            if not updates:raise ValueError('Selected archive has no changes: '+arcname)
            out=a.rebuild(updates);back=SteamArc(out);back.validate_stream_order()
            if any(e.payload!=updates.get(e.key,a.by_key[e.key].payload) for e in back.entries):raise ValueError('Unexpected output change')
            dest=outdir/'nativeDX10/X4/romPC'/target;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and dest.read_bytes()!=out:raise ValueError('Output collision')
            dest.write_bytes(out)
            row={'mode':mode,'target_arc':target,'original_target_arc':native,'source_bin_sha256':ptr['sha256'],'output':dest.relative_to(ROOT).as_posix(),'output_sha256':sha(out),'original_sha256':sha(a.raw),'install_eligible':True,'new_private_file':target!=native,'changed_entries':[e.name for e in a.entries if e.key in updates and e.payload!=updates[e.key]],'checks':checks,'runtime_verified':False}
            reports.append(row)
            if target!=native:routes.append({'original_arc':native,'private_arc':target,'sha256':sha(out)})
        print(mode,len([q for q in reports if q['mode']==mode]),'archives',flush=True)
        board=Image.new('RGB',(900,540),'#232b3b');d=ImageDraw.Draw(board);d.text((10,10),mode+' / Steam decoded assets / NOT gameplay capture',fill='white')
        for idx,name in enumerate(['dialogue_x_00','dialogue_x_03','dialogue_z_01','st0d_0x_00','st0d_0z_00']):
            im=Image.open(review/(name+'.png'));im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);x=(idx%3)*290+20;y=(idx//3)*270+40;board.paste(im,(x,y),im)
        board.save(review/'overview.png')
    write(W/'portrait_builds.json',reports);write(W/'portrait_routes.json',{'routes':routes,'requirements':{'nativeDX10/X4/romPC/'+r['target_arc']:r['output_sha256'] for r in reports}})
    print('Total',len(reports),'shared regional routes',len(routes))
if __name__=='__main__':main()
