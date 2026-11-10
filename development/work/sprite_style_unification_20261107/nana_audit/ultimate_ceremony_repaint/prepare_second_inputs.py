"""136/137에서 역사 출처가 확인되는 흰 효과만 분리한 의상 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,digest,sha,write,need
from pack_cycle import raw
from src.psx_player import composition_frame,compose_indices
from prepare_first_inputs import PROMPT
def full(a,n):
    z=a.layer(n)[0].copy()
    for pb in(8,5,7,6):p=a.layer(n,pb)[0];z[p>0]=p[p>0]
    return z
def main():
    p=N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC';need(digest(p)=='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5','부모')
    history=ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC';need(digest(history)=='89f9cc0a7c9a01a8d38dbc9fd67078413f06c71cc10234e358f5fde5e2643ab4','역사 부모')
    a=Archive(p.read_bytes());h=Archive(history.read_bytes());out=D/'second_inputs_v1';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));frames=[];effects=[]
    for col,n in enumerate((136,137)):
        cp=composition_frame(h.c,0,n);parts=[q for q in cp['parts']if q['tile']==7];need(parts,'원 효과 파츠')
        buf,size,box,_=compose_indices(raw(h,0,n),h.banks[0]['frames'][n]['tile_count'],{'parts':parts},allowed_cluts={0,1,2,3});v=np.frombuffer(buf,np.uint8).reshape(size[1],size[0]);fx=np.zeros((384,384),np.uint8);y,x=np.nonzero(v);fx[y+box[1]+160,x+box[0]+160]=v[y,x]
        Image.fromarray(fx).save(out/f'effect_{n:03}_indices.png');mask=fx>0
        for row,bits in enumerate((15,0)):
            z=full(a,n)if bits else a.layer(n)[0];need(np.array_equal(z[mask],fx[mask]),'현재/역사 효과 exact')
            im=a.composite(n,bits)[0];arr=np.array(im);arr[mask]=0;body=Image.fromarray(arr);body.save(out/f'{"before"if bits else"after"}_{n:03}_body.png')
            target.alpha_composite(body.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            ref=0 if col==0 else 47;style.alpha_composite(a.composite(ref,bits)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            yy,xx=np.nonzero(arr[:,:,3]);frames.append({'cell':row*2+col,'ref':n,'form':'before'if bits else'after','mask':bits,'body_rgba_sha256':sha(arr.tobytes()),'world_bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)],'fixed_cell_world':[-48,-48,48,48],'body_components8':int(label(arr[:,:,3]>0,np.ones((3,3)))[1])})
        effects.append({'ref':n,'history_source_sha256':digest(history),'original_tile':7,'original_parts':parts,'pixels':int(mask.sum()),'effect_sha256':sha(fx.tobytes()),'current_both_forms_exact_at_effect_pixels':True})
    prompt=PROMPT.replace('landing pose133','ready pose136').replace('rising into ready pose135','raised-hand pose137')
    start=prompt.index('Pose133 is');end=prompt.index('Preserve exact target',start)
    prompt=prompt[:start]+'Pose136 is a grounded ready posture with a bent forward arm and the compact pistol close to the face. Pose137 is the grounded transition with one hand raised beside the head and the opposite hand beside the hip, hair flowing rightward. Keep these exact gesture angles and each tiny held pistol in place. '+prompt[end:]
    target.save(out/'targets.png');style.save(out/'style.png');(out/'prompt.txt').write_text(prompt,'utf8')
    write(out/'manifest.json',{'source_arc':p.relative_to(ROOT).as_posix(),'source_arc_sha256':digest(p),'frames':sorted(frames,key=lambda q:q['cell']),'native_cell':[96,96],'render_scale':8,'effects_removed_from_generation_input_only':effects,'inputs':[{'path':(out/n).relative_to(ROOT).as_posix(),'sha256':digest(out/n)}for n in('targets.png','style.png','prompt.txt')],'scope':'역사baseline tile7 실제효과를 현재양폼에서exact 확인하여 생성입력에서만 분리.원효과파일과게임은불변.','native_packed':False,'runtime_verified':False})
    print(json.dumps({'frames':len(frames),'effects':[(q['ref'],q['pixels'])for q in effects]}))
if __name__=='__main__':main()
