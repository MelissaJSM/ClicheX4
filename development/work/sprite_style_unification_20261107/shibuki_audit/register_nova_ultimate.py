"""Ultimate 노바 준비4의 생성물을 보존하고 기존 고정셀 등록기로 읽는다."""
from pathlib import Path
from PIL import Image
from native_pose_pack import need,sha,write
from register_chaser_ultimate import main as register
H=Path(__file__).resolve().parent
def main():
    s=H/'nova_ultimate_inputs01';g=s/'generated.png';need(not g.exists(),'새 원화 보존')
    p=Path('<LOCAL_PATH>');g.write_bytes(p.read_bytes())
    write(s/'generation_receipt.json',{'tool':'builtin image_gen','source_default_path':str(p),'sha256':sha(g.read_bytes()),'actual_size':list(Image.open(g).size),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'accepted':False,'registration_pending':True,'scope':'Ultimate 준비213/215 전후4 의상. 생성된 신발/종아리 재질은 별도 검토.'})
    register('nova_ultimate_inputs01','nova_ultimate_native01',(213,215))
if __name__=='__main__':main()
