from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from src.epsxe_state import framebuffer,match_sprite
P=O/'rn43_lowhp_actual01';plan=json.loads((W/'staging_rn_v43.json').read_text('utf8'));src=plan['resources']['PL00_U.ARC'];blob=(ROOT/src['path']).read_bytes();assert hashlib.sha256(blob).hexdigest()==src['after'];a=Archive(blob)
board=Image.new('RGB',(1400,480),'#26313f');d=ImageDraw.Draw(board)
idle=a.composite(0,0)[0].crop((136,126,184,186)).resize((192,240),Image.Resampling.NEAREST);board.paste(idle,(4,44),idle);d.text((4,8),'CURRENT IDLE',fill='white');rows=[]
for col,n in enumerate(range(120,126),1):
    im=a.composite(n,0)[0];bb=im.getbbox();matches=[];chosen=None
    for video_path in sorted(O.glob('rn43_lowhp_actual*/vram_*.bin')):
        video=video_path.read_bytes()
        for py in(0,256):
            screen=framebuffer(video,0,py);hits=match_sprite(screen,im.crop(bb));matches.append({'source':video_path.relative_to(ROOT).as_posix(),'page_y':py,'matches':hits})
            if hits and chosen is None:chosen=(py,screen,hits[0])
    full_match=chosen is not None
    if chosen is None:
        # Some captures have foreground occlusion or upload/draw timing differences.
        # Keep the failed full-match result; the cause is not fully separated here.
        video=(P/f'vram_{n:03}.bin').read_bytes();chosen=(0,framebuffer(video,0,0),{'x':150,'y':154,'flip_x':None,'opaque_pixels_equal':None})
    py,screen,hit=chosen;x,y=hit['x'],hit['y'];pic=screen.crop((x-6,y-4,x+(bb[2]-bb[0])+6,y+(bb[3]-bb[1])+4));pic=pic.resize((pic.width*4,pic.height*4),Image.Resampling.NEAREST)
    board.paste(pic,(col*200+4,44));d.text((col*200+4,8),f'ref {n} / VRAM {py}',fill='white');d.text((col*200+4,25),f'exact {hit["opaque_pixels_equal"]} px' if full_match else 'no full screen match',fill='#9eeebd' if full_match else '#f5cf84')
    native=im.crop((136,126,184,186)).resize((144,180),Image.Resampling.NEAREST);board.paste(native,(col*200+24,296),native)
    rows.append({'ref':n,'matches':matches,'selected_buffer':py,'selected_match':hit if full_match else None,'full_opaque_screen_match':full_match})
board.save(P/'actual_six_vs_idle.png')
(P/'screen_matches.json').write_text(json.dumps({'frames':rows,'all_six_have_exact_opaque_framebuffer_match':all(q['full_opaque_screen_match']for q in rows),'scope':'두 프레임버퍼에서 전체 불투명 일치를 시도했다. 일치하지 않은 표본은 실패로 유지하고 고정 화면창을 표시한다. 일부 전경 가림과 업로드/그리기 시점 차이가 있으나 원인을 전부 분리하지는 않았다. RAM/GPU 타일 일치와 화면 전체 일치를 구분한다.','actually_viewed':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'frames':6,'full_matches':sum(q['full_opaque_screen_match']for q in rows)}))
