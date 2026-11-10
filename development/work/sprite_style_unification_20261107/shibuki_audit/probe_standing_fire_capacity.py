"""새40층 무손실32타일 배치/고정은행 용량 조사. ARC는 출력하지 않는다."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from scripts.export_x_consistency import Archive
from scripts.overhaul_sprites_costume_pack import pack_planes
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from repack_part_records_lossless import repack as repack_global
from pack_shibuki_hurt import raw,tile_seed
from src.psx_player import decode_stream,indexed_atlas,compose_indices
from src.psx_compress import encode_stream
PBS=(0,5,6,7,8)
def render(nr,rr):
    cp={'parts':[{'index':i,'tile':t,'x':x-80,'y':y-80,'flip_x':bool(fl&64),'flip_y':bool(fl&128),'clut':0,'page':0,'unknown_flags':0}for i,(t,x,y,fl)in enumerate(rr)]}
    if not rr:return np.zeros((384,384),np.uint8)
    pix,size,bb,_=compose_indices(nr,32,cp,allowed_cluts={0});v=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);out=np.zeros((384,384),np.uint8);yy,xx=np.nonzero(v);out[yy+bb[1]+160,xx+bb[0]+160]=v[yy,xx];return out
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='standing_fire_capacity02');args=ap.parse_args();d=(H/args.output).resolve();need(d.is_relative_to(H.resolve())and not d.exists(),'Fresh capacity probe');d.mkdir();s=H/'standing_fire_targets_probe01';a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());targets={n:{b:np.array(Image.open(s/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in range(85,93)};raws={};counts={};changes={b:{}for b in PBS};groups=[]
    for ns in((85,),(86,),(87,),(88,89),(90,),(91,),(92,)):
        n=89 if ns==(88,89)else ns[0];imgs=[crop(targets[n][b])for b in PBS];keep={7,8}if n==89 else set();seed=tile_seed(a,88,keep)if keep else bytes(4096);pool=set(range(32))-{0,16}-keep
        if n==89:
            variant=np.roll(targets[88][5],1,axis=1);imgs.append(crop(variant));nr,rr=pack_shared(seed,32,imgs,pool,[24]*len(imgs))
        else:nr,rr=pack_planes(seed,32,imgs,pool,[24]*len(imgs))
        for i,im in enumerate(imgs):need(np.array_equal(render(nr,rr[i])[80:240,80:240],im),'Packed plane differs')
        for k in ns:
            raws[k]=nr;counts[k]=32
            for i,b in enumerate(PBS):
                ps=rr[5]if k==88 and b==5 else rr[i];rec=b''.join(struct.pack('<BBbb',fl,t,x-80-(k==88),y-80)for t,x,y,fl in ps)or struct.pack('<BBbb',0,0,-8,-8)
                if k==88 and b==0:
                    cps=targets[k][0];fx=json.loads((s/'manifest.json').read_text('utf8'))['effect88']['source_records'];rec+=b''.join(struct.pack('<BBbb',p['flags'],p['tile'],p['x'],p['y'])for p in fx)
                need(len(rec)//4<=24,'Too many parts');changes[b][k]=rec
        code=encode_stream(nr);(d/f'group_{n:03}_raw.bin').write_bytes(nr);row={'refs':list(ns),'raw_sha256':sha(nr),'compressed_bytes':len(code),'parts':{str(k):{str(b):len(changes[b][k])//4 for b in PBS}for k in ns},'protected_full_effect_tiles':sorted(keep)};groups.append(row);print(json.dumps(row),flush=True);write(d/'progress.json',groups)
    part_reports={};nc=a.c
    for b,cr in changes.items():
        try:
            try:probe,slack=repack_parts(nc,b,cr);method='existing'
            except ValueError:probe,slack,method=repack_global(nc,b,cr)
            nc=probe;part_reports[str(b)]={'fits':True,'slack':slack,'method':method}
        except Exception as ex:part_reports[str(b)]={'fits':False,'error':str(ex)}
    bank=a.banks[0];payload=len(bank['frames'])*4;seen={};streams=[]
    for f in bank['frames']:
        n=f['index'];rr=raws[n]if n in raws else raw(a,0,n);count=counts.get(n,f['tile_count']);key=(rr,count)
        if key in seen:continue
        if n in raws:cb=encode_stream(rr)
        else:dec=decode_stream(a.g,f['offset'],f['limit'],count*128);cb=a.g[f['offset']:dec.end]
        seen[key]=payload;payload+=len(cb);streams.append({'first_ref':n,'size':len(cb),'selected':n in raws})
    span=bank['end']-bank['base'];r={'parent_sha256':sha(a.data),'target_manifest_sha256':sha((s/'manifest.json').read_bytes()),'groups':groups,'parts':part_reports,'graphics':{'fixed_span':span,'needed_bytes':payload,'remaining':span-payload,'fits':payload<=span,'unique_raw_and_count_streams':len(seen),'streams':streams},'arc_written':False,'pixel_reduction':False,'bank_directory_changed':False,'target_physical_layout_optimization_pending':True,'scope':'원화/효과무손실32타일첫배치용량만조사. 원총열/발/부분미술최종수용및ARC전체검증은별도.'};write(d/'report.json',r);print(json.dumps({'parts':part_reports,'graphics_remaining':span-payload}),flush=True)
if __name__=='__main__':main()
