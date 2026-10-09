"""Small explicit compatibility patches; retain unified diffs in the project."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]

def replace(path,old,new):
    text=path.read_text()
    if new in text:return
    if old not in text:raise ValueError(f'Expected upstream text not found: {path}')
    path.write_text(text.replace(old,new))

def main():
    src=ROOT/'.local/research/4C4D'
    knn=ROOT/'.local/research/4DGaussians/submodules/simple-knn'
    replace(knn/'setup.py','"nvcc": []','"nvcc": (["-Xcompiler=/Zc:preprocessor"] if os.name == "nt" else [])')
    raster=ROOT/'.local/research/4DGaussians/submodules/depth-diff-gaussian-rasterization'
    replace(raster/'setup.py','"nvcc": ["-I"','"nvcc": (["-Xcompiler=/Zc:preprocessor"] if os.name == "nt" else []) + ["-I"')
    replace(src/'diff-gaussian-rasterization/setup.py','"nvcc": ["-O3",','"nvcc": (["-Xcompiler=/Zc:preprocessor"] if os.name == "nt" else []) + ["-O3",')
    # CUDA translation units need tensor types, not Python/autograd bindings.
    # Keeping torch/extension.h in ext.cpp avoids an NVCC/MSVC compiled-autograd
    # namespace failure while retaining the official pybind entry points.
    for path in [knn/'spatial.h',raster/'rasterize_points.h',raster/'rasterize_points.cu',src/'diff-gaussian-rasterization/rasterize_points.h',src/'diff-gaussian-rasterization/rasterize_points.cu']:
        replace(path,'#include <torch/extension.h>','#include <torch/types.h>')
    replace(src/'diff-gaussian-rasterization/setup.py', '"cxx": [\'-O3\', \'-DNDEBUG\']', '"cxx": (["/O2", "/DNDEBUG"] if os.name == "nt" else ["-O3", "-DNDEBUG"])')
    path=src/'utils/general_utils.py'
    replace(path,'from pointops2.functions.pointops import furthestsampling, knnquery','''# Random downsampling does not require pointops; import only when requested.
# TF4DGS native compatibility: no replacement of the pointops algorithms.
def knnquery(*args, **kwargs):
    from pointops2.functions.pointops import knnquery as implementation
    return implementation(*args, **kwargs)

def furthestsampling(*args, **kwargs):
    from pointops2.functions.pointops import furthestsampling as implementation
    return implementation(*args, **kwargs)''')
    dest=ROOT/'configs/temporal_patches';dest.mkdir(exist_ok=True)
    for label,repo in [('4dgaussians',ROOT/'.local/research/4DGaussians'),('4c4d',src)]:
        diff=subprocess.check_output(['git','-C',str(repo),'diff','--binary','--ignore-submodules=dirty']).decode('utf8')
        (dest/f'{label}.patch').write_text(diff,encoding='utf8')
    diff=subprocess.check_output(['git','-C',str(knn),'diff','--binary']).decode('utf8')
    (dest/'simple-knn.patch').write_text(diff,encoding='utf8')
    diff=subprocess.check_output(['git','-C',str(raster),'diff','--binary']).decode('utf8')
    (dest/'4dgaussians-rasterizer.patch').write_text(diff,encoding='utf8')

if __name__=='__main__':main()
