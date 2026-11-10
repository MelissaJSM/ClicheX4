"""Conservatively clear invisible bank1 texels while preserving partial VRAM reads."""
from pathlib import Path
from collections import defaultdict
import sys,json,hashlib,struct,argparse,importlib.util
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,bank_offsets,indexed_atlas
from src.psx_frame_edit import frame_coverage
from src.psx_compress import encode_stream
PARENT=ROOT/'work/sprite_style_unification_20261107/riko/prepared_head_spaces_v1/PL01_U.ARC'
PARENT_SHA='488b679ed027fd8916e0f48716c9e3fa65d03ff42d4ac21d38dffb6ed0a7edaf'
OUT=D/'riko_restore/hidden_cleanup_v2'
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)

def compact(arc):
    need(sha(arc)==PARENT_SHA,'Wrong parent')
    g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,1);groups=defaultdict(list)
    for f in bank['frames']:groups[f['offset']].append(f)
    partial={42,43,44,45,46,47,48,49}
    # A one-tile upload retains previous VRAM outside tile0. Preserve every
    # sampled nibble, including transparent/overlapped cells, from all partial
    # compositions in every potential prior bank1 full upload.
    carried_pixels=set()
    for n in partial:
        cp=composition_frame(c,5,n)
        need(all(p['page']==0 and p['tile']<32 for p in cp['parts']),'Unknown partial texture page')
        for p in cp['parts']:
            y,x=p['tile']//16*16,p['tile']%16*16
            carried_pixels.update((y+dy)*256+x+dx for dy in range(16)for dx in range(16))
    # Bank6 attack effects use different texture pages, never bank1's page0.
    for n in range(composition_frame(c,6,0)['bank_frame_count']):
        need(all(p['page']!=0 for p in composition_frame(c,6,n)['parts']),'Unmodeled bank6 page0 read')
    replacements={};reports=[];total_gain=0
    for off,frames in groups.items():
        first=frames[0];count=first['tile_count'];decoded=decode_stream(g,off,first['limit'],count*128);raw=decoded.data
        ns=[f['index']for f in frames]
        if set(ns)&partial or len({f['tile_count']for f in frames})!=1:
            reports.append({'refs':ns,'preserved_group':True,'reason':'partial upload or heterogeneous count'});continue
        _,locations,_=indexed_atlas(raw,count)
        carried={locations[pixel] for pixel in carried_pixels if pixel<len(locations) and locations[pixel]is not None}
        demands={loc:(raw[loc[0]]>>loc[1])&15 for loc in carried}
        cps=[]
        for f in frames:
            cp=composition_frame(c,5,f['index'])
            need(all(p['page']==0 and p['tile']<count for p in cp['parts']),'Unmodeled normal texture read')
            pixels,size,bounds,_=compose_indices(raw,count,cp);coverage,_,_=frame_coverage(raw,count,cp);cps.append((cp,pixels,size,bounds))
            for value,locations in zip(pixels,coverage):
                if not value:continue
                visible=[s for s in locations if(raw[s[0]]>>s[1])&15]
                need(bool(visible),'Opaque pixel without source');loc=visible[-1]
                need(loc not in demands or demands[loc]==value,'Visible nibble conflict');demands[loc]=value
        out=bytearray(len(raw))
        for(pos,shift),value in demands.items():out[pos]=(out[pos]&~(15<<shift))|(value<<shift)
        out=bytes(out)
        for cp,pixels,size,bounds in cps:need(compose_indices(out,count,cp)[:3]==(pixels,size,bounds),'Union display changed')
        for pos,shift in carried:
            if pos<len(raw):need(((raw[pos]>>shift)&15)==((out[pos]>>shift)&15),'Partial history texel changed')
        need(all((a==b or b==0)for aa,bb in zip(raw,out)for a,b in ((aa&15,bb&15),(aa>>4,bb>>4))),'Nonzero texel invented')
        code=encode_stream(out);gain=(decoded.end-off)-len(code)
        kept=gain>0 and out!=raw
        if kept:
            for n in ns:replacements[n]=out
            total_gain+=gain
        reports.append({'refs':ns,'tiles':count,'old_code_bytes':decoded.end-off,'candidate_code_bytes':len(code),'saved_bytes':gain if kept else 0,'selected':kept,'changed_nibbles':sum(a!=b for aa,bb in zip(raw,out)for a,b in((aa&15,bb&15),(aa>>4,bb>>4))) if kept else 0})
    spec=importlib.util.spec_from_file_location('bounded',D/'riko_restore/pack_rear_head.py');packer=importlib.util.module_from_spec(spec);spec.loader.exec_module(packer)
    ng,layout=packer.repack_raw(g,1,replacements);result=replace_entry(arc,2,ng)
    need(replace_entry(result,2,g)==arc,'Other entry changed');need(bank_offsets(g)==bank_offsets(ng),'Bank boundary changed')
    counts={'raw':0,'display_exact':0,'changed_raw_refs':0,'unchanged_raw_refs':0,'partial_raw_exact':0}
    for bi in(0,1):
        ob=graphics_bank(g,bi);nb=graphics_bank(ng,bi)
        for of,nf in zip(ob['frames'],nb['frames']):
            n=of['index'];ar=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data;br=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
            need(of['tile_count']==nf['tile_count']<=32,'Tile count drift');counts['raw']+=1
            if bi==1 and n in replacements:need(br==replacements[n],'Changed raw mismatch');counts['changed_raw_refs']+=1
            else:need(ar==br,'Nonselected raw mismatch');counts['unchanged_raw_refs']+=1
            if bi==1 and n in partial:counts['partial_raw_exact']+=1;continue
            need(np.array_equal(render(arc,bi,bi*5,n)[0],render(result,bi,bi*5,n)[0]),'Rendered pixel changed');counts['display_exact']+=1
    need(counts['raw']==444 and counts['display_exact']==436 and counts['partial_raw_exact']==8,'Coverage mismatch')
    return result,{'source_arc_sha256':sha(arc),'after_sha256':sha(result),'selected_refs':sorted(replacements),'saved_encoded_bytes':total_gain,'layout':layout,'counts':counts,'groups':reports,'partial_carried_vram_pixel_count':len(carried_pixels),'carried_mapping_uses_each_stream_upload_width':True,'all_partial_carried_nibbles_preserved':True,'all_other_entries_exact':True,'composition_palette_audio_exact':True,'new_gpu_boundary_alpha':0,'only_nonzero_to_zero_texels':True,'runtime_verified':False}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',action='store_true');parser.add_argument('--minimum-savings',type=int,default=1498);args=parser.parse_args()
    arc=PARENT.read_bytes();out,proof=compact(arc);OUT.mkdir(exist_ok=True)
    (OUT/'analysis.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8')
    if args.build:
        need(args.minimum_savings>=0 and proof['saved_encoded_bytes']>=args.minimum_savings,'Insufficient conservative capacity')
        (OUT/'PL01_U.ARC').write_bytes(out)
    print(json.dumps({k:v for k,v in proof.items()if k not in('groups','selected_refs')}))
if __name__=='__main__':main()
