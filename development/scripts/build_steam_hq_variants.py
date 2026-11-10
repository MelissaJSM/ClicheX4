"""Build independent HQ outfit ARC variants from the verified final PS1 art."""
import importlib.util,json,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_steam_portraits import digest,sha,write,W
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.inspect_steam_portraits import frames
from scripts.build_steam_selection import render_frame
from src.psx_player import decode_stream,composition_frame
from src.psx_ui_atlas import write_tile,aliased_composition
from src.psx_ui_render import render_static_rgba
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from src.steam_portraits import pack,encode_banks
from src.steam_player import unpack_indices

def main():
    spec=importlib.util.spec_from_file_location('black_source',ROOT/'work/illustration_variants_20261108/black_ui.py');black=importlib.util.module_from_spec(spec);spec.loader.exec_module(black)
    parents=json.loads((W/'portrait_builds.json').read_text('utf8'));reports=[];verified=0
    for mode,short in [('ver_rin_nana','rn'),('ver_buki_riko','br')]:
        ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));game=(ROOT/ptr['cue']).with_suffix('.bin')
        if digest(game)!=ptr['sha256']:raise ValueError('PS1 source hash differs')
        raw,_=read_disc(game,['ST0D_0X.ARC','ST0D_0Z.ARC','COL0D_0X.ARC','COL0D_0Z.ARC','SLUS_005.61'])
        helper=black.palette_helper(mode)
        if raw['SLUS_005.61'][black.off(0x800ca048):black.off(0x800ca048)+len(helper)]!=helper:raise ValueError('Final Black design helper differs')
        blob=entry(raw['ST0D_0X.ARC'],13)[96:];chunks=[]
        if blob[:4]!=struct.pack('<I',0x52415148):raise ValueError('HQ container')
        for i in range(struct.unpack_from('<I',blob,4)[0]):
            k,start,off,size=struct.unpack_from('<4I',blob,16+i*16);chunks.append((k,start,decode_stream(blob,off,len(blob),size).data))
        states=next(b for k,s,b in chunks if k==0);dictionary=b''.join(b for k,s,b in chunks if k==1)
        if len(states)!=18*1412:raise ValueError('HQ state count')
        outdir=ROOT/'out'/mode/'steam_hq_variants_20261109_v1';review=outdir/'review';review.mkdir(parents=True,exist_ok=True)
        board=Image.new('RGB',(1000,950),'#252d40');draw=ImageDraw.Draw(board)
        for character,choices in [('x',range(1,18)),('z',[1])]:
            parent=next(r for r in parents if r['mode']==mode and r['original_target_arc']==f'st0d_0{character}.arc')
            source=(ROOT/parent['output']).read_bytes()
            if sha(source)!=parent['output_sha256']:raise ValueError('HQ base parent differs')
            arc=SteamArc(source);te=next(e for e in arc.entries if e.payload[:4]==b'TEX\0' and e.name.endswith('_002'));pe=next(e for e in arc.entries if e.payload[:4]==b'PAT\0')
            basepal=entry(raw[f'COL0D_0{character.upper()}.ARC'],5)[35*32:36*32]
            for state in choices:
                palette=bytearray(basepal)
                if character=='x':
                    data=states[state*1412:(state+1)*1412];g=bytearray(176*128)
                    for t,j in enumerate(struct.unpack('<176H',data[:352])):
                        if j!=65535:write_tile(g,t,unpack_indices(dictionary[j*128:j*128+128]))
                    p=struct.pack('<I',4)+data[352:];fr=frames(p)[0];comps=[composition_frame(p,0,f) for f in range(12)]
                else:
                    r=raw['ST0D_0Z.ARC'];p=entry(r,10);start=struct.unpack_from('<I',entry(r,12),8)[0];g=entry(r,0x10102)[start:];fr=frames(p)[2];comps=[aliased_composition(p,2,f) for f in range(14)]
                    for i,(red,green,blue) in black.CHANGES[mode].items():
                        old=struct.unpack_from('<H',palette,i*2)[0];struct.pack_into('<H',palette,i*2,(old&0x8000)|red|green<<5|blue<<10)
                newtex,newframes=pack(te.payload,fr,unpack_indices(g));banks=pat_frames(pe.payload);banks[2]=newframes;updates={te.key:newtex,pe.key:encode_banks(banks)}
                for e in arc.entries:
                    if e.payload[:4]==b'COL\0' and '\\stage\\col\\' in e.name:
                        b=bytearray(e.payload);b[12+35*32:12+36*32]=palette;updates[e.key]=bytes(b)
                target=f'cliche_{short}_hq{character}_{state:02}.arc';dest=outdir/'nativeDX10/X4/romPC'/target;dest.parent.mkdir(parents=True,exist_ok=True)
                result=arc.rebuild(updates);back=SteamArc(result);back.validate_stream_order()
                if any(e.payload!=updates.get(e.key,arc.by_key[e.key].payload) for e in back.entries):raise ValueError('Unrelated resource changed')
                if dest.exists() and dest.read_bytes()!=result:raise ValueError('Output collision')
                dest.write_bytes(result);preview=review/f'{character}_{state:02}';preview.mkdir(exist_ok=True)
                for n,(rec,c) in enumerate(zip(newframes,comps)):
                    im=render_frame(newtex,rec,palette,0);expected,bounds=render_static_rgba(g,c,{0:struct.unpack('<16H',palette)})
                    if im.size!=expected.size or im.tobytes()!=expected.tobytes():raise ValueError('Independent PS1/Steam render differs')
                    qs=list(struct.iter_unpack('<BBbb',rec));bb=(min(q[2] for q in qs),min(q[3] for q in qs),max(q[2]+16 for q in qs),max(q[3]+16 for q in qs))
                    if bb!=bounds:raise ValueError('HQ origin shifted')
                    im.save(preview/f'{n:02}.png');verified+=1
                    if n==0:
                        idx=state-1 if character=='x' else 17;x=idx%5*200+10;y=idx//5*230+20;draw.text((x,y),f'{character.upper()} {state:02}',fill='white');big=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);board.paste(big,(x,y+18),big)
                reports.append({'mode':mode,'target_arc':target,'output':dest.relative_to(ROOT).as_posix(),'output_sha256':sha(result),'original_target_arc':f'st0d_0{character}.arc','parent_sha256':sha(source),'source_bin_sha256':ptr['sha256'],'character':character,'state':state,'verified_frames':len(fr),'other_resources_unchanged':True,'install_eligible':True,'runtime_verified':False})
        board.save(review/'outfits.png');print(mode,'18 outfit archives',flush=True)
    write(W/'hq_variant_builds.json',reports);write(W/'hq_variant_static_verification.json',{'independent_rendered_frames':verified,'same_pixels_geometry_palettes':True,'archives':36,'runtime_verified':False})
    print('Verified frames',verified)
if __name__=='__main__':main()
