"""Read-only independent verification of the Rin one-pixel HUD translation."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.prepare_riko_ui import entry
from scripts.prepare_hud_emblems import all_compositions,composed
from src.psx_ui_atlas import tile_pixels
OUT=Path(__file__).parent
TARGETS={(1,n) for n in range(69,78)}
NAMES=('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC')

def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def read_assets(p):
    with p.open('rb') as f:
        disc=DiscReader(f,p.stat().st_size)
        records={r['name'].split(';')[0]:r for r in disc.inspect()['files']}
        return {n:disc.read(records[n]['lba'],records[n]['size']) for n in NAMES}
def expected_body(before,native,bb):
    # Explicit coordinates from the accepted metal body, without builder imports.
    left,top=bb[:2];body=before.copy()
    for y in range(22,47):
        for x in range(-24,5):body[y-top,x-left]=native[y-top,x-left]
    for y in range(24,41):
        for x in range(-24,5):
            value=0
            if 25<=y<=38:
                if -22<=x<=-15:value=int(native[y-top,-7-x-left])
                elif -14<=x<=4:value=int(native[y-top,5-left])
                if value==14:value=10
                if x>=2:value=int(native[y-top,x-left])
            elif y==24 and -18<=x<=2:value=int(native[y-top,x-left])
            body[y-top,x-left]=value
    for y in range(29,34):
        for x in range(-19,2):
            body[y-top,x-left]=12 if y in(29,33)or x in(-19,1) else (11 if y==32 else 10)
    return body
def layer(art,shape,bb,x):
    out=np.zeros(shape,np.uint8)
    out[23-bb[1]:42-bb[1],x-bb[0]:x-bb[0]+21]=art
    return out

def main():
    proposal_path=OUT/'prepared/ver_rin_nana/proposal.json'
    proposal=json.loads(proposal_path.read_text('utf8'))
    source=ROOT/proposal['baseline'];original=ROOT/'MegaMan X4.bin'
    art_path=ROOT/'work/hud_frame_fix_20261105/reticle_v8/art/rin.json'
    protected=[proposal_path,source,original,art_path]
    protected.extend(ROOT/v['path'] for v in proposal['files'].values())
    initial={str(p.relative_to(ROOT)):digest(p) for p in protected}
    assert digest(source)=='2ed8c388fafe4122aee301bf932632f1fef4ca80fff9cb8c93ea93ffc99bc29f'==proposal['baseline_sha256']
    assert digest(original)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
    assert digest(art_path)=='5414ac41ef5f30bb1d8c86b1ac123d627cd0917038416b884633fba3ced47436'
    art_json=json.loads(art_path.read_text('utf8'))
    art=np.array([[int(c,16) for c in row] for row in art_json['rows']],np.uint8)
    assert art.shape==(19,21) and np.count_nonzero(art)==225 and not np.any(art==14)
    old=read_assets(source);natives=read_assets(original)
    results={};all_huds=0
    for name in NAMES:
        before=old[name];spec=proposal['files'][name];after=(ROOT/spec['path']).read_bytes()
        assert sha(before)==spec['before'] and sha(after)==spec['after']
        assert len(before)==len(after)==spec['size']
        if name!='PL01_U.ARC':
            assert before==after
            results[name]={'byte_identical':True,'HUD_frames_preserved':9,'sha256':sha(after)}
            all_huds+=9;continue
        ar,br=psx_arc(before),psx_arc(after)
        structure=lambda rows:[{k:v for k,v in r.items() if k!='sha256'} for r in rows]
        assert structure(ar)==structure(br)
        rec=next(r for r in ar if int(r['type'],16)==0x10206)
        lo,hi=rec['offset'],rec['offset']+rec['size']
        assert before[:lo]==after[:lo] and before[hi:]==after[hi:]
        for r in ar:
            k=int(r['type'],16)
            if k!=0x10206:assert entry(before,k)==entry(after,k)
        ot,nt=entry(before,0x10206),entry(after,0x10206)
        comps=all_compositions(entry(before,3));ncomps=all_compositions(entry(natives[name],3))
        native_tex=entry(natives[name],0x10206);users={}
        for key,comp in comps.items():
            for part in comp['parts']:users.setdefault(part['page']*256+part['tile'],set()).add(key)
        changed={i for i in range(len(ot)//128) if tile_pixels(ot,i)!=tile_pixels(nt,i)}
        assert changed=={469,470,471,472}
        assert all(users[t]<=TARGETS for t in changed)
        glyphs=[]
        for digit in range(10):
            ga,gs,gb,_=composed(ot,comps[1,59+digit]);ng,ns,nb,_=composed(nt,comps[1,59+digit])
            assert gs==ns and gb==nb and np.array_equal(ga,ng);glyphs.append((ga,gb))
        frames=[];combos=0;expected_frames={};expected_demands={}
        for key in sorted(TARGETS):
            a,sz,bb,sources=composed(ot,comps[key]);b,bs,bbox,_=composed(nt,comps[key])
            native,ns,nb,_=composed(native_tex,ncomps[key]);assert sz==bs==ns and bb==bbox==nb
            body=expected_body(a,native,bb);oldlayer=layer(art,a.shape,bb,-18);newlayer=layer(art,a.shape,bb,-19)
            oldmask,newmask=oldlayer>0,newlayer>0
            assert oldmask.sum()==newmask.sum()==225
            old_expected=body.copy();old_expected[oldmask]=oldlayer[oldmask]
            expected=body.copy();expected[newmask]=newlayer[newmask]
            assert np.array_equal(old_expected,a), 'Source v8 is not canonical art on the known empty body'
            assert np.array_equal(expected,b), 'Target differs from a pure translation with restored background'
            assert np.array_equal(b[newmask],newlayer[newmask])
            cleared=oldmask&~newmask
            assert np.array_equal(b[cleared],body[cleared])
            assert np.array_equal(a[~(oldmask|newmask)],b[~(oldmask|newmask)])
            assert np.count_nonzero(native==14)==56
            assert np.array_equal(a==14,native==14) and np.array_equal(b==14,native==14)
            assert not np.any(newmask&(native==14))
            left,top=bb[:2]
            assert np.array_equal(a[:23-top],b[:23-top])
            assert np.array_equal(a[:,5-left:],b[:,5-left:])
            for y,x in zip(*np.where(a!=b)):
                locations=sources[int(y)*sz[0]+int(x)];assert locations
                for j,(off,shift) in enumerate(locations):
                    tile=(off//128//16)*16+(off%128)//8
                    assert tile in changed and users[tile]<=TARGETS
                    value=int(expected[y,x]) if j==len(locations)-1 else 0
                    assert (off,shift)not in expected_demands or expected_demands[off,shift]==value
                    expected_demands[off,shift]=value
            for glyph,box in glyphs:
                gy,gx=np.nonzero(glyph);dy=gy+box[1]+32-top;dx=gx+box[0]+7-left
                assert not np.any(newmask[dy,dx]) and np.array_equal(a[dy,dx],b[dy,dx])
                ac,bc=a.copy(),b.copy();ac[dy,dx]=glyph[gy,gx];bc[dy,dx]=glyph[gy,gx]
                assert np.array_equal(ac[:,5-left:],bc[:,5-left:]);combos+=1
            expected_frames[key]=expected
            frames.append({'frame':key[1],'art_pixels_translated_exactly':225,'translation':[-1,0],
                'old_origin':[-18,23],'new_origin':[-19,23],'changed_pixels':int(np.count_nonzero(a!=b)),
                'old_pixels_cleared_to_body':int(cleared.sum()),'number_E_pixels_preserved':56,
                'all_changed_pixels_within_existing_private_HUD_tiles':True})
        # Independently repack only the expected nibble changes and compare the entire atlas.
        packed=bytearray(ot)
        for(off,shift),value in expected_demands.items():packed[off]=(packed[off]&~(15<<shift))|(value<<shift)
        assert bytes(packed)==nt
        banks=int.from_bytes(entry(before,3)[:4],'little')//4
        static={1,2,3,4,6} if banks==7 else {1,2,3,4,*range(9,banks)}
        protected_frames=0
        for key,c in comps.items():
            if key[0]not in static or key in TARGETS:continue
            a,sz,bb,_=composed(ot,c);b,ns,nb,_=composed(nt,c)
            assert sz==ns and bb==nb and np.array_equal(a,b);protected_frames+=1
        results[name]={'before_sha256':sha(before),'after_sha256':sha(after),'frames':frames,
            'digit_composite_checks':combos,'changed_tiles':sorted(changed),'independently_repacked_atlas_byte_identical':True,
            'unchanged_non_target_static_frames':protected_frames,'all_nontexture_entries_and_archive_layout_preserved':True,
            'geometry_palette_animation_timing_audio_preserved':True,'unrelated_tiles_byte_identical':True,
            'all_original_number_E_masks_preserved':True,'health_gauge_y22_and_above_preserved':True}
        all_huds+=9
    assert initial=={str(p.relative_to(ROOT)):digest(p) for p in protected}
    report={'passed':True,'variant':'rin_optical_v9','resources':results,'HUD_frames_checked':all_huds,
      'Rin_HUD_frames_changed':9,'Rin_digit_composite_checks':90,'canonical_art_sha256':digest(art_path),
      'canonical_art_size_and_pixels_unchanged':True,'old_symbol_background_restored_without_stale_pixels':True,
      'input_and_prepared_files_unchanged':True,'active_savestate_cards_or_emulator_written':False,
      'runtime_verified':False,'source_hashes':initial,'writes':['work/hud_frame_fix_20261105/rin_optical_v9/independent.json']}
    destination=OUT/'independent.json';assert not destination.exists()
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'passed':True,'HUD_frames':all_huds,'Rin_frames':9,'digit_composites':90,
      'cleared_pixels_per_frame':results['PL01_U.ARC']['frames'][0]['old_pixels_cleared_to_body'],
      'changed_pixels_per_frame':results['PL01_U.ARC']['frames'][0]['changed_pixels'],
      'non_target_static_frames_preserved':results['PL01_U.ARC']['unchanged_non_target_static_frames']}))
if __name__=='__main__':main()
