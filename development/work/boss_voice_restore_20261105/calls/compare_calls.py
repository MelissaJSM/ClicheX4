"""Read-only native JP/US boss-call inventory. Outputs remain in this directory."""
from pathlib import Path
import sys, re, json, hashlib, struct, bisect
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
OUT=Path(__file__).resolve().parent

def sha(b): return hashlib.sha256(b).hexdigest()
def sections(region):
    p=ROOT/'work/research/decomp/config'/({'us':'SLUS_005.61','jp':'SLPS_009.02'}[region]+'.splat.yaml')
    a=[]
    for s in p.read_text().splitlines():
        m=re.search(r'\[0x([0-9A-Fa-f]+), (c|\.rodata|\.data|data), ([^\]]+)\]',s)
        if m:
            item={'offset':int(m[1],16),'kind':m[2],'name':m[3].strip()}
            # The supplied JP executable is not the YAML's advertised SHA1.
            # Native unique 16-byte entry anchors place these two starts +8.
            if region=='jp' and item['kind']=='c' and item['name'] in ('mains/main_44_anchored_mine','mains/main_45_train_boss'):
                item['config_offset']=item['offset'];item['offset']+=8
                item['boundary_evidence']='US exact 16-byte entry pattern has exactly one match within +/-64 bytes of configured JP start'
            a.append(item)
    a.sort(key=lambda d:d['offset'])
    for i in range(len(a)-1):a[i]['end']=a[i+1]['offset']
    a[-1]['end']=0x120800
    return a
def native(region):
    name={'us':'MegaMan X4.bin','jp':'Rockman X4.bin'}[region]
    p=ROOT/name
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<22),b''): h.update(b)
    with p.open('rb') as f:
        d=DiscReader(f,p.stat().st_size)
        rec={x['name'].split(';')[0]:x for x in d.inspect()['files']}
        exe_name={'us':'SLUS_005.61','jp':'SLPS_009.02'}[region]
        e=d.read(rec[exe_name]['lba'],rec[exe_name]['size'])
        (OUT/exe_name).write_bytes(e)
        arcs={}
        for n,r in rec.items():
            if n.endswith('.ARC'):
                data=d.read(r['lba'],r['size'])
                try: parsed=psx_arc(data)
                except ValueError: parsed={'not_psx_arc':True,'header':data[:16].hex()}
                arcs[n]={'sha256':sha(data),'size':len(data),'entries':parsed}
    return e,{'source':name,'source_sha256':h.hexdigest(),'executable':exe_name,'exe_sha256':sha(e),'exe_sha1':hashlib.sha1(e).hexdigest(),'files':rec,'arcs':arcs}

def calls(data,start,end,targets):
    out=[]
    for off in range(start,end,4):
        w=struct.unpack_from('<I',data,off)[0]
        if w>>26!=3:continue
        target=((w&0x3ffffff)<<2)|0x80000000
        if target in targets:
            a={'offset':off,'address':hex(off+0x8000f800),'target':hex(target),'api':targets[target], 'before_hex':data[max(start,off-40):off].hex(),'delay_hex':data[off+4:off+8].hex()}
            out.append(a)
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    es={}; inv={}
    for r in ('us','jp'):es[r],inv[r]=native(r)
    sec={r:sections(r) for r in es}
    # For candidate JP matching, unique 12-instruction non-address anchor of the US API.
    targets={}
    for addr,name in [(0x8001540c,'play_sound'),(0x800154e8,'sound_dispatch'),(0x800157ac,'sound_variant'),(0x80015930,'stop_sound'),(0x80015a10,'is_sound_finished'),(0x8001663c,'play_xa'),(0x8002217c,'dialogue')]:
        off=addr-0x8000f800
        a=es['us'][off:off+16]
        hits=[i for i in range(0x800,len(es['jp'])-16,4) if es['jp'][i:i+16]==a]
        targets[hex(addr)]={'name':name,'us_address':hex(addr),'jp_candidates':[hex(i+0x8000f800) for i in hits]}
    (OUT/'inventory.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2),encoding='utf8')
    (OUT/'api_candidates.json').write_text(json.dumps(targets,indent=2),encoding='utf8')
    summary=[]
    for u in sec['us']:
        if u['kind']!='c' or not u['name'].startswith('mains/'):continue
        j=next(x for x in sec['jp'] if x['name']==u['name'] and x['kind']=='c')
        ut={int(k,16):v['name'] for k,v in targets.items()}
        jt={int(v['jp_candidates'][0],16):v['name'] for v in targets.values() if len(v['jp_candidates'])==1}
        a=calls(es['us'],u['offset'],u['end'],ut)
        b=calls(es['jp'],j['offset'],j['end'],jt)
        if a or b:summary.append({'name':u['name'],'us':u,'jp':j,'us_calls':a,'jp_calls':b})
    (OUT/'calls_initial.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print(json.dumps({'input_hashes':{r:{k:v for k,v in d.items() if k not in ('files','arcs')} for r,d in inv.items()},'api_candidates':targets,'sections_with_calls':len(summary)},indent=2))

if __name__=='__main__':main()
