import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCRIPT = r'''
import socket
from core import offline
offline.enable()
for attempt in (
    lambda: socket.create_connection(("example.com", 80), timeout=1),
    lambda: socket.socket(socket.AF_INET, socket.SOCK_STREAM),
    lambda: socket.getaddrinfo("example.com", 80),
):
    try:
        attempt()
    except offline.OfflineError:
        continue
    raise SystemExit("rede nao bloqueada")
print("ok")
'''


def test_enable_blocks_network():
    result = subprocess.run(
        [sys.executable, '-c', SCRIPT], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert result.stdout.strip() == 'ok'
