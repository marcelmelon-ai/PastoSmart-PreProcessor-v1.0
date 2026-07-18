"""
PastoSmart PreProcessor v1.0
Interface gráfica principal (Tkinter).
Gerencia todos os controles, checkboxes e botões da UI.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os

from preprocess import PreProcessor


# ─────────────────────────────────────────────
#  Paleta de cores do tema
# ─────────────────────────────────────────────
BG_DARK    = "#1E1E2E"   # fundo principal
BG_PANEL   = "#2A2A3E"   # painéis internos
BG_HEADER  = "#12B76A"   # cabeçalho verde
FG_WHITE   = "#FFFFFF"
FG_GRAY    = "#A0A0B0"
FG_GREEN   = "#12B76A"
FG_YELLOW  = "#F5A623"
ACCENT     = "#3A3A5C"
BTN_GREEN  = "#12B76A"
BTN_HOVER  = "#0E9458"


class PastoSmartApp:
    """Janela principal do PastoSmart PreProcessor."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PastoSmart PreProcessor v1.0")
        self.root.geometry("780x980")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)

        # Variáveis de estado
        self.geotiff_path   = tk.StringVar(value="")
        self.output_dir     = tk.StringVar(value=os.path.abspath("outputs"))
        self.auto_detect    = tk.BooleanVar(value=True)

        # Mapeamento de bandas (índice 1-based dentro do GeoTIFF)
        self.band_vars = {
            "Green":    tk.IntVar(value=1),
            "Red":      tk.IntVar(value=2),
            "RedEdge":  tk.IntVar(value=3),
            "NIR":      tk.IntVar(value=4),
        }

        # Checkboxes de estatísticas
        self.stat_calc    = tk.BooleanVar(value=True)
        self.stat_min     = tk.BooleanVar(value=True)
        self.stat_max     = tk.BooleanVar(value=True)
        self.stat_mean    = tk.BooleanVar(value=True)
        self.stat_median  = tk.BooleanVar(value=True)
        self.stat_p2      = tk.BooleanVar(value=True)
        self.stat_p98     = tk.BooleanVar(value=True)
        self.stat_std     = tk.BooleanVar(value=True)
        self.stat_sat     = tk.BooleanVar(value=True)
        self.stat_inv     = tk.BooleanVar(value=True)

        # Checkboxes de processamento
        self.proc_norm    = tk.BooleanVar(value=True)
        self.proc_mask    = tk.BooleanVar(value=True)
        self.proc_outlier = tk.BooleanVar(value=True)
        self.proc_clip    = tk.BooleanVar(value=True)

        # Checkboxes de índices
        self.idx_vars = {
            "NDVI":    tk.BooleanVar(value=True),
            "GNDVI":   tk.BooleanVar(value=True),
            "NDRE":    tk.BooleanVar(value=True),
            "SAVI":    tk.BooleanVar(value=True),
            "MSAVI":   tk.BooleanVar(value=True),
            "OSAVI":   tk.BooleanVar(value=True),
            "VARI":    tk.BooleanVar(value=True),
            "ClGreen": tk.BooleanVar(value=True),
            "ClRE":    tk.BooleanVar(value=True),
            "EVI2":    tk.BooleanVar(value=True),
        }

        # Checkboxes de exportação
        self.exp_tif = tk.BooleanVar(value=True)
        self.exp_csv = tk.BooleanVar(value=True)
        self.exp_pdf = tk.BooleanVar(value=True)

        self._build_ui()

    # ─────────────────────────────────────────
    #  Construção da UI
    # ─────────────────────────────────────────

    def _build_ui(self):
        """Monta todos os painéis da interface."""

        # Canvas + Scrollbar para tornar a janela rolável
        canvas = tk.Canvas(self.root, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg=BG_DARK)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll com mouse
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        f = self.scroll_frame   # alias

        # ── Cabeçalho ──────────────────────────────────────────
        header = tk.Frame(f, bg=BG_HEADER, pady=12)
        header.pack(fill="x", padx=0, pady=(0, 10))

        tk.Label(header, text="🌿  PastoSmart PreProcessor  v1.0",
                 font=("Segoe UI", 16, "bold"),
                 bg=BG_HEADER, fg=FG_WHITE).pack()

        tk.Label(header, text="Pré-processamento multispectral para pastagens",
                 font=("Segoe UI", 9),
                 bg=BG_HEADER, fg="#D0FFE8").pack()

        # ── Arquivo GeoTIFF ────────────────────────────────────
        self._section(f, "📂  Arquivo GeoTIFF")
        fp = self._panel(f)

        tk.Entry(fp, textvariable=self.geotiff_path,
                 bg=ACCENT, fg=FG_WHITE, insertbackground=FG_WHITE,
                 relief="flat", font=("Segoe UI", 9), width=52
                 ).grid(row=0, column=0, padx=(8,4), pady=8, sticky="ew")

        self._btn(fp, "Selecionar", self._select_file
                  ).grid(row=0, column=1, padx=(0,8), pady=8)

        fp.columnconfigure(0, weight=1)

        # Detectar bandas automaticamente
        bp = self._panel(f)
        tk.Checkbutton(bp, text="✔  Detectar bandas automaticamente",
                       variable=self.auto_detect,
                       command=self._toggle_band_entries,
                       bg=BG_PANEL, fg=FG_GREEN,
                       selectcolor=BG_PANEL,
                       activebackground=BG_PANEL,
                       font=("Segoe UI", 9, "bold")
                       ).grid(row=0, column=0, columnspan=4,
                              sticky="w", padx=8, pady=(6,2))

        # Entradas manuais de bandas
        self.band_entries_frame = tk.Frame(bp, bg=BG_PANEL)
        self.band_entries_frame.grid(row=1, column=0, columnspan=4,
                                     sticky="w", padx=16, pady=(0,6))

        self.band_entry_widgets = {}
        for i, (name, var) in enumerate(self.band_vars.items()):
            tk.Label(self.band_entries_frame, text=f"{name}:",
                     bg=BG_PANEL, fg=FG_GRAY,
                     font=("Segoe UI", 9), width=8, anchor="e"
                     ).grid(row=0, column=i*2, padx=(4,2))
            e = tk.Spinbox(self.band_entries_frame, from_=1, to=20,
                           textvariable=var, width=4,
                           bg=ACCENT, fg=FG_WHITE,
                           buttonbackground=ACCENT,
                           relief="flat", font=("Segoe UI", 9))
            e.grid(row=0, column=i*2+1, padx=(0,8))
            self.band_entry_widgets[name] = e

        self._toggle_band_entries()   # aplica estado inicial

        # ── Estatísticas ───────────────────────────────────────
        self._section(f, "📊  Estatísticas")
        sp = self._panel(f)

        self._check(sp, "☑ Calcular",        self.stat_calc,   0, 0, bold=True, color=FG_GREEN)
        self._check(sp, "Min",               self.stat_min,    1, 0)
        self._check(sp, "Máx",               self.stat_max,    1, 1)
        self._check(sp, "Média",             self.stat_mean,   1, 2)
        self._check(sp, "Mediana",           self.stat_median, 2, 0)
        self._check(sp, "Percentil 2",       self.stat_p2,     2, 1)
        self._check(sp, "Percentil 98",      self.stat_p98,    2, 2)
        self._check(sp, "Desvio padrão",     self.stat_std,    3, 0)
        self._check(sp, "Pixels saturados",  self.stat_sat,    3, 1)
        self._check(sp, "Pixels inválidos",  self.stat_inv,    3, 2)

        # ── Processamento ──────────────────────────────────────
        self._section(f, "⚙️  Processamento")
        pp = self._panel(f)

        self._check(pp, "Normalização robusta", self.proc_norm,    0, 0)
        self._check(pp, "Aplicar máscara",      self.proc_mask,    0, 1)
        self._check(pp, "Corrigir outliers",    self.proc_outlier, 1, 0)
        self._check(pp, "Limitar 0–1",          self.proc_clip,    1, 1)

        # ── Índices ────────────────────────────────────────────
        self._section(f, "🌱  Índices de Vegetação")
        ip = self._panel(f)

        idx_list = list(self.idx_vars.items())
        for i, (name, var) in enumerate(idx_list):
            row, col = divmod(i, 5)
            self._check(ip, name, var, row, col)

        # ── Exportar ───────────────────────────────────────────
        self._section(f, "💾  Exportar")
        ep = self._panel(f)

        self._check(ep, "GeoTIFF",     self.exp_tif, 0, 0)
        self._check(ep, "CSV",         self.exp_csv, 0, 1)
        self._check(ep, "Relatório PDF", self.exp_pdf, 0, 2)

        tk.Label(ep, text="Destino:",
                 bg=BG_PANEL, fg=FG_GRAY,
                 font=("Segoe UI", 9)
                 ).grid(row=1, column=0, padx=(8,2), pady=(4,8), sticky="e")

        tk.Entry(ep, textvariable=self.output_dir,
                 bg=ACCENT, fg=FG_WHITE,
                 insertbackground=FG_WHITE,
                 relief="flat", font=("Segoe UI", 9), width=44
                 ).grid(row=1, column=1, columnspan=2,
                        padx=(0,4), pady=(4,8), sticky="ew")

        self._btn(ep, "📁", self._select_output
                  ).grid(row=1, column=3, padx=(0,8), pady=(4,8))

        ep.columnconfigure(1, weight=1)

        # ── Barra de progresso + Log ───────────────────────────
        self._section(f, "📋  Log de Processamento")
        lp = self._panel(f)

        self.progress = ttk.Progressbar(lp, mode="determinate",
                                        length=700, maximum=100)
        self.progress.grid(row=0, column=0, padx=8, pady=(8,4),
                           sticky="ew", columnspan=2)
        lp.columnconfigure(0, weight=1)

        self.log_text = tk.Text(lp, height=10, bg="#0D0D1A",
                                fg="#00FF88", font=("Consolas", 8),
                                relief="flat", state="disabled",
                                wrap="word")
        self.log_text.grid(row=1, column=0, padx=8, pady=(0,8),
                           sticky="ew", columnspan=2)

        # ── Botão PROCESSAR ───────────────────────────────────
        btn_frame = tk.Frame(f, bg=BG_DARK)
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))

        process_btn = tk.Button(
            btn_frame,
            text="▶   PROCESSAR",
            font=("Segoe UI", 13, "bold"),
            bg=BTN_GREEN, fg=FG_WHITE,
            activebackground=BTN_HOVER,
            activeforeground=FG_WHITE,
            relief="flat", cursor="hand2",
            pady=12,
            command=self._start_processing
        )
        process_btn.pack(fill="x")

        # Rodapé
        tk.Label(f, text="PastoSmart PreProcessor v1.0  •  2026",
                 bg=BG_DARK, fg=FG_GRAY,
                 font=("Segoe UI", 8)).pack(pady=(0, 10))

    # ─────────────────────────────────────────
    #  Helpers de UI
    # ─────────────────────────────────────────

    def _section(self, parent, title: str):
        """Rótulo de seção com linha separadora."""
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.pack(fill="x", padx=10, pady=(10, 2))
        tk.Label(frame, text=title,
                 bg=BG_DARK, fg=FG_YELLOW,
                 font=("Segoe UI", 10, "bold")).pack(side="left")
        tk.Frame(frame, bg=ACCENT, height=1).pack(
            side="left", fill="x", expand=True, padx=(8, 0))

    def _panel(self, parent) -> tk.Frame:
        """Painel com fundo escuro."""
        p = tk.Frame(parent, bg=BG_PANEL,
                     highlightbackground=ACCENT,
                     highlightthickness=1)
        p.pack(fill="x", padx=10, pady=2)
        return p

    def _check(self, parent, text: str, variable: tk.BooleanVar,
               row: int, col: int, bold=False, color=FG_WHITE):
        """Checkbox estilizado."""
        font_weight = "bold" if bold else "normal"
        cb = tk.Checkbutton(
            parent, text=text, variable=variable,
            bg=BG_PANEL, fg=color,
            selectcolor=BG_PANEL,
            activebackground=BG_PANEL,
            activeforeground=FG_GREEN,
            font=("Segoe UI", 9, font_weight)
        )
        cb.grid(row=row, column=col, sticky="w", padx=10, pady=3)

    def _btn(self, parent, text: str, command) -> tk.Button:
        """Botão estilizado."""
        return tk.Button(
            parent, text=text,
            bg=BTN_GREEN, fg=FG_WHITE,
            activebackground=BTN_HOVER,
            relief="flat", cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=10, pady=4,
            command=command
        )

    # ─────────────────────────────────────────
    #  Callbacks
    # ─────────────────────────────────────────

    def _select_file(self):
        path = filedialog.askopenfilename(
            title="Selecionar GeoTIFF",
            filetypes=[("GeoTIFF", "*.tif *.tiff"), ("Todos", "*.*")]
        )
        if path:
            self.geotiff_path.set(path)
            self._log(f"✔ Arquivo selecionado: {os.path.basename(path)}")

    def _select_output(self):
        path = filedialog.askdirectory(title="Selecionar pasta de saída")
        if path:
            self.output_dir.set(path)
            self._log(f"✔ Destino definido: {path}")

    def _toggle_band_entries(self):
        """Habilita/desabilita spinboxes de bandas conforme auto_detect."""
        state = "disabled" if self.auto_detect.get() else "normal"
        for w in self.band_entry_widgets.values():
            w.config(state=state)

    def _log(self, msg: str):
        """Escreve mensagem no log da interface (thread-safe)."""
        def _write():
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        self.root.after(0, _write)

    def _set_progress(self, value: float):
        """Atualiza a barra de progresso (0-100)."""
        self.root.after(0, lambda: self.progress.config(value=value))

    # ─────────────────────────────────────────
    #  Processamento principal (thread separada)
    # ─────────────────────────────────────────

    def _start_processing(self):
        if not self.geotiff_path.get():
            messagebox.showwarning("Aviso", "Selecione um arquivo GeoTIFF primeiro.")
            return

        # Coleta configurações da UI
        config = {
            "geotiff_path":  self.geotiff_path.get(),
            "output_dir":    self.output_dir.get(),
            "auto_detect":   self.auto_detect.get(),
            "band_indices": {k: v.get() for k, v in self.band_vars.items()},

            "statistics": {
                "calc":   self.stat_calc.get(),
                "min":    self.stat_min.get(),
                "max":    self.stat_max.get(),
                "mean":   self.stat_mean.get(),
                "median": self.stat_median.get(),
                "p2":     self.stat_p2.get(),
                "p98":    self.stat_p98.get(),
                "std":    self.stat_std.get(),
                "saturated": self.stat_sat.get(),
                "invalid":   self.stat_inv.get(),
            },

            "processing": {
                "normalize": self.proc_norm.get(),
                "mask":      self.proc_mask.get(),
                "outliers":  self.proc_outlier.get(),
                "clip":      self.proc_clip.get(),
            },

            "indices": {k: v.get() for k, v in self.idx_vars.items()},

            "export": {
                "tif": self.exp_tif.get(),
                "csv": self.exp_csv.get(),
                "pdf": self.exp_pdf.get(),
            },
        }

        # Executa em thread para não travar a UI
        thread = threading.Thread(
            target=self._run_pipeline,
            args=(config,),
            daemon=True
        )
        thread.start()

    def _run_pipeline(self, config: dict):
        """Executa o pipeline completo em background."""
        try:
            self._log("─" * 50)
            self._log("🚀 Iniciando processamento...")
            self._set_progress(0)

            processor = PreProcessor(config, self._log, self._set_progress)
            processor.run()

            self._log("─" * 50)
            self._log("✅ Processamento concluído com sucesso!")
            self._set_progress(100)
            self.root.after(0, lambda: messagebox.showinfo(
                "Concluído",
                f"Processamento finalizado!\nSaída: {config['output_dir']}"
            ))
        except Exception as e:
            self._log(f"❌ ERRO: {e}")
            self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))
