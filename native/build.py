"""Build the Windows x64 adapter and test its portable timing core. Requires ziglang."""
from pathlib import Path
import subprocess,sys,tempfile
root=Path(__file__).resolve().parents[1]
cc=[sys.executable,'-m','ziglang','cc']
with tempfile.TemporaryDirectory() as t:
    test=Path(t)/('timing-test.exe' if sys.platform == 'win32' else 'timing-test')
    subprocess.run(cc+['-O2','-UNDEBUG','-Wall','-Wextra','-Werror','-I',str(root/'native'),str(root/'tests/timing_test.c'),'-o',str(test)],check=True)
    subprocess.run([str(test)],check=True)
out=root/'scripts/io_packages/kh1_level_up_notices.dll'
out.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(cc+['-target','x86_64-windows-gnu','-O2','-shared','-s','-Wall','-Wextra','-Werror',str(root/'native/notices.c'),'-o',str(out),'-lkernel32'],check=True)
print(out)
