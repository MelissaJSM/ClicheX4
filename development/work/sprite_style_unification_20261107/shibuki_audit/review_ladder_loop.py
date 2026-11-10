"""정적 신규 사다리 루프의 실제 순서 비교. 물리/사다리 진행은 실행하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,write
from probe_ladder_capacity import mirror
from register_ladder_parts import compose

def main():
    folder=H/'ladder_parts_probe03';out=H/'ladder_loop_review01';need(not out.exists(),'Output exists');out.mkdir()
    a=Archive((H/'prepared_wall_front01/PL00_U.ARC').read_bytes());meta=json.loads((H/'ladder_detail_inputs01/manifest.json').read_text('utf8'))
    aliases={145:(144,-1),147:(146,0),148:(149,0),152:(151,0)}
    values={}
    for ref in (144,145,146,147,148,149,151,152):
        key,delta=aliases.get(ref,(ref,None));layers={b:np.array(Image.open(folder/f'{key:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}
        if delta is not None:layers={b:mirror(v,delta)for b,v in layers.items()}
        values[ref]=layers
    rows=[]
    for animation in [v for v in meta['animations']if v['id']in(31,32)]:
        for mask,form in((0,'base'),(15,'fourth')):
            items=[];frames=[];dur=[]
            for step in animation['steps']:
                ref=step['frame'];old=a.composite(ref,mask)[0];new=compose(a,values[ref],mask);items.extend([(f'{ref} current',old),(f'{ref} candidate',new)])
                canvas=Image.new('RGBA',(3*64,80),(25,31,42,255));d=ImageDraw.Draw(canvas)
                for col,(label,im)in enumerate((('idle',a.composite(0,mask)[0]),('current',old),('candidate',new))):
                    canvas.alpha_composite(im.crop((128,128,192,192)),(col*64,16));d.text((col*64+2,1),label,fill='white')
                frames.append(canvas.resize((768,320),Image.Resampling.NEAREST));dur.append(round(step['duration_calls_uninterrupted']*1000/60))
            frames[0].save(out/f'{form}_{animation["id"]}.webp',save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True)
            page(items,a.composite(0,mask)[0],out/f'{form}_{animation["id"]}_contact.png',cols=4,scale=3)
            rows.append({'form':form,'animation':animation,'timing_ms':dur,'candidate_art_source':folder.relative_to(ROOT).as_posix()})
    write(out/'review.json',{'rows':rows,'actual_exe_steps_preverified':'ladder_detail_inputs01/native_animation_source.json','ticks_per_second_assumed':60,'not_actual_gameplay':True,'physics_ladder_movement_event_execution':False,'pending_hand_foot_correction':[149,151,153],'candidate_not_packed':True})
    print(out)

if __name__=='__main__':main()
