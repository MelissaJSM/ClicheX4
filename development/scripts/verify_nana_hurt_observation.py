"""피격 실기 표본의 실제 팔레트와 전체/상체 화면 비교를 구분한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_pilot import entry,require,write
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from src.epsxe_state import framebuffer,match_sprite

def check(source,out,mode='hurt'):
    require(mode in ('hurt','special','elemental','hover'),'Unsupported observation mode')
    folder='nana_armor_hover' if mode=='hover' else 'nana_armor_elemental' if mode=='elemental' else ('nana_armor_special' if mode=='special' else 'nana_armor_hurt_palette')
    source,out=source.resolve(),out.resolve();require(source.is_relative_to(ROOT/'work/ver_rin_nana'/folder),'Unexpected observation')
    obs=json.loads((source/'observation.json').read_text('utf8'));build=ROOT/obs['build'];require(out.is_relative_to(build) and not out.exists(),'Fresh build evidence required')
    require(digest(build/'rin_nana.bin')==obs['bin_sha256'],'BIN changed');arc=(build/'modified.arc').read_bytes();g,c,p=entry(arc,2),entry(arc,3),entry(arc,9);bank=graphics_bank(g,0,allow_bank_aliases=True)
    expected={}
    for n in ([93,94]+list(range(221,231)) if mode=='hover' else (95,96,100,101,102,103,104,231,232) if mode=='elemental' else (88,89,90,91,97,98,99) if mode=='special' else (233,234,235,236)):
        f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        expected[n]=(raw,{b:canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,n)) for b in (0,5,6,7,8)})
    # The displayed framebuffer can lag both the active texture and live CLUT.
    # Only use complete palette sets actually captured in this same observation.
    palette_sets={}
    for sample in obs['samples']:
        video=(source/(sample['prefix']+'_vram.bin')).read_bytes();colors={};rows={};key=[]
        for b,address in ((0,sample['body_clut']),(5,0x7843),(6,0x7843),(7,0x7844),(8,0x7843)):
            pos=(address>>6)*2048+(address&63)*32;data=video[pos:pos+32];matches=[i for i in range(len(p)//32) if p[i*32:i*32+32]==data];require(matches,'Observed palette outside ARC');key.append(data)
            words=struct.unpack('<16H',data);colors[b]=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255 if i else 0] for i,w in enumerate(words)],np.uint8);rows[str(b)]=matches
        palette_sets.setdefault(tuple(key),{'source_prefix':sample['prefix'],'colors':colors,'rows':rows})
    out.mkdir();reports=[]
    for sample in obs['samples']:
        if sample['frame'] not in expected:continue
        prefix=sample['prefix'];video=(source/(prefix+'_vram.bin')).read_bytes();require(len(video)==1048576,'Truncated VRAM');colors={};rows={}
        for b,address in ((0,sample['body_clut']),(5,0x7843),(6,0x7843),(7,0x7844),(8,0x7843)):
            pos=(address>>6)*2048+(address&63)*32;data=video[pos:pos+32];matches=[i for i in range(len(p)//32) if p[i*32:i*32+32]==data];require(matches,'Live palette outside ARC')
            words=struct.unpack('<16H',data);colors[b]=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255 if i else 0] for i,w in enumerate(words)],np.uint8);rows[str(b)]=matches
        # Confirm captured uploaded bytes independently of observer's boolean.
        f=bank['frames'][sample['frame']];upload=bytearray()
        for first in range(0,f['tile_count'],16):
            width=min(16,f['tile_count']-first)*8
            for y in range(16):pos=(first//16*16+y)*2048+640;upload.extend(video[pos:pos+width])
        require(bytes(upload)==expected[sample['frame']][0],'Captured upload differs')
        screens={page:framebuffer(video,0,page) for page in (0,240)};full=[];upper=[]
        for n,(raw,layers) in expected.items():
            im=Image.new('RGBA',(160,160))
            for b in (0,8,5,7,6):im.alpha_composite(Image.fromarray(colors[b][layers[b]]))
            bb=im.getbbox();sprite=im.crop(bb)
            # Fixed actor-space y<0: head and upper torso, exclude the water foreground.
            a=np.array(im);a[80:,:,3]=0;head=Image.fromarray(a);hbb=head.getbbox()
            for page,screen in screens.items():
                found=match_sprite(screen,sprite)
                if found:full.append({'page':page,'buffer_frame':n,'matches':found})
                found=match_sprite(screen,head.crop(hbb))
                if found:upper.append({'page':page,'buffer_frame':n,'actor_y_below':0,'matches':found})
            if n==sample['frame']:sprite.resize((sprite.width*4,sprite.height*4),Image.Resampling.NEAREST).save(out/(prefix+'_expected_4x.png'))
        asynchronous=[]
        for palette in palette_sets.values():
            for n,(raw,layers) in expected.items():
                im=Image.new('RGBA',(160,160))
                for b in (0,8,5,7,6):im.alpha_composite(Image.fromarray(palette['colors'][b][layers[b]]))
                sprite=im.crop(im.getbbox())
                for page,screen in screens.items():
                    found=match_sprite(screen,sprite)
                    if found:asynchronous.append({'page':page,'buffer_frame':n,'palette_source_prefix':palette['source_prefix'],'palette_arc_rows':palette['rows'],'matches':found})
        reports.append({'active_frame':sample['frame'],'prefix':prefix,'texture_ram_equal_at_capture':sample['ram_vram_texture_equal'],'captured_vram_texture_equal':True,'palette_arc_rows':rows,'full_frame_matches':full,'upper_body_matches':upper,'limitation':'Framebuffer may show a different frame than active RAM. Upper-body matches are not whole-sprite verification.'})
        reports[-1]['full_frame_observed_palette_matches']=asynchronous
    write(out/'verification.json',{'build':obs['build'],'bin_sha256':obs['bin_sha256'],'observation':source.relative_to(ROOT).as_posix(),'samples':reports,'active_frames':sorted(q['active_frame'] for q in reports),'full_display_verified_frames':sorted({m['buffer_frame'] for q in reports for m in q['full_frame_observed_palette_matches']}),'upper_body_verified_frames':sorted({m['buffer_frame'] for q in reports for m in q['upper_body_matches']}),'fresh_disc_loading_verified':False})
    print(json.dumps({'output':out.relative_to(ROOT).as_posix(),'samples':reports}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--observation',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',choices=('hurt','special','elemental','hover'),default='hurt');a=p.parse_args();check(a.observation,a.output,a.mode)
