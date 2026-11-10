"""Build complete Korean dialogue proposal; no BIN mutation or runtime claim."""
import argparse,json,runpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D,messages
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import sha256
from src.psx_korean_text import build_dialogue,replace_text_same_capacity
from src.psx_korean_font import font_cache_proposal

def wrap(text,limit=20):
    lines=[];current=''
    for word in text.split(' '):
        if len(word)>limit:raise ValueError('Word exceeds line width')
        candidate=(current+' '+word).lstrip()
        if len(candidate)>limit:lines.append(current);current=word
        else:current=candidate
    if current:lines.append(current)
    return lines

def main(output):
    output.mkdir(parents=True,exist_ok=False)
    translation=runpy.run_path(str(D/'translation_ko.py'));reports={};files={};review=[]
    for name in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
        old=(D/'inventory'/name).read_bytes();source=entry(old,0x15);mm=messages(source)
        body=translation['R' if name=='PL01_U.ARC' else 'X'];pages={};speaker_pages=set()
        if set(body)!=set(range(len(mm)-1)):raise ValueError('Missing message translation')
        for mi,texts in body.items():
            if len(texts)!=len(mm[mi]['pages']):raise ValueError(f'{name}/{mi}: page mismatch {len(texts)} != {len(mm[mi]["pages"])}')
            pages[mi]=[]
            for pi,(text,oldpage) in enumerate(zip(texts,mm[mi]['pages'])):
                oldhead=oldpage['lines'][0]['text'].strip();header=translation['HEADERS'].get(oldhead)
                if header:speaker_pages.add((mi,pi))
                lines=([header] if header else [])+wrap(text)
                if len(lines)>3:raise ValueError(f'{name}/{mi}/{pi}: page overflow {lines}')
                pages[mi].append(lines)
                if name!='PL02_U.ARC':review.append(f'{name} {mi:02d}/{pi:02d}: '+' / '.join(lines))
        text,report=build_dialogue(source,mm,pages,immediate_headers=speaker_pages)
        report['explicit_header_pages']=[list(x) for x in sorted(speaker_pages)]
        capacity=len(old)-next(e['offset'] for e in __import__('scripts.discover_inputs',fromlist=['psx_arc']).psx_arc(old) if e['type']=='0x15')
        (output/(name+'.text')).write_bytes(text)
        report['old_text_size']=len(source);report['current_capacity']=capacity;report['extra_needed']=max(0,len(text)-capacity)
        if len(text)<=capacity:
            new=replace_text_same_capacity(old,text);(output/name).write_bytes(new)
            files[name]={'before':sha256(old),'after':sha256(new),'size':len(new)}
        reports[name]=report
    exe=(D/'inventory/SLUS_005.61').read_bytes();new,report=font_cache_proposal(exe)
    (output/'SLUS_005.61').write_bytes(new);files['SLUS_005.61']={'before':sha256(exe),'after':sha256(new),'size':len(new)}
    (output/'proposal.json').write_text(json.dumps({'kind':'korean_dialogue_full_proposal','bin_applied':False,'files':files,'dialogue':reports,'exe':report},ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'review_ko.txt').write_text('\n'.join(review),encoding='utf-8')
    print(json.dumps({n:{k:v for k,v in r.items() if k not in ('pages','glyphs')} for n,r in reports.items()},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
