"""
PastoSmart PreProcessor v1.0
Orquestrador do pipeline de processamento.
Coordena: leitura → estatísticas → normalização → máscara → índices → exportação.
"""

import os
import numpy as np
import rasterio

from statistics  import BandStatistics
from normalization import Normalizer
from masks       import MaskBuilder
from indices     import IndexCalculator
from exporter    import Exporter
from report      import ReportGenerator


# Palavras-chave para detecção automática de bandas nos metadados do GeoTIFF
BAND_KEYWORDS = {
    "Green":   ["green", "g", "band2", "b2", "550", "560"],
    "Red":     ["red",   "r", "band3", "b3", "660", "670"],
    "RedEdge": ["rededge", "re", "band4", "b4", "730", "740"],
    "NIR":     ["nir",  "near", "band5", "b5", "840", "860"],
}


class PreProcessor:
    """
    Orquestra todas as etapas do pipeline.

    Parâmetros
    ----------
    config : dict
        Dicionário com todas as opções escolhidas na interface.
    log_fn : callable
        Função para enviar mensagens de log à UI.
    progress_fn : callable
        Função para atualizar a barra de progresso (0-100).
    """

    def __init__(self, config: dict, log_fn, progress_fn):
        self.config      = config
        self.log         = log_fn
        self.set_progress = progress_fn

        self.src_path  = config["geotiff_path"]
        self.out_dir   = config["output_dir"]
        os.makedirs(self.out_dir, exist_ok=True)

        # Dados que serão preenchidos ao longo do pipeline
        self.meta       = {}          # metadados rasterio
        self.bands      = {}          # arrays numpy das bandas originais
        self.bands_norm = {}          # arrays normalizados
        self.mask       = None        # máscara booleana válida
        self.stats      = {}          # estatísticas por banda
        self.index_maps = {}          # índices calculados

    # ──────────────────────────────────────────────────
    #  ETAPA 1 – Abrir e ler o GeoTIFF
    # ──────────────────────────────────────────────────

    def _step_read(self):
        self.log("📂 [Etapa 1] Abrindo GeoTIFF...")

        with rasterio.open(self.src_path) as src:
            self.meta = src.meta.copy()
            self.meta.update(dtype="float32", count=1,
                             compress="lzw", nodata=np.nan)

            n_bands = src.count
            self.log(f"   Bandas encontradas no arquivo: {n_bands}")

            # ── Etapa 2: Detectar ou usar mapeamento manual ──
            band_map = self._detect_bands(src)
            self.log("🔍 [Etapa 2] Mapeamento de bandas:")
            for name, idx in band_map.items():
                self.log(f"   {name} → banda {idx}")

            # Lê cada banda como float32
            for name, idx in band_map.items():
                arr = src.read(idx).astype(np.float32)
                # Substitui nodata por NaN
                if src.nodata is not None:
                    arr[arr == src.nodata] = np.nan
                self.bands[name] = arr

        self.log(f"   Resolução: {self.meta['width']} x {self.meta['height']} px")
        self.set_progress(15)

    def _detect_bands(self, src) -> dict:
        """
        Tenta identificar bandas automaticamente por descrição/metadados.
        Fallback: usa os índices definidos manualmente na UI.
        """
        if not self.config["auto_detect"]:
            return self.config["band_indices"]

        descriptions = [
            (src.descriptions[i] or "").lower()
            for i in range(src.count)
        ]

        result = {}
        for band_name, keywords in BAND_KEYWORDS.items():
            found = False
            for i, desc in enumerate(descriptions):
                if any(kw in desc for kw in keywords):
                    result[band_name] = i + 1   # rasterio é 1-based
                    found = True
                    break
            if not found:
                # Usa fallback do config manual
                result[band_name] = self.config["band_indices"][band_name]

        return result

    # ──────────────────────────────────────────────────
    #  ETAPA 3 – Calcular estatísticas
    # ──────────────────────────────────────────────────

    def _step_statistics(self):
        if not self.config["statistics"]["calc"]:
            self.log("⏭  Estatísticas desativadas, pulando...")
            return

        self.log("📊 [Etapa 3] Calculando estatísticas...")
        stat_cfg = self.config["statistics"]
        calc = BandStatistics(stat_cfg)

        for name, arr in self.bands.items():
            self.stats[name] = calc.compute(arr)
            self.log(f"   {name}: "
                     f"P2={self.stats[name].get('p2', 'n/a'):.0f}  "
                     f"P98={self.stats[name].get('p98', 'n/a'):.0f}  "
                     f"Média={self.stats[name].get('mean', 'n/a'):.0f}")

        self.set_progress(30)

    # ──────────────────────────────────────────────────
    #  ETAPA 4 – Normalização
    # ──────────────────────────────────────────────────

    def _step_normalize(self):
        proc = self.config["processing"]

        if not proc["normalize"]:
            self.log("⏭  Normalização desativada, usando bandas originais.")
            self.bands_norm = {k: v.copy() for k, v in self.bands.items()}
            return

        self.log("🔧 [Etapa 4] Normalizando bandas (P2–P98 robusto)...")
        normalizer = Normalizer(
            correct_outliers=proc["outliers"],
            clip_01=proc["clip"]
        )

        for name, arr in self.bands.items():
            p2  = self.stats.get(name, {}).get("p2",  np.nanpercentile(arr, 2))
            p98 = self.stats.get(name, {}).get("p98", np.nanpercentile(arr, 98))
            self.bands_norm[name] = normalizer.normalize(arr, p2, p98)
            self.log(f"   {name}: normalizado  [{p2:.0f} → {p98:.0f}] ➜ [0, 1]")

        self.set_progress(50)

    # ──────────────────────────────────────────────────
    #  ETAPA 5 – Máscara
    # ──────────────────────────────────────────────────

    def _step_mask(self):
        if not self.config["processing"]["mask"]:
            self.log("⏭  Máscara desativada.")
            first = next(iter(self.bands_norm.values()))
            self.mask = np.ones(first.shape, dtype=bool)
            return

        self.log("🎭 [Etapa 5] Construindo máscara de pixels válidos...")
        builder = MaskBuilder()
        self.mask = builder.build(self.bands_norm)
        valid_pct = 100.0 * self.mask.sum() / self.mask.size
        self.log(f"   Pixels válidos: {valid_pct:.2f}%")
        self.set_progress(60)

    # ──────────────────────────────────────────────────
    #  ETAPA 6 – Calcular índices
    # ──────────────────────────────────────────────────

    def _step_indices(self):
        self.log("🌱 [Etapa 6] Calculando índices de vegetação...")
        calc = IndexCalculator(self.bands_norm, self.mask)

        idx_cfg = self.config["indices"]
        for idx_name, enabled in idx_cfg.items():
            if enabled:
                result = calc.compute(idx_name)
                if result is not None:
                    self.index_maps[idx_name] = result
                    valid = result[self.mask & ~np.isnan(result)]
                    mean_val = np.nanmean(valid) if valid.size > 0 else float("nan")
                    self.log(f"   ✔ {idx_name}  (média={mean_val:.4f})")
                else:
                    self.log(f"   ⚠ {idx_name}: bandas insuficientes.")

        self.set_progress(75)

    # ──────────────────────────────────────────────────
    #  ETAPA 7 – Exportar
    # ──────────────────────────────────────────────────

    def _step_export(self):
        self.log("💾 [Etapa 7] Exportando resultados...")
        exp_cfg = self.config["export"]
        exporter = Exporter(self.meta, self.out_dir)

        if exp_cfg["tif"]:
            # Bandas normalizadas
            for name, arr in self.bands_norm.items():
                exporter.save_tif(arr, f"{name}_norm.tif")
                self.log(f"   ✔ {name}_norm.tif")

            # Índices
            for name, arr in self.index_maps.items():
                exporter.save_tif(arr, f"{name}.tif")
                self.log(f"   ✔ {name}.tif")

        if exp_cfg["csv"]:
            exporter.save_csv(self.stats, "Estatisticas.csv")
            self.log("   ✔ Estatisticas.csv")

        self.set_progress(90)

    # ──────────────────────────────────────────────────
    #  ETAPA 8 – Relatório PDF
    # ──────────────────────────────────────────────────

    def _step_report(self):
        if not self.config["export"]["pdf"]:
            return

        self.log("📄 [Etapa 8] Gerando relatório PDF...")
        reporter = ReportGenerator(
            stats=self.stats,
            index_maps=self.index_maps,
            bands_norm=self.bands_norm,
            mask=self.mask,
            src_path=self.src_path,
            out_dir=self.out_dir,
        )
        reporter.generate("Relatorio.pdf")
        self.log("   ✔ Relatorio.pdf")
        self.set_progress(98)

    # ──────────────────────────────────────────────────
    #  Pipeline completo
    # ──────────────────────────────────────────────────

    def run(self):
        self._step_read()
        self._step_statistics()
        self._step_normalize()
        self._step_mask()
        self._step_indices()
        self._step_export()
        self._step_report()
