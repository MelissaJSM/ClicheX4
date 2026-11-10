"""v3 흰 금속 확장과 원작 숫자 구멍의 픽셀별 독립 검사."""
import json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.hud_underlay_verify import digest,read_assets,sha,picture,TARGETS,TILES
from scripts.prepare_riko_ui import entry
from scripts.prepare_hud_emblems import all_compositions,composed
from scripts.discover_inputs import psx_arc
from src.psx_ui_atlas import tile_pixels
import scripts.hud_frame_underlay as maker
OUT=ROOT/'work/hud_frame_fix_20261105/underlay_white_v3'

def run():
    initial={p.relative_to(ROOT).as_posix():digest(p)for p in OUT.rglob('*')if p.is_file()and p.name!='independent.json'}
    code={n:digest(ROOT/'scripts'/n)for n in('hud_frame_underlay.py','hud_frame_fix.py')}
    original=ROOT/'MegaMan X4.bin';assert digest(original)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
    names=('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC');originals=read_assets(original,names)
    maker.WHITE_ONLY=True;maker.configure();results={};rejected=[];sources={original.relative_to(ROOT).as_posix():digest(original)}
    for project,(stem,expected_sha)in maker.SOURCES.items():
        proposal=json.loads((OUT/project/'proposal.json').read_text('utf8'));source=ROOT/proposal['baseline'];symbol_path=ROOT/'out'/project/'overhaul_20261105_candidate04'/(stem+'.bin')
        assert digest(source)==expected_sha==proposal['baseline_sha256']and digest(symbol_path)==maker.SYMBOL_SOURCES[project]
        sources[source.relative_to(ROOT).as_posix()]=expected_sha;sources[symbol_path.relative_to(ROOT).as_posix()]=maker.SYMBOL_SOURCES[project]
        before=read_assets(source,names);symbol_arcs=read_assets(symbol_path,names);resources={}
        for name in names:
            old=before[name];spec=proposal['files'][name];new=(ROOT/spec['path']).read_bytes()
            assert sha(old)==spec['before']and sha(new)==spec['after']and len(old)==len(new)==spec['size']
            old_rows,new_rows=psx_arc(old),psx_arc(new);clean=lambda rows:[{k:v for k,v in r.items()if k!='sha256'}for r in rows]
            assert clean(old_rows)==clean(new_rows)
            e=next(r for r in old_rows if int(r['type'],16)==0x10206);lo,hi=e['offset'],e['offset']+e['size']
            assert old[:lo]==new[:lo]and old[hi:]==new[hi:]
            ot,nt=entry(old,0x10206),entry(new,0x10206);comps=all_compositions(entry(old,3));users={}
            for key,c in comps.items():
                for p in c['parts']:users.setdefault(p['page']*256+p['tile'],set()).add(key)
            changed={n for n in range(len(ot)//128)if tile_pixels(ot,n)!=tile_pixels(nt,n)}
            assert changed==TILES[project][name]and all(users[n]<=TARGETS for n in changed)
            digits=[]
            for digit in range(10):
                a,az,ab=picture(old,59+digit);b,bz,bb=picture(new,59+digit)
                assert az==bz and ab==bb and np.array_equal(a,b);digits.append((a,ab))
            frames=[];count=0
            for n in range(69,78):
                a,az,box=picture(old,n);b,bz,bb=picture(new,n);native,nz,nb=picture(originals[name],n);symbol,sz,sb=picture(symbol_arcs[name],n)
                assert az==bz==nz==sz and box==bb==nb==sb;l,t=box[:2];under=a.copy()
                for y in range(24,41):
                    for x in range(-24,5):
                        value=0
                        if 25<=y<=38:
                            if -22<=x<=-15:value=int(native[y-t,-7-x-l])
                            elif -14<=x<=4:value=int(native[y-t,5-l])
                            if value==14:value=10
                            if x>=2:value=int(native[y-t,x-l])
                        elif y==24 and -18<=x<=2:value=int(native[y-t,x-l])
                        under[y-t,x-l]=value
                native_E=native==14;under_E=under==14
                assert np.array_equal(under_E,native_E)
                expected_count=56 if name=='PL01_U.ARC'else 51
                assert np.count_nonzero(under_E)==expected_count
                mask=np.zeros(a.shape,bool);mask[24-t:41-t,-24-l:2-l]=symbol[24-t:41-t,-24-l:2-l]>0
                assert not np.any(mask&native_E)
                expected=under.copy();expected[mask]=symbol[mask]
                assert np.array_equal(b,expected)
                symbol_E=mask&(symbol==14);assert np.array_equal(b==14,native_E|symbol_E)
                assert np.array_equal(b[mask],symbol[mask])
                assert np.array_equal(b[:24-t],a[:24-t])and np.array_equal(b[:,5-l:],a[:,5-l:])
                assert np.array_equal(b[25-t:39-t,2-l:],native[25-t:39-t,2-l:])
                assert int(b[31-t,0-l])==int(b[31-t,1-l])==10
                assert np.all(b[31-t,-22-l:16-l]>0)
                for glyph,db in digits:
                    yy,xx=np.nonzero(glyph);gy=yy+db[1]+32-t;gx=xx+db[0]+7-l
                    assert np.array_equal(a[gy,gx],b[gy,gx]);aa=a.copy();ba=b.copy();aa[gy,gx]=glyph[yy,xx];ba[gy,gx]=glyph[yy,xx]
                    assert np.array_equal(aa[gy,gx],ba[gy,gx]);count+=1
                ys,xs=np.where(native_E)
                frames.append({'frame':n,'changed_pixels':int(np.count_nonzero(a!=b)),'native_number_dark_pixels':expected_count,'native_dark_mask_sha256':sha(native_E.tobytes()),'number_dark_world_bbox_exclusive':[int(xs.min()+l),int(ys.min()+t),int(xs.max()+l+1),int(ys.max()+t+1)],'native_E_mask_coordinate_exact':True,'symbol_own_E_pixels_separately_preserved':int(symbol_E.sum()),'accepted_symbol_opaque_pixels_preserved':int(mask.sum()),'no_extra_E_outside_native_aperture_or_existing_symbol':True,'numeric_rim_x2plus_y25_38_exact_native':True,'former_counter_cap_x0_1_y31_is_white_A':True})
                if project=='ver_rin_nana'and name=='PL00_U.ARC'and n==69:
                    for case,xy,val in(('erase_aperture',(5,31),0),('extend_aperture',(5,24),14)):
                        invalid=a.copy();x,y=xy;invalid[y-t,x-l]=val
                        try:maker.desired(invalid,native,symbol,box)
                        except ValueError as error:assert str(error)=='Native dark life-number aperture changed';rejected.append(case)
                        else:raise AssertionError('Incorrect numeric aperture accepted')
            bank_count=int.from_bytes(entry(old,3)[:4],'little')//4;static={1,2,3,4,6}if bank_count==7 else{1,2,3,4,*range(9,bank_count)};protected=0
            for key,c in comps.items():
                if key[0]not in static or key in TARGETS:continue
                a,az,ab,_=composed(ot,c);b,bz,bb,_=composed(nt,c);assert az==bz and ab==bb and np.array_equal(a,b);protected+=1
            fresh,_=maker.patch(old);assert fresh==new
            wrong=bytearray(old);wrong[-1]^=1
            try:maker.patch(bytes(wrong))
            except ValueError as error:assert str(error)=='Unsupported source ARC';rejected.append(project+'/'+name+'/wrong_source')
            else:raise AssertionError('Wrong source accepted')
            resources[name]={'before_sha256':sha(old),'after_sha256':sha(new),'changed_private_tiles':sorted(changed),'other_tiles_and_static_frames_preserved':True,'non_target_static_frames_checked':protected,'nontexture_entries_CLUT_palette_coordinates_timing_audio_identical':True,'frames':frames,'digit_0_to_9_composite_checks':count,'reproduced_byte_identical':True}
        results[project]=resources
    assert initial=={p.relative_to(ROOT).as_posix():digest(p)for p in OUT.rglob('*')if p.is_file()and p.name!='independent.json'}
    assert all(digest(ROOT/p)==h for p,h in sources.items())and all(digest(ROOT/'scripts'/n)==h for n,h in code.items())
    report={'passed':True,'variant':'white_only_v3','resources':results,'HUD_frames':54,'digit_composite_checks':540,'negative_cases_rejected':rejected,'source_discs':sources,'source_discs_prepared_files_production_code_unchanged':True,'native_number_E_pixels':{'X_and_Ultimate':51,'Zero':56},'number_dark_mask_unchanged_by_one_pixel':True,'symbol_E_is_foreground_not_aperture':True,'comparison_png_viewed':True,'visual_assessment':'흰 금속부가 심볼 아래로 이어지고 숫자칸의 짙은 내부는 원래 위치와 크기에 머문다.','runtime_verified':False,'user_accepted':False,'limitations':['정적 검사이며 새 v3 BIN의 실제 GPU 및 화면 확인은 별도이다. 사용자 디자인 수용은 검사 통과와 구별한다.'],'writes':['scripts/hud_white_underlay_verify.py','work/hud_frame_fix_20261105/underlay_white_v3/independent.json']}
    (OUT/'independent.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'HUD_frames':54,'digits':540,'negative_rejected':len(rejected),'native_E_counts':[51,56]}))
if __name__=='__main__':run()
