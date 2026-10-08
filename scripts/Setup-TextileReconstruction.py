"""Fetch pinned, local-only research inference tools without changing PyTorch.

Run with the existing tf4dgs-dynamic Python. Downloads stay outside Git.
MASt3R code and weights are CC BY-NC-SA 4.0; see the source manifest.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    dict(name='sam2', repository='https://github.com/facebookresearch/sam2.git',
         revision='0f6515ae853c40420ea8e3dd250f8031bbf03023', license='Apache-2.0',
         weights='sam2_hiera_tiny.pt', url='https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_tiny.pt'),
    dict(name='co-tracker', repository='https://github.com/facebookresearch/co-tracker.git',
         revision='82e02e8029753ad4ef13cf06be7f4fc5facdda4d', license='CC BY-NC 4.0 (model); see upstream license',
         weights='scaled_online.pth', url='https://huggingface.co/facebook/cotracker3/resolve/main/scaled_online.pth'),
    dict(name='mast3r', repository='https://github.com/naver/mast3r.git',
         revision='f5209afc300cec36239a7ac992263f36847bbba0', license='CC BY-NC-SA 4.0',
         weights='MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth',
         url='https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth'),
]
DEPENDENCIES = ['hydra-core==1.3.2', 'omegaconf==2.3.0',
                'antlr4-python3-runtime==4.9.3', 'iopath==0.1.10',
                'portalocker==3.2.0', 'einops==0.8.1',
                'huggingface-hub==0.28.1', 'tqdm==4.67.1', 'roma==1.5.6']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-packages', action='store_true')
    args = parser.parse_args()
    if not args.skip_packages:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check',
                        '-c', str(ROOT/'configs/dynamic_gpu_win64.lock.txt'), *DEPENDENCIES], check=True)
    manifest_path = ROOT/'configs/textile_reconstruction_sources.json'
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    previous_by_name = {s['name']: s for s in previous.get('sources', [])}
    for source in SOURCES:
        local = ROOT/'.local/tools'/source['name']
        if not local.exists():
            subprocess.run(['git', 'clone', '--recursive', source['repository'], str(local)], check=True)
            subprocess.run(['git', '-C', str(local), 'checkout', source['revision']], check=True)
            subprocess.run(['git', '-C', str(local), 'submodule', 'update', '--init', '--recursive'], check=True)
        revision = subprocess.check_output(['git', '-C', str(local), 'rev-parse', 'HEAD'], text=True).strip()
        if revision != source['revision']:
            raise ValueError(f"Refusing to replace existing {source['name']} revision {revision}")
        target = local/'checkpoints'/source['weights']
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            temporary = target.with_suffix(target.suffix+'.part')
            print('Downloading official weights: '+source['name'], flush=True)
            with urllib.request.urlopen(source['url'], timeout=90) as response, temporary.open('wb') as output:
                total = 0
                while chunk := response.read(8*1024*1024):
                    output.write(chunk)
                    total += len(chunk)
                    if total % (128*1024*1024) < len(chunk):
                        print(f"{source['name']}: {total/1024**2:.0f} MiB", flush=True)
            temporary.replace(target)
        digest = hashlib.sha256()
        with target.open('rb') as file:
            while chunk := file.read(8*1024*1024):
                digest.update(chunk)
        source['sha256'] = digest.hexdigest()
        expected = previous_by_name.get(source['name'], {}).get('sha256')
        if expected and expected != source['sha256']:
            raise ValueError('Checkpoint digest differs from the recorded official download')
        source['local'] = str(local.relative_to(ROOT)).replace('\\', '/')
        source['checkpoint'] = str(target.relative_to(ROOT)).replace('\\', '/')
        if source['name'] == 'mast3r':
            source['submodules'] = {'dust3r':'3cc8c88c413bb9e34c41db0e0eef99c2ee010b12',
                                    'dust3r/croco':'d7de0705845239092414480bd829228723bf20de'}
        print(source['name']+' SHA256 '+source['sha256'], flush=True)
        manifest = dict(purpose='Local inference for textile masks, dense stereo and temporal constraints',
                        torch_policy='Keep working torch 2.4.0+cu124 / gsplat 1.5.3 Windows wheel',
                        packages=DEPENDENCIES, sources=SOURCES[:SOURCES.index(source)+1])
        manifest_path.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    import torch
    print(json.dumps({'torch':torch.__version__, 'cuda':torch.cuda.is_available(),
                      'device':torch.cuda.get_device_name(0)}), flush=True)


if __name__ == '__main__':
    main()
