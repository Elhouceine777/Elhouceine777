import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from . import db


def refresh_categories(option_menu: ttk.Combobox):
    cats = db.get_categories()
    option_menu['values'] = [name for _, name in cats]
    if cats:
        option_menu.current(0)


class FinanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestion Financière Personnelle")
        self.geometry("800x600")
        db.init_db()
        self._create_widgets()

    # ---------------- GUI Setup -----------------
    def _create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_home = ttk.Frame(notebook)
        self.tab_add = ttk.Frame(notebook)
        self.tab_history = ttk.Frame(notebook)
        self.tab_stats = ttk.Frame(notebook)

        notebook.add(self.tab_home, text="Accueil")
        notebook.add(self.tab_add, text="Ajouter")
        notebook.add(self.tab_history, text="Historique")
        notebook.add(self.tab_stats, text="Statistiques")

        self._create_home_tab()
        self._create_add_tab()
        self._create_history_tab()
        self._create_stats_tab()

    # --------------- Home Tab -------------------
    def _create_home_tab(self):
        frame = self.tab_home
        self.summary_var = tk.StringVar()
        self.summary_label = ttk.Label(frame, textvariable=self.summary_var, font=("Arial", 14))
        self.summary_label.pack(pady=20)

        filter_frame = ttk.Frame(frame)
        filter_frame.pack(pady=10)
        ttk.Label(filter_frame, text="Mois:").grid(row=0, column=0)
        self.month_var_home = tk.StringVar()
        month_combo = ttk.Combobox(filter_frame, textvariable=self.month_var_home, width=5, values=[f"{i:02d}" for i in range(1,13)])
        month_combo.grid(row=0, column=1)
        ttk.Label(filter_frame, text="Année:").grid(row=0, column=2)
        self.year_var_home = tk.StringVar()
        year_combo = ttk.Combobox(filter_frame, textvariable=self.year_var_home, width=7, values=[str(y) for y in range(2020, 2051)])
        year_combo.grid(row=0, column=3)
        ttk.Button(filter_frame, text="Actualiser", command=self.update_summary).grid(row=0, column=4, padx=5)

        self.update_summary()

    def update_summary(self):
        month = self.month_var_home.get() or None
        year = self.year_var_home.get() or None
        income, expense, balance = db.get_summary(month=int(month) if month else None, year=int(year) if year else None)
        self.summary_var.set(f"Revenus: {income:.2f}    Dépenses: {expense:.2f}    Solde: {balance:.2f}")

    # --------------- Add Tab --------------------
    def _create_add_tab(self):
        frame = self.tab_add
        form = ttk.Frame(frame)
        form.pack(pady=20)

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W)
        self.date_entry = ttk.Entry(form)
        self.date_entry.grid(row=0, column=1)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(form, text="Type:").grid(row=1, column=0, sticky=tk.W)
        self.type_var = tk.StringVar(value="expense")
        ttk.Radiobutton(form, text="Dépense", variable=self.type_var, value="expense").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(form, text="Revenu", variable=self.type_var, value="income").grid(row=1, column=2, sticky=tk.W)

        ttk.Label(form, text="Catégorie:").grid(row=2, column=0, sticky=tk.W)
        self.category_combo = ttk.Combobox(form, state="readonly")
        self.category_combo.grid(row=2, column=1)

        ttk.Label(form, text="Montant:").grid(row=3, column=0, sticky=tk.W)
        self.amount_entry = ttk.Entry(form)
        self.amount_entry.grid(row=3, column=1)

        ttk.Label(form, text="Description:").grid(row=4, column=0, sticky=tk.W)
        self.desc_entry = ttk.Entry(form, width=40)
        self.desc_entry.grid(row=4, column=1, columnspan=2)

        ttk.Button(form, text="Ajouter", command=self.add_transaction).grid(row=5, column=0, columnspan=2, pady=10)

        cat_frame = ttk.LabelFrame(frame, text="Nouvelle catégorie")
        cat_frame.pack(pady=10, fill=tk.X, padx=20)
        ttk.Label(cat_frame, text="Nom:").grid(row=0, column=0)
        self.new_cat_entry = ttk.Entry(cat_frame)
        self.new_cat_entry.grid(row=0, column=1)
        ttk.Button(cat_frame, text="Ajouter", command=self.add_category).grid(row=0, column=2)

        refresh_categories(self.category_combo)

    def add_transaction(self):
        try:
            date = self.date_entry.get()
            datetime.strptime(date, "%Y-%m-%d")
            amount = float(self.amount_entry.get())
            cats = db.get_categories()
            category_map = {name: cid for cid, name in cats}
            category_id = category_map.get(self.category_combo.get())
            if category_id is None:
                messagebox.showerror("Erreur", "Veuillez sélectionner une catégorie")
                return
            db.add_transaction(date, category_id, self.type_var.get(), amount, self.desc_entry.get())
            messagebox.showinfo("Succès", "Transaction ajoutée")
            self.amount_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
            self.update_history()
            self.update_summary()
        except ValueError:
            messagebox.showerror("Erreur", "Montant ou date invalide")

    def add_category(self):
        name = self.new_cat_entry.get().strip()
        if name:
            db.add_category(name)
            refresh_categories(self.category_combo)
            self.new_cat_entry.delete(0, tk.END)

    # --------------- History Tab ----------------
    def _create_history_tab(self):
        frame = self.tab_history
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(pady=10)

        ttk.Label(filter_frame, text="Mois:").grid(row=0, column=0)
        self.month_var_hist = tk.StringVar()
        ttk.Combobox(filter_frame, textvariable=self.month_var_hist, width=5, values=[f"{i:02d}" for i in range(1,13)]).grid(row=0, column=1)
        ttk.Label(filter_frame, text="Année:").grid(row=0, column=2)
        self.year_var_hist = tk.StringVar()
        ttk.Combobox(filter_frame, textvariable=self.year_var_hist, width=7, values=[str(y) for y in range(2020, 2051)]).grid(row=0, column=3)
        ttk.Button(filter_frame, text="Filtrer", command=self.update_history).grid(row=0, column=4, padx=5)

        columns = ("id", "date", "cat", "type", "amount", "desc")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Exporter CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)

        self.update_history()

    def update_history(self):
        month = self.month_var_hist.get() or None
        year = self.year_var_hist.get() or None
        rows = db.get_transactions(month=int(month) if month else None, year=int(year) if year else None)
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            self.tree.insert("", tk.END, values=r)

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            month = self.month_var_hist.get() or None
            year = self.year_var_hist.get() or None
            db.export_csv(path, month=int(month) if month else None, year=int(year) if year else None)
            messagebox.showinfo("Export", f"Données exportées vers {path}")

    # --------------- Stats Tab ------------------
    def _create_stats_tab(self):
        frame = self.tab_stats
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(pady=5)
        ttk.Label(filter_frame, text="Mois:").grid(row=0, column=0)
        self.month_var_stats = tk.StringVar()
        ttk.Combobox(filter_frame, textvariable=self.month_var_stats, width=5, values=[f"{i:02d}" for i in range(1,13)]).grid(row=0, column=1)
        ttk.Label(filter_frame, text="Année:").grid(row=0, column=2)
        self.year_var_stats = tk.StringVar()
        ttk.Combobox(filter_frame, textvariable=self.year_var_stats, width=7, values=[str(y) for y in range(2020,2051)]).grid(row=0, column=3)
        ttk.Button(filter_frame, text="Afficher", command=self.show_stats).grid(row=0, column=4, padx=5)

        self.figure = plt.Figure(figsize=(5,4))
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def show_stats(self):
        month = self.month_var_stats.get() or None
        year = self.year_var_stats.get() or None
        rows = db.get_transactions(month=int(month) if month else None, year=int(year) if year else None)
        # summarize expenses by category
        summary = {}
        for _, date, cat, ttype, amount, desc in rows:
            if ttype == 'expense':
                summary[cat] = summary.get(cat, 0) + amount
        self.figure.clf()
        ax = self.figure.add_subplot(111)
        if summary:
            labels = list(summary.keys())
            values = list(summary.values())
            ax.pie(values, labels=labels, autopct='%1.1f%%')
        else:
            ax.text(0.5, 0.5, 'Aucune donnée', ha='center')
        self.canvas.draw()


if __name__ == '__main__':
    app = FinanceApp()
    app.mainloop()
