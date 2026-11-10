"""시험 ARC 재독출, 부분 파츠/총구/타일 경계와 비대상 바이트 보존을 확인한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
import numpy as np
from scripts.export_x_consistency import Archive,page
from scripts.prepare_riko_ui import entry
from src.psx_player import decode_stream,indexed_atlas,composition_frame
from native_pose_pack import need,sha,write
from prepare_lowhp_final import compose
from inspect_air_layers import P

def main():
    d=H/'air_pack_probe01';o=d/'readback';need(not o.exists(),'Fresh output required');o.mkdir();data=(d/'candidate_PL00_U.ARC').read_bytes();need(sha(data)=='c580b371564252fd73cb97aa31d3282dcebabf5855cbec6d5b00acc7f7b7c6be','Candidate changed');a=Archive(P.read_bytes());b=Archive(data);t=H/'air_targets_probe02';refs=range(33,55)
    parts=0;safe_tiles=set();conditions=0;gun_conditions=0;palette=entry(a.data,9);need(entry(data,9)==palette,'Palette changed');masks=[]
    for n in refs:
        layers={pb:np.array(Image.open(t/f'{n:03}_bank{pb}_indices.png'))for pb in(0,5,6,7,8)};f=b.banks[0]['frames'][n];raw=decode_stream(b.g,f['offset'],f['limit'],f['tile_count']*128).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
        for pb in(0,5,6,7,8):
            native=b.layer(n,pb)[0];need(np.array_equal(native,layers[pb]),'Layer source mismatch')
            for p in composition_frame(b.c,pb,n)['parts']:
                tile=p['tile'];parts+=1;safe_tiles.add((f['offset'],tile));ras=atlas[tile//16*16:tile//16*16+16,tile%16*16:tile%16*16+16]
                if tile%16==0:need(not ras[:,0].any(),'Page-edge first column is opaque')
                if p['flip_y']:need(not ras[0].any(),'Flipped first row is opaque')
        for mask in range(16):
            for arm in(1,2):
                actual=b.composite(n,mask,arm)[0];expected=compose(b,layers,mask,arm);need(actual.tobytes()==expected.tobytes(),'Partial native composite mismatch');conditions+=1
                if n%2==0:
                    gm=np.array(Image.open(H/f'air_barrel_guard02/{n:03}_mask.png'))>0;gun=np.array(Image.open(H/f'air_barrel_guard02/{n:03}_indices.png'));need(np.array_equal(np.array(actual)[gm],np.array(a.rgba(gun))[gm]),'Native muzzle/casing mismatch');gun_conditions+=1
            masks.append((n,mask,b.composite(n,mask,2)[0]))
        for name,mask in(('base',0),('fourth',15)):b.composite(n,mask)[0].save(o/f'{name}_{n:03}.png')
    for name,mask in(('base',0),('fourth',15)):
        for start in range(33,55,8):
            items=[]
            for n in range(start,min(55,start+8)):items.extend([(f'{n} previous',a.composite(n,mask)[0]),(f'{n} packed new',b.composite(n,mask)[0])])
            page(items,a.composite(0,mask)[0],o/f'{name}_actual_{(start-33)//8:02}.png',cols=4,scale=4)
    # Each strip shows all sixteen part states, one ref per row. Body is not
    # shifted between columns; numbers are actual armor masks.
    sheets=[]
    for start in range(33,55,4):
        rr=list(range(start,min(55,start+4)));im=Image.new('RGB',(16*110,len(rr)*134),(28,34,44));draw=ImageDraw.Draw(im)
        for row,n in enumerate(rr):
            for mask in range(16):
                pic=b.composite(n,mask)[0].crop((128,124,180,184)).resize((104,120),Image.Resampling.NEAREST);x=mask*110;y=row*134;im.paste(pic,(x,y+14),pic);draw.text((x+2,y+1),f'{n} / {mask:X}',fill=(230,230,230))
        path=o/f'partial_all_{(start-33)//4:02}.png';im.save(path);sheets.append(path.relative_to(ROOT).as_posix())
    # Every non-graphics/assembly entry remains exactly input bytes.
    from scripts.discover_inputs import psx_arc
    protected=[]
    for e in psx_arc(a.data):
        k=int(e['type'],16)
        if k not in(2,3):need(entry(a.data,k)==entry(data,k),'Unrelated ARC entry changed');protected.append(k)
    result={'passed':True,'candidate_sha256':sha(data),'parent_sha256':sha(a.data),'target_refs':list(refs),'target_layers_exact':110,'native_partial_conditions':conditions,'actual_muzzle_casing_conditions':gun_conditions,'gpu_part_static_checks':parts,'unique_stream_tiles':len(safe_tiles),'page_edge_opaque_violations':0,'flip_y_opaque_violations':0,'unchanged_entries':protected,'all_palette_bytes_exact':True,'timing_sound_entries_exact':True,'actual_native_source_images':44,'all_partial_contact_sheets':sheets,'all_partial_visual_review_pending':True,'runtime_mips_gpu_not_run_here':True,'game_bin_changed':False}
    write(d/'candidate_verification.json',result);print(json.dumps(result))
if __name__=='__main__':main()
