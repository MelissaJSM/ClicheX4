"""현재/원작 속도선 파츠 차이와 원시 타일을 읽기 전용 비교한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import decode_stream,indexed_atlas

def main():
    out=H/'ultimate_dash_streak_audit01';need(not out.exists(),'Fresh audit');out.mkdir();p=H/'prepared_ultimate_air01/PL02_U.ARC';q=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.arc';a=Archive(p.read_bytes());orig=Archive(q.read_bytes());rows=[];pics=[]
    for n in(73,74):
        source={}
        for label,arc in(('parent',a),('original',orig)):
            f=arc.banks[0]['frames'][n];raw=decode_stream(arc.g,f['offset'],f['limit'],f['tile_count']*128).data;tile=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)[:16,96:112];r=records(arc.c,0,n);parts=[(i//4,*struct.unpack('<BBbb',r[i:i+4]))for i in range(0,len(r),4)];parts=[v for v in parts if v[2]==6];im=np.zeros((384,384),np.uint8)
            for pos,fl,t,x,y in parts:
                need(fl==0,'Unexpected streak flip');yy,xx=np.nonzero(tile);im[yy+y+160,xx+x+160]=tile[yy,xx]
            Image.fromarray(im).save(out/f'{n:03}_{label}_indices.png');rgba=a.rgba(im,0);rgba.save(out/f'{n:03}_{label}.png');pics.append((f'{n} {label} streaks only',rgba));source[label]={'tile_sha256':sha(tile.tobytes()),'parts':parts,'record_hex':b''.join(struct.pack('<BBbb',fl,t,x,y)for pos,fl,t,x,y in parts).hex(),'pixels':int((im>0).sum()),'raw_source_sha256':sha(raw)}
        need(source['parent']['tile_sha256']==source['original']['tile_sha256'],'Actual tile changed')
        need(source['parent']['pixels']==30 and source['original']['pixels']==54,'Unexpected effect pixel count');rows.append({'ref':n,**source})
    page(pics,a.composite(0,0)[0],out/'comparison.png',cols=2,scale=5)
    write(out/'report.json',{'parent':p.relative_to(ROOT).as_posix(),'parent_sha256':sha(p.read_bytes()),'original':q.relative_to(ROOT).as_posix(),'original_sha256':sha(q.read_bytes()),'rows':rows,'interpretation':'현재 부모는 원9개 중5개 속도선 레코드가 몸체 이전 순서에 남아 있음. 원작9개는 몸체 이후 레코드. 동일 tile6. GPU 우선순위/새 몸체 중첩은 후속 패킹 검증과 구분.','palette_bytes_changed':False,'game_modified':False,'proposal_written':False});print(json.dumps({'rows':[(r['ref'],r['parent']['pixels'],r['original']['pixels'])for r in rows]}))
if __name__=='__main__':main()
