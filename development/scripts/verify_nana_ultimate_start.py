"""기본형214·얼티밋10·전용 저장을 독립 재현과 전체 자원 비교로 검사한다."""
import json,struct,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_ultimate_start import D,PARENT,PARENT_SHA,FRAMES,entry,require,write,records,save_icon
from scripts.prepare_nana_ultimate_base import EXCLUDED
from scripts.prepare_nana_fourth_pilot import render
from scripts.project import digest
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition,tile_pixels
from src.psx_static_effect import compose_static

def validate(folder,resources=None):
    recipe=json.loads((folder/'recipe.json').read_text('utf8'));require(recipe['parent_sha256']==PARENT_SHA and recipe['frames']==FRAMES,'Unexpected scope')
    resources=resources or {n:(folder/n).read_bytes() for n in recipe['files']};require(set(resources)=={'PL02_U.ARC','MOJIPAT.ARC','LOAD_U.ARC'},'Unexpected resource set')
    for name,data in resources.items():require(sha256(data)==recipe['files'][name],'Prepared resource differs')
    old=(PARENT/'PL02_U.ARC').read_bytes();base=(PARENT/'modified.arc').read_bytes();new=resources['PL02_U.ARC'];require(len(old)==len(new),'ARC size changed')
    require([{k:v for k,v in e.items() if k!='sha256'} for e in psx_arc(old)]==[{k:v for k,v in e.items() if k!='sha256'} for e in psx_arc(new)],'ARC layout changed')
    for e in psx_arc(old):
        kind=int(e['type'],16)
        if kind not in (2,3,9):require(old[e['offset']:e['offset']+e['size']]==new[e['offset']:e['offset']+e['size']],'Non-graphics changed')
    og,oc,op=[entry(old,k) for k in (2,3,9)];ng,nc,npal=[entry(new,k) for k in (2,3,9)];bp=entry(base,9)
    require(bank_offsets(og,allow_aliases=True)==bank_offsets(ng,allow_aliases=True) and bank_offsets(oc)==bank_offsets(nc),'Bank boundary changed')
    nb=graphics_bank(ng,0,allow_bank_aliases=True);ob=graphics_bank(og,0,allow_bank_aliases=True);counts={'base_direction_comparisons':0,'armor_layer_comparisons':0,'graphic_refs':0,'non_base_graphic_refs':0,'protected_compositions':0,'start_layer_direction_combinations':0,'gpu_parts':0};invalid=[]
    for n in range(237):
        f,of=nb['frames'][n],ob['frames'][n];nr=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data;before=decode_stream(og,of['offset'],of['limit'],of['tile_count']*128).data;require(f['tile_count']==of['tile_count'],'Tile count changed')
        if n not in EXCLUDED:
            got=canvas_from_parts(nr,f['tile_count'],composition_frame(nc,0,n));want=render(base,n)[1]
            for flip in (False,True):require(np.array_equal(got[:,::-1] if flip else got,want[:,::-1] if flip else want),'Pre-acquisition Nana differs');counts['base_direction_comparisons']+=1
        else:require(nr==before,'Excluded graphic changed')
        for b in (5,6,7,8):
            if b==5 and n in FRAMES:continue
            require(records(oc,b,n)==records(nc,b,n),'Protected armor composition changed')
            size=(256,160) if n==220 else (160,160)
            try:a=canvas_from_parts(before,of['tile_count'],local_composition(composition_frame(oc,b,n)),size=size)
            except ValueError:require(nr==before,'Unrenderable original changed');invalid.append([n,b]);continue
            z=canvas_from_parts(nr,f['tile_count'],local_composition(composition_frame(nc,b,n)),size=size);require(np.array_equal(a,z),'Other armor changed');counts['armor_layer_comparisons']+=1
        if n in FRAMES:
            got=canvas_from_parts(nr,f['tile_count'],composition_frame(nc,0,n));over=canvas_from_parts(nr,f['tile_count'],composition_frame(nc,5,n));want=np.array(Image.open(folder/f'ultimate_{n:03}.png'));require(np.array_equal(over,np.array(Image.open(folder/f'overlay_{n:03}.png'))),'Overlay PNG differs');require(np.array_equal(np.where(over,over,got),want),'Composite differs')
            exposed=(got>0)&(over==0);require(exposed.sum()==1,'Unexpected base leakage')
            for color in np.unique(got[exposed]):require(bp[int(color)*2:int(color)*2+2]==npal[32+int(color)*2:34+int(color)*2],'Eye color differs')
            require(np.nonzero(want)[0].max()==102,'Foot anchor differs')
            for mask in range(16):
                v=got.copy()
                for bit,b in ((8,8),(1,5),(4,7),(2,6)):
                    if mask&bit:
                        layer=canvas_from_parts(nr,f['tile_count'],local_composition(composition_frame(nc,b,n)));v=np.where(layer,layer,v)
                expected=want if mask&1 else got
                for flip in (False,True):require(np.array_equal(v[:,::-1] if flip else v,expected[:,::-1] if flip else expected),'Part combination differs');counts['start_layer_direction_combinations']+=1
            atlas=np.frombuffer(indexed_atlas(nr,f['tile_count'])[0],np.uint8).reshape(-1,256)
            for b in (0,5,6,7,8):
                for q in composition_frame(nc,b,n)['parts']:
                    t=q['tile'];patch=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16];require(t%16!=0 or not patch[:,0].any(),'Unsafe U edge');require(not q['flip_y'] or t//16%16!=0 or not patch[0].any(),'Unsafe V edge');counts['gpu_parts']+=1
    for bi in range(len(bank_offsets(ng,allow_aliases=True))):
        a,b=graphics_bank(og,bi,allow_bank_aliases=True),graphics_bank(ng,bi,allow_bank_aliases=True)
        for x,y in zip(a['frames'],b['frames']):
            before=decode_stream(og,x['offset'],x['limit'],x['tile_count']*128).data;after=decode_stream(ng,y['offset'],y['limit'],y['tile_count']*128).data;counts['graphic_refs']+=1
            if bi:require(x==y and before==after,'Other graphics bank changed');counts['non_base_graphic_refs']+=1
    for bi in range(len(bank_offsets(oc))):
        for n in range(composition_frame(oc,bi,0)['bank_frame_count']):
            if (bi==0 and n not in EXCLUDED) or (bi==5 and n in FRAMES):continue
            require(records(oc,bi,n)==records(nc,bi,n),'Non-target composition changed');counts['protected_compositions']+=1
    for row in recipe['base_palette_rows']:require(npal[row*32:(row+1)*32]==bp[row*32:(row+1)*32],'Nana body palette mismatch')
    allowed=set(recipe['base_palette_rows']+recipe['armor_palette_rows'])
    for row in range(len(op)//32):
        if row not in allowed:require(op[row*32:(row+1)*32]==npal[row*32:(row+1)*32],'Other palette changed')
    m=(PARENT/'fourth_ui/MOJIPAT.ARC').read_bytes();l=(PARENT/'fourth_ui/LOAD_U.ARC').read_bytes();nm=resources['MOJIPAT.ARC'];nl=resources['LOAD_U.ARC'];ot=entry(l,0x10008);nt=entry(nl,0x10008);require(len(m)==len(nm) and len(l)==len(nl),'UI size changed')
    from scripts.prepare_riko_ui import replace_entry
    require(replace_entry(l,0x10008,nt)==nl,'Other load entry changed');owned={q['tile']+q['page']*256 for q in composition_frame(m,2,52)['parts']}
    for t in set(range(256))-owned:require(tile_pixels(ot,t)==tile_pixels(nt,t),'Non-icon texture changed')
    po=struct.unpack_from('<I',m,4)[0];uiallow=set(range(po+30*32,po+32*32))|{i for q in composition_frame(m,2,52)['parts'] for i in range(q['record_offset'],q['record_offset']+4)};require(all(i in uiallow for i,(a,b) in enumerate(zip(m,nm)) if a!=b),'Non-icon menu changed')
    for n in range(composition_frame(m,2,0)['bank_frame_count']):
        if n!=52:require(composition_frame(m,2,n)==composition_frame(nm,2,n) and compose_static(ot,local_composition(composition_frame(m,2,n)))[:3]==compose_static(nt,local_composition(composition_frame(nm,2,n)))[:3],'Other save rendering changed')
    base0=render(base,0)[1];over=np.array(Image.open(folder/'overlay_000.png'));bw=np.array(struct.unpack_from('<16H',npal),np.uint16);aw=np.array(struct.unpack_from('<16H',npal,32),np.uint16)
    for mask in range(16):require(np.array_equal(save_icon(nm,nt,mask),np.where(over,aw[over],bw[base0]) if mask else bw[base0]),'Save mismatch')
    counts.update(save_combinations=16,unowned_save_tiles=256-len(owned),invalid_original_armor_preserved=invalid,runtime_verified=False);return counts

def main():
    folder=D/'start_v2';repro=D/'start_v2_repro';names={p.name for p in folder.iterdir()};require(names=={p.name for p in repro.iterdir()},'Reproduction file set differs')
    for n in names:require((folder/n).read_bytes()==(repro/n).read_bytes(),'Reproduction differs: '+n)
    require((D/'base_v1/PL02_U.ARC').read_bytes()==(D/'base_v1_repro/PL02_U.ARC').read_bytes(),'Base reproduction differs');proof=validate(folder);bad=[]
    for name in ('PL02_U.ARC','MOJIPAT.ARC','LOAD_U.ARC'):
        resources={n:(folder/n).read_bytes() for n in ('PL02_U.ARC','MOJIPAT.ARC','LOAD_U.ARC')};v=bytearray(resources[name]);v[len(v)//2]^=1;resources[name]=bytes(v)
        try:validate(folder,resources)
        except ValueError:bad.append(name)
        else:raise AssertionError('Corrupted resource accepted')
    suite=unittest.TestSuite()
    for pat in ('test_psx_bank_repack.py','test_psx_compress.py','test_psx_sector.py','test_psx_disc.py','test_ui_atlas.py','test_psx_tile_layout.py','test_psx_armor_palette.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pat))
    result=unittest.TextTestRunner().run(suite);require(result.wasSuccessful(),'Unit failure');proof.update(independent_files=len(names),base_reproduced=True,rejected_corrupted_resources=bad,unit_tests=result.testsRun);write(D/'start_verification.json',proof);print(json.dumps(proof))

if __name__=='__main__':main()
