from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
s=(H/'register_shibuki_ultimate_hurt.py').read_text('utf8').replace('Ultimate 피격 의상 편집','Ultimate 등장 의상 편집')
s=s.replace("parent=ROOT/meta['parent_path'];need(sha(parent.read_bytes())==meta['parent_sha256']", "parent=ROOT/meta['ultimate_parent']['path'];need(sha(parent.read_bytes())==meta['ultimate_parent']['sha256']")
s=s.replace("['edit_target.png','accepted_ultimate_style.png']", "['edit_target.png','accepted_ultimate_style.png','old_coordinate_reference.png']")
p=H/'register_ultimate_arrival.py';assert not p.exists();p.write_text(s,'utf8')
print(hashlib.sha256((H/'ultimate_arrival_inputs01/page01/generated.png').read_bytes()).hexdigest())
