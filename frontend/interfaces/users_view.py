import customtkinter as ctk
from tkinter import messagebox, ttk
from backend.services.user_service import get_all_users, create_user, delete_user

class UsersView(ctk.CTkFrame):
    def __init__(self, parent, role="Admin"):
        super().__init__(parent, fg_color="transparent")
        self.role = role

        # Configuración del diseño interno (Grid)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Título del Módulo
        self.title_label = ctk.CTkLabel(
            self, 
            text="Gestión y Control de Usuarios", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # 2. Contenedor principal dividido (Formulario a la izquierda / Tabla a la derecha)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.main_container.grid_columnconfigure(1, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # --- Panel Izquierdo: Formulario de Registro ---
        self.form_frame = ctk.CTkFrame(self.main_container, width=320, corner_radius=10)
        self.form_frame.grid(row=0, column=0, padx=(0, 15), pady=0, sticky="nsew")
        
        self.setup_form()

        # --- Panel Derecho: Tabla / Lista de Usuarios ---
        self.table_frame = ctk.CTkFrame(self.main_container, corner_radius=10)
        self.table_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        self.table_frame.grid_rowconfigure(1, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        self.setup_table()

    def setup_form(self):
        """Configura los campos del formulario para dar de alta usuarios según su rol."""
        lbl_form = ctk.CTkLabel(self.form_frame, text="Registrar Usuario", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_form.pack(padx=20, pady=(20, 15), anchor="w")

        # Nombre
        self.entry_nombre = ctk.CTkEntry(self.form_frame, placeholder_text="Nombre completo", width=260, height=40)
        self.entry_nombre.pack(padx=20, pady=8)

        # Correo
        self.entry_correo = ctk.CTkEntry(self.form_frame, placeholder_text="Correo electrónico", width=260, height=40)
        self.entry_correo.pack(padx=20, pady=8)

        # Contraseña
        self.entry_password = ctk.CTkEntry(self.form_frame, placeholder_text="Contraseña (mínimo 4 caracteres)", show="*", width=260, height=40)
        self.entry_password.pack(padx=20, pady=8)

        # Selector de Perfil / Rol
        lbl_rol = ctk.CTkLabel(self.form_frame, text="Perfil / Rol asignado:", font=ctk.CTkFont(size=12))
        lbl_rol.pack(padx=20, pady=(8, 2), anchor="w")

        # Regla de negocio: Admin puede asignar cualquier rol; Gerente solo puede dar de alta a Encargados
        roles_disponibles = ["Admin", "Gerente", "Encargado"] if self.role == "Admin" else ["Encargado"]
        
        self.combo_rol = ctk.CTkComboBox(self.form_frame, values=roles_disponibles, width=260, height=40)
        self.combo_rol.pack(padx=20, pady=(2, 15))
        if roles_disponibles:
            self.combo_rol.set(roles_disponibles[-1] if self.role != "Admin" else roles_disponibles[0])

        # Botón Guardar
        self.btn_guardar = ctk.CTkButton(
            self.form_frame, text="Guardar Usuario", fg_color="#27AE60", hover_color="#219653",
            command=self.save_user, width=260, height=40, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_guardar.pack(padx=20, pady=(10, 20))

    def setup_table(self):
        """Configura la barra superior de acciones y la tabla de usuarios."""
        # Barra superior con botón de actualizar y eliminar (si es Admin)
        toolbar = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        lbl_lista = ctk.CTkLabel(toolbar, text="Usuarios Registrados en el Sistema", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_lista.pack(side="left", padx=5)

        btn_refresh = ctk.CTkButton(toolbar, text="Actualizar", width=100, height=32, command=self.load_users_from_db)
        btn_refresh.pack(side="right", padx=5)

        if self.role == "Admin":
            btn_delete = ctk.CTkButton(
                toolbar, text="Eliminar Seleccionado", fg_color="#C0392B", hover_color="#962D22",
                width=160, height=32, command=self.delete_selected_user
            )
            btn_delete.pack(side="right", padx=5)

        # Tabla Treeview
        columns = ("ID", "Perfil", "Nombre", "Correo")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", height=15)
        
        widths = [60, 110, 200, 220]
        for col, width in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center")

        self.tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Cargar los datos desde la base de datos real
        self.load_users_from_db()

    def load_users_from_db(self):
        """Carga los usuarios reales desde PostgreSQL a través de user_service."""
        # Limpiar registros existentes en el Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        users = get_all_users()
        for user in users:
            self.tree.insert("", "end", values=(
                user["id_usuario"],
                user["perfil"],
                user["nombre"],
                user["correo"]
            ))

    def save_user(self):
        """Valida las entradas y llama al servicio para registrar el usuario."""
        nombre = self.entry_nombre.get().strip()
        correo = self.entry_correo.get().strip()
        password = self.entry_password.get().strip()
        perfil = self.combo_rol.get().strip()

        if not nombre or not correo or not password or not perfil:
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        success, msg = create_user(
            nombre=nombre,
            correo=correo,
            password=password,
            perfil=perfil,
            creator_role=self.role
        )

        if success:
            messagebox.showinfo("Éxito", msg)
            # Limpiar campos y refrescar tabla
            self.entry_nombre.delete(0, 'end')
            self.entry_correo.delete(0, 'end')
            self.entry_password.delete(0, 'end')
            self.load_users_from_db()
        else:
            messagebox.showerror("No se pudo registrar", msg)

    def delete_selected_user(self):
        """Elimina el usuario seleccionado en la tabla (Solo Administrador)."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un usuario de la tabla para eliminarlo.")
            return

        item_values = self.tree.item(selected_item[0], "values")
        id_usuario = int(item_values[0])
        nombre_usuario = item_values[2]
        perfil_usuario = item_values[1]

        if not messagebox.askyesno("Confirmar Eliminación", f"¿Está seguro de eliminar al usuario '{nombre_usuario}' ({perfil_usuario})?"):
            return

        success, msg = delete_user(id_usuario, creator_role=self.role)
        if success:
            messagebox.showinfo("Eliminado", msg)
            self.load_users_from_db()
        else:
            messagebox.showerror("Error al eliminar", msg)

if __name__ == "__main__":
    # Prueba unitaria individual de la vista
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
    
    app = ctk.CTk()
    app.title("Prueba Unitaria - Gestión de Usuarios")
    app.geometry("980x600")

    # Puedes cambiar role="Admin" o role="Gerente" para probar el comportamiento de permisos
    view = UsersView(parent=app, role="Admin")
    view.pack(fill="both", expand=True)

    app.mainloop()
