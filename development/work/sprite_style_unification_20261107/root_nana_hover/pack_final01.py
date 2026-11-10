"""Apply the verified empty-head encoding to the final 50 reviewed hover layers."""
from pathlib import Path
import hashlib
D=Path(__file__).resolve().parent;W=D.parent
source=W/'nana_audit/base_hover_pack_support01/build_candidate.py'
code=source.read_text('utf8')
before="D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1];R=W/'root_nana_hover';H=W/'shibuki_audit';U=N/'ultimate_hover_repaint'"
after="D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];R=D;N=W/'nana_audit';H=W/'shibuki_audit';U=N/'ultimate_hover_repaint'"
assert code.count(before)==1;code=code.replace(before,after)
before="folder=R/('body_layers_probe01'if n%2 else'shoot_layers_probe02')"
assert code.count(before)==1;code=code.replace(before,"folder=R/'final_targets01'")
assert code.count("default='candidate01'")==1;code=code.replace("default='candidate01'","default='packed_hover_final01'")
exec(compile(code,str(source),'exec'),dict(__file__=str(__file__),__name__='__main__'))
