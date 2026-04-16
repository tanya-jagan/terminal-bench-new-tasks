import subprocess
result = subprocess.run(["./licensechecker", "tb3testuser", "33408-12814-04757-36483"], capture_output=True, text=True)
print('returncode', result.returncode)
print('stdout:', repr(result.stdout))
print('stderr:', repr(result.stderr))
PY
