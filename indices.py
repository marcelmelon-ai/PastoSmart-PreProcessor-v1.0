"""
PastoSmart PreProcessor v1.0
Cálculo de índices de vegetação multiespectrais.

Índices implementados:
  NDVI, GNDVI, NDRE, SAVI, MSAVI, OSAVI, VARI, ClGreen, ClRE, EVI2
"""

import numpy as np
from typing import Dict, Optional


# Constante L para SAVI / OSAVI
SAVI_L  = 0.5
OSAVI_L = 0.16


class IndexCalculator:
    """
    Calcula índices de vegetação a partir de bandas normalizadas.

    Parâmetros
    ----------
    bands : dict {nome: array_float32}
        Bandas normalizadas (Green, Red, RedEdge, NIR).
    mask : np.ndarray (bool)
        Máscara de pixels válidos.
    """

    def __init__(self, bands: Dict[str, np.ndarray], mask: np.ndarray):
        self.b = bands
        self.mask = mask

    def _safe_div(self, numerator: np.ndarray,
                  denominator: np.ndarray) -> np.ndarray:
        """Divisão segura: retorna NaN onde denominador ≈ 0."""
        with np.errstate(invalid="ignore", divide="ignore"):
            result = np.where(
                np.abs(denominator) < 1e-10,
                np.nan,
                numerator / denominator
            )
        return result.astype(np.float32)

    def _get(self, *names) -> Optional[tuple]:
        """Retorna tupla de bandas ou None se alguma estiver ausente."""
        result = []
        for n in names:
            if n not in self.b:
                return None
            result.append(self.b[n].copy())
        return tuple(result)

    def compute(self, index_name: str) -> Optional[np.ndarray]:
        """
        Calcula o índice solicitado.

        Parâmetros
        ----------
        index_name : str — nome do índice (ex.: 'NDVI')

        Retorna
        -------
        np.ndarray (float32) ou None se bandas insuficientes.
        """
        fn = getattr(self, f"_calc_{index_name.lower()}", None)
        if fn is None:
            return None
        result = fn()
        if result is not None:
            # Aplica máscara: pixels inválidos → NaN
            result[~self.mask] = np.nan
        return result

    # ── Fórmulas ─────────────────────────────────────────────────────────

    def _calc_ndvi(self) -> Optional[np.ndarray]:
        """NDVI = (NIR - Red) / (NIR + Red)"""
        bands = self._get("NIR", "Red")
        if bands is None:
            return None
        nir, red = bands
        return self._safe_div(nir - red, nir + red)

    def _calc_gndvi(self) -> Optional[np.ndarray]:
        """GNDVI = (NIR - Green) / (NIR + Green)"""
        bands = self._get("NIR", "Green")
        if bands is None:
            return None
        nir, green = bands
        return self._safe_div(nir - green, nir + green)

    def _calc_ndre(self) -> Optional[np.ndarray]:
        """NDRE = (NIR - RedEdge) / (NIR + RedEdge)"""
        bands = self._get("NIR", "RedEdge")
        if bands is None:
            return None
        nir, re = bands
        return self._safe_div(nir - re, nir + re)

    def _calc_savi(self) -> Optional[np.ndarray]:
        """SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L)"""
        bands = self._get("NIR", "Red")
        if bands is None:
            return None
        nir, red = bands
        return self._safe_div(
            (nir - red) * (1 + SAVI_L),
            nir + red + SAVI_L
        )

    def _calc_msavi(self) -> Optional[np.ndarray]:
        """MSAVI = (2*NIR + 1 - sqrt((2*NIR+1)^2 - 8*(NIR-Red))) / 2"""
        bands = self._get("NIR", "Red")
        if bands is None:
            return None
        nir, red = bands
        with np.errstate(invalid="ignore"):
            inner = (2 * nir + 1) ** 2 - 8 * (nir - red)
            inner = np.where(inner < 0, 0, inner)   # evita sqrt negativo
            result = (2 * nir + 1 - np.sqrt(inner)) / 2.0
        return result.astype(np.float32)

    def _calc_osavi(self) -> Optional[np.ndarray]:
        """OSAVI = (NIR - Red) / (NIR + Red + L)  com L=0.16"""
        bands = self._get("NIR", "Red")
        if bands is None:
            return None
        nir, red = bands
        return self._safe_div(nir - red, nir + red + OSAVI_L)

    def _calc_vari(self) -> Optional[np.ndarray]:
        """VARI = (Green - Red) / (Green + Red - Blue)
           Nota: sem banda Blue, aproximamos Blue ≈ 0
        """
        bands = self._get("Green", "Red")
        if bands is None:
            return None
        green, red = bands
        # Sem banda Azul disponível, VARI simplificado:
        # VARI = (Green - Red) / (Green + Red)
        return self._safe_div(green - red, green + red)

    def _calc_clgreen(self) -> Optional[np.ndarray]:
        """ClGreen = (NIR / Green) - 1"""
        bands = self._get("NIR", "Green")
        if bands is None:
            return None
        nir, green = bands
        with np.errstate(invalid="ignore", divide="ignore"):
            result = np.where(green < 1e-10, np.nan, nir / green - 1)
        return result.astype(np.float32)

    def _calc_clre(self) -> Optional[np.ndarray]:
        """ClRE = (NIR / RedEdge) - 1"""
        bands = self._get("NIR", "RedEdge")
        if bands is None:
            return None
        nir, re = bands
        with np.errstate(invalid="ignore", divide="ignore"):
            result = np.where(re < 1e-10, np.nan, nir / re - 1)
        return result.astype(np.float32)

    def _calc_evi2(self) -> Optional[np.ndarray]:
        """EVI2 = 2.5 * (NIR - Red) / (NIR + 2.4*Red + 1)"""
        bands = self._get("NIR", "Red")
        if bands is None:
            return None
        nir, red = bands
        return self._safe_div(
            2.5 * (nir - red),
            nir + 2.4 * red + 1.0
        )
