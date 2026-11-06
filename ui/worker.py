"""Executa funções pesadas fora da thread da interface."""

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class _Signals(QObject):
    done = Signal(object)
    error = Signal(Exception)


class _Job(QRunnable):
    def __init__(self, fn, args, kwargs):
        super().__init__()
        self.fn, self.args, self.kwargs = fn, args, kwargs
        self.signals = _Signals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:  # repassado para a interface mostrar
            self.signals.error.emit(exc)
        else:
            self.signals.done.emit(result)


_jobs: set = set()  # mantém os sinais vivos até o fim do job


def run_in_thread(fn, *args, on_done=None, on_error=None, **kwargs) -> None:
    job = _Job(fn, args, kwargs)
    job.setAutoDelete(False)
    _jobs.add(job)

    def finish(_=None):
        _jobs.discard(job)

    if on_done:
        job.signals.done.connect(on_done)
    if on_error:
        job.signals.error.connect(on_error)
    job.signals.done.connect(finish)
    job.signals.error.connect(finish)
    QThreadPool.globalInstance().start(job)
