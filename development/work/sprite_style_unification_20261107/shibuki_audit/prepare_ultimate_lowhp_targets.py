"""새 원화 두 의상으로 원래 저체력 6참조의 호흡과 입 교대를 만든다."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from prepare_ultimate_lowhp_shared import make
from scripts.export_x_consistency import page, metrics
from native_pose_pack import need, write

O = H / 'ultimate_lowhp_targets01'

def breathe(q, dy):
    v = q.copy()
    for y in range(120, 178):
        shift = dy if y < 170 else round(dy * max(0, 178-y)/8)
        v[y] = q[y-shift]
    need(np.array_equal(v[178:], q[178:]), 'Ankles/soles moved')
    return v

def targets():
    arc, before, after, shared, source = make()
    full = {}; base = {}; records = []
    # Preserve the native three-phase order and two-pixel excursion. The new
    # painting is the first phase; this is not a resize of individual poses.
    for n in range(120, 126):
        dy = -((n-120)//2)
        b, a = before.copy(), after.copy()
        need(int(b[153,155]) == int(a[153,155]) == 13, 'New lower face anchor changed')
        if n % 2:
            b[153,155] = a[153,155] = 11
        full[n], base[n] = breathe(b,dy), breathe(a,dy)
        need(not np.any((base[n]>0)&(full[n]==0)), 'After alpha leaks outside jacket')
        records.append({'ref':n,'relative_breathing_y':dy,'mouth_open':bool(n%2),'mouth_master_world':[-5,-7],'mouth_shifted_world':[-5,-7+dy],'mouth_closed_index':13,'mouth_open_index':11,'feet_world_y18_plus_exact':True,'before':metrics(arc.rgba(full[n],16)),'after':metrics(arc.rgba(base[n],0))})
    return arc, full, base, {'source':source,'frames':records,'timing_changed':False,'body_scaled':False,'old_art_copied':False,'runtime_verified':False}

if __name__ == '__main__':
    need(not O.exists(),'Fresh output required')
    arc, full, base, proof = targets()
    O.mkdir()
    for name, values, start, mask in (('before',full,16,15),('after',base,0,0)):
        folder = O/name;folder.mkdir()
        for n,v in values.items():
            Image.fromarray(v).save(folder/f'{n:03}_indices.png')
            arc.rgba(v,start).save(folder/f'{n:03}.png')
        page([(f'{n} old',arc.composite(n,mask)[0]) for n in values]+[(f'{n} new',arc.rgba(v,start)) for n,v in values.items()],arc.composite(0,mask)[0],O/f'{name}_comparison.png',cols=3,scale=4)
        # Review simulation follows the real animation6 frame/duration order.
        order=[(122,12),(120,14),(122,12),(124,14)]*2+[(123,12),(121,14),(123,12),(125,14)]*2
        frames=[];durations=[]
        for n,ticks in order:
            frame=Image.new('RGBA',(64,64),'#1d2530')
            frame.alpha_composite(arc.rgba(values[n],start).crop((128,128,192,192)))
            frames.append(frame.resize((384,384),Image.Resampling.NEAREST));durations.append(round(ticks*1000/60))
        frames[0].save(O/f'{name}_simulation.webp',save_all=True,append_images=frames[1:],duration=durations,loop=0,lossless=True)
    proof['simulation']={'kind':'extracted_sequence_review','not_gameplay':True,'calls_per_second_assumption':60,'frame_durations':order}
    write(O/'provenance.json',proof)
    print({'before_sizes':[r['before']['size']for r in proof['frames']],'after_sizes':[r['after']['size']for r in proof['frames']]})
