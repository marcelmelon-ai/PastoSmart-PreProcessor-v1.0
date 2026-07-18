"""
PastoSmart PreProcessor v1.0
Exportação de resultados: GeoTIFF e CSV.
"""

import os
import numpy as np
import rasterio
import pandas as pd
from typing import Dict, Any


class Exporter:
    """
    Salva arrays como GeoTIFF e estatísticas como CSV.

    Parâmetros
    ----------
    meta : dict
        Metadados rasterio do arquivo de origem.
    out_dir : str
        Pasta de destino.
    """

    def __init__(self, meta: dict, out_dir: str):
        self.meta    = meta.copy()
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

        # Força float32 e 1 banda por arquivo
        self.meta.update(dtype="float32", count=1, compress="lzw")

    def save_tif(self, arr: np.ndarray, filename: str):
        """
        Salva um array 2D como GeoTIFF float32.

        Parâmetros
        ----------
        arr      : np.ndarray (2D, float32)
        filename : str  (ex.: 'NDVI.tif')
        """
        out_path = os.path.join(self.out_dir, filename)
        with rasterio.open(out_path, "w", **self.meta) as dst:
            dst.write(arr.astype(np.float32), 1)

    def save_csv(self, stats: Dict[str, Dict[str, Any]], filename: str):
        """
        Salva as estatísticas de todas as bandas em um CSV.

        Parâmetros
        ----------
        stats    : dict {banda: {metrica: valor}}
        filename : str  (ex.: 'Estatisticas.csv')
        """
        rows = []
        for band_name, metrics in stats.items():
            row = {"banda": band_name}
            row.update(metrics)
            rows.append(row)

        df = pd.DataFrame(rows)
        out_path = os.path.join(self.out_dir, filename)
        df.to_csv(out_path, index=False, float_format="%.4f",
                  encoding="utf-8-sig")
