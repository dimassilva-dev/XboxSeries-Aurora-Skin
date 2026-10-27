"""Fonte do relógio feita só de traços retos (cantos chanfrados), para o shader das capas.
Cada algarismo é uma máscara de bits sobre a lista SEGS (caixa 20 x 30 px, y para baixo)."""
SEGS = [
    ((7.5, 2), (12.5, 2)),  # 0  barra de cima
    ((7.5, 2), (2, 7.5)),   # 1  canto sup. esquerdo
    ((12.5, 2), (18, 7.5)), # 2  canto sup. direito
    ((2, 7.5), (2, 12)),    # 3  esquerda alta
    ((18, 7.5), (18, 12)),  # 4  direita alta
    ((5.5, 15), (14.5, 15)),  # 5  barra do meio
    ((2, 12), (5.5, 15)),  # 6  meio: esquerda alta -> barra
    ((18, 12), (14.5, 15)),  # 7  meio: direita alta -> barra
    ((5.5, 15), (2, 18)),  # 8  meio: barra -> esquerda baixa
    ((14.5, 15), (18, 18)),  # 9  meio: barra -> direita baixa
    ((2, 18), (2, 22.5)),   # 10 esquerda baixa
    ((18, 18), (18, 22.5)), # 11 direita baixa
    ((2, 22.5), (7.5, 28)), # 12 canto inf. esquerdo
    ((18, 22.5), (12.5, 28)),  # 13 canto inf. direito
    ((7.5, 28), (12.5, 28)),  # 14 barra de baixo
    ((2, 12), (2, 18)),    # 15 esquerda meio (0, 6)
    ((18, 12), (18, 18)),  # 16 direita meio (0, 9)
    ((18, 12), (2.5, 28)),  # 17 diagonal do 2
    ((2.5, 28), (18, 28)),  # 18 base reta do 2
    ((2, 2), (18, 2)),     # 19 topo reto (5, 7)
    ((18, 2), (8, 28)),    # 20 diagonal do 7
    ((11.5, 2), (11.5, 28)),  # 21 haste do 1
    ((11.5, 2), (6, 6.5)),  # 22 bandeira do 1
    ((14, 2), (2, 20)),    # 23 diagonal do 4
    ((2, 20), (18.5, 20)),  # 24 barra do 4
    ((14, 2), (14, 28)),   # 25 haste do 4
    ((2, 2), (2, 14)),     # 26 esquerda do 5
    ((2, 14), (14.5, 14)),  # 27 barra do 5
    ((14.5, 14), (18, 17.5)),  # 28 canto do 5
    ((18, 17.5), (18, 22.5)),  # 29 direita baixa do 5
    ((8, 15), (14.5, 15)),  # 30 barra curta do 3
]
DIGITS = {
    0: [0, 1, 2, 3, 4, 15, 16, 10, 11, 12, 13, 14],
    1: [21, 22],
    2: [1, 0, 2, 4, 17, 18],
    3: [1, 0, 2, 4, 7, 30, 9, 11, 13, 14, 12],
    4: [23, 24, 25],
    5: [19, 26, 27, 28, 29, 13, 14, 12],
    6: [2, 0, 1, 3, 15, 10, 12, 14, 13, 11, 9, 5, 8],
    7: [19, 20],
    8: [0, 1, 2, 3, 4, 6, 7, 5, 8, 9, 10, 11, 12, 13, 14],
    9: [1, 0, 2, 3, 4, 6, 5, 7, 16, 11, 13, 14, 12],
}
MASK = {n: sum(1 << s for s in segs) for n, segs in DIGITS.items()}
HALF = 2.9   # meia espessura do traço (negrito, ~5.8 px como a Inter Bold de 40 px)
