"""음성 전용 프로세스의 로컬 캐시·원격 모델 리비전을 고정한다."""
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "work/tools/seed-vc"
VOICE_ROOT = ROOT / "work/ver_buki_riko/voice_production/v1"


def configure():
    VOICE_ROOT.mkdir(parents=True, exist_ok=True)
    cache = ROOT / "work/tools/voice_cache"
    os.environ.update(HF_HOME=str(cache), HF_HUB_DISABLE_TELEMETRY="1", DO_NOT_TRACK="1",
                      HF_HUB_DISABLE_XET="1", HF_HUB_DISABLE_SYMLINKS_WARNING="1",
                      HF_HUB_DOWNLOAD_TIMEOUT="120", TOKENIZERS_PARALLELISM="false")
    sys.path.insert(0, str(REPO))
    os.chdir(REPO)


def model_revisions():
    from huggingface_hub import HfApi
    path = VOICE_ROOT / "model_revisions.local.json"
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    records = {}
    for name in ("Plachta/Seed-VC", "Plachta/ASTRAL-quantization", "funasr/campplus",
                 "nvidia/bigvgan_v2_22khz_80band_256x", "openai/whisper-small", "facebook/hubert-large-ll60k"):
        info = HfApi().model_info(name)
        records[name] = {"revision": info.sha,
                         "license": (info.card_data or {}).get("license", "unspecified")}
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


def load_v2():
    import torch
    import yaml
    from hydra.utils import instantiate
    from omegaconf import DictConfig
    import hf_utils
    from huggingface_hub import hf_hub_download
    revisions = model_revisions()

    def pinned_download(repo_id, model_filename="pytorch_model.bin", config_filename=None):
        kw = dict(repo_id=repo_id, revision=revisions[repo_id]["revision"],
                  cache_dir=str(ROOT / "work/tools/voice_cache/hub"))
        checkpoint = hf_hub_download(filename=model_filename, **kw)
        return checkpoint if config_filename is None else (checkpoint, hf_hub_download(filename=config_filename, **kw))

    hf_utils.load_custom_model_from_hf = pinned_download
    # Resolve Transformers and BigVGAN references to fixed local snapshots first.
    from huggingface_hub import snapshot_download
    snapshot_paths = {}
    for name, patterns in (
        ("openai/whisper-small", ["*.json", "*.txt", "*.model", "*.tiktoken"]),
        ("facebook/hubert-large-ll60k", ["config.json", "preprocessor_config.json", "model.safetensors", "pytorch_model.bin"]),
        ("nvidia/bigvgan_v2_22khz_80band_256x", ["config.json", "bigvgan_generator.pt"]),
    ):
        print("Preparing", name, flush=True)
        snapshot_paths[name] = snapshot_download(name, revision=revisions[name]["revision"], allow_patterns=patterns)
    config = yaml.safe_load((REPO / "configs/v2/vc_wrapper.yaml").read_text("utf-8"))
    for name in ("content_extractor_narrow", "content_extractor_wide"):
        for field in ("tokenizer_name", "ssl_model_name"):
            original = config[name][field]
            config[name][field] = snapshot_paths[original]
    config["vocoder"]["pretrained_model_name_or_path"] = snapshot_paths["nvidia/bigvgan_v2_22khz_80band_256x"]
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this local production run")
    torch.set_num_threads(8)
    wrapper = instantiate(DictConfig(config))
    wrapper.load_checkpoints()
    wrapper.to("cuda").eval()
    wrapper.setup_ar_caches(max_batch_size=1, max_seq_len=4096, dtype=torch.float16, device=torch.device("cuda"))
    return wrapper


def load_f0_model():
    """명시적 F0 조건을 받는 별도 Seed-VC 모델. v2 후보와 혼동하지 않는다."""
    import torch
    import yaml
    from types import SimpleNamespace
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download
    revisions = dict(model_revisions())
    pins_path = VOICE_ROOT / 'f0_model_revisions.local.json'
    if pins_path.exists():
        revisions = json.loads(pins_path.read_text('utf-8'))
    else:
        for name in ('lj1995/VoiceConversionWebUI', 'nvidia/bigvgan_v2_44khz_128band_512x'):
            info = HfApi().model_info(name)
            revisions[name] = {'revision':info.sha, 'license':(info.card_data or {}).get('license','unspecified')}
        pins_path.write_text(json.dumps(revisions,indent=2),encoding='utf-8')
    def download(repo_id, model_filename='pytorch_model.bin', config_filename=None):
        kw=dict(repo_id=repo_id,revision=revisions[repo_id]['revision'],cache_dir=str(ROOT/'work/tools/voice_cache/hub'))
        checkpoint=hf_hub_download(filename=model_filename,**kw)
        return checkpoint if config_filename is None else (checkpoint,hf_hub_download(filename=config_filename,**kw))
    import hf_utils
    hf_utils.load_custom_model_from_hf=download
    checkpoint,config_path=download('Plachta/Seed-VC','DiT_seed_v2_uvit_whisper_base_f0_44k_bigvgan_pruned_ft_ema_v2.pth',
        'config_dit_mel_seed_uvit_whisper_base_f0_44k.yml')
    config=yaml.safe_load(Path(config_path).read_text('utf-8'))
    for key,patterns in [('vocoder',['config.json','bigvgan_generator.pt']),
                         ('speech_tokenizer',['*.json','*.txt','*.model','*.tiktoken','model.safetensors'])]:
        name=config['model_params'][key]['name']
        print('Preparing F0 model dependency',name,flush=True)
        config['model_params'][key]['name']=snapshot_download(name,revision=revisions[name]['revision'],allow_patterns=patterns,
            cache_dir=str(ROOT/'work/tools/voice_cache/hub'))
    local_config=VOICE_ROOT/'f0_config.local.yml'
    local_config.write_text(yaml.safe_dump(config),encoding='utf-8')
    import inference
    inference.load_custom_model_from_hf=download
    os.environ['HF_HUB_CACHE']=str(ROOT/'work/tools/voice_cache/hub')
    torch.set_num_threads(8)
    return inference.load_models(SimpleNamespace(fp16=True,f0_condition=True,checkpoint=checkpoint,config=str(local_config)))


if __name__ == "__main__":
    configure()
    import torch
    print("Torch", torch.__version__, "GPU", torch.cuda.get_device_name(0), flush=True)
    model = load_v2()
    print("Seed-VC v2 loaded on CUDA", torch.cuda.memory_allocated() / 1024 ** 3, "GiB", flush=True)
