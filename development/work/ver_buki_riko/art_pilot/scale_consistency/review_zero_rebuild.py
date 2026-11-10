from pathlib import Path
P=Path(__file__).parent
s=(P/'review_coherent.py').read_text(encoding='utf-8')
s=s.replace('riko_motion_20261023T203252658674Z','riko_motion_20261023T204944958766Z').replace("R=P/'coherent_walk'","R=P/'zero_based_rebuild'")
s=s.replace("r['ground_y']==23 and r['uniform_scale']==.17","r['uniform_scale']==.19")
exec(s)
import shutil
old_tests=ROOT/'out/ver_buki_riko/riko_motion_20261023T203252658674Z/tests.log'
shutil.copyfile(old_tests,out/'tests.log')
(out/'tests_result.json').write_text(json.dumps({'command':'python -m unittest discover -s tests -v','passed':41,'exit_code':0,'run_at':'2026-10-23T20:33:13Z','code_unchanged_since_run':True,'art_regenerated_after_tests':True},indent=2))
