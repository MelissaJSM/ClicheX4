"""새 대시20 ARC 재독출:640부분·고정총열·원속도선·GPU페이지경계."""
from pathlib import Path
import json,sys,argparse
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from prepare_lowhp_final import compose
from prepare_dash_body_layers import P
from src.psx_player import decode_stream,indexed_atlas,composition_frame
from pack_dash_complete import protected_entries
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--folder',default='dash_pack_probe02');z=ap.parse_args();d=H/z.folder;o=d/'verification';need(not o.exists(),'Fresh output');o.mkdir();data=(d/'PL00_U.ARC').read_bytes();need(sha(data)=='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b','Candidate changed');a=Archive(data);parent=Archive(P.read_bytes());t=H/'dash_complete_targets01';refs=list(range(67,85))+[93,94];parts=combos=guns=0;unique=set();native_images={};gun_refs={68,70,72,76,78,80,82,84};rows=[]
    for n in refs:
        layers={b:np.array(Image.open(t/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};f=a.banks[0]['frames'][n];need(f['tile_count']==32,'Wrong tile budget');raw=decode_stream(a.g,f['offset'],f['limit'],4096).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
        for b,expected in layers.items():
            need(np.array_equal(a.layer(n,b)[0],expected),'Layer differs')
            for p in composition_frame(a.c,b,n)['parts']:
                tile=p['tile'];part=atlas[tile//16*16:tile//16*16+16,tile%16*16:tile%16*16+16];parts+=1;unique.add((f['offset'],tile));need(0<=tile<32,'Outside uploaded buffer')
                if tile%16==0:need(not part[:,0].any(),'Unsafe U boundary')
                if p['flip_y']:need(not part[0].any(),'Unsafe V boundary')
        for m in range(16):
            for arm in(1,2):
                actual=a.composite(n,m,arm)[0];want=compose(a,layers,m,arm);need(actual.tobytes()==want.tobytes(),'Partial readback mismatch');combos+=1
                if n in gun_refs:
                    guard=np.array(Image.open(H/f'dash_barrel_guard02/{n:03}_mask.png'))>0;module=np.array(Image.open(H/f'dash_barrel_guard02/{n:03}_indices.png'));need(np.array_equal(np.array(actual)[guard],np.array(a.rgba(module))[guard]),'Gun module or transparent guard differs');guns+=1
            native_images[n,m]=a.composite(n,m)[0]
        for form,m in(('base',0),('fourth',15)):native_images[n,m].save(o/f'{form}_{n:03}.png')
    sheets=[]
    for start in range(0,len(refs),4):
        rr=refs[start:start+4];cw=168;ch=152;im=Image.new('RGBA',(16*cw,len(rr)*ch),(28,34,44,255));draw=ImageDraw.Draw(im)
        for row,n in enumerate(rr):
            for m in range(16):
                pic=native_images[n,m];cut=pic.crop((116,128,192,192));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(pic)[:,:,3]),'Partial sheet clips art');cut=cut.resize((152,128),Image.Resampling.NEAREST);im.alpha_composite(cut,(m*cw+8,row*ch+20));draw.text((m*cw+3,row*ch+3),f'{n} mask{m:X}',fill='white')
        path=o/f'partial_all_{start//4:02}.png';im.save(path);sheets.append(path.relative_to(ROOT).as_posix())
    protected=protected_entries(parent.data,data)
    result={'passed':True,'candidate_sha256':sha(data),'parent_arc_sha256':sha(P.read_bytes()),'selected_refs':refs,'exact_target_layers':100,'native_partial_rgba_conditions':combos,'native_casing_conditions':guns,'gpu_part_boundary_checks':parts,'unique_stream_tiles':len(unique),'unsafe_U_V_violations':0,'protected_entries':protected,'actual_readback_pngs':40,'all_partial_sheets':sheets,'original_streak_geometry':'71/72新몸체와원US9개속도선파츠의좌표·플래그·tile6 원texel을유지한다. 새몸체이므로원US74의기존X겹침1px를복제하지않음.','visual_review_pending':True,'native_mips_run_here':False,'emulator_verified':False,'game_modified':False}
    write(d/'verification.json',result);print(json.dumps(result))
if __name__=='__main__':main()
