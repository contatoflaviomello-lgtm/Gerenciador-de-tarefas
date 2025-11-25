import json
import os
from datetime import datetime
import customtkinter as ctk

# =========================
# Configuração de tema
# =========================
ctk.set_appearance_mode("dark")            # "light" ou "dark"
ctk.set_default_color_theme("dark-blue")   # "blue", "green", "dark-blue"

# =========================
# Modelo e persistência
# =========================


class TaskStore:
    def __init__(self, path="tasks.json"):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def save(self, tasks):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)


def is_overdue(due_date_str, done=False):
    if done or not due_date_str:
        return False
    try:
        due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        return due < datetime.today().date()
    except ValueError:
        return False

# =========================
# Diálogo de adicionar/editar
# =========================


class TaskDialog(ctk.CTkToplevel):
    def __init__(self, master, title="Nova tarefa", initial=None, on_submit=None):
        super().__init__(master)
        self.title(title)
        self.geometry("420x360")
        self.resizable(False, False)
        self.on_submit = on_submit

        # Dados iniciais
        init = initial or {
            "title": "",
            "category": "Geral",
            "due_date": "",
            "priority": 2,  # 1 alta, 2 média, 3 baixa
            "status": "todo",
            "note": ""
        }

        # Layout
        pad = {"padx": 12, "pady": 6}

        ctk.CTkLabel(self, text="Título").grid(
            row=0, column=0, sticky="w", **pad)
        self.title_entry = ctk.CTkEntry(
            self, placeholder_text="Ex.: Preparar apresentação")
        self.title_entry.insert(0, init["title"])
        self.title_entry.grid(row=0, column=1, sticky="ew", **pad)

        ctk.CTkLabel(self, text="Categoria").grid(
            row=1, column=0, sticky="w", **pad)
        self.category_entry = ctk.CTkEntry(
            self, placeholder_text="Ex.: Trabalho")
        self.category_entry.insert(0, init["category"])
        self.category_entry.grid(row=1, column=1, sticky="ew", **pad)

        ctk.CTkLabel(self, text="Vencimento (YYYY-MM-DD)").grid(row=2,
                                                                column=0, sticky="w", **pad)
        self.due_entry = ctk.CTkEntry(self, placeholder_text="2025-11-30")
        self.due_entry.insert(0, init["due_date"])
        self.due_entry.grid(row=2, column=1, sticky="ew", **pad)

        ctk.CTkLabel(self, text="Prioridade").grid(
            row=3, column=0, sticky="w", **pad)
        self.priority_opt = ctk.CTkOptionMenu(
            self, values=["1 (Alta)", "2 (Média)", "3 (Baixa)"])
        self.priority_opt.set(
            f"{init['priority']} ({'Alta' if init['priority'] == 1 else 'Média' if init['priority'] == 2 else 'Baixa'})")
        self.priority_opt.grid(row=3, column=1, sticky="ew", **pad)

        ctk.CTkLabel(self, text="Status").grid(
            row=4, column=0, sticky="w", **pad)
        self.status_opt = ctk.CTkOptionMenu(
            self, values=["todo", "doing", "done"])
        self.status_opt.set(init["status"])
        self.status_opt.grid(row=4, column=1, sticky="ew", **pad)

        ctk.CTkLabel(self, text="Nota").grid(
            row=5, column=0, sticky="nw", **pad)
        self.note_text = ctk.CTkTextbox(self, height=80)
        self.note_text.insert("1.0", init["note"])
        self.note_text.grid(row=5, column=1, sticky="nsew", **pad)

        self.grid_columnconfigure(1, weight=1)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=6, column=0, columnspan=2,
                       sticky="ew", padx=12, pady=12)
        submit_btn = ctk.CTkButton(
            btn_frame, text="Salvar", command=self.submit)
        submit_btn.pack(side="left", padx=6)
        cancel_btn = ctk.CTkButton(
            btn_frame, text="Cancelar", fg_color="#444", command=self.destroy)
        cancel_btn.pack(side="right", padx=6)

        self.title_entry.focus_set()

    def submit(self):
        title = self.title_entry.get().strip()
        if not title:
            ctk.CTkMessagebox(title="Aviso", message="Título não pode ser vazio.") if hasattr(
                ctk, "CTkMessagebox") else None
            return

        category = self.category_entry.get().strip() or "Geral"
        due = self.due_entry.get().strip()
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                ctk.CTkMessagebox(
                    title="Aviso", message="Data inválida. Use YYYY-MM-DD.") if hasattr(ctk, "CTkMessagebox") else None
                return

        prio_val = int(self.priority_opt.get()[0])
        status = self.status_opt.get()
        note = self.note_text.get("1.0", "end").strip()

        data = {
            "title": title,
            "category": category,
            "due_date": due,
            "priority": prio_val,
            "status": status,
            "note": note
        }
        if self.on_submit:
            self.on_submit(data)
        self.destroy()

# =========================
# Cartão de tarefa (UI)
# =========================


class TaskCard(ctk.CTkFrame):
    PRIO_COLORS = {1: "#ff4d4d", 2: "#f1c40f",
                   3: "#2ecc71"}  # vermelho, amarelo, verde

    def __init__(self, master, task, on_edit, on_delete, on_move_left, on_move_right):
        super().__init__(master, corner_radius=10)
        self.task = task
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_move_left = on_move_left
        self.on_move_right = on_move_right

        self.build()

    def build(self):
        self.grid_columnconfigure(0, weight=1)

        # Header com prioridade e categoria
        prio_color = self.PRIO_COLORS.get(self.task["priority"], "#95a5a6")
        header = ctk.CTkFrame(self, fg_color=prio_color, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        h_text = f"Prioridade: {self.task['priority']}  •  {self.task['category']}"
        ctk.CTkLabel(header, text=h_text).pack(padx=8, pady=6)

        # Título
        title = self.task["title"]
        overdue = is_overdue(self.task.get("due_date"),
                             done=(self.task["status"] == "done"))
        title_color = "#ffffff" if not overdue else "#ff7675"
        title_lbl = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(
            size=16, weight="bold"), text_color=title_color)
        title_lbl.grid(row=1, column=0, sticky="w", padx=12, pady=(2, 0))

        # Metadados (vencimento)
        meta = f"Vencimento: {self.task['due_date']}" if self.task.get(
            "due_date") else "Sem vencimento"
        ctk.CTkLabel(self, text=meta, font=ctk.CTkFont(
            size=12), text_color="#bdc3c7").grid(row=2, column=0, sticky="w", padx=12)

        # Nota
        if self.task.get("note"):
            ctk.CTkLabel(self, text=self.task["note"], font=ctk.CTkFont(size=12)).grid(
                row=3, column=0, sticky="w", padx=12, pady=(4, 8))

        # Barra de botões
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.grid(row=4, column=0, sticky="ew", padx=8, pady=(0, 8))
        edit_btn = ctk.CTkButton(
            btn_bar, text="Editar", width=80, command=lambda: self.on_edit(self.task))
        del_btn = ctk.CTkButton(btn_bar, text="Remover", width=80, fg_color="#c0392b", hover_color="#a93226",
                                command=lambda: self.on_delete(self.task))
        left_btn = ctk.CTkButton(
            btn_bar, text="◀", width=40, command=lambda: self.on_move_left(self.task))
        right_btn = ctk.CTkButton(
            btn_bar, text="▶", width=40, command=lambda: self.on_move_right(self.task))

        edit_btn.pack(side="left", padx=4)
        del_btn.pack(side="left", padx=4)
        left_btn.pack(side="right", padx=4)
        right_btn.pack(side="right", padx=4)

# =========================
# Aplicação principal
# =========================


class TaskFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Soft Tech BH — Gerenciador de Tarefas")
        self.geometry("1000x700")
        self.store = TaskStore()
        self.tasks = self.store.load()  # lista de dicts
        self.filter_text = ""

        self.build_ui()
        self.refresh_all()

        # Atalhos
        self.bind_all("<Control-n>", lambda e: self.open_new_task())
        self.bind_all("<Delete>", lambda e: self.delete_selected())
        self.bind_all("<Return>", lambda e: self.edit_selected())

        # Track seleção simples
        self.selected_task_id = None

    # ----- Construção da UI -----
    def build_ui(self):
        # Top bar: busca e botões
        top = ctk.CTkFrame(self, corner_radius=0)
        top.pack(fill="x")

        ctk.CTkLabel(top, text="TaskFlow", font=ctk.CTkFont(
            size=20, weight="bold")).pack(side="left", padx=12, pady=12)

        self.search_entry = ctk.CTkEntry(
            top, placeholder_text="Pesquisar por título/categoria...")
        self.search_entry.pack(side="left", padx=10,
                               pady=12, fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_filter())

        add_btn = ctk.CTkButton(
            top, text="Nova tarefa (Ctrl+N)", command=self.open_new_task)
        add_btn.pack(side="left", padx=8, pady=12)

        save_btn = ctk.CTkButton(top, text="Salvar", command=self.save_tasks)
        save_btn.pack(side="left", padx=8, pady=12)

        theme_btn = ctk.CTkButton(
            top, text="Alternar tema", command=self.toggle_theme)
        theme_btn.pack(side="right", padx=12, pady=12)

        # Colunas Kanban
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=12, pady=12)

        self.column_frames = {}
        for i, (key, title) in enumerate([("todo", "A Fazer"), ("doing", "Em Progresso"), ("done", "Concluídas")]):
            col = ctk.CTkFrame(main, corner_radius=12)
            col.grid(row=0, column=i, sticky="nsew", padx=8)
            main.grid_columnconfigure(i, weight=1)

            header = ctk.CTkLabel(
                col, text=title, font=ctk.CTkFont(size=18, weight="bold"))
            header.pack(pady=(10, 6))

            scroll = ctk.CTkScrollableFrame(
                col, width=300, height=560, corner_radius=10)
            scroll.pack(fill="both", expand=True, padx=8, pady=8)

            # Guarda referência
            self.column_frames[key] = scroll

        # Rodapé
        footer = ctk.CTkFrame(self, corner_radius=0)
        footer.pack(fill="x")
        self.status_lbl = ctk.CTkLabel(footer, text="Pronto", anchor="w")
        self.status_lbl.pack(side="left", padx=12, pady=8)

    # ----- Funções de UI -----
    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("light" if current == "dark" else "dark")

    def open_new_task(self):
        TaskDialog(self, title="Nova tarefa", on_submit=self.add_task)

    def add_task(self, data):
        # Cria ID simples incremental
        next_id = (max([t.get("id", 0) for t in self.tasks], default=0) + 1)
        data["id"] = next_id
        self.tasks.append(data)
        self.save_tasks()
        self.refresh_all()
        self.status("Tarefa adicionada.")

    def edit_task(self, task):
        TaskDialog(self, title="Editar tarefa", initial=task,
                   on_submit=lambda d: self.apply_edit(task, d))

    def apply_edit(self, task, new_data):
        for k in ["title", "category", "due_date", "priority", "status", "note"]:
            task[k] = new_data[k]
        self.save_tasks()
        self.refresh_all()
        self.status("Tarefa atualizada.")

    def delete_task(self, task):
        self.tasks = [t for t in self.tasks if t["id"] != task["id"]]
        self.save_tasks()
        self.refresh_all()
        self.status("Tarefa removida.")

    def move_left(self, task):
        order = ["todo", "doing", "done"]
        i = order.index(task["status"])
        if i > 0:
            task["status"] = order[i - 1]
            self.save_tasks()
            self.refresh_all()
            self.status("Tarefa movida para a esquerda.")

    def move_right(self, task):
        order = ["todo", "doing", "done"]
        i = order.index(task["status"])
        if i < len(order) - 1:
            task["status"] = order[i + 1]
            self.save_tasks()
            self.refresh_all()
            self.status("Tarefa movida para a direita.")

    def status(self, text):
        self.status_lbl.configure(text=text)

    # ----- Filtro de busca -----
    def apply_filter(self):
        self.filter_text = self.search_entry.get().strip().lower()
        self.refresh_all()

    def match_filter(self, task):
        if not self.filter_text:
            return True
        txt = f"{task.get('title', '')} {task.get('category', '')} {task.get('note', '')}".lower()
        return self.filter_text in txt

    # ----- Renderização -----
    def clear_columns(self):
        for key, frame in self.column_frames.items():
            for child in frame.winfo_children():
                child.destroy()

    def refresh_all(self):
        self.clear_columns()
        # Ordena por prioridade e vencimento

        def sort_key(t):
            due = t.get("due_date") or "9999-12-31"
            return (t["status"], t.get("priority", 2), due)
        for t in sorted(self.tasks, key=sort_key):
            if not self.match_filter(t):
                continue
            self.add_card_to_column(t)

    def add_card_to_column(self, task):
        col = self.column_frames[task["status"]]
        card = TaskCard(
            col,
            task=task,
            on_edit=self.edit_task,
            on_delete=self.delete_task,
            on_move_left=self.move_left,
            on_move_right=self.move_right
        )
        card.pack(fill="x", padx=8, pady=6)
        # Seleção simples ao clicar (para atalhos)
        card.bind("<Button-1>", lambda e, t=task: self.select_task(t))

    def select_task(self, task):
        self.selected_task_id = task["id"]
        self.status(f"Selecionada: {task['title']}")

    def find_selected(self):
        if self.selected_task_id is None:
            return None
        return next((t for t in self.tasks if t["id"] == self.selected_task_id), None)

    def delete_selected(self):
        t = self.find_selected()
        if t:
            self.delete_task(t)

    def edit_selected(self):
        t = self.find_selected()
        if t:
            self.edit_task(t)

    # ----- Persistência -----
    def save_tasks(self):
        self.store.save(self.tasks)
        self.status("Tarefas salvas.")


# =========================
# Execução
# =========================
if __name__ == "__main__":
    app = TaskFlowApp()
    app.mainloop()
