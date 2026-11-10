"""실제 패킹 결과의 7,296 조합, 팔·총구·발 및 원화 대응을 검증."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,write,helper,need
from pack_cycle import PLACEHOLDERS,PARENT,RESTORED
from register_cycle import ORDER,TICKS
from PIL import Image,ImageDraw,ImageFont
import numpy as np
D=Path(__file__).parent;O=D/'packed_joint_v2';PBS=(0,5,6,7,8);DRAW=((8,8),(1,5),(4,7),(2,6))
def main():
    base=Archive((D/'baseline_PL00_U.ARC').read_bytes());a=Archive((D.parent/'native_restore/prepared_v1/PL00_U.ARC').read_bytes());b=Archive((O/'PL00_U.ARC').read_bytes());need(sha(base.data)==PARENT and sha(a.data)==RESTORED,'Input guard')
    targets={(n,pb):np.array(Image.open(D/'joint_layers_v1'/f'layer{pb}_{n:03}.png'))for n in range(1,33)for pb in PBS};checks=unchanged=0;palette_arm_equal=bool(np.array_equal(b.words[16:32],b.words[32:48]));motions=[]
    for n in range(237):
        if n in PLACEHOLDERS:continue
        layerimgs={pb:b.rgba(targets[n,pb],0 if pb==0 else 16)for pb in PBS}if n in range(1,33)else None
        for mask in range(16):
            for arm in (1,2):
                actual=b.composite(n,mask,arm)[0]
                if layerimgs is None:expected=a.composite(n,mask,arm)[0];unchanged+=1
                else:
                    expected=layerimgs[0].copy()
                    for bit,pb in DRAW:
                        if mask&bit:expected.alpha_composite(b.rgba(targets[n,pb],32 if pb==7 and arm==2 else 16))
                need(actual.tobytes()==expected.tobytes(),f'RGBA differs {n}/{mask}/{arm}');checks+=1
        if n in range(1,33):
            full=Image.open(D/'joint_layers_v1'/f'full_{n:03}_rgba.png').convert('RGBA');need(b.composite(n,15,1)[0].tobytes()==full.tobytes(),'Authored full RGBA differs')
            q=b.layer(n)[0];y,x=np.nonzero(q);motions.append({'ref':n,'base_floor_y':int(y.max()-160),'base_bbox':[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],'base_indexed_sha256':sha(q.tobytes()),'full_rgba_sha256':sha(full.tobytes())})
        if n%32==0:print(json.dumps({'frame':n,'checked':checks}),flush=True)
    for start in range(1,33,8):
        helper.grid([(f'run {n} / fire {n+1}',[('대기 기본',b.composite(0)[0]),('이전 run',base.composite(n)[0]),('새 run',b.composite(n)[0]),('새 fire',b.composite(n+1)[0]),('대기 포스',b.composite(0,15)[0]),('새 포스 run',b.composite(n,15)[0]),('새 포스 fire',b.composite(n+1,15)[0])])for n in range(start,start+8,2)],O/f'readback_{(start-1)//8+1}.png',4)
    for group,refs in enumerate(((1,7),(13,19),(25,27),(3,31)),1):
        helper.grid([(f'mask {m:X}',[(f'ref {n} {"run" if n%2 else "fire"}',b.composite(n,m)[0])for r in refs for n in(r,r+1)])for m in range(16)],O/f'partial_{group}.png',4)
    # Actual native timings, with display labels distinguishing source slots.
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);frames=[]
    for n in ORDER:
        board=Image.new('RGB',(4*320,420),'#b4c1c8');draw=ImageDraw.Draw(board)
        for i,(name,ref,mask)in enumerate((('기본 이동',n,0),('기본 이동사격',n+1,0),('포스 이동',n,15),('포스 이동사격',n+1,15))):
            im=b.composite(ref,mask)[0].crop((120,128,200,192)).resize((320,256),Image.Resampling.NEAREST);board.paste(im,(i*320,70),im);draw.text((i*320+6,20),f'{name} {ref}',font=font,fill='black')
        frames.append(board)
    frames[0].save(O/'native_timeline.gif',save_all=True,append_images=frames[1:],duration=[round(t*1000/60)for t in TICKS],loop=0,disposal=2)
    write(O/'mask_verification.json',{'passed':True,'prepared_sha256':sha(b.data),'rgba_combinations':checks,'unchanged_vs_ladder_restored':unchanged,'new_expected_combinations':checks-unchanged,'arm1_arm2_palette_equal':palette_arm_equal,'actual_mips_runtime_test':False,'emulator_test':False,'frames':motions,'animation_refs':ORDER,'animation_ticks':TICKS,'gif_is_static_reconstruction':True})
    print(json.dumps({'passed':True,'combinations':checks,'unchanged':unchanged,'new':checks-unchanged}),flush=True)
if __name__=='__main__':main()
