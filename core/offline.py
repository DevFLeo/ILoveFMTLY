"""Bloqueio de rede.

Chamado no início do app: depois disso, qualquer tentativa de abrir conexão
falha com OfflineError. É a garantia de que nenhum documento sai da máquina.
"""

import socket


class OfflineError(OSError):
    """Tentativa de acesso à rede com o modo offline ativo."""


_enabled = False


def _blocked(*_args, **_kwargs):
    raise OfflineError('ILoveFMTLY roda offline: acesso à rede bloqueado.')


class _BlockedSocket(socket.socket):
    def __init__(self, family=-1, type=-1, proto=-1, fileno=None):
        # AF_UNIX/socketpair locais continuam liberados; só rede é bloqueada.
        if family in (socket.AF_INET, socket.AF_INET6, -1):
            _blocked()
        super().__init__(family, type, proto, fileno)


def enable() -> None:
    global _enabled
    if _enabled:
        return
    socket.socket = _BlockedSocket
    socket.create_connection = _blocked
    socket.getaddrinfo = _blocked
    _enabled = True


def is_enabled() -> bool:
    return _enabled
