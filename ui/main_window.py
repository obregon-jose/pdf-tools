import customtkinter as ctk
from ui.sidebar import Sidebar
from tools.tools_registry import TOOLS_REGISTRY


class MainWindow(ctk.CTkFrame):
    def __init__(self, master, config):
        super().__init__(master)
        self.master = master
        self.config = config

        # Sidebar
        self.sidebar = Sidebar(
            self,
            on_load_tool=self.load_tool,
            on_home=self.show_home,
            on_settings=self.show_settings,
            on_support=self.show_support
        )
        self.sidebar.pack(side="left", fill="y")

        # Contenedor principal (todo lo visible a la derecha del sidebar)
        self.content = ctk.CTkFrame(self)
        self.content.pack(side="right", expand=True, fill="both")

        # Estado interno
        self.current_view = None
        self.scroll_container = None
        self.grid_frame = None
        self._resize_after_id = None
        self._last_cols = None
        self._cards = []

        # Detectar redimensionamiento de ventana
        self.master.bind("<Configure>", self._on_configure)

        self.show_home()

    # ------------------ HOME ------------------
    def show_home(self):
        """Muestra todas las herramientas registradas, con scroll y diseño responsive."""
        self.clear_content()
        self.current_view = "home"

        # Título
        ctk.CTkLabel(
            self.content,
            text="Herramientas disponibles",
            font=("Arial", 20, "bold")
        ).pack(pady=10)

        # Contenedor con scroll
        self.scroll_container = ctk.CTkScrollableFrame(self.content)
        self.scroll_container.pack(expand=True, fill="both", padx=20, pady=10)

        # Frame interno para la grilla
        self.grid_frame = ctk.CTkFrame(self.scroll_container)
        self.grid_frame.pack(expand=True, fill="both")

        self._last_cols = None
        self._build_or_update_grid(force=True)

    # Determinar columnas (1 o 2 según ancho)
    def _determine_cols(self):
        width = self.grid_frame.winfo_width() or self.content.winfo_width() or 600
        return 2 if width > 500 else 1

    def _build_or_update_grid(self, force=False):
        if not self.grid_frame:
            return

        cols = self._determine_cols()
        if (not force) and (cols == self._last_cols):
            self._adjust_wraplength(cols)
            return

        self._last_cols = cols

        for w in self.grid_frame.winfo_children():
            w.grid_forget()

        for c in range(cols):
            self.grid_frame.grid_columnconfigure(c, weight=1, uniform="col")

        needed = len(TOOLS_REGISTRY)
        while len(self._cards) < needed:
            card = self._create_card_widget()
            self._cards.append(card)

        for idx, tool in enumerate(TOOLS_REGISTRY):
            r, c = divmod(idx, cols)
            card = self._cards[idx]
            self._update_card_with_tool(card, tool, cols)

            # En una sola columna, debe tomar todo el ancho
            sticky_value = "ew" if cols == 1 else "nsew"
            card.grid(row=r, column=c, padx=10, pady=10, sticky=sticky_value)

        # Ocultar tarjetas sobrantes (si las hay)
        for j in range(len(TOOLS_REGISTRY), len(self._cards)):
            self._cards[j].grid_forget()

        self._adjust_wraplength(cols)

    def _create_card_widget(self):
        """Crea una tarjeta autoajustable."""
        card = ctk.CTkFrame(self.grid_frame, corner_radius=8)
        card.pack_propagate(True)

        # Título
        title = ctk.CTkLabel(card, text="", font=("Arial", 14, "bold"), anchor="w")
        title.pack(anchor="w", padx=10, pady=(10, 2), fill="x")

        # Descripción
        desc = ctk.CTkLabel(card, text="", anchor="w", wraplength=400, justify="left")
        desc.pack(anchor="w", padx=10, pady=(2, 6), fill="x")

        # Botón centrado
        btn = ctk.CTkButton(card, text="Abrir", width=100)
        btn.pack(anchor="center", pady=(4, 10))

        # Guardar referencias
        card._title = title
        card._desc = desc
        card._btn = btn
        return card

    def _update_card_with_tool(self, card, tool, cols):
        card._title.configure(text=tool["name"])
        card._desc.configure(text=tool["description"])

        total_width = self.grid_frame.winfo_width() or 600
        wrap = int((total_width / max(cols, 1)) * 0.85)
        card._desc.configure(wraplength=wrap)

        card._btn.configure(command=lambda t=tool["name"]: self.load_tool(t))

    def _adjust_wraplength(self, cols):
        total_width = self.grid_frame.winfo_width() or 600
        wrap = int((total_width / max(cols, 1)) * 0.85)
        for card in self._cards[:len(TOOLS_REGISTRY)]:
            card._desc.configure(wraplength=wrap)

    # ------------------ RESIZE ------------------
    def _on_configure(self, event):
        if self._resize_after_id:
            try:
                self.after_cancel(self._resize_after_id)
            except Exception:
                pass
        self._resize_after_id = self.after(150, self._on_resize_debounced)

    def _on_resize_debounced(self):
        self._resize_after_id = None
        if self.current_view == "home":
            self._build_or_update_grid(force=False)

    # ------------------ SETTINGS ------------------
    def show_settings(self):
        self.clear_content()
        self.current_view = "settings"
        ctk.CTkLabel(
            self.content,
            text="⚙️ Configuración",
            font=("Arial", 20, "bold")
        ).pack(pady=20)

    # ------------------ SUPPORT ------------------
    def show_support(self):
        self.clear_content()
        self.current_view = "support"
        ctk.CTkLabel(
            self.content,
            text="🧩 Soporte técnico",
            font=("Arial", 20, "bold")
        ).pack(pady=20)

    # ------------------ HERRAMIENTA ------------------
    def load_tool(self, tool_name):
        self.clear_content()
        self.current_view = f"tool:{tool_name}"

        header = ctk.CTkFrame(self.content)
        header.pack(fill="x", pady=(6, 6))
        ctk.CTkButton(header, text="⬅ Volver", width=90, command=self.show_home).pack(side="left", padx=10, pady=6)
        ctk.CTkLabel(header, text=tool_name, font=("Arial", 16, "bold")).pack(side="left", padx=10, pady=6)

        tool_data = next((t for t in TOOLS_REGISTRY if t["name"] == tool_name), None)
        if not tool_data:
            ctk.CTkLabel(self.content, text="Herramienta no encontrada").pack(pady=20)
            return

        try:
            tool_class = tool_data.get("class")
            tool_frame = tool_class(self.content, go_home=self.show_home)
            tool_frame.pack(expand=True, fill="both")
        except Exception as e:
            ctk.CTkLabel(self.content, text="Error al abrir la herramienta.", wraplength=600).pack(pady=10)
            ctk.CTkLabel(self.content, text=str(e), wraplength=600).pack(pady=6)
            print("Error al instanciar herramienta:", e)

    # ------------------ CLEAR ------------------
    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()
        self.grid_frame = None
        self.scroll_container = None
        self._cards = []
        self._last_cols = None
