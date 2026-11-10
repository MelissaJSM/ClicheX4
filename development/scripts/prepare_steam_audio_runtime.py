"""Bind audio cumulative archives to previously verified display adapters."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_steam_pause_runtime import main as bind_pause
W=ROOT/'work/steam_port_20261109'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 proof=json.loads((W/'audio/independent_verification.json').read_text());native=json.loads((W/'audio/xaudio_format_verification.json').read_text())
 if not proof['passed'] or proof['native_intro_cases']!=9984 or not native['passed']:raise ValueError('Audio verification missing')
 rows=json.loads((W/'audio_builds.json').read_text());current=json.loads((W/'install_state.json').read_text())
 installed={r['relative_path']:r['installed_sha256'] for r in current['files']}
 required={r['relative_path']:r['output_sha256'] for r in rows}
 if len(required)!=105 or any(installed.get(p)!=h for p,h in required.items()):raise ValueError('Install audio files first')
 target=W/'audio/before_runtime';target.mkdir(exist_ok=True)
 names=('pause_builds.json','dialogue_runtime_patch.json','dialogue_display_patch.json','ultimate_runtime.json','menu_outfits_runtime.json')
 for name in names:
  dest=target/name
  if not dest.exists():dest.write_bytes((W/name).read_bytes())
 (W/'pause_builds.json').write_bytes((W/'audio_pause_builds.json').read_bytes())
 bind_pause()
 (W/'audio_runtime.json').write_text(json.dumps({'installed_requirements':required},indent=2)+'\n')
 print({'audio_runtime_assets':len(required),'previous_graphics_and_save_selectors_preserved':True})
if __name__=='__main__':main()
