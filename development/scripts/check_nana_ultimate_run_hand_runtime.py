"""저장된 실제 VRAM에서 수정한 손 영역만 대조한다. 게임 입력/쓰기 없음."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.prepare_nana_fourth_pilot import require,write
from src.epsxe_state import framebuffer,match_sprite

def main(folder):
    folder=folder.resolve();require(folder.is_relative_to(ROOT/'work/ver_rin_nana/armor_capture'),'Unexpected evidence folder');q=json.loads((folder/'verification.local.json').read_text('utf8'));build=Path(q['source_build']);meta=json.loads((build/'ultimate_run/registration.json').read_text('utf8'));boxes={r['frames'][0]:r['hand_edit_box'] for r in meta};rows=[]
    for sample in q['results']+q['samples_without_full_match']:
        n=sample['frame'];direction=sample['direction_bit']
        if n not in boxes:continue
        require(sample['ram_equal'] and sample['vram_equal'] and all(v['matching_arc_rows'] for v in sample['palettes'].values()),'Unverified sample')
        sprite=Image.open(folder/f'expected_{n:03}.png').convert('RGBA').crop(tuple(boxes[n]));vram=(folder/f'sample_{n:03}_d{direction}.vram').read_bytes();matches=[]
        for page in (0,240,256):
            screen=framebuffer(vram,0,page);found=match_sprite(screen,sprite)
            if found:
                name=f'hand_actual_{n:03}_d{direction}_{page}.png';screen.save(folder/name);matches.extend({'image':name,'page':page,**m} for m in found)
        rows.append({'frame':n,'direction_bit':direction,'crop':boxes[n],'matches':matches})
    result={'source_build':str(build),'bin_sha256':q['modified_bin_sha256'],'scope':'edited hand/cuff/pistol region only; full body obscured by water effects','verified_hand_frames':sorted({r['frame'] for r in rows if r['matches']}),'verified_tags':sum(bool(r['matches']) for r in rows),'rows':rows,'process_memory_written':False,'input_sent':False};write(folder/'hand_verification.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);main(p.parse_args().folder)
