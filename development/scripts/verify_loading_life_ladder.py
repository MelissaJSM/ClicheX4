"""Independent preservation and renderer checks for the three UI fixes."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_loading_life_ladder import load,D,PARENT_HASH,SOURCE_HASH
from scripts.project import digest
from scripts.discover_inputs import sha256,psx_arc
from scripts.prepare_riko_ui import entry
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import bank_offsets,composition_frame,graphics_bank,decode_stream,indexed_atlas
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels
from src.psx_static_effect import compose_static
from src.psx_ui_render import render_static_rgba

def verify(candidate,repro):
    candidate=candidate.resolve();repro=repro.resolve()
    if any(not p.is_relative_to(D) for p in (candidate,repro)):raise ValueError('Wrong task path')
    rr,old=load();recipe=json.loads((candidate/'recipe.json').read_text())
    if recipe['parent_sha256']!=PARENT_HASH or recipe['source_sha256']!=SOURCE_HASH or digest(ROOT/'MegaMan X4.bin')!=SOURCE_HASH:raise ValueError('Source identity differs')
    if set(recipe['files'])!={'PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','LOAD_U.ARC','MOJIPAT.ARC','SLUS_005.61'}:raise ValueError('Unexpected scope')
    new={};protected_entries=protected_parts=decoded=gpu_parts=0
    for name,meta in recipe['files'].items():
        data=(candidate/name).read_bytes();new[name]=data
        if sha256(old[name])!=meta['before'] or sha256(data)!=meta['after'] or len(data)!=len(old[name]) or data!=(repro/name).read_bytes() or rr[name]!=recipe['records'][name]:raise ValueError('Hash/length/record/reproduction differs')
        if name in ('MOJIPAT.ARC','SLUS_005.61'):continue
        allowed={'PL00_U.ARC':{0x10206},'PL01_U.ARC':{0x10206,3},'PL02_U.ARC':{0x10206,2,3},'LOAD_U.ARC':{0x10008}}[name]
        layout=lambda blob:[(e['type'],e['offset'],e['size']) for e in psx_arc(blob)]
        if layout(data)!=layout(old[name]):raise ValueError('ARC layout changed')
        for e in psx_arc(data):
            k=int(e['type'],16)
            if k not in allowed:
                if entry(data,k)!=entry(old[name],k):raise ValueError('Protected entry changed')
                protected_entries+=1
        if not name.startswith('PL'):continue
        a,b=entry(old[name],3),entry(data,3)
        for bi in range(len(bank_offsets(a))):
            for n in range(composition_frame(a,bi,0)['bank_frame_count']):
                if name=='PL02_U.ARC' and bi==5 and n==183:continue
                x,y=records(a,bi,n),records(b,bi,n)
                if name=='PL01_U.ARC' and bi==3 and n in set(range(89,99))-{95}:
                    original=composition_frame(a,bi,n)['parts'];fixed=composition_frame(b,bi,n)['parts']
                    for p,q in zip(original,fixed):
                        expected=dict(p);expected['record_offset']=q['record_offset']
                        if p['page']*256+p['tile'] not in (513,514,515):expected['flags']|=4;expected['clut']=1
                        if q!=expected:raise ValueError('Pickup part changes exceed CLUT')
                elif x!=y:raise ValueError('Protected part changed')
                else:protected_parts+=1
        if name=='PL02_U.ARC':
            g,ng=entry(old[name],2),entry(data,2)
            if bank_offsets(g,allow_aliases=True)!=bank_offsets(ng,allow_aliases=True):raise ValueError('Graphics bank boundaries moved')
            for bi in range(len(bank_offsets(g,allow_aliases=True))):
                a1,b1=graphics_bank(g,bi,allow_bank_aliases=True),graphics_bank(ng,bi,allow_bank_aliases=True)
                if len(a1['frames'])!=len(b1['frames']):raise ValueError('Frame count changed')
                for f,z in zip(a1['frames'],b1['frames']):
                    if f['tile_count']!=z['tile_count']:raise ValueError('VRAM allocation changed')
                    raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
                    nr=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data;decoded+=1
                    if (bi,f['index'])!=(0,183) and raw!=nr:raise ValueError('Protected sprite changed')
                    if (bi,f['index'])==(0,183):
                        atlas,_,shape=indexed_atlas(nr,z['tile_count'])
                        for p in composition_frame(b,5,183)['parts']:
                            tile=p['tile']
                            if tile%16==0 and any(atlas[(tile//16*16+y)*256] for y in range(16)):raise ValueError('GPU boundary would clip new ladder pixel')
                            gpu_parts+=1
        # Native color preview uses real per-part palette offsets, including
        # the unchanged shared bubble, rather than recoloring the whole item.
        pals={i:struct.unpack_from('<16H',entry(data,9),(11+i)*32) for i in range(4)}
        sheet=Image.new('RGB',(1000,140),'#263441');draw=ImageDraw.Draw(sheet)
        for i,n in enumerate(range(89,99)):
            im,bb=render_static_rgba(entry(data,0x10206),composition_frame(b,3,n),pals)
            im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST);sheet.paste(im,(i*100,30),im);draw.text((i*100,4),str(n),fill='white')
        sheet.save(candidate/f'{name}_life_sequence.png')
    # Only the exact five declared bytes may differ in the executable proposal.
    diff=[i for i,(a,b) in enumerate(zip(old['SLUS_005.61'],new['SLUS_005.61'])) if a!=b]
    expected=[0xDED1C,0xDED21,0xDED24,0xDED28,0xDED2C]
    if diff!=expected:raise ValueError('EXE changes exceed five display data bytes')
    for offset in (0xDED1C,0xDED24,0xDED2C):
        x,y,t,w,h,p=struct.unpack_from('<hhBBBB',new['SLUS_005.61'],offset)
        if y!=192 or h!=1 or p!=0 or x+w*16>320 or t%16+w>16:raise ValueError('Invalid loading rectangle')
    for n in range(53):
        if n in (5,6):continue
        before=compose_static(entry(old['LOAD_U.ARC'],0x10008),local_composition(aliased_composition(old['MOJIPAT.ARC'],2,n)))[:3]
        after=compose_static(entry(new['LOAD_U.ARC'],0x10008),local_composition(aliased_composition(new['MOJIPAT.ARC'],2,n)))[:3]
        if before!=after:raise ValueError('Protected menu pixels changed')
    report={'candidate':str(candidate.relative_to(ROOT)),'reproduction_files':6,'protected_entries':protected_entries,'protected_parts':protected_parts,'decoded_references':decoded,'new_ladder_gpu_parts':gpu_parts,'protected_menu_frames':51,'exe_proposal_offsets':diff,'source_original_sha256':SOURCE_HASH,'files':recipe['files'],'runtime_verified':False,'loading_exe_approval_required':True}
    (candidate/'verification.json').write_text(json.dumps(report,indent=2));return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.candidate,a.repro)))
