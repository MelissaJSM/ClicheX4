"""Native English character-name replacement with page and control preservation."""
import re,struct,textwrap
from src.psx_text import ALPHABET,message_ranges

NAME=re.compile(r'(?<![A-Za-z0-9])(?:[Mm][Ee][Gg][Aa] ?[Mm][Aa][Nn](?: X)?|X)(?![A-Za-z0-9])')
LAYOUT_REPHRASES={
    'But your search is over\ue086 Get ready Shibuki\ue087':'Your search is over\ue086 Get ready Shibuki\ue087',
    'I\ue08bm giving you a new head module\ue085 Shibuki\ue086':'A new head module for you\ue085 Shibuki\ue086',
    'Equip with this new body module\ue085 Shibuki\ue086':'Equip this new body module\ue085 Shibuki\ue086',
    'Shibuki\ue087 I\ue08bll wait for you at Memorial Hall\ue086':'Shibuki\ue087 meet me at Memorial Hall\ue086',
    'Think it over in heaven\ue087 Die\ue085 Shibuki\ue087':'Think in heaven\ue087 Die\ue085 Shibuki\ue087',
    '\ue086\ue086\ue086You must hurry Shibuki\ue086 The earth is\ue086\ue086\ue086':'Hurry Shibuki\ue086 The earth is\ue086\ue086\ue086',
    'This is amusing\ue086\ue086\ue086 It really is Shibuki\ue086\ue086\ue086':'How amusing\ue086\ue086\ue086 It is\ue085 Shibuki\ue086\ue086\ue086',
    'Try hard Shibuki\ue086 Your life depends on it\ue087':'Try hard Shibuki\ue086 Your life\ue08bs at risk\ue087',
    'Shibuki\ue085 please forgive our foolishness\ue086\ue086\ue086':'Shibuki\ue085 forgive our foolishness\ue086\ue086\ue086',
}

def char(word):
    k=word&511
    return ALPHABET[k-64] if 64<=k<64+len(ALPHABET) else ' ' if k==511 else chr(0xe000+k)

def code(ch):
    return ALPHABET.index(ch)+64 if ch in ALPHABET else 511 if ch==' ' else ord(ch)-0xe000

def rename_page(words):
    lines=[];line=[]
    for w in words:
        line.append(w)
        if w&0x4000:lines.append(line);line=[]
    if line:lines.append(line)
    changes=[];result=[]
    # Keep the first, speaker line separate when the original page has one.
    for li,line in enumerate(lines):
        s=''.join(map(char,line));changed=[];cursor=0
        for m in NAME.finditer(s):
            changed.extend(line[cursor:m.start()]);old=line[m.start():m.end()]
            for j,ch in enumerate('Shibuki'):
                flags=old[0]&~(511|0xe000)
                if j==6:flags|=old[-1]&0xe000
                changed.append(flags|code(ch))
            changes.append({'from':m.group(),'to':'Shibuki','line':li});cursor=m.end()
        changed.extend(line[cursor:]);result.append(changed)
    if not changes:return words,[]
    # Reflow only overflowing lines, retaining page-end flags and dialogue pages.
    header=result[0] if len(result)>1 and len(result[0])<=20 else None
    if any(len(line)>20 for line in result):
        body=result[1:] if header is not None else result
        flat=[]
        for i,line in enumerate(body):
            if i and flat and char(flat[-1])!=' ':flat.append((line[0]&0x1800)|511)
            flat.extend(w&~0x4000 for w in line)
        s=''.join(map(char,flat));wrapped=textwrap.wrap(s,width=20,break_long_words=False,break_on_hyphens=False,drop_whitespace=True)
        if len(wrapped)> (2 if header is not None else 3):
            if s not in LAYOUT_REPHRASES:raise ValueError('Name expansion exceeds original dialogue page: '+repr(s))
            shorter=LAYOUT_REPHRASES[s];changes.append({'layout_from':s,'layout_to':shorter})
            flags=flat[0]&~(511|0xe000);flat=[flags|code(ch) for ch in shorter];s=shorter
            wrapped=textwrap.wrap(s,width=20,break_long_words=False,break_on_hyphens=False)
            if len(wrapped)>(2 if header is not None else 3):raise ValueError('Reviewed name layout still overflows')
        new=[];cursor=0
        for line in wrapped:
            start=s.index(line,cursor);part=flat[start:start+len(line)];cursor=start+len(line)
            part[-1]|=0x4000;new.append(part)
        new[-1][-1]=(new[-1][-1]&~0xe000)|(words[-1]&0xe000)
        result=([header] if header is not None else [])+new
    out=[w for line in result for w in line]
    if [w&0xa000 for w in out if w&0xa000]!=[w&0xa000 for w in words if w&0xa000]:raise ValueError('Page control changed')
    return out,changes

def rename_shibuki(data):
    ranges=message_ranges(data);encoded=[];changes=[];pages_count=0
    for mi,(start,end) in enumerate(ranges):
        original=list(struct.unpack('<'+'H'*((end-start)//2),data[start:end]));new=[];page=[]
        for w in original:
            page.append(w)
            if w&0xa000:
                out,cc=rename_page(page);new.extend(out);changes.extend(dict(message=mi,page=pages_count,**v) for v in cc);pages_count+=1;page=[]
        if page:new.extend(page)
        encoded.append(struct.pack('<'+'H'*len(new),*new))
    offsets=[];cursor=len(ranges)*2
    for raw in encoded:offsets.append(cursor);cursor+=len(raw)
    if cursor>=65536:raise ValueError('Native dialogue offset overflow')
    out=struct.pack('<'+'H'*len(offsets),*offsets)+b''.join(encoded)
    return out,{'changes':changes,'name_count':sum('from' in c for c in changes),'layout_rephrases':sum('layout_from' in c for c in changes),'message_count':len(ranges),'pages':pages_count,'bytes_before':len(data),'bytes_after':len(out),'growth':len(out)-len(data),'page_count_preserved':True}
