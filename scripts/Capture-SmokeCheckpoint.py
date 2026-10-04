"""Keep a genuine intermediate checkpoint for the installation resume test."""
import os
from pathlib import Path
import shutil

import lichtfeld as lf


@lf.on_post_step
def capture_intermediate_checkpoint(_hook):
    if lf.context().iteration == 10:
        output = Path(os.environ['TF4DGS_SMOKE_OUTPUT'])
        source = output / 'checkpoints' / 'checkpoint.resume'
        destination = output / 'checkpoints' / 'intermediate_10.resume'
        shutil.copy2(source, destination)
        lf.log.info('TF4DGS: preserved the iteration-10 checkpoint for resume validation')
