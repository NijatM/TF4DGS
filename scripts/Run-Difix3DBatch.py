"""Run the audited PLY list sequentially in isolated CUDA processes."""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'outputs/difix3d_necto_001'
LOGS=ROOT/'.local/workflows/difix3d_necto_001'
manifest=json.loads((WORK/'manifest.json').read_text())
LOGS.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,HF_HOME=str(ROOT/'.local/cache/difix3d'),PYTHONUNBUFFERED='1')
results=[]
for index,entry in enumerate(manifest['files']):
    status='failed'
    for edge in (768,512):
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        logfile=LOGS/f'model_{index:02d}_edge_{edge}_{stamp}.log'
        with logfile.open('w',encoding='utf8') as log:
            code=subprocess.call([sys.executable,str(ROOT/'scripts/Repair-Difix3DSplats.py'),
                '--stage','batch','--index',str(index),'--steps','750','--training-edge',str(edge)],
                cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        if code==0:status='completed';break
        text=logfile.read_text(encoding='utf8',errors='replace')
        if 'out of memory' not in text.lower():break
    results.append(dict(index=index,input=entry['name'],folder=entry['folder'],status=status))
    (WORK/'batch_state.json').write_text(json.dumps(dict(updated_utc=datetime.now(timezone.utc).isoformat(),models=results),indent=2))
    print(f'{index+1}/{len(manifest["files"])} {entry["name"]}: {status}',flush=True)
print('Batch finished; inspect per-model provenance and documentation.',flush=True)
if any(x['status']!='completed' for x in results):sys.exit(1)
