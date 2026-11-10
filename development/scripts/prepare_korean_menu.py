"""Compile all generic menu strings to native compositions and private glyphs.

This proposal requires fully translated dialogue: unused English letter tiles
are replaced, while all characters used by the translated dialogue are checked.
The 60 runtime cache slots are never used for menu glyphs.
"""
import argparse,json,re,runpy,struct,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_cliche_logo_v3 import pack_bank,old_records
from scripts.inventory_korean_ui import grey
from scripts.inventory_shibuki_ui import sheet
from scripts.discover_inputs import sha256
from src.psx_korean_text import LEGACY
from src.psx_korean_typography import render_mask,profile_metadata
from src.psx_ui_atlas import write_tile,tile_pixels,aliased_composition,local_composition
from src.psx_static_effect import compose_static

# Menu objects share an x=160 anchor, but their native part lists encode the
# actual columns. Recentring every translation moves DATA 1/2/3 into the save
# preview and disconnects text from the selection cursor. Only headings are
# centred; selectable rows and related prose retain their native left edge.
CENTERED_HEADINGS={0,8,41,47,50,58,60,62,83,89,94}
TWO_COLUMNS=set(range(26,32))|set(range(35,41))

def native_menu_ramp(menu,font):
    """Read the native white menu ramp; palette bytes remain input-only."""
    offsets=struct.unpack_from('<4I',menu)
    words=struct.unpack_from('<16H',menu,offsets[1])
    indices=np.arange(2,15,dtype=np.uint8)
    colors=np.array([[(words[int(i)]>>s)&31 for s in (0,5,10)] for i in indices],np.int16)
    if not np.all(colors[:,0]==colors[:,1]) or not np.all(colors[:,1]==colors[:,2]):
        raise ValueError('Native white menu palette is not grayscale')
    levels=colors[:,0]
    if levels[0]!=0 or levels[-1]!=31 or np.any(np.diff(levels)<0):
        raise ValueError('Native menu shade order differs')
    original_indices=sorted({v for tile in range(10,36) for v in tile_pixels(font,tile)})
    if not {2,3,4,9,14}<=set(original_indices):raise ValueError('Native Latin font shades differ')
    return indices,levels,{'source':'MOJIPAT.ARC palette bank, row 0',
                          'palette_words':list(words),'ramp_indices':indices.tolist(),
                          'ramp_gray_5bit':levels.tolist(),'native_latin_indices':original_indices,
                          'shadow_index':2,'palette_bytes_modified':False}

def render_menu_tile(char,indices,levels):
    """Fit menu ink before its 1px shadow, leaving the 12px advance intact."""
    mask=np.array(render_mask(char,'menu',size=12,max_size=(11,12)),np.uint8)
    if mask.ndim!=2 or mask.shape[0]>12 or mask.shape[1]>11:raise ValueError('Menu ink exceeds its advance budget')
    visible=mask>=24
    if not visible.any():raise ValueError(f'Missing menu glyph: {char}')
    # Match antialias coverage to the actual nonlinear native grayscale ramp.
    # Native dimmed/selected menu palettes continue to color these same indices.
    target=mask.astype(np.float32)*31/255
    shades=indices[np.abs(target[:,:,None]-levels).argmin(axis=2)]
    a=np.zeros((16,16),np.uint8);h,w=mask.shape
    shadow=mask>=96
    a[3:3+h,1:1+w][shadow]=2
    a[2:2+h,:w][visible]=shades[visible]
    ys,xs=np.nonzero(visible);ink=[int(xs.min()),int(ys.min())+2,int(xs.max())+1,int(ys.max())+3]
    ys,xs=np.nonzero(a);bounds=[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1]
    if ink[2]-ink[0]>11 or ink[3]-ink[1]>12 or bounds[2]>12 or bounds[1]<2 or bounds[3]>15:
        raise ValueError(f'Menu glyph or shadow collides with the next cell: {char}')
    if not set(np.unique(a))<={0,*indices.tolist()}:raise ValueError('Menu glyph uses an unverified shade')
    return a,{'ink_bounds':ink,'tile_ink_and_shadow_bounds':bounds,'source_mask_size':[w,h],
              'palette_indices':np.unique(a).tolist(),'visible_ink_pixels':int(visible.sum()),
              'advance':12,'top_margin':2,'shadow_offset':[1,1]}

def native_parts(records):
    return [struct.unpack('<BBbb',r) for r in records]

def text_parts(text,mapping,x,y):
    parts=[];start=x
    for ch in text:
        if ch==' ':x+=6;continue
        tile=mapping[ch] if ch in mapping else LEGACY[ch]
        if not -128<=x<=127 or not -128<=y<=127:
            raise ValueError(f'Menu coordinate exceeds s8: {(x,y)}')
        parts.append(struct.pack('<BBbb',0,tile,x,y));x+=12
    return parts,x-start

def translated_parts(n,texts,segments,mapping,records):
    native=native_parts(records);parts=[];meta=[]
    if n in segments:
        # Keep each original button symbol and the following text column.
        # Spaces in a translation must not move the second button symbol.
        cursor=0
        for kind,value in segments[n]:
            if kind=='icon':
                index=next((i for i in range(cursor,len(native)) if native[i][1]==value),None)
                if index is None:raise ValueError(f'Menu {n}: native button icon missing')
                flags,tile,x,y=native[index];parts.append(records[index]);cursor=index+1
                meta.append({'kind':'icon','tile':tile,'origin':[x,y],'native_origin_preserved':True})
            else:
                # Native prompts have a colon tile between symbol and label.
                while cursor<len(native) and native[cursor][1]==52:cursor+=1
                if cursor==len(native):raise ValueError(f'Menu {n}: native prompt text missing')
                x,y=native[cursor][2:];p,width=text_parts(value.strip(),mapping,x,y);parts.extend(p)
                meta.append({'kind':'text','width':width,'origin':[x,y],'alignment':'native_button_label'})
    elif n in TWO_COLUMNS:
        columns=re.split(r'\s{2,}',texts[n])
        ordered=sorted(native,key=lambda p:(p[3],p[2]))
        starts=[ordered[0]]+[p for prev,p in zip(ordered,ordered[1:]) if p[2]-prev[2]>32]
        if len(columns)!=2 or len(starts)!=2:raise ValueError(f'Menu {n}: expected two native columns')
        for text,p in zip(columns,starts):
            x,y=p[2:];new,width=text_parts(text,mapping,x,y);parts.extend(new)
            meta.append({'kind':'text','width':width,'origin':[x,y],'alignment':'native_column'})
    else:
        lines=texts[n].split('\n');ys=sorted({p[3] for p in native})
        if len(lines)!=len(ys):raise ValueError(f'Menu {n}: translated/native row count differs')
        for text,y in zip(lines,ys):
            row=[p for p in native if p[3]==y];left=min(p[2] for p in row)
            width=sum(6 if c==' ' else 12 for c in text)
            if n in CENTERED_HEADINGS:x=-(width//2);alignment='heading_center'
            elif n==93:
                # NO DATA is centred inside a separate save-preview panel,
                # whose native composition centre is +40, not screen centre.
                right=max(p[2]+16 for p in row);x=(left+right-width)//2;alignment='native_panel_center'
            else:x=left;alignment='native_left'
            new,actual_width=text_parts(text,mapping,x,y);parts.extend(new)
            meta.append({'kind':'text','width':actual_width,'origin':[x,y],'native_left':left,'alignment':alignment})
    if n in {20,21,22,23}:
        coords=native_parts(parts)
        if min(p[2] for p in coords)!=-112 or max(p[2]+12 for p in coords)>-48:
            raise ValueError('Load/save choice entered the preview-panel column')
    return parts,meta

def main(output):
    output.mkdir(exist_ok=False);data=runpy.run_path(str(D/'menu_ko.py'));texts=data['TEXT'];segments=data['SEGMENTS']
    raw=(D/'inventory/LOAD_U.ARC').read_bytes();font=entry(raw,0x10001);menu=(D/'inventory/MOJIPAT.ARC').read_bytes();old=old_records(menu,0);frames=list(old)
    chars=sorted({c for t in texts.values() for c in t if '\uac00'<=c<='\ud7a3'}|{c for seg in segments.values() for k,t in seg if k=='text' for c in t if '\uac00'<=c<='\ud7a3'})
    protected=set(range(0,13))|set(range(36,44))|{50,51,52,56,57}|set(range(64,74))|set(range(128,142))|set(range(144,154))|set(range(192,252))
    for n,records in enumerate(old):
        if n not in texts and n not in segments:protected|={r[1] for r in records}
    free=[i for i in range(256) if i not in protected]
    if len(chars)>len(free):raise ValueError(f'Menu glyph budget {len(chars)}>{len(free)}')
    mapping=dict(zip(chars,free));ng=bytearray(font);glyphs={}
    shade_indices,shade_levels,palette_proof=native_menu_ramp(menu,font)
    for c,tile in mapping.items():
        a,glyphs[c]=render_menu_tile(c,shade_indices,shade_levels)
        write_tile(ng,tile,a.tobytes())
        if tile_pixels(ng,tile)!=a.tobytes():raise ValueError(f'Menu glyph atlas roundtrip differs: {c}')
    if len(glyphs)!=119 or set(glyphs)!=set(chars):raise ValueError('Expected 119 complete menu glyphs')
    typography={'profile':profile_metadata('menu'),'native_palette':palette_proof,
                'glyph_count':len(glyphs),'available_glyph_slots':len(free),'glyphs':glyphs,
                'ink_limit':[11,12],'tile_extent_limit':[12,15],
                'advance':12,'space_advance':6,'top_margin':2,'shadow_offset':[1,1],
                'antialias_coverage_threshold':24,'shadow_coverage_threshold':96,
                'atlas_roundtrip_verified':True,'coordinates_changed_by_font_rendering':False}
    # The only Latin-dependent consumer found locally is the dialogue emitter.
    # Verify every actually encoded legacy glyph before accepting the proposal.
    dialogue=json.loads((D/'dialogue_full_v5/proposal.json').read_text('utf-8'))
    used={LEGACY[c] for r in dialogue['dialogue'].values() for p in r['pages'] for line in p['lines'] for c in line if c in LEGACY and c!=' '}
    used.add(56)  # native dummy final message
    if used&set(mapping.values()):raise ValueError('Menu glyph overrides a live dialogue glyph')
    previews=[];layouts={}
    for n in sorted(set(texts)|set(segments)):
        frames[n],layouts[n]=translated_parts(n,texts,segments,mapping,old[n])
    offsets=struct.unpack_from('<4I',menu);bank,proof=pack_bank(frames,offsets[1]-offsets[0]);new_menu=menu[:offsets[0]]+bank+menu[offsets[1]:]
    for n in range(len(old)):
        cp=local_composition(aliased_composition(new_menu,0,n));px,size,_,_=compose_static(ng,cp)
        if n not in texts and n not in segments:
            before=local_composition(aliased_composition(menu,0,n))
            if compose_static(font,before)[:2]!=(px,size):raise ValueError('Menu icon changed')
        else:previews.append((f'menu text {n}',grey(px,size)))
    if new_menu[offsets[1]:]!=menu[offsets[1]:]:raise ValueError('Other MOJIPAT banks changed')
    for tile in protected:
        if tile_pixels(ng,tile)!=tile_pixels(font,tile):raise ValueError('Protected font changed')
    new_load=replace_entry(raw,0x10001,bytes(ng));(output/'LOAD_U.ARC').write_bytes(new_load);(output/'MOJIPAT.ARC').write_bytes(new_menu)
    for start in range(0,len(previews),24):sheet(previews[start:start+24],output/f'preview_{start//24}.png',4,(310,80))
    result={'kind':'korean_generic_menu_proposal','bin_applied':False,'requires_full_korean_dialogue':True,'glyph_count':len(chars),'translated_frames':len(layouts),'glyph_slots':mapping,'protected_font_slots':sorted(protected),'dialogue_legacy_tiles_preserved':sorted(used),'bank':proof,'layouts':layouts,'typography':typography,'files':{n:{'before':sha256(a),'after':sha256(z),'size':len(z)} for n,a,z in [('LOAD_U.ARC',raw,new_load),('MOJIPAT.ARC',menu,new_menu)]}}
    (output/'proposal.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'glyphs':len(chars),'free_slots':len(free),'menu_frames':len(layouts),'bank':proof}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
