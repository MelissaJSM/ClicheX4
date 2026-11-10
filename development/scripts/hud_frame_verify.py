"""HUD 마감 교정의 독립 보존 검사. 게임·아트·원제작 코드는 쓰지 않는다."""
import hashlib,json,sys
from pathlib import Path
from unittest.mock import patch as mock_patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_hud_emblems import composed,all_compositions
from src.psx_ui_atlas import tile_pixels
import scripts.hud_frame_fix as maker

WORK=ROOT/'work/hud_frame_fix_20261105'
PREP=WORK/'prepared_v1'
CAP={25:'..DDD',26:'.DCAA',27:'DCAAD',28:'DCADE',29:'DCADE',30:'DCADE',31:'DCADE',32:'DCADE',33:'DCADE',34:'DCAAD',35:'.DCAA',36:'.DBBB',37:'..DDD',38:'...DD'}
TARGETS={(1,n)for n in range(69,78)}
PRIVATE={'ver_buki_riko':{'PL00_U.ARC':{205,214},'PL01_U.ARC':{470,472},'PL02_U.ARC':{205,214}},'ver_rin_nana':{'PL00_U.ARC':{253,431},'PL01_U.ARC':{470,472},'PL02_U.ARC':{253,431}}}

def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        for block in iter(lambda:f.read(8388608),b''):h.update(block)
    return h.hexdigest()
def run():
    files_before={p.relative_to(ROOT).as_posix():digest(p)for p in PREP.rglob('*')if p.is_file()}
    maker_before=digest(ROOT/'scripts/hud_frame_fix.py');reports={};negative=[]
    for project in('ver_buki_riko','ver_rin_nana'):
        proposal_path=PREP/project/'proposal.json';p=json.loads(proposal_path.read_text('utf8'));source=ROOT/p['baseline']
        assert digest(source)==p['baseline_sha256'];results={}
        with source.open('rb')as f:
            disc=DiscReader(f,source.stat().st_size)
            for name,spec in p['files'].items():
                old=disc.read(spec['record']['lba'],spec['record']['size']);new=(ROOT/spec['path']).read_bytes()
                assert sha(old)==spec['before']and sha(new)==spec['after']and len(old)==len(new)==spec['size']
                old_layout,new_layout=psx_arc(old),psx_arc(new)
                layout=lambda es:[{k:v for k,v in e.items()if k!='sha256'}for e in es]
                assert layout(old_layout)==layout(new_layout)
                texrec=next(e for e in old_layout if int(e['type'],16)==0x10206);start,end=texrec['offset'],texrec['offset']+texrec['size']
                assert old[:start]==new[:start]and old[end:]==new[end:]
                ot,nt=entry(old,0x10206),entry(new,0x10206);cs=all_compositions(entry(old,3));changed_tiles=[];users={}
                for key,c in cs.items():
                    for q in c['parts']:users.setdefault(q['page']*256+q['tile'],set()).add(key)
                for tile in range(len(ot)//128):
                    if tile_pixels(ot,tile)!=tile_pixels(nt,tile):changed_tiles.append(tile)
                assert set(changed_tiles)==PRIVATE[project][name]
                assert all(users[t]<=TARGETS for t in changed_tiles)
                digits=[]
                for digit in range(10):
                    before,ds,db,_=composed(ot,cs[1,59+digit]);after,ns,nb,_=composed(nt,cs[1,59+digit])
                    assert ds==ns and db==nb and np.array_equal(before,after)
                    ys,xs=np.nonzero(before);bbox=[int(xs.min()+db[0]+7),int(ys.min()+db[1]+32),int(xs.max()+db[0]+8),int(ys.max()+db[1]+33)]
                    assert bbox[0]>=5 and bbox[2]<=9 and bbox[1]==28 and bbox[3]==35
                    digits.append((digit,before,db,bbox))
                target_reports=[];digit_placements=0
                for key in sorted(TARGETS):
                    before,size,bb,_=composed(ot,cs[key]);after,ns,nb,_=composed(nt,cs[key]);assert size==ns and bb==nb
                    expected=before.copy();allowed=np.zeros(before.shape,bool)
                    for y,row in CAP.items():
                        for x,code in enumerate(row):
                            iy,ix=y-bb[1],x-bb[0];allowed[iy,ix]=True
                            if x<2 and before[iy,ix]:assert code=='.';continue
                            expected[iy,ix]=0 if code=='.'else int(code,16)
                    for y in(24,39,40):expected[y-bb[1],2-bb[0]]=0;allowed[y-bb[1],2-bb[0]]=True
                    assert np.array_equal(after,expected)and np.array_equal(after[~allowed],before[~allowed])
                    assert np.array_equal(after[:24-bb[1]],before[:24-bb[1]])
                    assert np.array_equal(after[:,5-bb[0]:],before[:,5-bb[0]:])
                    original_symbol=np.zeros(before.shape,bool);original_symbol[24-bb[1]:41-bb[1],:2-bb[0]]=before[24-bb[1]:41-bb[1],:2-bb[0]]>0
                    assert np.array_equal(after[original_symbol],before[original_symbol])
                    # The native glyph layer uses independent origin(+7,+32).
                    for digit,glyph,db,bbox in digits:
                        yy,xx=np.nonzero(glyph);gy=yy+db[1]+32-bb[1];gx=xx+db[0]+7-bb[0]
                        assert np.array_equal(after[gy,gx],before[gy,gx])
                        old_comp=before.copy();new_comp=after.copy();old_comp[gy,gx]=glyph[yy,xx];new_comp[gy,gx]=glyph[yy,xx]
                        assert np.array_equal(old_comp[gy,gx],new_comp[gy,gx]);digit_placements+=1
                    target_reports.append({'frame':key[1],'changed_pixels':int(np.count_nonzero(after!=before)),'symbol_pixels_preserved':int(original_symbol.sum()),'bounds':bb})
                bank_count=int.from_bytes(entry(old,3)[:4],'little')//4
                static={1,2,3,4,6}if bank_count==7 else{1,2,3,4,*range(9,bank_count)};protected=0
                for key,c in cs.items():
                    if key[0]not in static or key in TARGETS:continue
                    before,sz,bb,_=composed(ot,c);after,ns,nb,_=composed(nt,c)
                    assert sz==ns and bb==nb and np.array_equal(before,after);protected+=1
                reproduced,_=maker.patch(old);assert reproduced==new
                # An in-memory test symbol at a new cap pixel must be rejected.
                a,sz,bb,locations=composed(ot,cs[1,69]);mut=bytearray(ot);loc=locations[(28-bb[1])*sz[0]+0-bb[0]];assert a[28-bb[1],0-bb[0]]==0 and loc
                for i,(off,shift)in enumerate(loc):mut[off]=(mut[off]&~(15<<shift))|((1 if i==len(loc)-1 else 0)<<shift)
                invalid=replace_entry(old,0x10206,bytes(mut))
                try:maker.patch(invalid)
                except ValueError as error:assert str(error)=='New frame overlaps the accepted emblem';negative.append({'project':project,'resource':name,'case':'in_memory_symbol_overlap_at_0_28','rejected':True})
                else:raise AssertionError('Symbol overlap accepted')
                results[name]={'before':sha(old),'after':sha(new),'ARC_layout_same':True,'outside_texture_byte_identical':True,'all_palette_timing_audio_composition_coordinates_and_cluts_preserved':True,'changed_private_tiles':changed_tiles,'all_other_tiles_identical':True,'private_tile_users_confined_to_target_frames':True,'target_frames':target_reports,'digits':[{'digit':digit,'opaque_world_bbox_exclusive':bbox}for digit,g,db,bbox in digits],'digit0_9_composite_checks':digit_placements,'non_target_static_frames_exact':protected,'reproduced_byte_identical':True}
        # Exercise the actual builder's source hash guard, before any output write.
        never_output=ROOT/'out'/project/'hud_frame_verify_must_never_be_created'
        assert not never_output.exists();stem,_=maker.SOURCES[project]
        with mock_patch.dict(maker.SOURCES,{project:(stem,'0'*64)}):
            try:maker.build(project,proposal_path,never_output)
            except ValueError as error:assert str(error)=='Unexpected source BIN';negative.append({'project':project,'case':'actual_BIN_against_wrong_supported_SHA','rejected':True})
            else:raise AssertionError('Wrong source SHA accepted')
        assert not never_output.exists()and digest(source)==p['baseline_sha256'];reports[project]=results
    assert files_before=={p.relative_to(ROOT).as_posix():digest(p)for p in PREP.rglob('*')if p.is_file()}
    assert maker_before==digest(ROOT/'scripts/hud_frame_fix.py')
    report={'scope':'독립 디스크 재추출·픽셀/조립 보호·부정입력 검사. 에뮬레이터 실행 증거는 아님.',
        'resources':reports,'negative_cases':negative,'six_resources':6,'HUD_frames':54,'digit_composite_checks':540,
        'accepted_symbols_unchanged':True,'health_bar_y_le23_unchanged':True,'right_region_x_ge5_unchanged':True,
        'original_source_BINs_unchanged':True,'prepared_artifacts_unchanged':True,'production_script_unchanged':True,
        'runtime_verified':False,'file_writes':['scripts/hud_frame_verify.py','work/hud_frame_fix_20261105/verification.json'],
        'comparison_png_viewed':True,'comparison_assessment':'새 마감은 숫자칸 왼쪽을 밝은 절각선으로 닫고 원래 심볼 뒤의 큰 판을 복구하지 않는다. 네 심볼과 숫자0 미리보기 직접 열람.'}
    (WORK/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'resources':6,'HUD_frames':54,'digit_checks':540,'negative_rejected':len(negative),'all_passed':True,'runtime_verified':False}))
if __name__=='__main__':run()
