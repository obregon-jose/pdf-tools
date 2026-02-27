import customtkinter as ctk
from typing import Literal, Callable, Optional, List


class Toast(ctk.CTkFrame):    
    COLORS = {
        "info": {
            "bg": "#cfe2ff",#3498db"
            "border": "#2980b9", # ->"#b6d4fe"
            "text": "#084298", #"white"
            "hover": "#2980b9"
        },
        "success": {
            "bg": "#d1e7dd", #"#27ae60"
            "border": "#229954", # -> "#badbcc"
            "text": "#0f5132", #"white"
            "hover": "#229954"
        },
        "warning": {
            "bg": "#fff3cd", # "#f39c12"
            "border": "#d68910", # ->"#ffecb5"
            "text": "#664d03", # "white"
            "hover": "#d68910"
        },
        "error": {
            "bg": "#f8d7da", #"#e74c3c"
            "border": "#c0392b", #-> #f5c2c7
            "text": "#842029", #"white"
            "hover": "#c0392b"
        },
        "loading": {
            "bg": "#9b59b6",
            "border": "#8e44ad",
            "text": "white"
        }
    }
    
    ICONS = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    def __init__(
        self,
        parent,
        message: str,
        toast_type: Literal["info", "success", "warning", "error"] = "info",
        seconds_duration: int = 3000,
        y_position: int = 20
    ):
        colors = self.COLORS.get(toast_type, self.COLORS["info"])
        
        # Obtener color de fondo del parent para esquinas transparentes
        try:
            parent_bg = parent._apply_appearance_mode(parent._fg_color)
        except:
            appearance_mode = ctk.get_appearance_mode()
            parent_bg = "#1e1e1e" if appearance_mode == "Dark" else "#f0f0f0"
        
        super().__init__(
            parent,
            fg_color=colors["bg"],
            corner_radius=12,
            border_width=2,
            border_color=colors["border"],
            bg_color=parent_bg
        )
        
        self.message = message
        self.toast_type = toast_type
        self.seconds_duration = seconds_duration
        self.colors = colors
        self.is_closing = False
        self.y_position = y_position
        self._close_callback: Optional[Callable] = None
        self._after_id: Optional[str] = None
        
        self._build_ui()
        self.place(relx=1.0, y=y_position, anchor="ne", x=-20)
        self.lift()
        
        if seconds_duration > 0:
            self._after_id = self.after(seconds_duration, self.close)
    
    def _build_ui(self):
        """Construye la interfaz del toast."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=14, pady=12)
        
        # Icono
        ctk.CTkLabel(
            main_frame,
            text=self.ICONS[self.toast_type],
            font=ctk.CTkFont(size=20),
            text_color=self.colors["text"]
        ).pack(side="left", padx=(0, 12))
        
        # Mensaje
        ctk.CTkLabel(
            main_frame,
            text=self.message,
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text"],
            wraplength=260,
            justify="left",
            anchor="w"
        ).pack(side="left", fill="both", expand=True)
        
        # Botón cerrar
        ctk.CTkButton(
            main_frame,
            text="✕",
            width=26,
            height=26,
            corner_radius=13,
            fg_color="transparent",
            hover_color=self.colors["hover"],
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.close
        ).pack(side="left", padx=(12, 0))
    
    def set_close_callback(self, callback: Callable):
        """Establece callback al cerrar."""
        self._close_callback = callback
    
    def update_position(self, new_y: int, animate: bool = True):
        """Actualiza posición Y."""
        self.y_position = new_y
        self.place(relx=1.0, y=new_y, anchor="ne", x=-20)
    
    def get_height(self) -> int:
        """Retorna altura del toast."""
        self.update_idletasks()
        return self.winfo_height()
    
    def close(self):
        """Cierra el toast."""
        if self.is_closing:
            return
        
        self.is_closing = True
        
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except:
                pass
        
        if self._close_callback:
            try:
                self._close_callback(self)
            except Exception as e:
                print(f"[WARNING] Error en callback: {e}")
        
        try:
            self.place_forget()
            self.destroy()
        except:
            pass


class ToastManager:
    
    _instance = None
    _root = None
    _toasts: List[Toast] = []
    _initial_y = 20
    _spacing = 10
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, root):
        """Inicializa el manager. Llamar UNA VEZ en main.py"""
        cls._root = root
        cls._toasts = []
    
    @classmethod
    def _calculate_next_position(cls) -> int:
        """Calcula posición Y para el próximo toast."""
        y = cls._initial_y
        for toast in cls._toasts:
            if not toast.is_closing:
                y += toast.get_height() + cls._spacing
        return y
    
    @classmethod
    def _reposition_toasts(cls):
        """Reposiciona toasts después de cerrar uno."""
        y = cls._initial_y
        for toast in cls._toasts:
            if not toast.is_closing:
                toast.update_position(y, animate=True)
                y += toast.get_height() + cls._spacing
    
    @classmethod
    def show(
        cls,
        message: str,
        toast_type: Literal["info", "success", "warning", "error"] = "info",
        seconds_duration: int = 3
    ) -> Optional[Toast]:

        if cls._root is None:
            print(f"[ERROR] ToastManager no inicializado.")
            return None
        
        try:
            y_position = cls._calculate_next_position()
            toast = Toast(cls._root, message, toast_type, seconds_duration*1000, y_position)
            toast.set_close_callback(cls._on_toast_closed)
            cls._toasts.append(toast)
            cls._root.after(50, cls._reposition_toasts)
            return toast
        except Exception as e:
            print(f"[ERROR] No se pudo crear toast: {e}")
            return None
    
    @classmethod
    def _on_toast_closed(cls, toast: Toast):
        """Callback cuando un toast se cierra."""
        if toast in cls._toasts:
            cls._toasts.remove(toast)
        if cls._root:
            cls._root.after(10, cls._reposition_toasts)
    
    @classmethod
    def clear_all(cls):
        """Cierra todos los toasts."""
        for toast in cls._toasts[:]:
            toast.close()
        cls._toasts.clear()
    
    @classmethod
    def get_active_count(cls) -> int:
        """Retorna número de toasts activos."""
        return len([t for t in cls._toasts if not t.is_closing])
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Verifica si está inicializado."""
        return cls._root is not None


# ==================== FUNCIONES GLOBALES ====================

def toast(
    message: str,
    toast_type: Literal["info", "success", "warning", "error"] = "info",
    seconds_duration: int = 5
) -> Optional[Toast]:
    return ToastManager.show(message, toast_type, seconds_duration)

# Funciones específicas (opcionales, para quien prefiera)
def toast_info(message: str, seconds_duration: int = 3) -> Optional[Toast]:
    return ToastManager.show(message, "info", seconds_duration)

def toast_success(message: str, seconds_duration: int = 3) -> Optional[Toast]:
    return ToastManager.show(message, "success", seconds_duration)

def toast_warning(message: str, seconds_duration: int = 4) -> Optional[Toast]:
    return ToastManager.show(message, "warning", seconds_duration)

def toast_error(message: str, seconds_duration: int = 5) -> Optional[Toast]:
    return ToastManager.show(message, "error", seconds_duration)