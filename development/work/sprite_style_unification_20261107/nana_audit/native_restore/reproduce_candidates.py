from prepare_native import *

def main():
 assets,_=data();report={'reproducible':True,'files':{},'rejected':[],'scope':'최초 전조합 검사가 통과한 자원을 동일 입력으로 재구성하여 실제 ARC와 바이트 대조. 같은 전조합을 반복 실행하지 않음.'}
 for name,original in assets.items():
  result,*_=build_candidate(original,name);f=OUT/'prepared_v1'/name;need(f.read_bytes()==result,'Reproduction mismatch');report['files'][name]=sha(result)
 cases={'bad_arc':lambda:build_candidate(bytes([assets['PL00_U.ARC'][0]^1])+assets['PL00_U.ARC'][1:],'PL00_U.ARC'),'wrong_resource':lambda:build_candidate(assets['PL00_U.ARC'],'PL02_U.ARC'),'wrong_manifest':lambda:validate_registration(b'{}'),'changed_target':lambda:validate_registration(overrides={'fourth_target_144.png':b'changed'}),'changed_hair':lambda:validate_registration(overrides={'ultimate_target_069.png':b'changed'}),'changed_source_recipe':lambda:validate_registration(overrides={'preview_restore.py':b'changed'}),'changed_registration':lambda:validate_registration(overrides={'ultimate_registration_v1.json':b'changed'})}
 for name,fn in cases.items():
  try:fn()
  except ValueError as e:report['rejected'].append({'case':name,'reason':str(e)})
  else:raise ValueError('Invalid input accepted: '+name)
 need(digest(SOURCE)==EXPECTED,'Parent changed');write(OUT/'prepared_v1/reproduction.json',report);print(json.dumps(report))

if __name__=='__main__':main()
