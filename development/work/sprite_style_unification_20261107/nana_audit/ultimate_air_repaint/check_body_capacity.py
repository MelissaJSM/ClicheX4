"""새 몸체 자체의 32타일/16파트 배치를 시험. 양폼·사격 전체 합격 아님."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,write,need
from make_body_cycle import source
from scripts.prepare_shibuki_ultimate_production import pack_shared
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());rows=[]
 for n in range(33,55,2):
  body=np.array(Image.open(source(n)));raw,assign=pack_shared(bytes(4096),32,[body[80:240,80:240]],set(range(32))-{0,16},[16]);parts=assign[0];need(all(t%16 for t,x,y,f in parts),'GPU first-column tile');rows.append({'ref':n,'body_indexed_sha256':sha(body.tobytes()),'assigned_parts':len(parts),'used_tiles':len({p[0]for p in parts}),'native_buffer_bytes':len(raw),'tile0_16_unused':True,'before_body_only':True})
 write(D/'body_capacity.json',{'passed':True,'parent_sha256':sha(a.data),'frames':rows,'scope':'Capacity probe for each nonfiring before body alone. Not a complete before/after/firing pair packing claim. No game ARC produced.','full_4_variants_per_pair_verified':False,'native_packed':False});print(json.dumps(rows))
if __name__=='__main__':main()
