"""원본 제로 이동16참조를 동일 월드 원점의 포즈 참고 시트로 추출."""
import json,struct,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from scripts.extract_zero import save_image
from scripts.project import digest

def main():
    e=ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z';out=ROOT/'work/ver_rin_nana/run_production/v1';out.mkdir(parents=True,exist_ok=True)
    g=(e/'graphics_entry.bin').read_bytes();p=(e/'composition_entry.bin').read_bytes();words=struct.unpack_from('<16H',(e/'palette_bank.bin').read_bytes());bank=graphics_bank(g,0)
    ids=[3,4,*range(7,21)];board=Image.new('RGBA',(256,256));meta=[]
    for i,n in enumerate(ids):
        f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;c=composition_frame(p,0,n);data,size,bounds,_=compose_indices(raw,f['tile_count'],c)
        pic=save_image(data,size,words,out/f'zero_{n:03}.png');board.alpha_composite(pic.convert('RGBA'),((i%4)*64+32+bounds[0],(i//4)*64+32+bounds[1]))
        meta.append({'frame':n,'cell':[i%4,i//4],'bounds':bounds,'size':size,'sha256':digest(out/f'zero_{n:03}.png'),'tile_count':f['tile_count']})
    board.resize((1024,1024),Image.Resampling.NEAREST).save(out/'zero_pose_reference_4x.png')
    (out/'original_motion.json').write_text(json.dumps({'frames':meta,'cell_native_size':[64,64],'world_origin':[32,32],'run_ids':list(range(7,21)),'run_ticks':[2,3,2,2,2,3,2]*2},indent=2)+'\n','utf-8')
    print(str(out))

if __name__=='__main__':main()
