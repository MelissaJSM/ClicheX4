"""연속 HUD 몸체를 원작/원심볼과 독립 대조한다. 게임과 제작 입력은 읽기 전용."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.prepare_riko_ui import entry
from scripts.prepare_hud_emblems import composed,all_compositions
from src.psx_ui_atlas import tile_pixels
import scripts.hud_frame_underlay as maker

OUT=ROOT/'work/hud_frame_fix_20261105/underlay_v2'
TARGETS={(1,n)for n in range(69,78)}
TILES={'ver_buki_riko':{'PL00_U.ARC':{205,206,213,214},'PL01_U.ARC':{469,470,471,472},'PL02_U.ARC':{205,206,213,214}},'ver_rin_nana':{'PL00_U.ARC':{252,253,254,431},'PL01_U.ARC':{469,470,471,472},'PL02_U.ARC':{252,253,254,431}}}
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def read_assets(p,names):
    with p.open('rb')as f:
        d=DiscReader(f,p.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']}
        return {n:d.read(rs[n]['lba'],rs[n]['size'])for n in names}
def picture(arc,number):return composed(entry(arc,0x10206),all_compositions(entry(arc,3))[1,number])[:3]
def run():
    protected={p.relative_to(ROOT).as_posix():digest(p)for p in OUT.rglob('*')if p.is_file()and p.name!='independent.json'}
    script_hashes={n:digest(ROOT/'scripts'/n)for n in('hud_frame_underlay.py','hud_frame_fix.py')}
    original=ROOT/'MegaMan X4.bin';assert digest(original)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
    names=('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC');native=read_assets(original,names)
    maker.load_context();results={};rejected=[];inputs={original.relative_to(ROOT).as_posix():digest(original)}
    for project,(stem,source_sha)in maker.SOURCES.items():
        proposal=json.loads((OUT/project/'proposal.json').read_text('utf8'))
        source=ROOT/proposal['baseline'];assert digest(source)==source_sha==proposal['baseline_sha256']
        symbol_path=ROOT/'out'/project/'overhaul_20261105_candidate04'/(stem+'.bin');assert digest(symbol_path)==maker.SYMBOL_SOURCES[project]
        inputs[source.relative_to(ROOT).as_posix()]=source_sha;inputs[symbol_path.relative_to(ROOT).as_posix()]=maker.SYMBOL_SOURCES[project]
        old=read_assets(source,names);symbols=read_assets(symbol_path,names);details={}
        for name in names:
            before=old[name];after=(ROOT/proposal['files'][name]['path']).read_bytes();spec=proposal['files'][name]
            assert sha(before)==spec['before']and sha(after)==spec['after']and len(before)==len(after)==spec['size']
            arows,brows=psx_arc(before),psx_arc(after)
            layout=lambda rows:[{k:v for k,v in r.items()if k!='sha256'}for r in rows]
            assert layout(arows)==layout(brows)
            rec=next(r for r in arows if int(r['type'],16)==0x10206);a,b=rec['offset'],rec['offset']+rec['size']
            assert before[:a]==after[:a]and before[b:]==after[b:]
            ot,nt=entry(before,0x10206),entry(after,0x10206);parts=all_compositions(entry(before,3));users={}
            for k,c in parts.items():
                for p in c['parts']:users.setdefault(p['page']*256+p['tile'],set()).add(k)
            changed_tiles={n for n in range(len(ot)//128)if tile_pixels(ot,n)!=tile_pixels(nt,n)}
            assert changed_tiles==TILES[project][name]and all(users[t]<=TARGETS for t in changed_tiles)
            digits=[];frame_reports=[];combinations=0
            for digit in range(10):
                da,ds,db=picture(before,59+digit);ea,es,eb=picture(after,59+digit)
                assert ds==es and db==eb and np.array_equal(da,ea);digits.append((da,db))
            for frame in range(69,78):
                bef,size,box=picture(before,frame);aft,ns,nb=picture(after,frame);ori,os,ob=picture(native[name],frame);sym,ss,sb=picture(symbols[name],frame)
                assert size==ns==os==ss and box==nb==ob==sb
                expected=bef.copy();underlay={};left,top=box[:2]
                # Independent per-coordinate definition of the complete replacement.
                for y in range(24,41):
                    for x in range(-24,5):
                        value=0
                        if 25<=y<=38:
                            if -22<=x<=-15:value=int(ori[y-top,-7-x-left])
                            elif -14<=x<=4:value=int(ori[y-top,5-left])
                        elif y==24 and -18<=x<=2:value=int(ori[y-top,x-left])
                        underlay[x,y]=value
                        if x<2 and sym[y-top,x-left]:value=int(sym[y-top,x-left])
                        expected[y-top,x-left]=value
                assert np.array_equal(expected,aft)
                mask=np.zeros(bef.shape,bool);mask[24-top:41-top,-24-left:2-left]=sym[24-top:41-top,-24-left:2-left]>0
                assert np.array_equal(aft[mask],sym[mask])
                assert np.array_equal(aft[:24-top],bef[:24-top])and np.array_equal(aft[:,5-left:],bef[:,5-left:])
                assert all(underlay[x,y]==int(ori[y-top,-7-x-left])for y in range(25,39)for x in range(-22,-14))
                assert all(underlay[x,y]==int(ori[y-top,5-left])for y in range(25,39)for x in range(-14,5))
                # At the middle, the old individual counter cap is now interior E.
                assert all(underlay[x,31]==14 and aft[31-top,x-left]==14 for x in range(5))
                assert np.all(aft[31-top,-22-left:16-left]>0)
                digit_bounds=[]
                for da,db in digits:
                    yy,xx=np.nonzero(da);ys=yy+db[1]+32-top;xs=xx+db[0]+7-left
                    assert np.array_equal(bef[ys,xs],aft[ys,xs])
                    old_composite=bef.copy();new_composite=aft.copy();old_composite[ys,xs]=da[yy,xx];new_composite[ys,xs]=da[yy,xx]
                    assert np.array_equal(old_composite[ys,xs],new_composite[ys,xs]);combinations+=1
                    digit_bounds.append([int(xs.min()+left),int(ys.min()+top),int(xs.max()+left+1),int(ys.max()+top+1)])
                frame_reports.append({'frame':frame,'changed_pixels':int(np.count_nonzero(bef!=aft)),'accepted_symbol_pixels_preserved':int(mask.sum()),'continuous_middle_world_span':[-22,16],'former_counter_cap_x0_4_y31_now_native_interior_E':True,'glyph_bounds':digit_bounds})
            bank_count=int.from_bytes(entry(before,3)[:4],'little')//4;static={1,2,3,4,6}if bank_count==7 else{1,2,3,4,*range(9,bank_count)};count=0
            for k,c in parts.items():
                if k[0]not in static or k in TARGETS:continue
                aa,az,ab,_=composed(ot,c);ba,bz,bb,_=composed(nt,c);assert az==bz and ab==bb and np.array_equal(aa,ba);count+=1
            fresh,_=maker.patch(before);assert fresh==after
            invalid=bytearray(before);invalid[-1]^=1
            try:maker.patch(bytes(invalid))
            except ValueError as error:assert str(error)=='Unsupported source ARC';rejected.append(project+'/'+name)
            else:raise AssertionError('Altered source accepted')
            details[name]={'before_sha256':sha(before),'after_sha256':sha(after),'all_nontexture_bytes_and_ARC_layout_preserved':True,'palette_CLUT_coordinates_timing_audio_preserved':True,'changed_private_tiles':sorted(changed_tiles),'non_target_static_frames_exact':count,'frames':frame_reports,'digit_composite_checks':combinations,'native_cap_middle_and_y24_template_exact_before_symbol_overlay':True,'old_individual_cap_replaced_by_continuous_body':True,'reproduced_identical':True}
        results[project]=details
    assert protected=={p.relative_to(ROOT).as_posix():digest(p)for p in OUT.rglob('*')if p.is_file()and p.name!='independent.json'}
    assert all(digest(ROOT/p)==h for p,h in inputs.items())and all(digest(ROOT/'scripts'/n)==h for n,h in script_hashes.items())
    report={'passed':True,'resources':results,'source_discs':inputs,'all_source_discs_unchanged':True,'prepared_files_unchanged':True,'production_scripts_unchanged':True,'HUD_frames':54,'digits_0_to_9_composite_checks':540,'unsupported_source_ARC_rejections':rejected,'comparison_png_viewed':True,'visual_assessment':'원작 금속 외곽과 중간 몸체가 현재 심볼 아래로 연속되며, 개별 숫자칸의 이전 왼마감은 제거되었다. 기존 심볼은 전경에 유지된다.','runtime_verified':False,'limitations':['정적 자원/정수배 미리보기 검사이며 실제 새 BIN 표시 및 배경과의 합성은 별도 검증한다.'],'writes':['scripts/hud_underlay_verify.py','work/hud_frame_fix_20261105/underlay_v2/independent.json']}
    (OUT/'independent.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'passed':True,'resources':6,'HUD_frames':54,'digit_composite_checks':540,'negative_rejected':len(rejected)}))
if __name__=='__main__':run()
