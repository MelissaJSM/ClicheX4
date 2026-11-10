from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;d=H/'ultimate_arrival135_arms01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not(d/'generated.png').exists()
data={'tool':'builtin imagegen','success':False,'output_saved':False,'http_status':400,'error_code':'moderation_blocked','stage':'output','category':['other'],'request_id':'bed2289a-5cd3-4046-a548-9e2e932d184a','prompt_sha256':sha(d/'prompt.txt'),'input_sha256':{n:sha(d/n)for n in('edit_target.png','joint_reference.png')},'candidate_accepted':False,'automatic_retry':False,'remaining':'135전후관절차이를미완료로유지.기존원화/동결ARC보존,효과관계및다른독립준비계속.'}
(d/'generation_failure.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
print(sha(d/'generation_failure.json'))
