"""
PastoSmart PreProcessor v1.0
Construção de máscara de pixels válidos.
Um pixel é válido quando:
  - Não é NaN em nenhuma banda
  - Não é zero em todas as bandas (borda da imagem)
  - Está dentro de limites razoáveis (0 ≤ valor ≤ 1 após normalização)
"""

import numpy as np
from typing import Dict


class MaskBuilder:
    """Gera máscara booleana de pixels válidos a partir das bandas normalizadas."""

    def build(self, bands_norm: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Parâmetros
        ----------
        bands_norm : dict {nome_banda: array_float32}
            Bandas já normalizadas (valores esperados em [0, 1]).

        Retorna
        -------
        mask : np.ndarray (bool)
            True onde o pixel é válido.
        """
        first = next(iter(bands_norm.values()))
        mask = np.ones(first.shape, dtype=bool)

        for name, arr in bands_norm.items():
            # Pixels NaN → inválidos
            mask &= ~np.isnan(arr)
            # Pixels negativos após normalização → inválidos
            mask &= (arr >= 0.0)

        # Pixels onde TODAS as bandas são zero → provavelmente borda
        all_zero = np.ones(first.shape, dtype=bool)
        for arr in bands_norm.values():
            all_zero &= (arr == 0.0)
        mask &= ~all_zero

        return mask
