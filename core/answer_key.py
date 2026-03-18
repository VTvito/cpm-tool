"""
CPM – Coloured Progressive Matrices
Chiave di risposta ufficiale (36 item, 3 set da 12).

⚠ Verificare sempre con il manuale dell'edizione in uso.
"""

# Risposta corretta per ogni item (numero 1-6)
ANSWER_KEY: dict[str, int] = {
    # Set A
    "A1":  4, "A2":  5, "A3":  1, "A4":  2, "A5":  6, "A6":  3,
    "A7":  6, "A8":  2, "A9":  1, "A10": 3, "A11": 4, "A12": 5,
    # Set Ab
    "Ab1": 6, "Ab2": 2, "Ab3": 1, "Ab4": 2, "Ab5": 5, "Ab6": 3,
    "Ab7": 5, "Ab8": 6, "Ab9": 4, "Ab10": 3, "Ab11": 4, "Ab12": 5,
    # Set B
    "B1":  3, "B2":  4, "B3":  3, "B4":  4, "B5":  2, "B6":  5,
    "B7":  6, "B8":  1, "B9":  2, "B10": 5, "B11": 6, "B12": 4,
}

# Raggruppamento item per set
SETS: dict[str, list[str]] = {
    "A":  [f"A{i}" for i in range(1, 13)],
    "Ab": [f"Ab{i}" for i in range(1, 13)],
    "B":  [f"B{i}" for i in range(1, 13)],
}

# Numero totale di item
TOTAL_ITEMS = 36
MAX_PER_SET = 12
