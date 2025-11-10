
import customtkinter as ctk
from collections import defaultdict
from tools.tools_registry import TOOLS_REGISTRY
from core.config import APP_NAME

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_load_tool, on_home, on_settings, on_support):
        super().__init__(master, width=200)
        self.on_load_tool = on_load_tool
        self.on_home = on_home
        self.on_settings = on_settings
        self.on_support = on_support

        # Mantener ancho fijo
        self.pack_propagate(False)

        # Home (arriba)
        ctk.CTkLabel(self, 
                     text=APP_NAME, 
                     font=("Arial", 24, "bold")).pack(pady=(12, 6))

        ctk.CTkButton(self, text="Herramientas", command=self.on_home).pack(padx=10, pady=(10, 5), fill="x")
        

        # Agrupar herramientas por categoría
        tools_by_cat = defaultdict(list)
        for tool in TOOLS_REGISTRY:
            tools_by_cat[tool["category"]].append(tool["name"])

        # Guardamos referencias a frames abiertos para poder cerrarlos
        self._open_tools_frame = None
        self._open_category_btn = None

        # Crear sección por categoría
        for category, tools in tools_by_cat.items():
            self._create_category_section(category, tools)

        # Spacer para empujar inferior al final
        self._spacer = ctk.CTkLabel(self, text="")
        self._spacer.pack(expand=True, fill="y")

        # Botones inferiores
        ctk.CTkButton(self, text="⚙️ Configuración", command=self.on_settings).pack(padx=10, pady=5, fill="x")
        ctk.CTkButton(self, text="🧩 Soporte", command=self.on_support).pack(padx=10, pady=(0, 10), fill="x")

    def _create_category_section(self, category, tools):
        """
        Cada categoría:
         - botón visible
         - cuando se abre, crea tools_frame y lo empaca AFTER del botón (justo debajo)
         - cierra cualquier tools_frame previamente abierto para evitar solapamientos
        """
        # Botón de categoría
        category_btn = ctk.CTkButton(
            self,
            text=f"▸ {category} ({len(tools)})",
            anchor="w",
            fg_color="transparent",
            text_color="#000000",
            # hover=False,
            font=("Arial", 14, "bold"),
        )
        category_btn.pack(fill="x", padx=10, pady=(2, 0))

        # Frame vacío (no empaquetado aún)
        tools_frame = ctk.CTkFrame(self, fg_color="transparent")
        tools_frame.visible = False

        def toggle():
            nonlocal tools_frame
            if tools_frame.visible:
                # cerrar esta misma categoría
                for w in tools_frame.winfo_children():
                    w.destroy()
                tools_frame.pack_forget()
                tools_frame.visible = False
                category_btn.configure(text=f"▸ {category} ({len(tools)})")
                # reset trackers si esta era la abierta
                if self._open_tools_frame is tools_frame:
                    self._open_tools_frame = None
                    self._open_category_btn = None
            else:
                # cerrar cualquier otra abierta primero
                if self._open_tools_frame and self._open_tools_frame is not tools_frame:
                    try:
                        for w in self._open_tools_frame.winfo_children():
                            w.destroy()
                        self._open_tools_frame.pack_forget()
                    except Exception:
                        pass
                    if self._open_category_btn:
                        # asegurar que el texto del anterior vuelva a estado cerrado
                        try:
                            prev_text = self._open_category_btn.cget("text")
                            if prev_text.startswith("▾"):
                                self._open_category_btn.configure(text=f"▸{prev_text[1:]}")
                        except Exception:
                            pass
                    self._open_tools_frame = None
                    self._open_category_btn = None

                # llenar tools_frame con botones (sin contenedores extra ni colores)
                for w in tools_frame.winfo_children():
                    w.destroy()
                for tool_name in tools:
                    btn = ctk.CTkButton(
                        tools_frame,
                        text=tool_name,
                        anchor="w",
                        command=lambda t=tool_name: self.on_load_tool(t)
                    )
                    btn.pack(fill="x", padx=25, pady=2)

                # Empacar justo DESPUÉS del botón de categoría para que aparezca inmediatamente debajo
                try:
                    tools_frame.pack(fill="x", padx=0, pady=(2, 2), after=category_btn)
                except TypeError:
                    # fallback si la versión de tkinter no soporta 'after' (muy raro)
                    # en ese caso usamos before=spacer como plan B
                    tools_frame.pack(fill="x", padx=0, pady=(2, 2), before=self._spacer)

                tools_frame.visible = True
                # marcar como abierto
                self._open_tools_frame = tools_frame
                self._open_category_btn = category_btn
                category_btn.configure(text=f"▾ {category} ({len(tools)})")

        category_btn.configure(command=toggle)
