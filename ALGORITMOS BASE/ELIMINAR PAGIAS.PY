

# import customtkinter as ctk
# from tkinter import filedialog, messagebox
# import fitz  # PyMDF
# import os
# from PIL import Image
# from io import BytesIO
# import threading


# class PDFEditorApp:   
#     """Aplicación principal para editar PDFs con PyMuPDF"""
    
#     def __init__(self, root):
#         self.root = root
#         self.root.title("📄 Editor de Páginas PDF")
#         self.root.geometry("1400x900")
#         self.root.minsize(800, 700)
#         self.root.resizable(True, True)
        
#         # Variables
#         self.pdf_path = None
#         self.pdf_doc = None
#         self.check_vars = []
#         self.checkboxes = []
#         self. thumbnails = []
#         self.last_operation = None
#         self. loading = False
#         self.num_columnas = 5  # Columnas iniciales
        
#         # Configurar tema
#         ctk.set_appearance_mode("dark")
#         ctk.set_default_color_theme("blue")
        
#         self.crear_interfaz()
        
#         # Bind para detectar cambios de tamaño
#         self.root.bind("<Configure>", self. on_window_resize)
    
#     def crear_interfaz(self):
#         """Crea todos los elementos de la interfaz"""
        
#         # ===== HEADER CON TÍTULO =====
#         header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
#         header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
#         lbl_titulo = ctk.CTkLabel(
#             header_frame,
#             text="📄 Editor de Páginas PDF",
#             font=ctk.CTkFont(size=28, weight="bold")
#         )
#         lbl_titulo.pack()
        
#         lbl_subtitulo = ctk.CTkLabel(
#             header_frame,
#             text="Elimina páginas de tus documentos PDF de forma rápida y sencilla",
#             font=ctk.CTkFont(size=13),
#             text_color="gray60"
#         )
#         lbl_subtitulo.pack(pady=(5, 0))
        
#         # ===== TOP FRAME PRINCIPAL =====
#         top_frame = ctk.CTkFrame(self.root, corner_radius=15)
#         top_frame.pack(fill="x", padx=20, pady=15)
        
#         # Row 0:  PDF de entrada
#         lbl_pdf = ctk.CTkLabel(
#             top_frame, 
#             text="PDF de entrada:",
#             font=ctk.CTkFont(size=13, weight="bold"),
#             width=120,
#             anchor="w"
#         )
#         lbl_pdf.grid(row=0, column=0, padx=(15, 10), pady=(15, 8), sticky="w")
        
#         self.entrada_ruta = ctk.CTkEntry(
#             top_frame,
#             placeholder_text="Escribe la ruta o usa el botón Seleccionar",
#             font=ctk.CTkFont(size=12),
#             height=38,
#             corner_radius=8
#         )
#         self.entrada_ruta.grid(row=0, column=1, padx=(0, 10), pady=(15, 8), sticky="we")
#         self.entrada_ruta.bind("<Return>", lambda e: self.cargar_desde_entrada())
        
#         btn_seleccionar = ctk. CTkButton(
#             top_frame,
#             text="📁 Seleccionar",
#             command=self.seleccionar_pdf,
#             width=130,
#             height=38,
#             font=ctk.CTkFont(size=13, weight="bold"),
#             corner_radius=8
#         )
#         btn_seleccionar.grid(row=0, column=2, padx=(0, 15), pady=(15, 8))
        
#         # Info del archivo
#         self.lbl_info = ctk.CTkLabel(
#             top_frame,
#             text="",
#             font=ctk.CTkFont(size=11),
#             text_color="gray60",
#             anchor="w"
#         )
#         self.lbl_info.grid(row=1, column=1, columnspan=2, padx=(0, 15), pady=(0, 8), sticky="w")
        
#         # Row 2: Carpeta de salida
#         lbl_salida = ctk.CTkLabel(
#             top_frame,
#             text="Carpeta de salida:",
#             font=ctk.CTkFont(size=13, weight="bold"),
#             width=120,
#             anchor="w"
#         )
#         lbl_salida.grid(row=2, column=0, padx=(15, 10), pady=8, sticky="w")
        
#         self.entrada_salida = ctk.CTkEntry(
#             top_frame,
#             placeholder_text="Por defecto:  misma carpeta del PDF de entrada",
#             font=ctk.CTkFont(size=12),
#             height=38,
#             corner_radius=8
#         )
#         self.entrada_salida.grid(row=2, column=1, padx=(0, 10), pady=8, sticky="we")
        
#         btn_carpeta = ctk.CTkButton(
#             top_frame,
#             text="📂 Carpeta",
#             command=self. seleccionar_carpeta_salida,
#             width=130,
#             height=38,
#             font=ctk.CTkFont(size=13, weight="bold"),
#             corner_radius=8,
#             fg_color="gray30",
#             hover_color="gray40"
#         )
#         btn_carpeta.grid(row=2, column=2, padx=(0, 15), pady=8)
        
#         # Row 3: Nombre del archivo
#         lbl_nombre = ctk.CTkLabel(
#             top_frame,
#             text="Nombre del archivo:",
#             font=ctk.CTkFont(size=13, weight="bold"),
#             width=120,
#             anchor="w"
#         )
#         lbl_nombre. grid(row=3, column=0, padx=(15, 10), pady=8, sticky="w")
        
#         self. entrada_nombre = ctk.CTkEntry(
#             top_frame,
#             placeholder_text="Nombre del PDF resultante (sin . pdf)",
#             font=ctk.CTkFont(size=12),
#             height=38,
#             corner_radius=8
#         )
#         self.entrada_nombre.grid(row=3, column=1, columnspan=2, padx=(0, 15), pady=8, sticky="we")
        
#         # Separador visual
#         separador = ctk.CTkFrame(top_frame, height=2, fg_color="gray25")
#         separador.grid(row=4, column=0, columnspan=3, sticky="we", padx=15, pady=(12, 8))
        
#         # Row 5: Botones de acción
#         btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
#         btn_frame.grid(row=5, column=0, columnspan=3, sticky="we", padx=15, pady=(8, 15))
#         btn_frame.grid_columnconfigure(0, weight=1)
#         btn_frame.grid_columnconfigure(1, weight=1)
        
#         self.btn_eliminar_top = ctk.CTkButton(
#             btn_frame,
#             text="🗑️ Eliminar y Guardar",
#             command=self.eliminar_paginas,
#             height=45,
#             font=ctk. CTkFont(size=15, weight="bold"),
#             fg_color="#2563eb",
#             hover_color="#1d4ed8",
#             corner_radius=10
#         )
#         self.btn_eliminar_top.grid(row=0, column=0, padx=(0, 8), sticky="we")
        
#         self.btn_deshacer = ctk.CTkButton(
#             btn_frame,
#             text="↶ Deshacer",
#             command=self.deshacer,
#             height=45,
#             font=ctk.CTkFont(size=15, weight="bold"),
#             fg_color="#f59e0b",
#             hover_color="#d97706",
#             text_color="gray10",
#             corner_radius=10,
#             state="disabled"
#         )
#         self.btn_deshacer. grid(row=0, column=1, padx=(8, 0), sticky="we")
        
#         top_frame.grid_columnconfigure(1, weight=1)
        
#         # ===== FRAME DE PÁGINAS =====
#         self.frame_paginas = ctk.CTkFrame(self.root, corner_radius=15)
#         self.frame_paginas. pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
#         # Header del frame de páginas
#         header_paginas = ctk.CTkFrame(self.frame_paginas, fg_color="transparent")
#         header_paginas.pack(fill="x", padx=20, pady=(20, 10))
        
#         lbl_titulo_paginas = ctk.CTkLabel(
#             header_paginas,
#             text="📋 Páginas del documento",
#             font=ctk.CTkFont(size=16, weight="bold"),
#             anchor="w"
#         )
#         lbl_titulo_paginas. pack(side="left")
        
#         self.lbl_contador = ctk.CTkLabel(
#             header_paginas,
#             text="",
#             font=ctk.CTkFont(size=13),
#             text_color="gray60",
#             anchor="e"
#         )
#         self.lbl_contador.pack(side="right")
        
#         # Descripción
#         lbl_desc = ctk.CTkLabel(
#             self.frame_paginas,
#             text="Marca las páginas que deseas eliminar del documento",
#             font=ctk.CTkFont(size=12),
#             text_color="gray50",
#             anchor="w"
#         )
#         lbl_desc.pack(anchor="w", padx=20, pady=(0, 10))
        
#         # ScrollableFrame para checkboxes - Con GRID para layout responsivo
#         self.scroll_frame = ctk.CTkScrollableFrame(
#             self. frame_paginas,
#             height=320,
#             fg_color="gray15",
#             corner_radius=10
#         )
#         self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
#         # Configurar grid inicial
#         self.actualizar_grid_columnas()
    
#     def on_window_resize(self, event):
#         """Detecta cambios de tamaño y ajusta el número de columnas"""
#         if event.widget != self.root:
#             return
        
#         ancho = self.root.winfo_width()
        
#         # Calcular número de columnas según el ancho - MÁS COMPACTO
#         if ancho < 900: 
#             nuevas_columnas = 3
#         elif ancho < 1100:
#             nuevas_columnas = 4
#         elif ancho < 1300:
#             nuevas_columnas = 5
#         elif ancho < 1500:
#             nuevas_columnas = 6
#         else:
#             nuevas_columnas = 7
        
#         # Si cambió el número de columnas, reorganizar
#         if nuevas_columnas != self.num_columnas and self.check_vars: 
#             self.num_columnas = nuevas_columnas
#             self.reorganizar_grid()
    
#     def actualizar_grid_columnas(self):
#         """Configura el grid con el número correcto de columnas"""
#         # Limpiar configuración anterior
#         for i in range(10):
#             try:
#                 self.scroll_frame.grid_columnconfigure(i, weight=0)
#             except:
#                 pass
        
#         # Configurar nuevas columnas
#         for i in range(self.num_columnas):
#             self.scroll_frame.grid_columnconfigure(i, weight=1)
    
#     def reorganizar_grid(self):
#         """Reorganiza los widgets en el nuevo grid"""
#         if not self.checkboxes: 
#             return
        
#         self.actualizar_grid_columnas()
        
#         # Reorganizar cada item
#         for idx, checkbox in enumerate(self.checkboxes):
#             page_item = checkbox.master. master  # El padre del checkbox es content_frame, el padre de ese es page_card
#             fila = idx // self.num_columnas
#             columna = idx % self.num_columnas
            
#             page_item.grid(row=fila, column=columna, padx=4, pady=4, sticky="n")
    
#     def obtener_ruta_corta(self, ruta_completa):
#         """Obtiene la ruta desde después de user/ en adelante"""
#         try:
#             ruta_normalizada = os.path.normpath(ruta_completa)
#             partes = ruta_normalizada. split(os.sep)
            
#             for i, parte in enumerate(partes):
#                 if parte. lower() in ['users', 'user', 'usuarios', 'usuario']:
#                     if i + 2 < len(partes):
#                         return os.sep.join(partes[i + 2:])
            
#             return os.path.basename(ruta_completa)
#         except:
#             return os.path.basename(ruta_completa)
    
#     def cargar_desde_entrada(self):
#         """Carga el PDF desde la ruta escrita en el input"""
#         ruta_escrita = self.entrada_ruta.get().strip()
        
#         if not ruta_escrita:
#             return
        
#         if not os.path.isabs(ruta_escrita):
#             home = os.path.expanduser("~")
#             ruta_completa = os.path.join(home, ruta_escrita)
#         else:
#             ruta_completa = ruta_escrita
        
#         if not os.path.exists(ruta_completa):
#             messagebox.showerror(
#                 "Error",
#                 f"El archivo no existe:\n{ruta_completa}"
#             )
#             return
        
#         if not ruta_completa.lower().endswith('.pdf'):
#             messagebox.showerror(
#                 "Error",
#                 "El archivo debe ser un PDF"
#             )
#             return
        
#         self.cargar_pdf(ruta_completa)
    
#     def seleccionar_pdf(self):
#         """Abre diálogo para seleccionar un PDF"""
#         ruta = filedialog.askopenfilename(
#             title="Seleccionar archivo PDF",
#             filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
#         )
        
#         if not ruta:
#             return
        
#         self.cargar_pdf(ruta)
    
#     def seleccionar_carpeta_salida(self):
#         """Abre diálogo para seleccionar carpeta de salida"""
#         carpeta = filedialog.askdirectory(
#             title="Seleccionar carpeta de salida"
#         )
        
#         if not carpeta:
#             return
        
#         self.entrada_salida.delete(0, "end")
#         self.entrada_salida.insert(0, carpeta)
    
#     def cargar_pdf(self, ruta):
#         """Carga el PDF y actualiza la interfaz"""
#         self.pdf_path = ruta
#         ruta_corta = self.obtener_ruta_corta(ruta)
        
#         try:
#             # Abrir PDF con fitz (mucho más rápido)
#             self.pdf_doc = fitz.open(ruta)
#             total_paginas = len(self.pdf_doc)
#             tamaño_mb = os.path.getsize(ruta) / (1024 * 1024)
            
#             # Actualizar entrada con ruta corta
#             self.entrada_ruta.delete(0, "end")
#             self.entrada_ruta.insert(0, ruta_corta)
            
#             # Establecer carpeta de salida por defecto
#             carpeta_entrada = os.path.dirname(ruta)
#             self.entrada_salida.delete(0, "end")
#             self.entrada_salida.insert(0, carpeta_entrada)
            
#             # Sugerir nombre para archivo de salida
#             nombre_base = os.path.splitext(os.path.basename(ruta))[0]
#             self.entrada_nombre.delete(0, "end")
#             self.entrada_nombre. insert(0, f"{nombre_base}_editado")
            
#             # Actualizar info
#             self.lbl_info.configure(
#                 text=f"✓ {total_paginas} páginas • {tamaño_mb:.2f} MB",
#                 text_color="#10b981"
#             )
            
#             # Cargar páginas en un hilo para no bloquear la UI
#             threading.Thread(target=self.cargar_paginas, daemon=True).start()
            
#         except Exception as e:
#             messagebox.showerror(
#                 "Error",
#                 f"No se pudo leer el archivo PDF:\n{str(e)}"
#             )
    
#     def generar_miniatura(self, num_pagina):
#         """Genera miniatura ULTRA PEQUEÑA de una página usando fitz"""
#         try:
#             pagina = self.pdf_doc[num_pagina]
#             # Renderizar página a imagen MUY PEQUEÑA - 0.2x del tamaño original
#             pix = pagina.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
#             img_data = pix.tobytes("ppm")
            
#             # Convertir a imagen PIL
#             imagen = Image.open(BytesIO(img_data))
            
#             return imagen
#         except: 
#             return None
    
#     def cargar_paginas(self):
#         """Carga los checkboxes de las páginas del PDF con miniaturas en grid responsivo ultra compacto"""
#         # Limpiar widgets existentes
#         for widget in self.scroll_frame.winfo_children():
#             widget.destroy()
        
#         self.check_vars. clear()
#         self.checkboxes. clear()
#         self.thumbnails.clear()
        
#         try:
#             total = len(self.pdf_doc)
            
#             for i in range(total):
#                 var = ctk.BooleanVar()
                
#                 # Crear card de página - ULTRA COMPACTA
#                 page_card = ctk.CTkFrame(
#                     self.scroll_frame,
#                     fg_color="gray20",
#                     corner_radius=6,
#                     border_width=1,
#                     border_color="gray25"
#                 )
                
#                 # Calcular posición en grid
#                 fila = i // self.num_columnas
#                 columna = i % self.num_columnas
#                 page_card.grid(row=fila, column=columna, padx=4, pady=4, sticky="n")
                
#                 # Contenedor vertical dentro de la card - SIN PADDING
#                 content_frame = ctk.CTkFrame(page_card, fg_color="transparent")
#                 content_frame.pack(fill="both", expand=False, padx=0, pady=0)
                
#                 # ===== MINIATURA - ULTRA PEQUEÑA =====
#                 try:
#                     img = self.generar_miniatura(i)
#                     if img:
#                         # Obtener el tamaño real de la miniatura
#                         img_width, img_height = img.size
                        
#                         ctk_img = ctk.CTkImage(light_image=img, size=(img_width, img_height))
#                         lbl_img = ctk.CTkLabel(
#                             content_frame, 
#                             image=ctk_img, 
#                             text="",
#                             corner_radius=3
#                         )
#                         lbl_img.pack(fill="both", padx=0, pady=0)
#                         self.thumbnails.append(ctk_img)
#                 except: 
#                     pass
                
#                 # ===== INFO Y CONTROLS - COMPACTO =====
#                 info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
#                 info_frame.pack(fill="x", padx=3, pady=3)
                
#                 # Número de página - MÁS PEQUEÑO
#                 lbl_numero = ctk.CTkLabel(
#                     info_frame,
#                     text=f"{i + 1}",
#                     font=ctk.CTkFont(size=8, weight="bold"),
#                     anchor="w"
#                 )
#                 lbl_numero.pack(anchor="w", pady=(0, 1))
                
#                 # Checkbox - MÁS PEQUEÑO
#                 chk = ctk.CTkCheckBox(
#                     info_frame,
#                     text="",
#                     variable=var,
#                     font=ctk.CTkFont(size=8),
#                     command=self.actualizar_contador,
#                     corner_radius=3,
#                     width=20,
#                     checkbox_width=16,
#                     checkbox_height=16
#                 )
#                 chk.pack(anchor="w", pady=0)
                
#                 self.check_vars.append(var)
#                 self.checkboxes.append(chk)
            
#             self.actualizar_contador()
            
#         except Exception as e:
#             messagebox.showerror(
#                 "Error",
#                 f"Error al cargar las páginas:\n{str(e)}"
#             )
    
#     def actualizar_contador(self):
#         """Actualiza el contador de páginas seleccionadas"""
#         seleccionadas = sum(1 for var in self.check_vars if var.get())
#         total = len(self.check_vars)
        
#         if seleccionadas > 0:
#             self.lbl_contador.configure(
#                 text=f"🗑️ {seleccionadas} de {total} páginas seleccionadas",
#                 text_color="#ef4444"
#             )
#         else:
#             self.lbl_contador.configure(
#                 text=f"0 de {total} páginas seleccionadas",
#                 text_color="gray60"
#             )
    
#     def eliminar_paginas(self):
#         """Elimina las páginas seleccionadas y guarda el nuevo PDF automáticamente"""
#         if not self.pdf_doc:
#             messagebox.showwarning(
#                 "Advertencia",
#                 "Por favor, seleccione un archivo PDF primero"
#             )
#             return
        
#         paginas_a_eliminar = [
#             i for i, var in enumerate(self.check_vars) if var.get()
#         ]
        
#         if not paginas_a_eliminar:
#             messagebox.showwarning(
#                 "Advertencia",
#                 "No ha seleccionado ninguna página para eliminar"
#             )
#             return
        
#         try:
#             total_paginas = len(self.pdf_doc)
            
#             if len(paginas_a_eliminar) == total_paginas:
#                 messagebox.showerror(
#                     "Error",
#                     "No se pueden eliminar todas las páginas.\nDebe quedar al menos una página en el PDF."
#                 )
#                 return
            
#             respuesta = messagebox.askyesno(
#                 "Confirmar",
#                 f"¿Está seguro de eliminar {len(paginas_a_eliminar)} página(s)?\n\n"
#                 f"El PDF resultante tendrá {total_paginas - len(paginas_a_eliminar)} página(s)."
#             )
            
#             if not respuesta:
#                 return
            
#             # Crear documento nuevo y copiar solo las páginas que no se eliminan
#             doc_nuevo = fitz.open()
            
#             for i in range(total_paginas):
#                 if i not in paginas_a_eliminar:
#                     doc_nuevo.insert_pdf(self.pdf_doc, from_page=i, to_page=i)
            
#             # Obtener carpeta de salida
#             carpeta_salida = self.entrada_salida.get().strip()
#             if not carpeta_salida: 
#                 carpeta_salida = os.path.dirname(self.pdf_path)
            
#             nombre_archivo = self.entrada_nombre.get().strip()
#             if not nombre_archivo:
#                 nombre_archivo = f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}_editado"
            
#             if nombre_archivo.lower().endswith('.pdf'):
#                 nombre_archivo = nombre_archivo[:-4]
            
#             ruta_salida = os.path.join(carpeta_salida, f"{nombre_archivo}.pdf")
            
#             contador = 1
#             ruta_base = ruta_salida
#             while os.path.exists(ruta_salida):
#                 nombre_sin_ext = os.path.splitext(ruta_base)[0]
#                 ruta_salida = f"{nombre_sin_ext} ({contador}).pdf"
#                 contador += 1
            
#             # Guardar con fitz (muy eficiente)
#             doc_nuevo.save(ruta_salida, garbage=4, deflate=True)
#             doc_nuevo.close()
            
#             self.last_operation = {
#                 'original':  self.pdf_path,
#                 'created': ruta_salida,
#                 'deleted_pages': paginas_a_eliminar. copy()
#             }
            
#             self.btn_deshacer.configure(state="normal")
            
#             messagebox.showinfo(
#                 "Éxito",
#                 f"✓ PDF generado correctamente\n\n{total_paginas - len(paginas_a_eliminar)} páginas guardadas en:\n{ruta_salida}"
#             )
            
#             for var in self.check_vars:
#                 var.set(False)
#             self.actualizar_contador()
            
#         except Exception as e: 
#             messagebox.showerror(
#                 "Error",
#                 f"Error al procesar el PDF:\n{str(e)}"
#             )
    
#     def deshacer(self):
#         """Deshace la última operación eliminando el archivo creado"""
#         if not self.last_operation:
#             messagebox.showinfo("Info", "No hay operación para deshacer")
#             return
        
#         archivo_creado = self.last_operation. get('created')
        
#         if not archivo_creado or not os.path.exists(archivo_creado):
#             messagebox.showwarning(
#                 "Advertencia",
#                 "El archivo creado ya no existe"
#             )
#             self.last_operation = None
#             self.btn_deshacer.configure(state="disabled")
#             return
        
#         respuesta = messagebox.askyesno(
#             "Confirmar Deshacer",
#             f"¿Está seguro de eliminar el archivo creado?\n\n{archivo_creado}"
#         )
        
#         if not respuesta:
#             return
        
#         try:
#             os.remove(archivo_creado)
            
#             messagebox.showinfo(
#                 "Deshacer completado",
#                 f"El archivo ha sido eliminado:\n{archivo_creado}"
#             )
            
#             self. last_operation = None
#             self.btn_deshacer.configure(state="disabled")
            
#         except Exception as e:
#             messagebox.showerror(
#                 "Error",
#                 f"No se pudo eliminar el archivo:\n{str(e)}"
#             )


# def main():
#     """Función principal"""
#     root = ctk.CTk()
#     app = PDFEditorApp(root)
#     root.mainloop()


# if __name__ == "__main__":
#     main()

import customtkinter as ctk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
import os
from PIL import Image
from io import BytesIO
import threading


class PDFEditorApp(ctk.CTkFrame):
    """Aplicación para editar PDFs eliminando páginas - Estilo PDFSplitterApp completo"""
    
    def __init__(self, master, go_home=None):
        super().__init__(master)
        
        # ===== STATE CENTRALIZED =====
        # Archivo y documento
        self.pdf_path = ""
        self. pdf_doc = None
        
        # Páginas y selección
        self.page_count = 0
        self.check_vars = []              # Variables observables para checkboxes
        self.checkboxes = []              # Widgets de checkbox
        self.thumbnails = []              # Cache de imágenes CTkImage
        
        # Configuración de layout
        self.num_columnas = 5             # Columnas responsive
        self.last_num_columnas = 5
        
        # Operación y historial
        self.last_operation = None        # {'original': path, 'created': path, 'deleted_pages': [... ]}
        self.loading = False              # Flag de carga
        
        # Entradas del usuario (para observar cambios)
        self.carpeta_salida_var = ctk.StringVar()
        self.nombre_archivo_var = ctk.StringVar()
        
        # ===== CONFIGURACIÓN GENERAL =====
        self.master = master
        self.master.title("📄 Editor de Páginas PDF")
        self.master.geometry("1400x900")
        self.master.minsize(800, 700)
        self.master.resizable(True, True)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # ===== BUILD UI =====
        self._crear_ui()
        
        # ===== EVENT BINDING =====
        self.master.bind("<Configure>", self._on_window_resize)
    
    # ==================== UI BUILDING ====================
    
    def _crear_ui(self):
        """Crea la interfaz completa"""
        self.pack(fill="both", expand=True)
        
        self._crear_header()
        self._crear_top_frame()
        self._crear_frame_paginas()
    
    def _crear_header(self):
        """Header con título y subtítulo"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        lbl_titulo = ctk.CTkLabel(
            header_frame,
            text="📄 Editor de Páginas PDF",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        lbl_titulo. pack()
        
        lbl_subtitulo = ctk.CTkLabel(
            header_frame,
            text="Elimina páginas de tus documentos PDF de forma rápida y sencilla",
            font=ctk.CTkFont(size=13),
            text_color="gray60"
        )
        lbl_subtitulo.pack(pady=(5, 0))
    
    def _crear_top_frame(self):
        """Frame superior con controles de entrada/salida - ESTILO PDFSplitterApp"""
        top_frame = ctk.CTkFrame(self, corner_radius=15)
        top_frame.pack(fill="x", padx=6, pady=6)
        top_frame.grid_columnconfigure(1, weight=1)
        
        # ===== Row 0:  PDF de entrada =====
        lbl_pdf = ctk.CTkLabel(
            top_frame,
            text="PDF:",
            width=40,
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        lbl_pdf.grid(row=0, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.entrada_ruta = ctk.CTkEntry(
            top_frame,
            placeholder_text="Escribe la ruta del PDF o usa Seleccionar",
            width=500,
            height=32,
            font=ctk. CTkFont(size=11)
        )
        self.entrada_ruta.grid(row=0, column=1, padx=(0, 6), pady=4, sticky="we")
        self.entrada_ruta.bind("<Return>", lambda e: self.cargar_desde_entrada())
        
        btn_seleccionar = ctk. CTkButton(
            top_frame,
            text="Seleccionar PDF",
            command=self.seleccionar_pdf,
            width=140,
            height=32,
            font=ctk. CTkFont(size=11, weight="bold"),
            corner_radius=6
        )
        btn_seleccionar.grid(row=0, column=2, padx=(0, 6), pady=4)
        
        # Info del archivo
        self.lbl_info = ctk.CTkLabel(
            top_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray60",
            anchor="w"
        )
        self.lbl_info.grid(row=1, column=1, columnspan=2, padx=(0, 6), pady=(0, 4), sticky="w")
        
        # ===== Row 2: Carpeta de salida =====
        lbl_salida = ctk.CTkLabel(
            top_frame,
            text="Salida:",
            width=60,
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        lbl_salida.grid(row=2, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.entrada_salida = ctk.CTkEntry(
            top_frame,
            placeholder_text="Carpeta de salida (opcional)",
            width=420,
            height=32,
            font=ctk.CTkFont(size=11),
            textvariable=self.carpeta_salida_var
        )
        self.entrada_salida.grid(row=2, column=1, padx=(0, 6), pady=4, sticky="we")
        
        btn_carpeta = ctk.CTkButton(
            top_frame,
            text="Seleccionar Carpeta",
            command=self.seleccionar_carpeta_salida,
            width=140,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=6
        )
        btn_carpeta.grid(row=2, column=2, padx=(0, 6), pady=4)
        
        # ===== Row 3: Nombre del archivo =====
        lbl_nombre = ctk.CTkLabel(
            top_frame,
            text="Nombre:",
            width=60,
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        lbl_nombre.grid(row=3, column=0, padx=(6, 4), pady=4, sticky="w")
        
        self.entrada_nombre = ctk.CTkEntry(
            top_frame,
            placeholder_text="Nombre del PDF resultante",
            width=420,
            height=32,
            font=ctk.CTkFont(size=11),
            textvariable=self.nombre_archivo_var
        )
        self.entrada_nombre.grid(row=3, column=1, columnspan=2, padx=(0, 6), pady=4, sticky="we")
        
        # ===== Row 4: Spacer (compacto) =====
        spacer = ctk.CTkFrame(top_frame, height=2)
        spacer.grid(row=4, column=0, columnspan=3, sticky="we", padx=6, pady=(2, 4))
        
        # ===== Row 5: Botones de acción =====
        btn_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=3, sticky="we", padx=6, pady=(0, 6))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        
        self.btn_eliminar = ctk.CTkButton(
            btn_frame,
            text="🗑️ Eliminar y Guardar",
            command=self.eliminar_paginas,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1f6feb",
            corner_radius=6
        )
        self.btn_eliminar.grid(row=0, column=0, padx=6, pady=4, sticky="we")
        
        self.btn_deshacer = ctk.CTkButton(
            btn_frame,
            text="↶ Deshacer",
            command=self.deshacer,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#f0ad4e",
            text_color="black",
            corner_radius=6,
            state="disabled"
        )
        self.btn_deshacer.grid(row=0, column=1, padx=6, pady=4, sticky="we")
        
        self. btn_limpiar = ctk.CTkButton(
            btn_frame,
            text="🧹 Limpiar selección",
            command=self._limpiar_seleccion,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="gray30",
            corner_radius=6
        )
        self.btn_limpiar.grid(row=0, column=2, padx=6, pady=4, sticky="we")
    
    def _crear_frame_paginas(self):
        """Frame para mostrar páginas con grid responsivo"""
        self.frame_paginas = ctk.CTkFrame(self, corner_radius=15)
        self.frame_paginas.pack(fill="both", expand=True, padx=6, pady=6)
        
        # Header del frame
        header_paginas = ctk.CTkFrame(self.frame_paginas, fg_color="transparent")
        header_paginas.pack(fill="x", padx=6, pady=(6, 4))
        header_paginas.grid_columnconfigure(1, weight=1)
        
        lbl_titulo_paginas = ctk.CTkLabel(
            header_paginas,
            text="📋 Páginas del documento",
            font=ctk. CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        lbl_titulo_paginas. grid(row=0, column=0, sticky="w")
        
        self.lbl_contador = ctk.CTkLabel(
            header_paginas,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray60",
            anchor="e"
        )
        self.lbl_contador.grid(row=0, column=1, sticky="e")
        
        # Descripción
        lbl_desc = ctk.CTkLabel(
            self.frame_paginas,
            text="Marca las páginas que deseas eliminar del documento",
            font=ctk.CTkFont(size=10),
            text_color="gray50",
            anchor="w"
        )
        lbl_desc.pack(anchor="w", padx=6, pady=(0, 4))
        
        # ScrollableFrame con grid
        self.scroll_frame = ctk.CTkScrollableFrame(
            self. frame_paginas,
            height=320,
            fg_color="gray15",
            corner_radius=10
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        
        self._actualizar_grid_columnas()
    
    # ==================== EVENT HANDLERS ====================
    
    def _on_window_resize(self, event):
        """Detecta cambios de tamaño y ajusta columnas"""
        if event.widget != self.master:
            return
        
        ancho = self.master.winfo_width()
        
        # Calcular columnas según ancho - IGUAL QUE ANTES
        if ancho < 900:  
            nuevas_columnas = 3
        elif ancho < 1100:
            nuevas_columnas = 4
        elif ancho < 1300:
            nuevas_columnas = 5
        elif ancho < 1500:
            nuevas_columnas = 6
        else:
            nuevas_columnas = 7
        
        # Si cambió, reorganizar
        if nuevas_columnas != self.num_columnas and self.checkboxes:  
            self. num_columnas = nuevas_columnas
            self._reorganizar_grid()
    
    def _actualizar_grid_columnas(self):
        """Configura grid con número correcto de columnas"""
        # Limpiar configuración anterior
        for i in range(10):
            try:
                self.scroll_frame.grid_columnconfigure(i, weight=0)
            except:
                pass
        
        # Configurar nuevas columnas
        for i in range(self.num_columnas):
            self.scroll_frame.grid_columnconfigure(i, weight=1)
    
    def _reorganizar_grid(self):
        """Reorganiza widgets cuando cambian las columnas"""
        if not self.checkboxes:
            return
        
        self._actualizar_grid_columnas()
        
        for idx, checkbox in enumerate(self.checkboxes):
            page_item = checkbox.master. master
            fila = idx // self.num_columnas
            columna = idx % self.num_columnas
            
            page_item.grid(row=fila, column=columna, padx=4, pady=4, sticky="n")
    
    # ==================== PDF LOADING ====================
    
    def seleccionar_pdf(self):
        """Abre diálogo para seleccionar PDF"""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        
        if ruta:
            self.cargar_pdf(ruta)
    
    def cargar_desde_entrada(self):
        """Carga PDF desde ruta escrita"""
        ruta_escrita = self.entrada_ruta.get().strip()
        
        if not ruta_escrita:
            return
        
        # Resolver ruta
        if not os.path.isabs(ruta_escrita):
            home = os.path.expanduser("~")
            ruta_completa = os.path.join(home, ruta_escrita)
        else:
            ruta_completa = ruta_escrita
        
        # Validaciones
        if not os.path. exists(ruta_completa):
            messagebox.showerror("Error", f"El archivo no existe:\n{ruta_completa}")
            return
        
        if not ruta_completa.lower().endswith('.pdf'):
            messagebox.showerror("Error", "El archivo debe ser un PDF")
            return
        
        self.cargar_pdf(ruta_completa)
    
    def cargar_pdf(self, ruta):
        """Carga el PDF y actualiza UI"""
        self.pdf_path = ruta
        ruta_corta = self._obtener_ruta_corta(ruta)
        
        try:
            self.pdf_doc = fitz.open(ruta)
            self.page_count = len(self.pdf_doc)
            tamaño_mb = os.path.getsize(ruta) / (1024 * 1024)
            
            # Actualizar entradas
            self.entrada_ruta. delete(0, "end")
            self.entrada_ruta.insert(0, ruta_corta)
            
            carpeta_entrada = os.path.dirname(ruta)
            self.carpeta_salida_var.set(carpeta_entrada)
            
            nombre_base = os.path.splitext(os.path.basename(ruta))[0]
            self. nombre_archivo_var.set(f"{nombre_base}_editado")
            
            # Actualizar info
            self.lbl_info.configure(
                text=f"✓ {self.page_count} páginas • {tamaño_mb:.2f} MB",
                text_color="#10b981"
            )
            
            # Cargar páginas en hilo
            threading.Thread(target=self._cargar_paginas, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el PDF:\n{str(e)}")
            print(f"[ERROR] Cargar PDF: {e}")
    
    def seleccionar_carpeta_salida(self):
        """Selecciona carpeta de salida"""
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        
        if carpeta:
            self.carpeta_salida_var.set(carpeta)
    
    @staticmethod
    def _obtener_ruta_corta(ruta_completa):
        """Obtiene ruta corta desde después de user/"""
        try:
            ruta_normalizada = os.path.normpath(ruta_completa)
            partes = ruta_normalizada. split(os.sep)
            
            for i, parte in enumerate(partes):
                if parte. lower() in ['users', 'user', 'usuarios', 'usuario']:
                    if i + 2 < len(partes):
                        return os.sep.join(partes[i + 2:])
            
            return os.path.basename(ruta_completa)
        except:
            return os.path.basename(ruta_completa)
    
    # ==================== PAGE THUMBNAIL GENERATION ====================
    
    def _generar_miniatura(self, num_pagina):
        """Genera miniatura ultra pequeña (0.2x) de una página"""
        try:
            pagina = self.pdf_doc[num_pagina]
            pix = pagina.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
            img_data = pix.tobytes("ppm")
            
            imagen = Image.open(BytesIO(img_data))
            return imagen
        except Exception as e:  
            print(f"[WARN] Error generando miniatura página {num_pagina}: {e}")
            return None
    
    # ==================== PAGE LOADING ====================
    
    def _cargar_paginas(self):
        """Carga checkboxes y miniaturas en grid responsivo - ESTILO COMPLETO"""
        # Limpiar widgets anteriores
        for widget in self.scroll_frame.winfo_children():
            widget. destroy()
        
        self. check_vars. clear()
        self.checkboxes. clear()
        self.thumbnails.clear()
        
        try:
            for i in range(self.page_count):
                var = ctk.BooleanVar()
                
                # Card de página - ULTRA COMPACTA
                page_card = ctk.CTkFrame(
                    self.scroll_frame,
                    fg_color="gray20",
                    corner_radius=6,
                    border_width=1,
                    border_color="gray25"
                )
                
                fila = i // self.num_columnas
                columna = i % self. num_columnas
                page_card.grid(row=fila, column=columna, padx=4, pady=4, sticky="n")
                
                # Contenedor vertical
                content_frame = ctk.CTkFrame(page_card, fg_color="transparent")
                content_frame.pack(fill="both", expand=False, padx=0, pady=0)
                
                # ===== MINIATURA CON NÚMERO DE PÁGINA =====
                try:
                    img = self._generar_miniatura(i)
                    if img:
                        img_width, img_height = img.size
                        
                        # Frame para la miniatura y el número
                        thumb_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                        thumb_frame.pack(fill="both", padx=0, pady=0)
                        
                        # Miniatura
                        ctk_img = ctk.CTkImage(light_image=img, size=(img_width, img_height))
                        lbl_img = ctk.CTkLabel(
                            thumb_frame,
                            image=ctk_img,
                            text="",
                            corner_radius=3
                        )
                        lbl_img.pack(fill="both", padx=0, pady=0)
                        self.thumbnails.append(ctk_img)
                        
                        # NÚMERO DE PÁGINA SUPERPUESTO EN LA MINIATURA
                        num_label = ctk.CTkLabel(
                            lbl_img,
                            text=f"Página {i + 1}",
                            font=ctk.CTkFont(size=12, weight="bold"),
                            text_color="white",
                            bg_color="transparent",
                            corner_radius=3
                        )
                        # Posicionar en esquina inferior derecha
                        num_label. place(relx=1, rely=1, anchor="se", padx=4, pady=4)
                        
                except Exception as e:
                    print(f"[WARN] Error mostrando miniatura {i}: {e}")
                
                # ===== INFO Y CONTROLES =====
                info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                info_frame. pack(fill="x", padx=3, pady=3)
                
                # Checkbox con texto "ELIMINAR"
                chk = ctk.CTkCheckBox(
                    info_frame,
                    text="Eliminar",
                    variable=var,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    command=self._actualizar_contador,
                    corner_radius=3,
                    width=20,
                    checkbox_width=18,
                    checkbox_height=18
                )
                chk.pack(anchor="w", pady=2, padx=2)
                
                self.check_vars.append(var)
                self.checkboxes.append(chk)
            
            self._actualizar_contador()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar las páginas:\n{str(e)}")
            print(f"[ERROR] Cargar páginas: {e}")
    
    def _actualizar_contador(self):
        """Actualiza el contador de páginas seleccionadas"""
        seleccionadas = sum(1 for var in self. check_vars if var.get())
        total = len(self.check_vars)
        
        if seleccionadas > 0:
            self.lbl_contador.configure(
                text=f"🗑️ {seleccionadas} de {total} páginas para eliminar",
                text_color="#ef4444"
            )
        else:
            self.lbl_contador.configure(
                text=f"0 de {total} páginas seleccionadas",
                text_color="gray60"
            )
    
    def _limpiar_seleccion(self):
        """Limpia todas las selecciones"""
        for var in self.check_vars:
            var.set(False)
        self._actualizar_contador()
    
    # ==================== PDF OPERATIONS ====================
    
    def eliminar_paginas(self):
        """Elimina las páginas seleccionadas y guarda el PDF"""
        if not self.pdf_doc:
            messagebox. showwarning("Advertencia", "Por favor, seleccione un archivo PDF primero")
            return
        
        paginas_a_eliminar = [i for i, var in enumerate(self.check_vars) if var.get()]
        
        if not paginas_a_eliminar:
            messagebox.showwarning("Advertencia", "No ha seleccionado ninguna página para eliminar")
            return
        
        if len(paginas_a_eliminar) == self.page_count:
            messagebox.showerror(
                "Error",
                "No se pueden eliminar todas las páginas.\nDebe quedar al menos una página en el PDF."
            )
            return
        
        # Confirmar
        respuesta = messagebox.askyesno(
            "Confirmar",
            f"¿Está seguro de eliminar {len(paginas_a_eliminar)} página(s)?\n\n"
            f"El PDF resultante tendrá {self.page_count - len(paginas_a_eliminar)} página(s)."
        )
        
        if not respuesta:
            return
        
        try:
            # Crear documento nuevo
            doc_nuevo = fitz.open()
            
            for i in range(self.page_count):
                if i not in paginas_a_eliminar:
                    doc_nuevo.insert_pdf(self.pdf_doc, from_page=i, to_page=i)
            
            # Obtener ruta de salida
            ruta_salida = self._obtener_ruta_salida(paginas_a_eliminar)
            
            # Guardar
            doc_nuevo.save(ruta_salida, garbage=4, deflate=True)
            doc_nuevo.close()
            
            # Guardar estado para deshacer
            self. last_operation = {
                'original':  self.pdf_path,
                'created': ruta_salida,
                'deleted_pages': paginas_a_eliminar. copy()
            }
            
            self.btn_deshacer.configure(state="normal")
            
            # Mensaje de éxito
            messagebox.showinfo(
                "Éxito",
                f"✓ PDF generado correctamente\n\n"
                f"{self.page_count - len(paginas_a_eliminar)} páginas guardadas en:\n{ruta_salida}"
            )
            
            # Limpiar selección
            for var in self.check_vars:
                var.set(False)
            self._actualizar_contador()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar el PDF:\n{str(e)}")
            print(f"[ERROR] Eliminar páginas: {e}")
    
    def _obtener_ruta_salida(self, paginas_eliminadas):
        """Obtiene la ruta de salida con manejo de duplicados"""
        carpeta_salida = self.carpeta_salida_var.get().strip()
        if not carpeta_salida:  
            carpeta_salida = os.path.dirname(self.pdf_path)
        
        nombre_archivo = self.nombre_archivo_var.get().strip()
        if not nombre_archivo: 
            nombre_archivo = f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}_editado"
        
        if nombre_archivo.lower().endswith('.pdf'):
            nombre_archivo = nombre_archivo[:-4]
        
        ruta_salida = os.path.join(carpeta_salida, f"{nombre_archivo}.pdf")
        
        # Evitar duplicados
        contador = 1
        ruta_base = ruta_salida
        while os.path.exists(ruta_salida):
            nombre_sin_ext = os.path.splitext(ruta_base)[0]
            ruta_salida = f"{nombre_sin_ext} ({contador}).pdf"
            contador += 1
        
        return ruta_salida
    
    def deshacer(self):
        """Deshace la última operación"""
        if not self.last_operation:
            messagebox.showinfo("Info", "No hay operación para deshacer")
            return
        
        archivo_creado = self.last_operation. get('created')
        
        if not archivo_creado or not os.path.exists(archivo_creado):
            messagebox.showwarning("Advertencia", "El archivo creado ya no existe")
            self.last_operation = None
            self.btn_deshacer.configure(state="disabled")
            return
        
        respuesta = messagebox.askyesno(
            "Confirmar Deshacer",
            f"¿Está seguro de eliminar el archivo creado?\n\n{archivo_creado}"
        )
        
        if not respuesta:
            return
        
        try:
            os.remove(archivo_creado)
            
            messagebox.showinfo(
                "Deshacer completado",
                f"El archivo ha sido eliminado:\n{archivo_creado}"
            )
            
            self.last_operation = None
            self.btn_deshacer. configure(state="disabled")
            
        except Exception as e:  
            messagebox.showerror("Error", f"No se pudo eliminar el archivo:\n{str(e)}")
            print(f"[ERROR] Deshacer: {e}")


def main():
    """Función principal"""
    root = ctk.CTk()
    app = PDFEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()