"""Repair native Frost COF mapping and the omitted HQ Korean caption bank."""
import hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.inspect_steam_portraits import frames
from src.psx_player import graphics_bank,decode_stream
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from src.steam_player import unpack_indices
from src.steam_portraits import pack,encode_banks
W=ROOT/'work/steam_port_20261109';D=W/'stage_labels_ice'
OUT=ROOT/'out/steam_frost_labels_20261109_v1'

def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def one(a,magic,end):
    hits=[e for e in a.entries if e.payload[:4]==magic and e.name.endswith(end)]
    if len(hits)!=1:raise ValueError(('Ambiguous resource',magic,end,len(hits)))
    return hits[0]
def cof_table(c):
    pos=17+c[16]
    if c[:8]!=b'COF\0'+struct.pack('<I',2) or len(c)!=pos+1028:raise ValueError('COF layout')
    return struct.unpack_from('<I',c,pos)[0],struct.unpack_from('<256I',c,pos+4)
def tokens(tex,record,yoff=0,tilebase=0):
    atlas=np.frombuffer(tex[20:],np.uint8).reshape(-1,256);out=np.zeros((320,320),np.uint16)
    for flags,t,x,y in struct.iter_unpack('<BBbb',record):
        if flags&0x30:raise ValueError('Unknown PAT flags')
        t+=(flags&3)*256+tilebase
        a=atlas[yoff+t//16*16:yoff+t//16*16+16,t%16*16:t%16*16+16]
        if a.shape!=(16,16):raise ValueError('Texture bounds')
        if flags&64:a=a[:,::-1]
        if flags&128:a=a[::-1]
        yy,xx=np.nonzero(a);out[160+y+yy,160+x+xx]=a[yy,xx].astype(np.uint16)|((flags>>2&3)<<8)
    return out
def preview(a,palette=None):
    if palette is None:
        rgba=np.zeros((*a.shape,4),np.uint8);v=np.where(a!=0,40+(a&15)*14,0).astype(np.uint8)
        rgba[:,:,:3]=v[:,:,None];rgba[:,:,3]=np.where(a!=0,255,0)
    else:
        rgba=np.zeros((*a.shape,4),np.uint8)
        for row in range(4):
            words=struct.unpack_from('<16H',palette,row*32)
            colors=np.array([[(v>>s&31)*255//31 for s in (0,5,10)]+[255 if i else 0]for i,v in enumerate(words)],np.uint8)
            m=(a>>8)==row;rgba[m]=colors[a[m]&15]
    return Image.fromarray(rgba)

def main():
    D.mkdir(exist_ok=True);review=OUT/'review';review.mkdir(parents=True,exist_ok=True)
    state=json.loads((W/'install_state.json').read_text('utf8'));base=json.loads((W/'backup_manifest.json').read_text('utf8'))
    install=Path(base['steam_root']);known={r['relative_path']:r for r in state['files']};originals={r['relative_path']:r['sha256']for r in base['originals']}
    parents=[]
    for name in ('pause_builds.json','portrait_builds.json','hq_variant_builds.json'):
        for r in json.loads((W/name).read_text('utf8')):
            if r['target_arc'].startswith(('pl00','pl02')) or r.get('original_target_arc') in ('st0d_0x.arc','st0d_0z.arc'):parents.append(r)
    if len(parents)!=44 or len({r['target_arc']for r in parents})!=44:raise ValueError('Expected four players and forty HQ variants')
    psnames=['PL00_U.ARC','PL02_U.ARC','ST0D_0X.ARC','ST0D_0Z.ARC']
    original_disc=ROOT/'MegaMan X4.bin'
    with original_disc.open('rb')as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b':raise ValueError('Original PS1 hash')
    psorig,_=read_disc(original_disc,psnames);sources={};ptrs={}
    for mode in ('ver_rin_nana','ver_buki_riko'):
        ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));disc=(ROOT/ptr['cue']).with_suffix('.bin')
        with disc.open('rb')as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=ptr['sha256']:raise ValueError('PS1 source hash')
        sources[mode]=read_disc(disc,psnames)[0];ptrs[mode]=ptr
    reports=[];proof=[];unchanged=0;label_previews=[];frost_previews=[]
    for parent in parents:
        target=parent['target_arc'];mode=parent['mode'];rel='nativeDX10/X4/romPC/'+target
        raw=(ROOT/parent['output']).read_bytes()
        if sha(raw)!=parent['output_sha256'] or sha((install/rel).read_bytes())!=sha(raw) or known[rel]['installed_sha256']!=sha(raw):raise ValueError('Installed cumulative parent differs: '+target)
        arc=SteamArc(raw);updates={};item={'target_arc':target}
        if target.startswith(('pl00','pl02')):
            pl=target[:4];psname=pl.upper()+'_U.ARC'
            original_raw=(W/'original'/rel).read_bytes();oa=SteamArc(original_raw,originals[rel])
            tex=one(arc,b'TEX\0',pl+'_003');cof=one(arc,b'COF\0',pl+'_003')
            ot=oa.by_key[tex.key];oc=oa.by_key[cof.key]
            if tex.payload!=ot.payload:raise ValueError('Frost TEX differs from native original')
            pat=one(arc,b'PAT\0',pl.upper());op=oa.by_key[pat.key]
            bank=pat_frames(pat.payload)[11]
            if bank!=pat_frames(op.payload)[11]:raise ValueError('Frost PAT differs')
            old_g=entry(psorig[psname],2);new_g=entry(sources[mode][psname],2)
            old_frames=graphics_bank(old_g,3,allow_bank_aliases=True)['frames'];new_frames=graphics_bank(new_g,3,allow_bank_aliases=True)['frames']
            if len(old_frames)!=21 or len(new_frames)!=21:raise ValueError('Frost source frame count')
            for a,b in zip(old_frames,new_frames):
                if a['tile_count']!=b['tile_count'] or decode_stream(old_g,a['offset'],a['limit'],a['tile_count']*128).data!=decode_stream(new_g,b['offset'],b['limit'],b['tile_count']*128).data:raise ValueError('PS1 Frost artwork modified')
            old_count,old_y=cof_table(oc.payload);bad_count,bad_y=cof_table(cof.payload)
            if old_count!=10 or bad_count!=21 or old_y[9]!=32 or old_y[10:21]!=(0,)*11 or bad_y[9:21]!=(32,)*12:raise ValueError('Unexpected Frost failure signature')
            palette=one(arc,b'COL\0','charge'+pl[-2:]).payload[12:]
            if palette[32*32:33*32]!=oa.by_key[one(arc,b'COL\0','charge'+pl[-2:]).key].payload[12+32*32:12+33*32]:raise ValueError('Frost color row changed')
            for n in range(9):
                if not np.array_equal(tokens(tex.payload,bank[n],bad_y[n]),tokens(ot.payload,bank[n],old_y[n])):raise ValueError('Normal ice changed')
            counts=[]
            for n in range(9,21):
                bad=tokens(tex.payload,bank[n],bad_y[n],32);good=tokens(ot.payload,bank[n],old_y[n],32)
                counts.append({'frame':n,'before_visible_pixels':int(np.count_nonzero(bad)),'native_visible_pixels':int(np.count_nonzero(good))})
                if np.any(bad):raise ValueError('Expected invisible charged Frost reproduction')
                if n>=10 and not np.any(good):raise ValueError('Original charged frame unexpectedly empty')
                if target=='pl00.arc' and n in (9,10,13,17,20):frost_previews.append((n,bad,good,palette[32*32:36*32]))
            updates[cof.key]=oc.payload
            item.update(category='frost',texture_and_pat_and_palette_unchanged=True,native_cof_restored=True,normal_frames_preserved=9,charged_frames=counts)
        else:
            kind='X' if parent['original_target_arc']=='st0d_0x.arc' else 'Z';psname=f'ST0D_0{kind}.ARC';source=sources[mode][psname]
            source_frames=frames(entry(source,10))[1]
            if len(source_frames)!=11:raise ValueError('HQ bank frame count')
            offsets=struct.unpack_from('<5I',entry(source,12));start=offsets[1]
            static=bytearray(entry(source,0x10102))
            if kind=='X':
                blob=entry(source,13)[96:]
                if blob[:4]!=struct.pack('<I',0x52415148):raise ValueError('Expected current HQ compressed container')
                for j in range(struct.unpack_from('<I',blob,4)[0]):
                    k,tile,off,size=struct.unpack_from('<4I',blob,16+j*16)
                    if k==2:
                        chunk=decode_stream(blob,off,len(blob),size).data;pos=tile*128
                        if pos!=len(static):raise ValueError('HQ static chunk gap/overlap')
                        static.extend(chunk)
            end=min([v for v in offsets if start<v<=len(static)]+[len(static)])
            pix=unpack_indices(static[start:end]);te=one(arc,b'TEX\0','_001');ce=one(arc,b'COF\0','_001')
            if any(cof_table(ce.payload)[1]):raise ValueError('HQ static COF unexpectedly offset')
            pe=next(e for e in arc.entries if e.payload[:4]==b'PAT\0');banks=pat_frames(pe.payload)
            nt,nf=pack(te.payload,source_frames,pix);oldbank=banks[1]
            for n,(old,new) in enumerate(zip(oldbank,nf)):
                a=tokens(te.payload,old);b=tokens(nt,new)
                # Preserve the original map photograph above the 16px caption.
                if n==10 and not np.array_equal(a,b):raise ValueError('HQ extra frame changed')
                records=list(struct.iter_unpack('<BBbb',old));bottom=max(q[3]+16 for q in records)+160
                if not np.array_equal(a[:bottom-16],b[:bottom-16]) or not np.array_equal(a[bottom:],b[bottom:]):raise ValueError(('Photo/geometry changed',target,n))
                st=bytearray(nt[:20])+pix;struct.pack_into('<I',st,8,1|(256<<6)|((len(pix)//256)<<19))
                if not np.array_equal(b,tokens(st,source_frames[n])):raise ValueError('Caption differs from accepted PS1 source')
                if target=='st0d_0x.arc' and n<10:label_previews.append((n,a,b))
            banks[1]=nf;updates={te.key:nt,pe.key:encode_banks(banks)}
            item.update(category='hq_labels',labels=10,photographs_and_other_banks_preserved=True)
        result=arc.rebuild(updates);back=SteamArc(result);back.validate_stream_order()
        changed=[]
        for e in back.entries:
            expected=updates.get(e.key,arc.by_key[e.key].payload)
            if e.payload!=expected:raise ValueError('Non-target resource changed')
            if e.payload!=arc.by_key[e.key].payload:changed.append({'name':e.name,'kind':hex(e.kind)})
            else:unchanged+=1
        dest=OUT/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        if dest.exists() and dest.read_bytes()!=result:raise ValueError('Output collision')
        dest.write_bytes(result)
        reports.append({'mode':mode,'target_arc':target,'relative_path':rel,'output':dest.relative_to(ROOT).as_posix(),'output_sha256':sha(result),'parent':parent['output'],'parent_sha256':sha(raw),'source_bin_sha256':ptrs[mode]['sha256'],'changed_entries':changed,'install_eligible':True,'runtime_verified':False})
        proof.append(item)
    board=Image.new('RGB',(5*208,2*235),'#172132');draw=ImageDraw.Draw(board)
    for k,(n,bad,good,pal) in enumerate(frost_previews):
        for r,a in enumerate([bad,good]):
            im=preview(a).crop((112,96,208,216)).resize((144,180),Image.Resampling.NEAREST);board.paste(im,(k*208+32,r*235+30),im)
            draw.text((k*208+8,r*235+8),f'{"BEFORE" if r==0 else "RESTORED (INDEX VIEW)"} {n}',fill='white')
    board.save(review/'frost_before_after.png')
    board=Image.new('RGB',(5*256,2*290),'#172132');draw=ImageDraw.Draw(board)
    for k,(n,a,b) in enumerate(label_previews):
        x=k%5*256;y=k//5*290
        for r,q in enumerate([a,b]):
            im=preview(q);box=im.getbbox();im=im.crop(box);board.paste(im,(x+(256-im.width)//2,y+r*140+20),im)
        draw.text((x+8,y+4),f'{n} BEFORE / KOREAN (INDEX VIEW)',fill='white')
    board.save(review/'hq_captions.png')
    save(W/'frost_labels_builds.json',reports)
    save(D/'asset_verification.json',{'passed':True,'archives':len(reports),'frost_archives':4,'hq_archives':40,'hq_captions_compared':400,'non_target_resources_preserved':unchanged,'only_four_cofs_and_hq_caption_banks_changed':True,'actual_gameplay_verified':False,'results':proof})
    print({'archives':len(reports),'non_target_resources_preserved':unchanged,'frost_fully_invisible_before_reproduced':True,'hq_captions':400})

if __name__=='__main__':main()
