"""
PastoSmart PreProcessor v1.0
Módulo de cálculo de estatísticas por banda.
"""

import numpy as np
from typing import Dict, Any


class BandStatistics:
    """
    Calcula estatísticas descritivas de um array de banda.

    Parâmetros
    ----------
    config : dict
        Flags booleanas indicando quais métricas calcular
        (min, max, mean, median, p2, p98, std, saturated, invalid).
    """

    # Valor máximo para um pixel de 16 bits (DJI Mavic Multispectral, etc.)
    SATURATED_THRESHOLD_16BIT = 65530

    def __init__(self, config: dict):
        self.cfg = config

    def compute(self, arr: np.ndarray) -> Dict[str, Any]:
        """
        Calcula e retorna um dicionário com as métricas solicitadas.

        Parâmetros
        ----------
        arr : np.ndarray (float32)
            Array 2D da banda. NaN representa pixels inválidos/nodata.

        Retorna
        -------
        dict com as métricas calculadas.
        """
        stats: Dict[str, Any] = {}

        # Máscara de pixels válidos (não-NaN)
        valid = arr[~np.isnan(arr)]
        total_pixels = arr.size

        if valid.size == 0:
            return {"error": "Banda sem pixels válidos"}

        if self.cfg.get("min"):
            stats["min"] = float(np.min(valid))

        if self.cfg.get("max"):
            stats["max"] = float(np.max(valid))

        if self.cfg.get("mean"):
            stats["mean"] = float(np.mean(valid))

        if self.cfg.get("median"):
            stats["median"] = float(np.median(valid))

        if self.cfg.get("p2"):
            stats["p2"] = float(np.percentile(valid, 2))

        if self.cfg.get("p98"):
            stats["p98"] = float(np.percentile(valid, 98))

        if self.cfg.get("std"):
            stats["std"] = float(np.std(valid))

        if self.cfg.get("saturated"):
            # Pixels acima do limiar de saturação
            n_sat = int(np.sum(valid >= self.SATURATED_THRESHOLD_16BIT))
            stats["saturated_count"] = n_sat
            stats["saturated_pct"]   = 100.0 * n_sat / total_pixels

        if self.cfg.get("invalid"):
            # Pixels NaN ou zero
            n_inv = int(np.sum(np.isnan(arr)) + np.sum(arr == 0))
            stats["invalid_count"] = n_inv
            stats["invalid_pct"]   = 100.0 * n_inv / total_pixels

        return stats
