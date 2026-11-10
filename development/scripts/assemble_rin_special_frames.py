"""특수기술의 공유 포즈와 원작 차지 오라를 월드 좌표에서 결속한다."""
import struct,json
import numpy as np
from scripts.prepare_rin_specials import ROOT,OUT
from scripts.build_rin_idle import entry
from scripts.extract_zero import save_image
from src.psx_frame_edit import read_indexed_png
from scripts.register_rin_style_revision import repack_windows
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_hurt_launch import compose_launch
from src.psx_frame_edit import frame_coverage
from src.psx_rakuhouha import CHARGE_BOXES,CHARGE_REMAP
from src.rin_registration import align_contact_x,contact_span,translate_body_x
from scripts.project import digest

def world(frame,bounds):
    px,size=frame;a=np.zeros((256,256),np.uint8);x,y,r,b=bounds
    a[128+y:128+b,128+x:128+r]=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);return a

def prepare(g,oldparts,parts,frames,words,groups):
    parts=bytearray(parts)
    worlds={0:{},1:{}};bindings=[];aura={};thrust_contacts={};dash_contacts={};contacts={}
    for bi in (0,1):
        for n,frame in frames[bi].items():
            f=graphics_bank(g,bi)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            bounds=compose_launch(raw,f['tile_count'],composition_frame(parts,0 if bi==0 else 5,n))[2]
            worlds[bi][n]=world(frame,bounds)
    def place(bi,n):
        nonlocal parts
        pb=0 if bi==0 else 5;w=worlds[bi][n];f=graphics_bank(g,bi)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        def check():
            c=composition_frame(parts,pb,n);coverage,size,b=frame_coverage(raw,f['tile_count'],c)
            a=w[128+b[1]:128+b[3],128+b[0]:128+b[2]];safe=np.array([bool(q) for q in coverage]).reshape(size[1],size[0])
            for q in c['parts']:
                if q['tile']%16==0:safe[q['y']-b[1]:q['y']-b[1]+16,q['x']-b[0]+(15 if q['flip_x'] else 0)]=False
            bad=np.count_nonzero(w)-np.count_nonzero(a)+np.count_nonzero((a>0)&~safe)
            return int(bad),(a.tobytes(),size)
        bad,frame=check()
        if bad:
            yy,xx=np.nonzero(w);x=int(xx.min());y=int(yy.min());a=w[y:int(yy.max())+1,x:int(xx.max())+1]
            revised=repack_windows(parts,pb,n,a,x-128,y-128)
            if revised is not None:parts=revised;bad,frame=check()
        if bad:raise ValueError(f'Special body/charge outside parts {bi}:{n}: {bad}')
        frames[bi][n]=frame
    def bind(bi,target,source):
        pb=0 if bi==0 else 5;src=composition_frame(parts,pb,source)['parts'];dst=composition_frame(parts,pb,target)['parts'];mapping={};used=set()
        if len(dst)<len(src):raise ValueError('Shared target lacks windows')
        for p in dst:
            matches=[i for i,q in enumerate(src) if q['tile']==p['tile']]
            if matches:mapping[p['record_offset']]=matches[0];used.add(matches[0])
        def compatible(p,q):
            if p['tile']%16:return True
            col=128+q['x']+(15 if p['flip_x'] else 0)
            return not worlds[bi][source][128+q['y']:128+q['y']+16,col].any()
        for p in sorted(dst,key=lambda p:p['tile']%16!=0):
            if p['record_offset'] in mapping:continue
            options=[i for i,q in enumerate(src) if i not in used and compatible(p,q)]
            if not options:options=[i for i,q in enumerate(src) if compatible(p,q)]
            if not options:raise ValueError('Shared U0 edge mapping failed')
            i=min(options,key=lambda i:abs(src[i]['x']-p['x'])+abs(src[i]['y']-p['y']));mapping[p['record_offset']]=i;used.add(i)
        for i,q in enumerate(src):
            if i not in used and worlds[bi][source][128+q['y']:128+q['y']+16,128+q['x']:128+q['x']+16].any():raise ValueError(f'Shared mapping omits occupied window {target}/{source}:{q["tile"]}')
        for p in dst:
            q=src[mapping[p['record_offset']]]
            if (p['flip_x'],p['flip_y'])!=(q['flip_x'],q['flip_y']):raise ValueError('Shared orientation differs')
            parts[p['record_offset']+2]=q['x']&255;parts[p['record_offset']+3]=q['y']&255
        worlds[bi][target]=worlds[bi][source].copy();place(bi,target);bindings.append({'bank':bi,'target':target,'source':source})
    if 'thrust' in groups:
        idle=graphics_bank(g,0)['frames'][147];raw=decode_stream(g,idle['offset'],idle['limit'],idle['tile_count']*128).data;pic=compose_launch(raw,idle['tile_count'],composition_frame(oldparts,0,147));anchor=contact_span(world(pic[:2],pic[2]))['center_x']
        for n in (114,125):worlds[1][n]=worlds[1][108].copy()
        # Palette index15 is not a shared eye landmark between Zero and Rin.
        # The windup, active strike and recovery all remain on the same ground
        # anchor. Never move the whole body just to pin the lightning to a hand.
        for n in sorted(worlds[1]):
            if n not in (91,93,101,103,105,107,108,110,112,114,116,119,122,125,128,129,130,131):continue
            worlds[1][n],thrust_contacts[str(n)]=align_contact_x(worlds[1][n],anchor);place(1,n)
        for target,source in ((103,101),(128,130),(129,130),(131,130)):bind(1,target,source)
        for n in thrust_contacts:
            thrust_contacts[n]['final_after_shared_binding']=contact_span(worlds[1][int(n)])
    if 'dashslash' in groups:
        folder=OUT/'dashslash';anchors=json.loads((folder/'registration_anchors.json').read_text('utf-8'));registered=json.loads((folder/'registered.json').read_text('utf-8'))
        # Crouching hands and raised boots contaminate generic footprint bands.
        # Use explicitly inspected head landmarks and the accepted dash/recovery
        # poses; these are authored positions, not extracted game coordinates.
        for n in (155,156,158,160,162,164,166,168,170,172):
            rec=anchors['frames'][str(n)]
            if digest(folder/f'prepared_{n:03d}.png')!=rec['prepared_sha256']:raise ValueError('Head landmark belongs to different art')
            r=registered['frames'][str(n)];before_x=r['registration'][0]+rec['native_head_center_x'];dx=rec['target_world_head_x']-before_x
            before=contact_span(worlds[0][n]);worlds[0][n]=translate_body_x(worlds[0][n],dx);after=contact_span(worlds[0][n]);place(0,n)
            dash_contacts[str(n)]={**rec,'translate_x':dx,'before':before,'after':after,'floor_y_unchanged':before['floor_y']==after['floor_y'],'pixel_values_count_preserved':True}
    if 'burst' in groups:
        # The first charge stance is upright, matching the compact windup.
        rec=json.loads((OUT/'thrust/registered.json').read_text('utf-8'))['frames']['101']
        worlds[1][177]=world(read_indexed_png(OUT/'thrust'/rec['file'],words),rec['bounds'])
        idle=graphics_bank(g,0)['frames'][147];raw=decode_stream(g,idle['offset'],idle['limit'],idle['tile_count']*128).data;pic=compose_launch(raw,idle['tile_count'],composition_frame(oldparts,0,147));target=contact_span(world(pic[:2],pic[2]))['center_x']
        for n in range(177,190):
            worlds[1][n],contacts[str(n)]=align_contact_x(worlds[1][n],target);place(1,n)
        for target,source in ((183,182),(184,185),(187,186)):bind(1,target,source)
        for n in range(177,190):
            contacts[str(n)]['final_after_shared_binding']=contact_span(worlds[1][n])
        original=(ROOT/'work/ver_rin_nana/zero_extract/20261028T080358573477Z/original.arc').read_bytes();og=entry(original,2)[1];op=entry(original,3)[1];ow=struct.unpack_from('<16H',entry(original,9)[1])
        rgb=lambda v:np.array([(v>>s&31) for s in (0,5,10)],int)
        remap={i:1+int(np.argmin([np.sum((rgb(ow[i])-rgb(v))**2) for v in words[1:]])) for i in CHARGE_REMAP}
        for n,box in CHARGE_BOXES.items():
            f=graphics_bank(og,1)['frames'][n];raw=decode_stream(og,f['offset'],f['limit'],f['tile_count']*128).data;pic=compose_launch(raw,f['tile_count'],composition_frame(op,5,n));source=world(pic[:2],pic[2]);w=worlds[1][n];points=[]
            for y in range(box[1],box[3]):
                for x in range(box[0],box[2]):
                    old=int(source[128+y,128+x])
                    if old in remap:w[128+y,128+x]=remap[old];points.append([x,y,remap[old]])
            save_image(w.tobytes(),(256,256),words,OUT/'burst'/f'combined_{n}.png')
            place(1,n)
            if any(worlds[1][n][128+y,128+x]!=v for x,y,v in points):raise ValueError('Aura shape changed')
            aura[str(n)]={'pixels':len(points),'world_pixels':points,'palette_remap':remap}
    return parts,frames,{'shared_pose_bindings':bindings,'embedded_charge_aura':aura,'thrust_contact_registration':thrust_contacts,'dashslash_head_registration':dash_contacts,'burst_contact_registration':contacts},worlds
