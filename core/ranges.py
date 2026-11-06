"""Interpretação de intervalos de páginas digitados pelo usuário ("1-3, 5")."""


def parse_ranges(text: str, n_pages: int) -> list[list[int]]:
    """Converte "1-3, 5" em [[0, 1, 2], [4]] (índices base 0).

    Cada item separado por vírgula vira um grupo. Levanta ValueError para
    texto vazio, intervalo invertido ou página fora de 1..n_pages.
    """
    groups: list[list[int]] = []
    for raw in text.split(','):
        part = raw.strip()
        if not part:
            continue
        if '-' in part:
            a, _, b = part.partition('-')
            try:
                start, end = int(a), int(b)
            except ValueError:
                raise ValueError(f'Intervalo inválido: "{part}"') from None
            if start > end:
                raise ValueError(f'Intervalo invertido: "{part}"')
        else:
            try:
                start = end = int(part)
            except ValueError:
                raise ValueError(f'Página inválida: "{part}"') from None
        if start < 1 or end > n_pages:
            raise ValueError(f'"{part}" fora do documento (1 a {n_pages})')
        groups.append(list(range(start - 1, end)))
    if not groups:
        raise ValueError('Nenhuma página informada')
    return groups
