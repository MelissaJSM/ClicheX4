from pathlib import Path
import json,hashlib,shutil
D=Path(__file__).resolve().parent;ROOT=D.parents[2];out=D/'inputs_page03'
shutil.copy2(out/'prompt.txt',out/'prompt_attempt01.txt');shutil.copy2(out/'manifest.json',out/'manifest_attempt01.json')
failure={'tool':'builtin image_gen','result':'output moderation rejection','category':'sexual','request_id':'894fe801-c380-4128-b266-f2ff8ecab37c','image_returned':False,'scope':'사다리의 정상 이동 자세를 제작하던 중 결과물이 제공되지 않았다.','followup':'비성적이며 의상으로 덮인 정상 사다리 동작이라는 조건을 명확히 한다. 출력 검수 전 적용하지 않는다.'}
(out/'attempt01_failure.json').write_text(json.dumps(failure,ensure_ascii=False,indent=2)+'\n','utf8')
s=(out/'prompt.txt').read_text('utf8')
s+='\nThese are nonsexual, fully clothed game-action sprites. Keep the outfits opaque and closed over the torso and hips in every climbing pose, including the rear crouch: the skirt and opaque dark fitted shorts cover the hips completely. No exposed buttocks, underwear, lingerie, suggestive posing or upskirt viewpoint. The camera stays at the original side-on game angle. Focus on readable hands gripping the ledge, the cloth folds and hair strands.'
(out/'prompt.txt').write_text(s,'utf8');m=json.loads((out/'manifest.json').read_text('utf8'))
for q in m['inputs']:q['sha256']=hashlib.sha256((ROOT/q['path']).read_bytes()).hexdigest()
(out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8')
