"""Ferramentas de desenvolvedor (inspiradas no fmtly.dev, MIT), todas offline.

Forma das funções, conforme `Tool.dev_input` em ui/tools.py:
- 'text': fn(text, **params) -> str | bytes
- 'two':  fn(a, b, **params) -> str
- 'none': fn(**params) -> str | bytes
- 'file': fn(path, **params) -> str

Erro de entrada vira ValueError com mensagem em português.
"""
