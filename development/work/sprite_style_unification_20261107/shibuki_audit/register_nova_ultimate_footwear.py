"""Ultimate 노바 하체 교정 원화를 별도 보존·고정 등록한다."""
from pathlib import Path
import json
from PIL import Image
from native_pose_pack import need,sha,write
from register_chaser_ultimate import main as register
H=Path(__file__).resolve().parent

def main():
    s=H/'nova_ultimate_footwear_inputs01';g=s/'generated.png';need(not g.exists(),'기존 원화 보존')
    m=json.loads((s/'input.json').read_text('utf8'))
    for name,digest in m['files'].items():need(sha((s/name).read_bytes())==digest,'입력 변경')
    p=Path('<LOCAL_PATH>')
    g.write_bytes(p.read_bytes());write(s/'generation_receipt.json',{'tool':'builtin image_gen','source_default_path':str(p),'sha256':sha(g.read_bytes()),'actual_size':list(Image.open(g).size),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'accepted':False,'policy':'종아리·신발만 국소 donor. 전체 몸체 교체로 채택하지 않음.'})
    register('nova_ultimate_footwear_inputs01','nova_ultimate_footwear_native01',(213,215))
if __name__=='__main__':main()
