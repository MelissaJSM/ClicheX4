"""린 한 프레임 후보의 같은 뱅크 내 재압축 가능성 검사. 원래 BIN/ARC는 변경하지 않는다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from scripts.project import digest

def main():
    pointer=ROOT/'projects/ver_rin_nana/rin_candidate.json';p=json.loads(pointer.read_text('utf-8'));out=ROOT/p['candidate'];extract=ROOT/p['extract']
    if not out.resolve().is_relative_to(ROOT/'out/ver_rin_nana') or not extract.resolve().is_relative_to(ROOT/'work/ver_rin_nana'):raise ValueError('Wrong variant')
    gfx=(extract/'graphics_entry.bin').read_bytes();parts=(extract/'composition_entry.bin').read_bytes();code=(out/'candidate_block.compressed').read_bytes();bank=graphics_bank(gfx,0);groups={}
    for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f)
    old={start:decode_stream(gfx,refs[0]['offset'],refs[0]['limit'],refs[0]['tile_count']*128) for start,refs in groups.items()}
    target=bank['frames'][147]['offset'];slack=bank['end']-bank['base']-len(bank['frames'])*4-sum(v.end-v.start for v in old.values())
    needed=len(code)-(old[target].end-old[target].start)-slack
    replacements={f['index']:code for f in groups[target]};savings=0;recompressed=[]
    # Only re-encode as many unchanged streams as needed; their decoded pixels stay identical.
    for start,stream in sorted(old.items(),key=lambda x:-(x[1].end-x[1].start)):
        if savings>=needed:break
        if start==target:continue
        encoded=encode_stream(stream.data);gain=stream.end-stream.start-len(encoded)
        if gain<=0:continue
        if decode_stream(encoded,0,len(encoded),len(stream.data)).data!=stream.data:raise ValueError('Lossless recompression failed')
        for f in groups[start]:replacements[f['index']]=encoded
        recompressed.append({'frames':[f['index'] for f in groups[start]],'saved_bytes':gain,'decoded_bytes_unchanged':True});savings+=gain
        print(f'Unchanged stream recompression saved {savings} bytes, required {needed}',flush=True)
    result,report=repack_graphics_bank(gfx,0,replacements);newbank=graphics_bank(result,0);body_changes=[];unassembled=[]
    for n,(before,after) in enumerate(zip(bank['frames'],newbank['frames'])):
        a=old[before['offset']].data;b=decode_stream(result,after['offset'],after['limit'],after['tile_count']*128).data
        if a==b:continue
        if n not in (146,147,148):raise ValueError('Unrelated decoded pixels changed')
        comp=composition_frame(parts,0,n);x=compose_indices(a,before['tile_count'],comp);y=compose_indices(b,after['tile_count'],comp)
        if x[:3]!=y[:3]:body_changes.append(n)
    if body_changes!=[147]:raise ValueError('Visible modifications outside single pilot frame')
    if result[bank['end']:]!=gfx[bank['end']:]:raise ValueError('Other graphics bank changed')
    (out/'repacked_graphics.bin').write_bytes(result)
    final={'input_graphics_sha256':digest(extract/'graphics_entry.bin'),'output_graphics_sha256':digest(out/'repacked_graphics.bin'),'first_attempt_original_slot_bytes':len(code),'original_slot_budget':old[target].end-old[target].start,'needed_extra_bank_bytes':max(0,needed),'lossless_recompressed_streams':recompressed,'all_254_bank0_references_checked':True,'only_changed_composed_frame':147,'bank1_byte_identical':True,'graphics_entry_length_unchanged':len(result)==len(gfx),'parts_animation_palette_untouched':True,'game_bin_written':False,'same_bank_fit_verified':True,'repack':report}
    (out/'fit_verification.json').write_text(json.dumps(final,ensure_ascii=False,indent=2)+'\n','utf-8')
    p['same_bank_fit_verified']=True;p['fit_verification']=(out/'fit_verification.json').relative_to(ROOT).as_posix();pointer.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({'same_bank_fit_verified':True,'remaining_slack':report['remaining_slack'],'lossless_streams':len(recompressed),'changed_display_frames':body_changes,'game_bin_written':False}))

if __name__=='__main__':main()
