"""새 before와 after 재교정의 독립 고정 축척 읽기. 원래 후보를 덮지 않는다."""
from pathlib import Path
import json
import register_ultimate_wall_page01 as m
H=Path(__file__).resolve().parent
m.O=H/'ultimate_wall_native02';m.PATHS['after']=H/'ultimate_wall_after_retry01/generated.png'
m.SOURCES['after']='8a0f505b9a3f95156d5ad8f06f1eab373ef2ac891e2f1985a96bfc9403affcac'
m.UPDATE_INPUT_INFO=False
if __name__=='__main__':
    m.main()
    p=H/'ultimate_wall_after_retry01/inputs.json';v=json.loads(p.read_text('utf8'));v.update({'generated':True,'generated_sha256':m.SOURCES['after'],'native_registration':str(m.O.relative_to(m.ROOT)),'accepted':False,'slot_returned_to':'Nana Fourth dash / root'})
    m.write(p,v)
