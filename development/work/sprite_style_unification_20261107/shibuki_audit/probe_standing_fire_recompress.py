"""부모의 원시 데이터는 그대로 두고 독립 LZ 재압축의 여유만 읽는다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'work/tools'))
from native_pose_pack import need,write,sha
from scripts.export_x_consistency import Archive
from src.psx_player import decode_stream
from src.psx_compress import encode_stream
from psx_compress_cost import encoded_cost
def main():
    d=H/'standing_fire_recompress01';need(not d.exists(),'새 폴더 필요');d.mkdir()
    a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());groups={}
    for f in a.banks[0]['frames']:groups.setdefault(f['offset'],[]).append(f)
    rows=[]
    for off,fs in groups.items():
        if any(f['index']in range(85,93)for f in fs):continue
        f=fs[0];dec=decode_stream(a.g,off,f['limit'],f['tile_count']*128);before=dec.end-off;after=encoded_cost(dec.data)
        if after<before:
            code=encode_stream(dec.data);need(len(code)==after and decode_stream(code,0,len(code),len(dec.data)).data==dec.data,'재압축 왕복 불일치')
            (d/f'{f["index"]:03}_compressed.bin').write_bytes(code)
        rows.append({'refs':[q['index']for q in fs],'offset':off,'tile_count':f['tile_count'],'raw_sha256':sha(dec.data),'before':before,'after':after,'saving':max(0,before-after)})
    r={'parent_sha256':sha(a.data),'groups':rows,'total_saving':sum(r['saving']for r in rows),'arc_written':False,'raw_changed':False,'scope':'동일 원시 압축스트림의 독립 종료 토큰 왕복. 후보 ARC에는 미적용.'};write(d/'report.json',r);print(json.dumps({'groups':len(rows),'saving':r['total_saving'],'positive':[r for r in rows if r['saving']]}))
if __name__=='__main__':main()
