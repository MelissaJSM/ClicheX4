"""원본 X 이동·사격 공유 구조를 나나 승인 마스터와 함께 읽기 전용으로 준비한다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
from scripts.prepare_nana_idle_shot import INV,PILOT,write
from scripts.project import digest
from src.psx_player import composition_frame

def main():
    out=ROOT/'work/ver_rin_nana/nana_art/run_v1';out.mkdir(parents=True,exist_ok=True)
    inv=json.loads(INV.read_text('utf8'));parts=(INV.parent/'composition_entry.bin').read_bytes()
    if digest(INV.parent/'original.arc')!='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a':raise ValueError('Native source changed')
    order=[1,3]+[s['frame'] for s in inv['animations'][8]['steps']];pairs=[]
    board=Image.new('RGBA',(8*256,2*288),(0,0,0,0))
    for i,n in enumerate(order):
        a,b=inv['base_frames'][n:n+2]
        if a['offset']!=b['offset'] or inv['stream_sharing'][str(a['offset'])]!=[[0,n],[0,n+1]]:raise ValueError('Unexpected sharing')
        base={q['tile'] for q in a['composition']['parts']};shot={q['tile'] for q in b['composition']['parts']}
        armor={str(k):sorted({q['tile'] for m in (n,n+1) for q in composition_frame(parts,k,m)['parts']}) for k in (5,6,7,8)}
        pairs.append({'frames':[n,n+1],'stream':a['offset'],'budget':a['compressed_end']-a['offset'],'tile_count':a['tile_count'],'common_base_tiles':sorted(base&shot),'nonshoot_only_tiles':sorted(base-shot),'shoot_only_tiles':sorted(shot-base),'armor_overlay_tiles':armor,'bounds':[a['bounds'],b['bounds']]})
        im=Image.open(INV.parent/a['image']).convert('RGBA');bb=a['bounds'];im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST)
        board.paste(im,((i%8)*256+128+bb[0]*4,(i//8)*288+144+bb[1]*4),im)
    board.save(out/'native_motion_reference.png')
    write(out/'plan.json',{'task':'x_nana','source_inventory':INV.relative_to(ROOT).as_posix(),'order':order,'paired_frames':pairs,'start_animation':inv['animations'][7],'run_animation':inv['animations'][8],'timing_assumption_for_gif':60})
    write(out/'order.json',{'frames':order})
    print(json.dumps({'directory':str(out),'order':order,'pairs':len(pairs)}))
if __name__=='__main__':main()
