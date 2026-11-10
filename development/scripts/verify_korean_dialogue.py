"""Independent decode and preservation audit of the proposed Korean resources."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D,messages
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc,sha256
from src.psx_korean_font import font_cache_proposal,emit_cache_code
from src.psx_korean_text import LEGACY,glyph_bitmap

def verify_typewriter(original_lines,translated_lines,*,speaker_header=False):
    """Compare native timing from decoded words, not generator metadata.

    Nonterminal body glyphs define output mode. Header-final and page-final
    controls have separate native 0xB000 yield/end semantics. Line wrapping
    may change, but these semantics must remain the same.
    """
    original=[w for line in original_lines for w in line]
    translated=[w for line in translated_lines for w in line]
    header=bool(original_lines[0][-1]&0x4000 and (speaker_header or not original_lines[0][0]&0x1000))
    if speaker_header and not header:raise ValueError('Speaker line has no native newline')
    original_body=original_lines[1:] if header else original_lines
    translated_body=translated_lines[1:] if header else translated_lines
    if not translated_body:raise ValueError('Immediate speaker/body boundary removed')
    source_body=[w for line in original_body for w in line]
    target_body=[w for line in translated_body for w in line]
    source_modes={bool(w&0x1000) for w in source_body[:-1]}
    if len(source_modes)>1:raise ValueError('Unmapped mixed native body timing')
    expected_typed=next(iter(source_modes)) if source_modes else bool(source_body[-1]&0x1000)
    if any(bool(w&0x1000)!=expected_typed for w in target_body[:-1]):
        raise ValueError('Body typewriter flag changed')
    if header:
        if any(w&0x1000 for w in translated_lines[0][:-1]):raise ValueError('Immediate speaker became typed')
        if translated_lines[0][-1]&0xf800!=original_lines[0][-1]&0xf800:
            raise ValueError('Immediate speaker final yield/newline changed')
    if translated[-1]&0xf800!=original[-1]&0xf800:raise ValueError('Page-final timing/control changed')
    return {'immediate_header':header,'body_typewriter':expected_typed,
            'header_final_yield':bool(original_lines[0][-1]&0x1000) if header else None,
            'terminal_control':hex(original[-1]&0xf800),
            'source_body_words':len(source_body),'translated_body_words':len(target_body),
            'translated_typed_nonterminal_words':sum(bool(w&0x1000) for w in target_body[:-1])}


def verify(candidate):
    report=json.loads((candidate/'proposal.json').read_text('utf-8'));results={}
    for name,meta in report['files'].items():
        old=(D/'inventory'/name).read_bytes();new=(candidate/name).read_bytes()
        if sha256(old)!=meta['before'] or sha256(new)!=meta['after'] or len(old)!=len(new):raise ValueError('Resource identity/size mismatch')
        if name=='SLUS_005.61':
            expected,proof=font_cache_proposal(old)
            if expected!=new:raise ValueError('Unexpected executable change')
            results[name]={'changed_bytes':proof['changed_bytes']};continue
        before,after=psx_arc(old),psx_arc(new)
        if any(int(e['type'],16)<0x10000 and e['size']%4 for e in after):raise ValueError('Unaligned native ARC RAM resource')
        for a,z in zip(before,after):
            if a['offset']!=z['offset'] or a['type']!=z['type']:raise ValueError('Resource relocated')
            if a['type']!='0x15' and (a!=z or old[a['offset']:a['offset']+a['size']]!=new[z['offset']:z['offset']+z['size']]):raise ValueError('Non-dialogue data changed')
        text=entry(new,0x15);r=report['dialogue'][name]
        original_messages=messages(entry(old,0x15))
        if text[128:132]!=b'KOR1' or struct.unpack_from('<III',text,132)!=(r['font_offset'],r['glyph_count'],r['code_offset']):raise ValueError('Invalid font header')
        if text[r['code_offset']:r['font_offset']]!=emit_cache_code():raise ValueError('Helper differs')
        for i,ch in enumerate(r['glyphs']):
            if text[r['font_offset']+i*18:r['font_offset']+(i+1)*18]!=glyph_bitmap(ch):raise ValueError('Font differs')
        inverse={v:k for k,v in LEGACY.items()};inverse.update({256+i:c for i,c in enumerate(r['glyphs'])})
        checked=0;previous=None;timing_checks=[]
        for page in r['pages']:
            if previous!=page['message']:pos=struct.unpack_from('<H',text,page['message']*2)[0];previous=page['message']
            lines=[];line='';visible=0;word_lines=[];word_line=[]
            while True:
                w=struct.unpack_from('<H',text,pos)[0];pos+=2;g=w&2047
                if g not in inverse:raise ValueError('Unmapped character')
                line+=inverse[g];visible+=g!=2047;word_line.append(w)
                if w&0x800!=page['side']:raise ValueError('Speaker side changed')
                if w&0xe000:lines.append(line);line='';word_lines.append(word_line);word_line=[]
                if w&0xa000:
                    if w&0xe000!=page['end_flags']:raise ValueError('Page control changed')
                    break
            if lines!=page['lines'] or visible>60 or any(len(x)>20 for x in lines) or len(lines)>3:raise ValueError('Text/geometry decode mismatch')
            original_page=original_messages[page['message']]['pages'][page['page']]
            original_lines=[line['words'] for line in original_page['lines']]
            if any(w&0x800!=original_lines[0][0]&0x800 for row in word_lines for w in row):
                raise ValueError('Native speaker side differs')
            timing=verify_typewriter(original_lines,word_lines,
                speaker_header=[page['message'],page['page']] in r.get('explicit_header_pages',[]))
            timing_checks.append({'message':page['message'],'page':page['page'],**timing})
            checked+=1
        results[name]={'decoded_translated_pages':checked,'font_glyphs':r['glyph_count'],'protected_entries':len(before)-1,'remaining_text_allocation':r['current_capacity']-len(text),'same_resource_offsets':True,'ram_word_alignment_preserved':True,
                       'typewriter_pages_checked':len(timing_checks),'body_typewriter_pages':sum(p['body_typewriter'] for p in timing_checks),
                       'immediate_header_pages':sum(p['immediate_header'] for p in timing_checks),
                       'header_final_yield_pages':sum(p['header_final_yield'] is True for p in timing_checks),
                       'original_typewriter_semantics_preserved':True,'typewriter_profiles':timing_checks}
    result={'kind':'static_korean_dialogue_verification','results':results,'game_runtime_verified':False}
    (candidate/'verification.json').write_text(json.dumps(result,indent=2));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.candidate)))
