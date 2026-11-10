"""검증된 원표 미리보기 구조를 새85..92 두폼 검토용으로 분리한다."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'review_standing_special_sequence.py').read_text('utf8')
s=s.replace('새특수3 네폼을 실제 BR21 원표95/96/97/104/105 순서로 표시한다.','새85..92 두폼을 실제 BR22 원표88/89/90/91/94 순서로 표시한다.')
s=s.replace("standing_special_sequence01","standing_fire_sequence01")
start=s.index("    paths=");end=s.index("    arcs={}",start)
s=s[:start]+"    paths={'base':H/'prepared_standing_fire_base01/PL00_U.ARC'}\n    expected={'base':'4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175'}\n"+s[end:]
s=s.replace('20261107_v21','20261107_v22').replace('6d550cbcbcf06315c07aa17bbee75e07f64e4f0dc4efd6b2f381a3dc7a40db42','54e53da83b0255e6123dc3c9d6ffeab867bc5201107b1a0ed89c798038739e99')
s=s.replace('(95,96,97,104,105)','(88,89,90,91,94)').replace("forms=['base','fourth','before','after']","forms=['base','fourth']")
s=s.replace("(('base','base',0),('fourth','base',15),('before','ultimate',15),('after','ultimate',0))","(('base','base',0),('fourth','base',15))")
s=s.replace('# 95/96은 같은 전환을 공유하고104/105는마지막99유지시간만다르다.','# 88은 일반사격 복귀,91은 위로 들어올리는 동작까지 포함한다.').replace('(95,104)','(88,91)')
s=s.replace('시부키 특수3 네폼 원순서 검토','시부키85..92 두폼 원순서 검토').replace('특수95/96/97 네폼 원표 표시','새85..92 기본·포스 원표 표시').replace('왼쪽부터 기본·포스·재킷·후폼. 실제 BR21 EXE 표95/96/97/104/105','왼쪽부터 기본·포스. 실제 BR22 EXE 표88/89/90/91/94')
s=s.replace('width:1152px','width:768px').replace('height:288px','height:384px').replace('max-width:1152px','max-width:768px').replace('width="384"','width="192"').replace('clearRect(0,0,384,96)','clearRect(0,0,192,96)')
s=s.replace('말미96을 고정 대기시간으로 주장하지 않습니다. 표97은 복제체의 그림96이며 그림97과 구별합니다.','말미92를 고정96 게임프레임으로 주장하지 않습니다. 별도 투사체와 외부 타이머는 이 검토기에서 실행하지 않습니다.')
s=s.replace('reset(id=95)','reset(id=88)').replace('ready=true;reset()','ready=true;reset()')
out=H/'review_standing_fire_sequence.py'
if out.exists():raise ValueError('기존 도구 보호')
out.write_text(s,'utf8')
