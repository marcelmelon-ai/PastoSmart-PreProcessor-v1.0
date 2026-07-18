"""
PastoSmart PreProcessor v1.0
Normalização robusta de bandas usando percentis P2–P98.
Opcionalmente corrige outliers e limita ao intervalo [0, 1].
"""

import numpy as np


class Normalizer:
    """
    Aplica normalização linear robusta em um array de banda.

    Parâmetros
    ----------
    correct_outliers : bool
        Se True, valores abaixo de p2 são substituídos por p2,
        e valores acima de p98 são substituídos por p98 (clamp).
    clip_01 : bool
        Se True, o resultado é limitado ao intervalo [0.0, 1.0].
    """

    def __init__(self, correct_outliers: bool = True, clip_01: bool = True):
        self.correct_outliers = correct_outliers
        self.clip_01          = clip_01

    def normalize(self, arr: np.ndarray,
                  p2: float, p98: float) -> np.ndarray:
        """
        Normaliza o array usando a fórmula:
            norm = (arr - p2) / (p98 - p2)

        Parâmetros
        ----------
        arr  : np.ndarray (float32) — array bruto da banda
        p2   : float — percentil 2 (mínimo robusto)
        p98  : float — percentil 98 (máximo robusto)

        Retorna
        -------
        np.ndarray (float32) normalizado.
        """
        out = arr.copy().astype(np.float32)

        # Corrige outliers antes da normalização
        if self.correct_outliers:
            out = np.where(out < p2,  p2,  out)
            out = np.where(out > p98, p98, out)

        # Evita divisão por zero
        denom = p98 - p2
        if denom == 0:
            return np.zeros_like(out)

        out = (out - p2) / denom

        # Limita ao intervalo [0, 1]
        if self.clip_01:
            out = np.clip(out, 0.0, 1.0)

        # Preserva NaN original
        out[np.isnan(arr)] = np.nan

        return out
