"""블랙 상태 정상 색상과 리코의 누락된 탑승 머리만 수정 자원으로 준비한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import D,BASES,load,entry,sha,write,render,rgba,board
from scripts.discover_inputs import psx_arc
from scripts.prepare_riko_ui import replace_entry
from scripts.prepare_rin_run import quantize
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_frame_edit import edit_frame_set
from src.psx_hurt_launch import compose_launch
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank

HEADS={66:66,67:66,68:66,69:66,70:66,71:66,72:66,73:66,74:66,75:75,76:75,77:77,78:78,79:78,81:81,82:81,83:81,84:81,85:81}

def normalize_heads(arc):
    folder=D/'riko_ride_heads';im=Image.open(folder/'generated.png').convert('RGBA')
    if im.getchannel('A').getextrema()[0]!=0:raise ValueError('Missing real alpha')
    crops=[]
    for i in range(6):
        crop=im.crop((i%3*im.width//3,i//3*im.height//2,(i%3+1)*im.width//3,(i//3+1)*im.height//2))
        a=np.array(crop);a[:,:,3]=np.where(a[:,:,3]>=192,255,0);crop=Image.fromarray(a)
        if crop.getbbox() is None:raise ValueError('Missing head cell')
        crops.append(crop.crop(crop.getbbox()))
    pal=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
    scale=min(15/max(c.width for c in crops),16/max(c.height for c in crops));images={};details=[]
    preview=Image.new('RGB',(6*192,200),(28,34,45));draw=ImageDraw.Draw(preview)
    for i,(frame,crop) in enumerate(zip([None,66,75,77,78,81],crops)):
        px=quantize(crop,colors,scale);h,w=px.shape;target=np.zeros((16,16),np.uint8)
        if w>15 or h>16:raise ValueError('Head exceeds tile')
        x=1+(15-w)//2;y=16-h;target[y:y+h,x:x+w]=px
        if np.any(target[:,0]):raise ValueError('U0 mirror boundary occupied')
        path=folder/('calibration.png'if frame is None else f'head_{frame}.png')
        p=save_image(target.tobytes(),(16,16),pal,path);big=p.convert('RGBA').resize((160,160),Image.Resampling.NEAREST)
        preview.paste(big,(i*192+16,28),big);draw.text((i*192+8,6),str(frame),fill='white')
        if frame is not None:images[frame]=(target.tobytes(),(16,16))
        details.append({'frame':frame,'size':[w,h],'placement':[x,y],'sha256':sha(path.read_bytes())})
    preview.save(folder/'normalized_review.png')
    write(folder/'normalization.json',{'generated_sha256':sha((folder/'generated.png').read_bytes()),'uniform_scale':scale,'alpha_threshold':192,'palette':list(pal),'frames':details,'runtime_verified':False})
    return images

def patch_heads(arc,images):
    g,p=entry(arc,2),entry(arc,3);frames={n:images[s] for n,s in HEADS.items()};streams={}
    for f in graphics_bank(g,1)['frames']:streams.setdefault(f['offset'],[]).append(f)
    replacements={};codes={};selected_groups={}
    for offset,refs in streams.items():
        selected=[f for f in refs if f['index'] in HEADS]
        if not selected:continue
        f=refs[0];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
        edits=[(composition_frame(p,5,q['index']),*frames[q['index']])for q in selected]
        protected=[composition_frame(p,5,q['index'])for q in refs if q not in selected]
        changed=edit_frame_set(raw,f['tile_count'],edits,preserved_compositions=protected)
        code=encode_stream(changed)
        for q in refs:replacements[q['index']]=code
        codes[offset]=code;selected_groups[offset]=refs
    # 다섯 머리 스트림만 기존 연속 구간 안에서 다시 배치한다.
    # 전체 은행의 다른 59개 스트림 주소는 그대로 둔다.
    first=min(codes);last=max(streams[o][0]['limit']for o in codes)
    if {o for o in streams if first<=o<last}!=set(codes):raise ValueError('Heads are not an isolated contiguous range')
    if sum(map(len,codes.values()))>last-first:raise ValueError('Heads exceed original combined range')
    ng=bytearray(g);cursor=first;locations=[];bank=graphics_bank(g,1)
    for old,code in sorted(codes.items()):
        ng[cursor:cursor+len(code)]=code
        for f in selected_groups[old]:struct.pack_into('<I',ng,bank['base']+f['index']*4,(f['tile_count']<<20)|(cursor-bank['base']))
        locations.append({'before':old,'after':cursor,'encoded_bytes':len(code)});cursor+=len(code)
    ng=bytes(ng);repack={'used':True,'scope':'five head streams only','range':[first,last],'remaining_bytes':last-cursor,'other_stream_addresses_unchanged':True,'locations':locations};checks=0;unchanged=0
    for gb in(0,1):
        for a,b in zip(graphics_bank(g,gb)['frames'],graphics_bank(ng,gb)['frames']):
            n=a['index'];old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data
            if a['tile_count']!=b['tile_count']:raise ValueError('Tile count changed')
            if gb==1 and n in HEADS:
                if compose_launch(new,b['tile_count'],composition_frame(p,5,n))[:2]!=frames[n]:raise ValueError('Head readback mismatch')
            elif gb==1 and n==80:
                c=composition_frame(p,5,n)
                if compose_launch(new,b['tile_count'],c)[:3]!=compose_launch(old,a['tile_count'],c)[:3] or any(compose_launch(new,b['tile_count'],c)[0]):raise ValueError('Blank80 display changed')
                unchanged+=1
            else:
                if old!=new:raise ValueError(f'Other reference changed: {gb}:{n}')
                unchanged+=1
            checks+=1
    out=replace_entry(arc,2,ng)
    for e in psx_arc(arc):
        if int(e['type'],16)!=2 and out[e['offset']:e['offset']+e['size']]!=arc[e['offset']:e['offset']+e['size']]:raise ValueError('Other entry changed')
    return out,{'head_references':sorted(HEADS),'unique_heads':5,'all_raw_references_checked':checks,'unchanged_references':unchanged,'blank80_preserved':True,'parts_palettes_timing_unchanged':True,'repack':repack}

def main():
    output=D/'patch_v1';output.mkdir(exist_ok=True)
    summary={}
    for project in BASES:
        assets,records=load(project);edited=dict(assets);out=output/project;out.mkdir(exist_ok=True);details={}
        arc=assets['PL01_U.ARC'];pal=entry(arc,9);black=pal[13*32:14*32]
        if sha(black)!='ced2b2b7962345341dc152e198060b0acfdc118e3e5869ce93b5ea38f5788f26':raise ValueError('Unsupported old Black palette')
        n=bytearray(pal);n[13*32:14*32]=pal[:32];edited['PL01_U.ARC']=replace_entry(arc,9,bytes(n))
        menu=assets['MOJIPAT.ARC'];po=struct.unpack_from('<I',menu,4)[0]
        if menu[po+29*32:po+30*32]!=black or menu[po+10*32:po+11*32]!=pal[:32]:raise ValueError('Save palette source mismatch')
        menu=bytearray(menu);menu[po+29*32:po+30*32]=pal[:32];edited['MOJIPAT.ARC']=bytes(menu)
        details['C-02']={'normal_palette_restored_for_black':True,'new_black_design':False,'gameplay_palette_row':13,'save_palette_row':29,'independent_black_bitmap':False,'runtime_verified':False}
        if project=='ver_buki_riko':
            heads=normalize_heads(arc);edited['PL01_U.ARC'],details['R-03']=patch_heads(edited['PL01_U.ARC'],heads)
        changes={}
        for name,new in edited.items():
            old=assets[name]
            if new==old:continue
            if len(new)!=len(old):raise ValueError('Resource length changed')
            path=out/name;path.write_bytes(new);offsets=[i for i,(a,b)in enumerate(zip(old,new))if a!=b]
            changes[name]={'before':sha(old),'after':sha(new),'size':len(new),'path':path.relative_to(ROOT).as_posix(),'record':records[name],'changed_bytes':len(offsets),'changed_offsets':offsets}
        proposal={'project':project,'baseline':BASES[project][0],'baseline_sha256':BASES[project][1],'files':changes,'checks':details,'runtime_verified':False}
        write(out/'proposal.json',proposal);summary[project]={'files':{k:v['changed_bytes']for k,v in changes.items()},'checks':details}
    write(output/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':main()
