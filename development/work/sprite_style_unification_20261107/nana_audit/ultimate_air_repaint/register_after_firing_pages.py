"""맨팔 사격 원화를 별도 등록한다. 게임 자원은 수정하지 않는다."""
from pathlib import Path
import json,hashlib,subprocess,sys
D=Path(__file__).resolve().parent
DATA=[('a','e5839c04f1dce5a7f777d9b65f57667be69c8a1b0d493204957046c97eab361f'),('b','a78b9f7407242a01241741ffa478cf7c87b202017461b1d9e0acb935c8fb7331'),('c','c53c34a45bb69c5941778d12e7581096833ab4955070be00efc17b9a030a742b')]
for page,h in DATA:
    folder=D/f'firing_{page}_inputs_v1'
    plan=json.loads((folder/'before_poses.json').read_text('utf8'))
    for q in plan:
        q['mask']=0
        q['source_anchor']='matching new before firing body; common eye and original sole height'
        q.pop('rgba_sha256',None)
    (folder/'after_poses.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    subprocess.run([sys.executable,str(D/'register_body_page.py'),'--art',f'firing_{page}_after_v1/generated.png','--art-sha',h,'--inputs',f'firing_{page}_inputs_v1','--out',f'firing_{page}_after_registered_v1','--form','after'],check=True)
    art=D/f'firing_{page}_after_v1/generated.png'
    record={'tool':'builtin image_gen','source_art_sha256':h,'image_size':[1280,1280],'targets':[q['ref']for q in plan],'change':'새 재킷 사격 원화의 의상만 맨팔로 변경. 실제 등록·연결 검수는 별도.','native_packed':False,'runtime_verified':False}
    assert hashlib.sha256(art.read_bytes()).hexdigest()==h
    (art.parent/'generation.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
