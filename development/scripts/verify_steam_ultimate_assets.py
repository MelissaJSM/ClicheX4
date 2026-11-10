"""Compare every converted atlas and assembled Ultimate body against PS1 data."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,graphics_bank,decode_stream,indexed_atlas,composition_frame,compose_indices
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
W=ROOT/'work/steam_port_20261109'

def main():
    records=[]
    original,_=read_disc(ROOT/'MegaMan X4.bin',['PL02_U.ARC']);op=entry(original['PL02_U.ARC'],3);og=entry(original['PL02_U.ARC'],2)
    original_frames=graphics_bank(og,0,allow_bank_aliases=True)['frames'];excluded={105,*range(175,183)}
    for r in json.loads((W/'ultimate_builds.json').read_text('utf8')):
        mode=r['mode'];ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));ps,_=read_disc((ROOT/ptr['cue']).with_suffix('.bin'),['PL02_U.ARC'])
        source=ps['PL02_U.ARC'];g=entry(source,2);p=entry(source,3);colors=entry(source,9)
        arc=SteamArc((ROOT/r['output']).read_bytes(),r['output_sha256']);arc.validate_stream_order()
        pat=pat_frames(next(e.payload for e in arc.entries if e.payload[:4]==b'PAT\0' and e.name.endswith('PL02')))
        assert next(e.payload[12:] for e in arc.entries if e.payload[:4]==b'COL\0' and e.name.endswith('charge02'))==colors
        atlases={};frames={};references=parts=0
        for bank in range(len(bank_offsets(g,allow_aliases=True))):
            name=f'X4\\chr\\pl\\pl02\\pl02_{bank:03}'
            tex=next(e.payload for e in arc.entries if e.name==name and e.payload[:4]==b'TEX\0');cof=next(e.payload for e in arc.entries if e.name==name and e.payload[:4]==b'COF\0')
            cp=17+cof[16];ys=struct.unpack_from('<256I',cof,cp+4);ff=graphics_bank(g,bank,allow_bank_aliases=True)['frames']
            assert struct.unpack_from('<I',cof,cp)[0]==len(ff)
            for f,y in zip(ff,ys):
                raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;expected,_,height=indexed_atlas(raw,f['tile_count'])
                actual=tex[20+y*256:20+(y+height)*256];assert actual==expected,(mode,bank,f['index'])
                atlases[bank,f['index']]=np.frombuffer(actual,np.uint8).reshape(-1,256);frames[bank,f['index']]=(raw,f['tile_count']);references+=1
        for bank,ff in enumerate(pat):
            for n,record in enumerate(ff):
                comp=composition_frame(p,bank,n)
                assert record==b''.join(p[q['record_offset']:q['record_offset']+4] for q in comp['parts']);parts+=1
        def ps_layer(bank,n,base_row,gb=0):
            comp=composition_frame(p,bank,n);out=np.zeros((384,384),np.uint16)
            if not comp['parts']:return out
            raw,tiles=frames[gb,n]
            try:pix,size,bounds,_=compose_indices(raw,tiles,comp,allowed_cluts={0,1,2,3})
            except ValueError as e:raise ValueError((mode,gb,bank,n,tiles,str(e))) from e
            small=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);y,x=np.nonzero(small&15);v=small[y,x].astype(np.uint16)
            out[y+bounds[1]+160,x+bounds[0]+160]=(v&15)|((base_row+(v>>4))<<8)
            return out
        def pc_layer(bank,n,base_row,gb=0):
            out=np.zeros((384,384),np.uint16);atlas=atlases[gb,n]
            for flags,tile,x,y in struct.iter_unpack('<BBbb',pat[bank][n]):
                assert not flags&0x30
                tile+=(flags&3)*256;a=atlas[(tile//16)*16:(tile//16+1)*16,(tile%16)*16:(tile%16+1)*16]
                assert a.shape==(16,16)
                if flags&64:a=a[:,::-1]
                if flags&128:a=a[::-1]
                yy,xx=np.nonzero(a);out[y+160+yy,x+160+xx]=a[yy,xx].astype(np.uint16)|((base_row+(flags>>2&3))<<8)
            return out
        # Nine original one-tile placeholders refer outside their own upload.
        # Preserve them and report them separately; do not call them rendered.
        for n in excluded:
            f=original_frames[n];raw,tiles=frames[0,n]
            assert tiles==f['tile_count']==1 and raw==decode_stream(og,f['offset'],f['limit'],128).data
            for bank in (0,8,5,7,6):
                c=composition_frame(op,bank,n);assert pat[bank][n]==b''.join(op[q['record_offset']:q['record_offset']+4] for q in c['parts'])
        count=0;samples={}
        for post in (False,True):
            for arm in (0,2):
                for n in range(237):
                    if n in excluded:continue
                    layers=[(0,16)]+([(8,19),(5,19),(7,20 if arm==2 else 19),(6,19)] if not post or 217<=n<=230 else [])
                    expected=np.zeros((384,384),np.uint16);actual=expected.copy()
                    for bank,row in layers:
                        a=ps_layer(bank,n,row);b=pc_layer(bank,n,row);expected[a!=0]=a[a!=0];actual[b!=0]=b[b!=0]
                    assert np.array_equal(expected,actual),(mode,post,arm,n)
                    # Token includes the palette row as well as the color index.
                    assert np.array_equal(expected[:,::-1],actual[:,::-1]);count+=2
                    if arm==0 and n in (0,11,29,58,67,71,90,109,133,136,148,163,183,205,217,224,230):samples[post,n]=actual
        capsule=0
        for bank in range(18,22):
            for n in range(12):
                assert np.array_equal(ps_layer(bank,n,19,bank-8),pc_layer(bank,n,19,bank-8));capsule+=1
        # Representative reconstruction: known base/armor/arm palette rows.
        review=(ROOT/r['output']).parents[3]/'review';review.mkdir(exist_ok=True)
        selected=[0,11,29,58,67,71,90,109,133,136,148,163,183,205,217,224,230]
        board=Image.new('RGB',(8*160,5*176),(24,30,42));draw=ImageDraw.Draw(board)
        words={16:struct.unpack_from('<16H',colors,0),19:struct.unpack_from('<16H',colors,32),20:struct.unpack_from('<16H',colors,64)}
        for idx,((post,n),arr) in enumerate(samples.items()):
            rgba=np.zeros((384,384,4),np.uint8)
            for row in words:
                mask=(arr>>8)==row;ix=arr[mask]&15;pal=np.array([[(v>>s&31)*255//31 for s in (0,5,10)]+[255 if j else 0] for j,v in enumerate(words[row])],np.uint8);rgba[mask]=pal[ix]
            image=Image.fromarray(rgba);image.save(review/f'{"after" if post else "before"}_{n:03}.png')
            x=idx%8*160;y=idx//8*176;draw.text((x+6,y+4),f'{"AFTER" if post else "BEFORE"} {n:03}',fill='white')
            crop=image.crop((96,80,224,224));board.paste(crop,(x+16,y+22),crop)
        board.save(review/'ultimate_comparison.png')
        records.append({'mode':mode,'atlas_references':references,'pat_frames':parts,'body_composites_both_directions':count,'capsule_composites':capsule,'original_placeholder_frames_preserved_not_rendered':sorted(excluded),'pixels_coordinates_palette_rows_exact':True,'review':(review/'ultimate_comparison.png').relative_to(ROOT).as_posix()})
    report={'modes':records,'actual_runtime_scenes':False,'scope':'Converted source indices, palette row tokens, native PAT and COF. No gameplay capture.'}
    (W/'ultimate_static_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
