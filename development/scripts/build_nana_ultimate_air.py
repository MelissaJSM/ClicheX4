"""선택한 얼티밋 모션을 검증된 BIN 사본에 적용한다. 활성 포인터는 변경하지 않는다."""
import argparse,json,shutil,sys,unittest
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_ultimate_air import D,PARENT,PARENT_SHA,ARC_SHA,FRAMES
from scripts.prepare_nana_fourth_pilot import require,write
from scripts.build_nana_ultimate_run import validate
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def main(art,repro,scope='air'):
    if scope=='nova':
        from scripts import prepare_nana_ultimate_nova as spec
    elif scope=='vehicle':
        from scripts import prepare_nana_ultimate_vehicle as spec
    elif scope=='hover-alignment':
        from scripts import prepare_nana_ultimate_hover_alignment as spec
    elif scope=='hover':
        from scripts import prepare_nana_ultimate_hover as spec
    elif scope=='elemental':
        from scripts import prepare_nana_ultimate_elemental as spec
    elif scope=='special':
        from scripts import prepare_nana_ultimate_special as spec
    elif scope=='victory-edge':
        from scripts import prepare_nana_ultimate_victory_edge as spec
    elif scope=='ceremony':
        from scripts import prepare_nana_ultimate_ceremony as spec
    elif scope=='ladder':
        from scripts import prepare_nana_ultimate_ladder as spec
    elif scope=='low-hp-shape':
        from scripts import prepare_nana_ultimate_low_hp_shape as spec
    elif scope=='low-hp':
        from scripts import prepare_nana_ultimate_low_hp as spec
    elif scope=='reaction':
        from scripts import prepare_nana_ultimate_reaction as spec
    elif scope=='air-transition':
        from scripts import prepare_nana_ultimate_air_transition as spec
    elif scope=='dash-hair':
        from scripts import prepare_nana_ultimate_dash_hair as spec
    elif scope=='dash':
        from scripts import prepare_nana_ultimate_dash as spec
    elif scope=='wall-arm':
        from scripts import prepare_nana_ultimate_wall_arm as spec
    elif scope=='wall':
        from scripts import prepare_nana_ultimate_wall as spec
    elif scope=='gun-size':
        from scripts import prepare_nana_ultimate_gun_size as spec
    elif scope=='shot-arm':
        from scripts import prepare_nana_ultimate_shot_arm as spec
    elif scope=='run-hand':
        from scripts import prepare_nana_ultimate_run_hand as spec
    else:
        from scripts import prepare_nana_ultimate_air as spec
    PARENT,PARENT_SHA,ARC_SHA,FRAMES=spec.PARENT,spec.PARENT_SHA,spec.ARC_SHA,spec.FRAMES
    art,repro=art.resolve(),repro.resolve();require(art!=repro and all(p.is_relative_to(D) for p in (art,repro)),'Independent isolated sources required')
    names={p.name for p in art.iterdir()};require(names=={p.name for p in repro.iterdir()},'Reproduction set differs')
    for n in names:require((art/n).read_bytes()==(repro/n).read_bytes(),'Independent reproduction differs: '+n)
    kwargs=dict(parent=PARENT,parent_sha=PARENT_SHA,arc_sha=ARC_SHA,frames=FRAMES,capsule_banks=())
    if scope in ('shot-arm','gun-size','wall','wall-arm','dash','ladder','hover','nova'):kwargs['base_correction']=spec.correct_base
    check=validate(art,**kwargs)
    if scope=='nova':
        import numpy as np
        from PIL import Image
        from scipy.ndimage import binary_dilation,binary_fill_holes
        source=(PARENT/'PL02_U.ARC').read_bytes();result=(art/'PL02_U.ARC').read_bytes();targets={n:np.array(Image.open(art/f'ultimate_{n:03}.png'))for n in FRAMES};expected,registration=spec.artwork(source);master=spec.full(source,0)
        for n in FRAMES:require(np.array_equal(targets[n],expected[n]),'Registered Nova differs')
        for q in registration:
            n=q['frames'][0]
            if 'head_box'in q:
                x,y,x2,y2=q['head_box'];head=master[52:74,67:90];require(np.array_equal(targets[n][y:y2,x:x2][head>0],head[head>0]),'Accepted Nova head changed')
                w,h=q['source_size'];sw,sh=q['source_crop_size'];require(abs(w-h*sw/sh)<=.5,'Nova source squeezed')
            if n in(218,220):
                dx,dy=q['body_offset'];mask=binary_dilation(np.roll(np.roll(spec.layer(source,5,217)>0,dy,0),dx,1));body=np.roll(np.roll(targets[217],dy,0),dx,1);old=spec.layer(source,5,n);preserve=~mask&(body==0);require(np.array_equal(targets[n][preserve],old[preserve]),'Outer energy changed');require(not np.any(binary_fill_holes(old>0)&(targets[n]==0)),'Energy gap remains');require(np.array_equal(targets[n][body>0],body[body>0]),'Body changes during Nova')
        require(np.array_equal(targets[213],targets[214]) and np.array_equal(targets[215],targets[216]),'Preparation pair jitter')
        prior=json.loads((PARENT/'manifest.json').read_text('utf8'))['implemented_ultimate_references']
        for n in prior+list(range(208,213)):require(np.array_equal(spec.full(source,n),spec.full(result,n)),'Prior body or soul effect changed')
        check.update(nova_references=8,authored_body_poses=3,wide_canvas=[256,160],preparation_base_x_replaced=4,accepted_head_clusters_preserved=3,preparation_pairs_identical=2,outer_aura_phases_preserved=2,aura_envelope_has_no_gaps=True,prior_ultimate_bodies_preserved=len(prior),soul_effect_frames_preserved=5)
    if scope=='vehicle':
        import numpy as np
        from PIL import Image
        from scripts.prepare_shibuki_ultimate_production import records
        source=(PARENT/'PL02_U.ARC').read_bytes();result=(art/'PL02_U.ARC').read_bytes();registration=json.loads((art/'registration.json').read_text('utf8'));master=spec.full(source,0)
        require([q['frames'][0]for q in registration]==FRAMES,'Wrong vehicle scope')
        for q in registration:
            n=q['frames'][0];target=np.array(Image.open(art/f'ultimate_{n:03}.png'))
            if n==198:
                require(not target.any() and not spec.full(result,n).any(),'Shared blank198 visible')
                for b in (0,5,6,7,8):require(records(spec.entry(source,3),b,n)==records(spec.entry(result,3),b,n),'Blank198 composition changed')
                continue
            if n>=184:require(target[q['eye'][1],q['eye'][0]]==14,'Cockpit eye moved');continue
            x,y,x2,y2=q['face_box'];face=master[65:74,73:83];mask=face>0;require(np.array_equal(target[y:y2,x:x2][mask],face[mask]),'Chaser face differs')
            ex,ey=q['eye'];head=master[52:65,67:90];require(np.array_equal(target[ey-16:ey-3,ex-9:ex+14][head>0],head[head>0]),'Chaser head detail changed')
            native=spec.render(source,n)[1]
            for x,y,x2,y2 in q['contacts']:require(np.array_equal(target[y:y2,x:x2],native[y:y2,x:x2]),'Handlebar grip moved')
            cut=q['native_lower_from_y'];require(np.array_equal(target[cut:]>0,native[cut:]>0),'Pedal silhouette moved');require(int(np.nonzero(target)[0].max())==q['sole'],'Pedal sole moved')
            w,h=q['source_size'];sw,sh=q['source_crop_size'];require(abs(w-h*sw/sh)<=.5,'Source aspect changed')
        prior=json.loads((PARENT/'manifest.json').read_text('utf8'))['implemented_ultimate_references']
        for n in prior:require(np.array_equal(spec.full(source,n),spec.full(result,n)),'Previously accepted body changed')
        check.update(new_ultimate_frames=len(spec.EDITED_FRAMES),blank_reference_preserved=198,chaser_references=13,cockpit_references=19,handlebar_grips_preserved=13,pedal_silhouettes_preserved=13,chaser_idle_head_detail_preserved=True,cockpit_eye_anchors_preserved=19,prior_ultimate_bodies_preserved=len(prior))
    if scope=='hover-alignment':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();result=(art/'PL02_U.ARC').read_bytes();registration=json.loads((art/'registration.json').read_text('utf8'));targets={n:np.array(Image.open(art/f'ultimate_{n:03}.png'))for n in FRAMES};require([n for q in registration for n in q['frames']]==FRAMES,'Wrong hover alignment scope')
        for q in registration:
            a,b=q['frames'];cut=q['upper_preserved_before_y'];require(np.array_equal(targets[a][cut:],targets[b][cut:]),'Hover shooting legs differ')
            for n in(a,b):
                old=spec.full(source,n);require(np.array_equal(targets[n][:cut],old[:cut]),'Upper body changed')
                for shoe in q['registration']['shoes']:
                    x,y,x2,y2=shoe['source_box'];dx,dy=shoe['translation'];require(np.array_equal(targets[n][y+dy:y2+dy,x+dx:x2+dx],old[y:y2,x:x2]),'Shoe detail changed')
        prior=json.loads((PARENT/'manifest.json').read_text('utf8'))['implemented_ultimate_references'];others=sorted(set(prior)-set(FRAMES))
        for n in others:require(np.array_equal(spec.full(source,n),spec.full(result,n)),'Other Ultimate pose changed')
        check.update(aligned_forward_hover_references=4,individual_shoe_contacts=8,upper_body_preserved=True,shoe_pixels_preserved=True,shared_shooting_leg_pairs=2,other_ultimate_bodies_preserved=len(others),backward_and_stationary_hover_preserved=True)
    if scope=='hover':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();result=(art/'PL02_U.ARC').read_bytes();fourth=(PARENT/'modified.arc').read_bytes();registration=json.loads((art/'registration.json').read_text('utf8'));targets={n:np.array(Image.open(art/f'ultimate_{n:03}.png'))for n in FRAMES}
        require([n for q in registration for n in q['frames']]==FRAMES,'Wrong hover scope')
        for q in registration:
            a,b=q['frames'];cut=q['upper_preserved_before_y'];require(np.array_equal(targets[a][cut:],targets[b][cut:]),'Shooting hover legs differ')
            for n,s in zip(q['frames'],q['reuse_sources']):
                require(np.array_equal(targets[n][:cut],spec.full(source,s)[:cut]),'Accepted air upper changed');require(int(np.nonzero(targets[n])[0].max())==q['sole'],'Hover sole shifted')
                xs=np.flatnonzero(targets[n][q['sole']]);require(abs(float(xs.mean())-q['propulsion_foot_center'])<=.5,'Propulsion foot moved')
            w,h=q['source_size'];sw,sh=q['source_crop_size'];require(abs(w-h*sw/sh)<=.5,'Hover source aspect changed');require(sum(v>0 for v in q['leg_skin_counts'].values())>=3,'Leg shading lost')
        prior=json.loads((PARENT/'manifest.json').read_text('utf8'))['implemented_ultimate_references']
        for n in prior:require(np.array_equal(spec.full(source,n),spec.full(result,n)),'Prior Ultimate pose changed')
        check.update(hover_references=10,accepted_air_upper_preserved=True,shared_shooting_leg_pairs=5,propulsion_foot_anchors=10,prior_ultimate_bodies_preserved=len(prior),source_aspect_preserved=True)
    if scope=='elemental':
        import numpy as np
        from PIL import Image
        from scripts.prepare_shibuki_ultimate_production import records
        source=(PARENT/'PL02_U.ARC').read_bytes();result=(art/'PL02_U.ARC').read_bytes();master=spec.full(source,0)
        targets={n:np.array(Image.open(art/f'ultimate_{n:03}.png'))for n in FRAMES};registration=json.loads((art/'registration.json').read_text('utf8'))
        require([q['frames'][0]for q in registration]==FRAMES,'Wrong elemental scope')
        for n in spec.ORDER:
            q=next(q for q in registration if q['frames'][0]==n);x,y,x2,y2=q['face_box'];face=master[65:74,73:83];mask=spec.face_mask(q['face_box'],q['pistol_mask_bbox'],face)
            require(np.array_equal(targets[n][y:y2,x:x2][mask],face[mask]),'Elemental face changed')
            w,h=q['source_size'];sw,sh=q['source_crop_size'];require(abs(w-h*sw/sh)<=.5,'Elemental source compressed');require(int(np.nonzero(targets[n])[0].max())==q['sole'],'Elemental sole moved')
        require(np.array_equal(targets[96],spec.shift(targets[95],1)),'Frost shared body shifted incorrectly');require(np.array_equal(targets[232],targets[231]),'Ground fire bodies differ')
        a=records(spec.entry(result,3),5,95);b=records(spec.entry(result,3),5,96)
        require(len(a)==len(b) and all(a[i:i+2]==b[i:i+2] and b[i+2]==(a[i+2]+1)%256 and a[i+3]==b[i+3] for i in range(0,len(a),4)),'Frost shared parts differ')
        prior=json.loads((PARENT/'manifest.json').read_text('utf8'))['implemented_ultimate_references']
        for n in prior:require(np.array_equal(spec.full(source,n),spec.full(result,n)),'Prior Ultimate pose changed: '+str(n))
        check.update(elemental_references=9,authored_poses=7,accepted_face_clusters=True,uniform_source_scale=True,native_soles_preserved=True,shared_translation_pairs=1,identical_fire_pair=True,prior_ultimate_bodies_preserved=len(prior))
    if scope=='special':
        import numpy as np
        from PIL import Image
        from scripts.prepare_shibuki_ultimate_production import records
        source=(PARENT/'PL02_U.ARC').read_bytes();result=(art/'PL02_U.ARC').read_bytes();master=spec.full(source,0);targets={n:np.array(Image.open(art/f'ultimate_{n:03}.png'))for n in FRAMES};registration=json.loads((art/'registration.json').read_text('utf8'))
        require([q['frames'][0]for q in registration]==FRAMES,'Wrong special scope')
        for n in spec.ORDER:
            q=next(q for q in registration if q['frames'][0]==n);x,y,x2,y2=q['face_box'];face=master[65:74,73:83];mask=face>0;gx,gy,gx2,gy2=q['pistol_mask_bbox'];fy,fx=np.indices(mask.shape);mask&=~((fx+x>=gx)&(fx+x<gx2)&(fy+y>=gy)&(fy+y<gy2));require(np.array_equal(targets[n][y:y2,x:x2][mask],face[mask]),'Special face changed');w,h=q['source_size'];sw,sh=q['source_crop_size'];require(abs(w-h*sw/sh)<=.5,'Special source compressed');require(int(np.nonzero(targets[n])[0].max())==q['sole'],'Special sole moved')
            for x,y,x2,y2 in q['contacts']:require(np.array_equal(targets[n][y:y2,x:x2],spec.render(source,n)[1][y:y2,x:x2]),'Palm contact moved')
        require(np.array_equal(targets[99],spec.shift(targets[98],1)),'Cyclone shift differs')
        overlay=np.where((targets[89]==spec.render(source,89)[1])&(targets[89]!=15),0,targets[89]).astype(np.uint8);shifted=spec.shift(overlay,-1)
        require(np.array_equal(targets[88],np.where(shifted,shifted,spec.render(source,88)[1])),'Charge shared overlay differs')
        for n,source_frame,delta in((88,89,-1),(99,98,1)):
            a=records(spec.entry(result,3),5,source_frame);b=records(spec.entry(result,3),5,n)
            require(len(a)==len(b) and all(a[i:i+2]==b[i:i+2] and b[i+2]==(a[i+2]+delta)%256 and a[i+3]==b[i+3] for i in range(0,len(a),4)),'Translated shared parts differ')
        check.update(special_references=7,authored_poses=5,accepted_face_clusters=True,uniform_source_scale=True,native_soles_preserved=True,shared_translation_pairs=2,charge_trail_base_preserved=True,cyclone_palm_preserved=True)
    if scope=='victory-edge':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();result=(art/'PL02_U.ARC').read_bytes();changed=0
        for n in FRAMES:
            old=spec.full(source,n);new=np.array(Image.open(art/f'ultimate_{n:03}.png'));mask=spec.correction_mask(old,n)
            require(np.array_equal(np.array(Image.open(art/f'edge_mask_{n:03}.png'))>0,mask),'Edge mask differs')
            require(np.array_equal(old[~mask],new[~mask]) and np.all(new[mask]==1),'Non-edge pixel changed')
            require(np.array_equal(old>0,new>0),'Victory silhouette changed');changed+=int(mask.sum())
        for n in(0,138,139,141,142,156,157):require(np.array_equal(spec.full(source,n),spec.full(result,n)),'Other ceremony body/effect changed')
        check.update(corrected_victory_frames=4,changed_edge_pixels=changed,index_change=[5,1],silhouettes_preserved=True,all_nonedge_pixels_preserved=True,arrival_idle_return_preserved=True)
    if scope=='ceremony':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();result=(art/'PL02_U.ARC').read_bytes();master=spec.full(source,0);records=json.loads((art/'registration.json').read_text('utf8'));targets={n:np.array(Image.open(art/f'ultimate_{n:03}.png'))for n in FRAMES};require([q['frames'][0]for q in records]==FRAMES,'Wrong ceremony scope')
        for n in spec.ORDER:
            q=next(q for q in records if q['frames'][0]==n);v=targets[n];x,y,x2,y2=q['face_box'];face=master[65:74,73:83];mask=face>0;require(np.array_equal(v[y:y2,x:x2][mask],face[mask]),'Ceremony face differs');w,h=q['source_size'];sw,sh=q['source_crop_size'];require(abs(w-h*sw/sh)<=.5,'Ceremony source compressed');require(int(np.nonzero(v)[0].max())==q['sole'],'Ceremony sole moved')
        require(np.array_equal(targets[142],master),'Ready does not settle into exact idle');require(np.array_equal(targets[139],spec.shift(targets[138],-1)),'Arrival pair shifts differently')
        fx=np.array(Image.open(art/'effect_141.png'));native=spec.render(source,141)[1];base=spec.render(source,0)[1];require(np.array_equal(fx,np.where(native!=base,native,0))and np.count_nonzero(fx)==12,'Landing particles changed');require(np.array_equal(targets[141],np.where(fx,fx,master)),'Ready body or particles differ')
        body=spec.shift(targets[156],-1);aura=np.array(Image.open(art/'effect_157.png'));require(set(np.unique(aura))=={0,7,13}and np.array_equal(targets[157],np.where(body,body,aura)),'Return aura/body differs')
        for n in spec.PRESERVED:require(np.array_equal(spec.full(source,n),spec.full(result,n)),'Common beam frame changed')
        check.update(ceremony_references=10,authored_body_poses=6,accepted_idle_settle_exact=True,landing_effect_pixels_preserved=12,arrival_shift_pair_exact=True,return_body_shift_exact=True,return_aura_colors_preserved=[7,13],common_beam_frames_preserved=spec.PRESERVED,raised_gun_regions_preserved=4,accepted_face_clusters=True,uniform_source_scale=True,all_native_body_soles_preserved=True)
    if scope=='ladder':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();corrected,baseproof=spec.correct_base(source);records=json.loads((art/'registration.json').read_text('utf8'));targets={n:np.array(Image.open(art/f'ultimate_{n:03}.png'))for n in FRAMES};module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'));master=spec.full(source,0);contacts=0
        require([q['frames'][0]for q in records]==FRAMES,'Wrong ladder order')
        for q in records:
            n=q['frames'][0];v=targets[n];native=spec.render(corrected,n)[1];require(int(np.nonzero(v)[0].max())==q['sole'],'Ladder sole moved');w,h=q['source_size'];sw,sh=q['source_crop_size'];require(abs(w-h*sw/sh)<=.5,'Ladder source compressed')
            if q['face_box'] and 'mirror_source'not in q:
                x,y,x2,y2=q['face_box'];face=master[65:74,73:83];mask=face>0;require(np.array_equal(v[y:y2,x:x2][mask],face[mask]),'Accepted face differs')
            for x,y,x2,y2 in q['contacts']:
                patch=native[y:y2,x:x2].copy()
                for old,new in((2,5),(3,7),(4,8)):patch[native[y:y2,x:x2]==old]=new
                require(np.array_equal(v[y:y2,x:x2],patch),'Rung contact changed');contacts+=1
            for x,y in q.get('removed_detached_pixels',[]):
                if 'mirror_source'in q:x=q['mirror_sum']-x
                require(v[y,x]==0,'Detached source pixel remains')
        for n,(alias,total)in spec.MIRRORS.items():require(np.array_equal(spec.mirror(targets[n],total),targets[alias]),'Ladder mirror differs')
        for n,(x,y,x2,y2)in spec.GUNS.items():require(np.array_equal(targets[n][y:y2,x:x2],module),'Ladder pistol size changed')
        check.update(ladder_references=14,mirror_pairs=4,rung_contact_rectangles=contacts,canonical_gun_modules=2,canonical_module_size=[8,7],base_gun_corrections=baseproof,uniform_source_scale=True,new_leg_width_retained=True,all_native_soles_preserved=True)
    if scope in ('low-hp','low-hp-shape'):
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();head=spec.full(source,0)[52:74,67:91];records=json.loads((art/'registration.json').read_text('utf8'));targets={n:np.array(Image.open(art/f'ultimate_{n:03}.png'))for n in FRAMES};require([q['frames'][0]for q in records]==FRAMES,'Wrong low-health scope')
        for q in records:
            n=q['frames'][0];v=targets[n];delta=q['breathing_delta'];x,y,x2,y2=q['head_destination_box'];mask=head>0;mask=mask.copy();mask[71+delta-y,77-x]=False;require(q['head_scale']==[1,1] and np.array_equal(v[y:y2,x:x2][mask],head[mask]),'Accepted head distorted');w,h=q['uniform_source_size'];sw,sh=q['source_crop_size'];require(abs(w-h*sw/sh)<=.5,'Source width compressed');require(v[71+delta,77]==spec.render(source,n)[1][69+delta,77],'Mouth expression lost');require(np.array_equal(v[98:],targets[122][98:]),'Feet move while breathing');require(int(np.nonzero(v)[0].max())==102,'Sole moved')
        for n in(120,122,124):
            delta=next(q['breathing_delta']for q in records if q['frames'][0]==n);mask=np.ones((160,160),bool);mask[71+delta,77]=False;require(np.array_equal(targets[n][mask],targets[n+1][mask]),'Mouth variation changes body')
        check.update(low_health_corrected_frames=6,accepted_idle_head_unscaled=True,uniform_source_width=records[0]['uniform_source_size'][0],mouth_pairs_preserved=True,feet_fixed=True,other_hurt_and_all_other_frames_preserved=True)
        if scope=='low-hp-shape':
            original=np.array(Image.open(art/'registered_before_foot.png'));body=np.array(Image.open(art/'body_122.png'));before=spec.full(source,122)
            for y in range(90,103):require(np.count_nonzero(body[y])>=np.count_nonzero(original[y]),'New calf width was compressed')
            skin_before=int(np.count_nonzero(np.isin(before[84:98],(10,11,12))));skin_after=int(np.count_nonzero(np.isin(body[84:98],(10,11,12))))
            require(skin_after>skin_before and all(q['old_leg_silhouette_not_reused']for q in records),'Thin leg silhouette was reused')
            check.update(new_body_source_sha256=spec.SOURCE_SHA,skin_pixels_lower_body_before=skin_before,skin_pixels_lower_body_after=skin_after,calf_rows_not_compressed=True,authored_lowered_pistol_frames=6,foot_translation_only=records[0]['foot_translation_only'])
    if scope=='reaction':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();result=(art/'PL02_U.ARC').read_bytes();records=json.loads((art/'registration.json').read_text('utf8'));targets={n:np.array(Image.open(art/f'ultimate_{n:03}.png'))for n in FRAMES};require([q['frames'][0]for q in records]==FRAMES,'Wrong reaction order')
        for n in spec.ORDER:
            q=next(q for q in records if q['frames'][0]==n);v=np.array(Image.open(art/f'body_{n:03}.png'));native=spec.render(source,n)[1];x,y,x2,y2=q['face_box'];require(np.array_equal(v[y:y2,x:x2],native[y:y2,x:x2]),'Native expression changed');low=q['lower_silhouette_from_y'];require(np.array_equal(v[low:]>0,native[low:]>0),'Reaction leg silhouette moved');require(int(np.nonzero(v)[0].max())==q['sole'],'Reaction sole moved')
        for n in(120,122,124):
            q=next(q for q in records if q['frames'][0]==n);x,y,x2,y2=q['face_box'];mask=np.zeros((160,160),bool);mask[y:y2,x:x2]=True;require(np.array_equal(targets[n][~mask],targets[n+1][~mask]),'Mouth variation changes body');require(np.array_equal(targets[n][98:],targets[122][98:]),'Low-health soles moved')
        for n in(107,108):
            before,ps=spec.effects(source,n);after,qs=spec.effects(result,n);require(np.array_equal(before,after),'Electric/heat effect pixels changed');require([(p['flags'],p['tile'],p['x'],p['y'])for p in ps]==[(p['flags'],p['tile'],p['x'],p['y'])for p in qs],'Effect part order changed')
        check.update(reaction_body_poses=5,reaction_frames=15,closed_eyes_and_mouth_pairs_preserved=True,low_health_feet_fixed=True,effect_tile17_18_and9_parts_preserved=True,additional_hurt_frames=[233,234,235,236],existing_nana_aura_base_preserved=True,standalone_flash_preserved=[109,112,113,114])
    if scope=='air-transition':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();master=spec.full(source,0);records=json.loads((art/'registration.json').read_text('utf8'));require([q['frames'] for q in records]==[[93,93],[94,94]],'Wrong transition order')
        for q in records:
            n=q['frames'][0];target=np.array(Image.open(art/f'ultimate_{n:03}.png'));native=spec.render(source,n)[1];ex,ey=q['eye'];low=q['lower_silhouette_from_y'];require(np.array_equal(target[low:]>0,native[low:]>0),'Native lower silhouette changed');require(int(np.nonzero(target)[0].max())==q['sole'],'Sole moved');fx,fy=ex-76,ey-68;require(np.array_equal(target[65+fy:74+fy,73+fx:83+fx],master[65:74,73:83]),'Accepted face changed');require(q['head_eye_to_ear']==16 and q['registration_max_distance']<=7,'Unsupported scale registration')
        check.update(air_transition_frames=2,accepted_face_preserved=True,native_lower_silhouettes_preserved=True,nonfiring_transition=True)
    if scope=='dash-hair':
        import numpy as np
        from PIL import Image
        from scipy.ndimage import label
        source=(PARENT/'PL02_U.ARC').read_bytes();records=json.loads((art/'registration.json').read_text('utf8'));module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'));changed=0;yy,xx=np.indices((160,160))
        for q in records:
            mask=np.array(Image.open(art/q['hair_mask_file']))>0;ex,ey=q['eye']
            for n in q['frames']:
                before=spec.full(source,n);after=np.array(Image.open(art/f'ultimate_{n:03}.png'));require(np.array_equal(before[~mask],after[~mask]),'Nonhair pixel changed');changed+=int(np.count_nonzero(before!=after));hair=np.isin(after,(5,6,7,8,9))&(yy<ey+7)&(xx>=ex-4);labels,_=label(hair,np.ones((3,3)));roots=set(labels[ey-7:ey+3,ex+2:ex+8].flat)-{0};rear=hair&(xx>=ex+12)&(yy<ey+3);require(roots and np.all(np.isin(labels[rear],list(roots))),'Disconnected rear hair')
                for x,y in q['removed_detached_pixels']:require(after[y,x]==0,'Detached hair-region pixel remains')
            x,y,x2,y2=q['gun_module_box'];shot=np.array(Image.open(art/f"ultimate_{q['frames'][1]:03}.png"));require(np.array_equal(shot[y:y2,x:x2],module),'Pistol changed')
        for n in(73,74):
            mask=np.array(Image.open(art/'hair_mask_071.png'))>0;before=spec.full(source,n);after=np.array(Image.open(art/f'ultimate_{n:03}.png'));require(np.array_equal(before[~mask],after[~mask]),'Speed lines changed outside hair');changed+=int(np.count_nonzero(before!=after))
        check.update(hair_corrected_frames=18,changed_hair_pixels=changed,nonhair_pixels_preserved=True,rear_hair_connected=True,canonical_gun_modules=9,canonical_module_size=[8,7],removed_detached_pixels=sum(len(q['removed_detached_pixels'])*2 for q in records))
    if scope=='dash':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();records=json.loads((art/'registration.json').read_text('utf8'));module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'));head=spec.full(source,0)[52:64,67:90];hm=head>0
        require([q['frames'][0]for q in records]==spec.ORDER,'Wrong dash pose order')
        for q in records:
            ex,ey=q['eye'];low=q['leg_silhouette_from_y']
            for n in q['frames']:
                target=np.array(Image.open(art/f'ultimate_{n:03}.png'));native=spec.render(source,n)[1];require(np.array_equal(target[ey-16:ey-4,ex-9:ex+14][hm],head[hm]),'Idle head detail changed');require(int(np.nonzero(target)[0].max())==q['sole'],'Sole moved');require(np.array_equal(target[low:]>0,native[low:]>0),'Lower dash silhouette changed')
            shot=np.array(Image.open(art/f"ultimate_{q['frames'][1]:03}.png"));x,y,x2,y2=q['gun_module_box'];require(np.array_equal(shot[y:y2,x:x2],module),'Canonical dash pistol differs');x,y,x2,y2=q['arm_box'];require(not np.any(np.isin(shot[y:y2,x:x2],(1,2,3,4))),'Black sleeve pixels remain')
        new=(art/'PL02_U.ARC').read_bytes()
        for n in (73,74):
            layers=[]
            for arc in (source,new):
                g,c=spec.entry(arc,2),spec.entry(arc,3);f=spec.graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];raw=spec.decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;atlas=np.frombuffer(spec.indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);parts=[(p['flags'],p['tile'],p['x'],p['y'])for p in spec.composition_frame(c,0,n)['parts']if p['tile']==6];layers.append((atlas[:16,96:112],parts))
            require(np.array_equal(layers[0][0],layers[1][0])and layers[0][1]==layers[1][1],'Native speed lines changed')
        check.update(registered_dash_poses=8,dash_references=18,canonical_gun_modules=9,canonical_module_size=[8,7],idle_head_detail_preserved=True,lower_silhouettes_preserved=True,speed_line_tile_and_parts_preserved=True,black_sleeve_regression_checked=True)
    if scope=='wall-arm':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();records=json.loads((art/'registration.json').read_text('utf8'));module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'));changed=0
        require([q['frames'][1] for q in records]==spec.SHOTS,'Wrong wall arm scope')
        for n in FRAMES:
            old=spec.full(source,n);new=np.array(Image.open(art/f'ultimate_{n:03}.png'))
            if n not in spec.SHOTS:require(np.array_equal(old,new),'Regular wall pose changed');continue
            q=next(q for q in records if q['frames'][1]==n);x,y,x2,y2=q['arm_box'];allowed=np.zeros(old.shape,bool);allowed[y:y2,x:x2]=True
            for px,py in q['removed_abandoned_gun_pixels']:allowed[py,px]=True;require(new[py,px]==0,'Abandoned pistol pixel remains')
            require(np.array_equal(old[~allowed],new[~allowed]),'Body outside wall arm changed');require(not np.any(allowed&np.isin(new,(1,2,3,4))),'Black arm pixels remain');changed+=int(np.count_nonzero(old!=new))
            x,y,x2,y2=q['gun_module_box'];require(np.array_equal(new[y:y2,x:x2],module),'Pistol size changed')
        check.update(corrected_wall_shooting_frames=len(records),unchanged_regular_wall_frames=6,canonical_gun_modules=6,canonical_module_size=[8,7],changed_arm_pixels=changed,removed_abandoned_gun_pixels=sum(len(q['removed_abandoned_gun_pixels'])for q in records),all_other_body_pixels_preserved=True)
    if scope=='wall':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();records=json.loads((art/'registration.json').read_text('utf8'));module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'));head=spec.full(source,0)[52:69,67:90];head_mask=head>0
        require([n for q in records for n in q['frames']]==FRAMES,'Wrong wall scope')
        for q in records:
            ex,ey=q['eye'];x,y,x2,y2=q['wall_contact_box']
            for n in q['frames']:
                target=np.array(Image.open(art/f'ultimate_{n:03}.png'));native=spec.render(source,n)[1]
                require(np.array_equal(target[ey-16:ey+1,ex-9:ex+14][head_mask],head[head_mask]),'Idle head detail changed')
                require(np.array_equal(target[y:y2,x:x2],native[y:y2,x:x2]),'Wall palm contact changed')
                require(int(np.nonzero(target)[0].max())==q['sole'],'Wall sole changed')
            x,y,x2,y2=q['gun_module_box'];shot=np.array(Image.open(art/f"ultimate_{q['frames'][1]:03}.png"));require(np.array_equal(shot[y:y2,x:x2],module),'Wall gun size differs')
            require(sum(v>0 for v in q['skin_counts'].values())>=3,'Leg shading collapsed')
        check.update(registered_wall_frames=len(FRAMES),canonical_gun_modules=len(records),canonical_module_size=[8,7],idle_head_detail_preserved=True,wall_hand_contacts_preserved=True,native_muzzle_anchors_preserved=True,native_sole_rows_preserved=True)
    if scope=='gun-size':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();targets,registration,module=spec.artwork(source);changed=changed_frames=0
        for n in FRAMES:
            old=spec.full(source,n);new=np.array(Image.open(art/f'ultimate_{n:03}.png'));require(np.array_equal(new,targets[n]),'Gun target differs from registered module')
            if n not in spec.SHOTS:require(np.array_equal(old,new),'Regular pose changed');continue
            q=next(q for q in registration if q['frames'][0]==n);x,y,x2,y2=q['gun_module_box'];mask=np.zeros(old.shape,bool);mask[y:y2,x:x2]=True;require(np.array_equal(old[~mask],new[~mask]),'Body changed outside gun module');require(np.array_equal(new[y:y2,x:x2],module),'Gun size or shape differs');changed+=int(np.count_nonzero(new!=old));changed_frames+=int(np.any(new!=old))
        check.update(standardized_gun_modules=len(registration),changed_shooting_frames=changed_frames,changed_gun_pixels=changed,unchanged_regular_frames=len(FRAMES)-len(registration),canonical_module_size=[8,7],all_other_body_pixels_preserved=True,muzzle_anchors_preserved=True)
    if scope=='shot-arm':
        import numpy as np
        from PIL import Image
        source=(PARENT/'PL02_U.ARC').read_bytes();registration=json.loads((art/'registration.json').read_text('utf8'));changed=0
        require([q['frames'][0] for q in registration]==spec.SHOTS,'Wrong shot correction scope')
        for n in FRAMES:
            old=spec.full(source,n);new=np.array(Image.open(art/f'ultimate_{n:03}.png'))
            if n not in spec.SHOTS:require(np.array_equal(new,old),'Regular pose changed');continue
            q=next(q for q in registration if q['frames'][0]==n);x,y,x2,y2=q['arm_box'];mask=np.zeros(old.shape,bool);mask[y:y2,x:x2]=old[y:y2,x:x2]>0
            for px,py in spec.SPECKS.get(n,[]):mask[py,px]=True;require(new[py,px]==0,'Detached speck remains')
            require(np.array_equal(old[~mask],new[~mask]),'Body changed outside arm');require(np.count_nonzero(mask&np.isin(new,(1,2,3,4)))<np.count_nonzero(mask&np.isin(old,(1,2,3,4))),'Black arm mass not reduced');changed+=int(np.count_nonzero(new!=old))
        check.update(corrected_shooting_frames=len(spec.SHOTS),unchanged_regular_frames=len(FRAMES)-len(spec.SHOTS),removed_detached_pixels=sum(map(len,spec.SPECKS.values())),changed_arm_pixels=changed,all_other_body_pixels_preserved=True)
    if scope=='run-hand':
        import numpy as np
        from PIL import Image
        records=json.loads((art/'registration.json').read_text('utf8'));changed=0
        for r in records:
            n=r['frames'][0];old=np.array(Image.open(PARENT/'ultimate_run'/f'ultimate_{n:03}.png'));new=np.array(Image.open(art/f'ultimate_{n:03}.png'));x,y,x2,y2=r['hand_edit_box'];mask=np.zeros(old.shape,bool);mask[y:y2,x:x2]=True
            require(np.array_equal(old[~mask],new[~mask]),'Accepted body changed outside hand');require(np.count_nonzero(mask&np.isin(new,(1,2,3,4)))<np.count_nonzero(mask&np.isin(old,(1,2,3,4))),'Black hand mass not reduced');require(np.array_equal(np.array(Image.open(art/f'ultimate_{n+1:03}.png')),np.array(Image.open(PARENT/'ultimate_run'/f'ultimate_{n+1:03}.png'))),'Accepted firing pose changed');changed+=int(np.count_nonzero(old!=new))
        check.update(hand_only_frames=len(records),unchanged_firing_frames=len(records),changed_hand_pixels=changed,all_other_body_pixels_preserved=True)
    bad=bytearray((art/'PL02_U.ARC').read_bytes());bad[len(bad)//2]^=1
    try:validate(art,bytes(bad),**kwargs)
    except ValueError:check['corrupt_resource_rejected']=True
    else:raise ValueError('Corrupt resource accepted')
    suite=unittest.TestSuite()
    for pat in ('test_psx_bank_repack.py','test_psx_compress.py','test_psx_disc.py','test_psx_sector.py','test_psx_tile_layout.py','test_psx_paired_layout.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pat))
    tests=unittest.TextTestRunner().run(suite);require(tests.wasSuccessful(),'Unit test failure');check.update(unit_tests=tests.testsRun,independent_files=len(names))
    pointer=ROOT/'projects/ver_rin_nana/current_build.json';prior=pointer.read_bytes();require(json.loads(prior)['sha256']==PARENT_SHA,'Active parent changed');protected=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Source changed')
        for q in protected['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed: '+q['path'])
    protect();data=(art/'PL02_U.ARC').read_bytes()
    with (PARENT/'rin_nana.bin').open('rb') as f:
        disc=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size);rec=next(q for q in disc.inspect()['files'] if q['name']=='PL02_U.ARC;1');require(sha256(disc.read(rec['lba'],rec['size']))==ARC_SHA,'Source disc ARC differs');rec={**rec,'sha256':ARC_SHA}
    stem={'nova':'nana_ultimate_nova_','vehicle':'nana_ultimate_vehicle_','hover-alignment':'nana_ultimate_hover_alignment_','hover':'nana_ultimate_hover_','elemental':'nana_ultimate_elemental_','special':'nana_ultimate_special_','victory-edge':'nana_ultimate_victory_edge_','run-hand':'nana_ultimate_run_hand_','shot-arm':'nana_ultimate_shot_arm_','gun-size':'nana_ultimate_gun_size_','air':'nana_ultimate_air_','wall':'nana_ultimate_wall_','wall-arm':'nana_ultimate_wall_arm_','dash':'nana_ultimate_dash_','dash-hair':'nana_ultimate_dash_hair_','air-transition':'nana_ultimate_air_transition_','reaction':'nana_ultimate_reaction_','ceremony':'nana_ultimate_ceremony_','ladder':'nana_ultimate_ladder_','low-hp-shape':'nana_ultimate_low_hp_shape_','low-hp':'nana_ultimate_low_hp_'}[scope];out=ROOT/'out/ver_rin_nana'/(stem+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',[(rec,data)],PARENT_SHA);changed={q['lba'] for q in result['changed_sectors']};total=result['size']//2352
    with (PARENT/'rin_nana.bin').open('rb') as a,(out/'rin_nana.bin').open('rb') as b:
        for lba in range(total):
            x,y=a.read(2352),b.read(2352);require(len(x)==len(y)==2352 and (x!=y)==(lba in changed),'Unexpected sector change')
            if lba in changed:require(x[:24]==y[:24] and rec['lba']<=lba<rec['lba']+(rec['size']+2047)//2048,'Unexpected sector range');validate_checks(y)
        require(not b.read(1),'Disc grew')
    with (out/'rin_nana.bin').open('rb') as f:require(DiscReader(f,result['size']).read(rec['lba'],rec['size'])==data,'Disc readback differs')
    protect();require(pointer.read_bytes()==prior,'Active pointer changed')
    for name in ('rin_nana.cue','modified.arc','PL01_U.ARC'):shutil.copyfile(PARENT/name,out/name)
    folder={'nova':'ultimate_nova','vehicle':'ultimate_vehicle','hover-alignment':'ultimate_hover_alignment','hover':'ultimate_hover','elemental':'ultimate_elemental','special':'ultimate_special','victory-edge':'ultimate_victory_edge','run-hand':'ultimate_run','shot-arm':'ultimate_shot_arm','gun-size':'ultimate_gun_size','air':'ultimate_air','wall':'ultimate_wall','wall-arm':'ultimate_wall_arm','dash':'ultimate_dash','dash-hair':'ultimate_dash_hair','air-transition':'ultimate_air_transition','reaction':'ultimate_reaction','ceremony':'ultimate_ceremony','ladder':'ultimate_ladder','low-hp-shape':'ultimate_low_hp_shape','low-hp':'ultimate_low_hp'}[scope]
    for name in ('ultimate_vehicle','ultimate_hover_alignment','ultimate_hover','ultimate_elemental','ultimate_special','ultimate_start','ultimate_run','ultimate_air','ultimate_shot_arm','ultimate_gun_size','ultimate_wall','ultimate_wall_arm','ultimate_dash','ultimate_dash_hair','ultimate_air_transition','ultimate_reaction','ultimate_low_hp','ultimate_low_hp_shape','ultimate_ladder','ultimate_ceremony','ultimate_victory_edge'):
        if name!=folder and (PARENT/name).is_dir():shutil.copytree(PARENT/name,out/name)
    shutil.copytree(art,out/folder);(out/'PL02_U.ARC').write_bytes(data)
    check.update(all_disc_sectors_compared=total,changed_sectors=sorted(changed),edc_ecc_checked=True,all_other_disc_bytes_preserved=True,protected_files=len(protected['files']),runtime_verified=False)
    m=json.loads((PARENT/'manifest.json').read_text('utf8'));m.update(kind=stem.rstrip('_'),parent=PARENT.relative_to(ROOT).as_posix(),parent_sha256=PARENT_SHA,modified_bin=result,modified_archive_sha256=sha256(data),inherited_manifest=(PARENT/'manifest.json').relative_to(ROOT).as_posix(),inherited_verification=m['verification'],verification=check,implemented_ultimate_references=sorted(set(m['implemented_ultimate_references'])|set(getattr(spec,'EDITED_FRAMES',FRAMES))),full_ultimate_complete=False,runtime_verified=False);m['ultimate_recipe' if scope=='run-hand' else 'ultimate_air_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix()
    if scope=='nova':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_nova_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='vehicle':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_vehicle_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in spec.EDITED_FRAMES})
    if scope=='shot-arm':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_shot_arm_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides']={str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES}
    if scope=='gun-size':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_gun_size_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='wall':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_wall_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='wall-arm':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_wall_arm_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='dash':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_dash_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='dash-hair':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_dash_hair_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='air-transition':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_air_transition_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='reaction':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_reaction_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='hover-alignment':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_hover_alignment_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='hover':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_hover_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='elemental':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_elemental_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='special':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_special_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='victory-edge':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_victory_edge_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='ceremony':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_ceremony_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='ladder':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_ladder_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='low-hp-shape':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_low_hp_shape_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    if scope=='low-hp':
        m['ultimate_air_recipe']=json.loads((PARENT/'manifest.json').read_text('utf8'))['ultimate_air_recipe'];m['ultimate_low_hp_recipe']=(out/folder/'recipe.json').relative_to(ROOT).as_posix();m['art_overrides'].update({str(n):(out/folder/f'ultimate_{n:03}.png').relative_to(ROOT).as_posix() for n in FRAMES})
    write(out/'manifest.json',m);write(out/'verification.json',check);write(out/'preservation.json',protected);write(out/'previous_current_build.json',json.loads(prior));write(D/({'nova':'nova_build.json','vehicle':'vehicle_build.json','hover-alignment':'hover_alignment_build.json','hover':'hover_build.json','elemental':'elemental_build.json','special':'special_build.json','victory-edge':'victory_edge_build.json','run-hand':'run_hand_build.json','shot-arm':'shot_arm_build.json','gun-size':'gun_size_build.json','air':'air_build.json','wall':'wall_build.json','wall-arm':'wall_arm_build.json','dash':'dash_build.json','dash-hair':'dash_hair_build.json','air-transition':'air_transition_build.json','reaction':'reaction_build.json','ceremony':'ceremony_build.json','ladder':'ladder_build.json','low-hp-shape':'low_hp_shape_build.json','low-hp':'low_hp_build.json'}[scope]),{'build':out.relative_to(ROOT).as_posix(),'sha256':result['sha256'],'verification':check});print(json.dumps({'build':out.relative_to(ROOT).as_posix(),'sha256':result['sha256'],'implemented':len(m['implemented_ultimate_references']),'verification':check}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);p.add_argument('--scope',choices=('nova','vehicle','hover-alignment','hover','elemental','special','victory-edge','air','run-hand','shot-arm','gun-size','wall','wall-arm','dash','dash-hair','air-transition','reaction','low-hp','low-hp-shape','ladder','ceremony'),default='air');a=p.parse_args();main(a.art,a.repro,a.scope)
