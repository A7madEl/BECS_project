# file: app.py
import tkinter as tk
from tkinter import messagebox, ttk

from constants import BLOOD_TYPES, POPULATION_PERCENT
from db import DB
from service import Service
from style import apply_theme

class App(ttk.Frame):
    def __init__(self, master, service: Service, theme_mode: str = "dark"):
        super().__init__(master)
        self.service = service
        self.master.title("BECS — מערכת בנק דם (Tkinter/ttk)")
        self.master.geometry("1040x700")
        self.master.minsize(980, 640)

        # עיצוב
        self.palette = apply_theme(self.master, mode=theme_mode)

        self._build_ui()

    def _build_ui(self):
        root = ttk.Frame(self.master, padding=12)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="מערכת BECS - בנק הדם הישראלי", style="Title.TLabel").pack(pady=(0, 10))

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True)

        self.tab_intake = ttk.Frame(nb, padding=10)
        self.tab_routine = ttk.Frame(nb, padding=10)
        self.tab_emergency = ttk.Frame(nb, padding=10)
        self.tab_stock = ttk.Frame(nb, padding=10)

        nb.add(self.tab_intake, text="קליטת תרומות")
        nb.add(self.tab_routine, text="ניפוק שגרה")
        nb.add(self.tab_emergency, text="ניפוק חירום (אר\"ן)")
        nb.add(self.tab_stock, text="מצב מלאי")

        self._build_intake_tab()
        self._build_routine_tab()
        self._build_emergency_tab()
        self._build_stock_tab()

    # ---------- Intake ----------
    def _build_intake_tab(self):
        form = ttk.Labelframe(self.tab_intake, text="טופס קליטת תרומה", style="Card.TLabelframe")
        form.pack(side="left", fill="both", expand=True)

        self.e_id = ttk.Entry(form, width=30)
        self.e_name = ttk.Entry(form, width=30)
        self.cb_type = ttk.Combobox(form, values=BLOOD_TYPES, state="readonly", width=27)
        self.e_date = ttk.Entry(form, width=30)

        import datetime as _dt
        self.e_date.insert(0, _dt.datetime.now().strftime("%d/%m/%Y"))

        ttk.Label(form, text='ת"ז תורם:').grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.e_id.grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(form, text="שם מלא:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.e_name.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(form, text="סוג דם:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.cb_type.grid(row=2, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(form, text="תאריך תרומה (dd/mm/yyyy):").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.e_date.grid(row=3, column=1, sticky="w", padx=6, pady=6)

        ttk.Button(form, text="שמור תרומה", style="Accent.TButton", command=self._on_intake)\
            .grid(row=4, column=1, sticky="w", padx=6, pady=(12, 0))

        help_box = ttk.Labelframe(self.tab_intake, text="עזרה מהירה", style="Card.TLabelframe")
        help_box.pack(side="left", fill="both", expand=True, padx=(10, 0))
        ttk.Label(help_box, text="מלא ושמור. שמירה מעדכנת את המלאי מיד.\nולידציה: ת\"ז=9 ספרות, סוג דם מהרשימה, תאריך תקין.")\
            .pack(anchor="w", padx=8, pady=8)

    def _on_intake(self):
        donor_id = self.e_id.get().strip()
        name = self.e_name.get().strip()
        btype = self.cb_type.get().strip()
        date_str = self.e_date.get().strip()
        if not all([donor_id, name, btype, date_str]):
            messagebox.showerror("שגיאה", "יש למלא את כל השדות")
            return
        try:
            self.service.intake(donor_id, name, btype, date_str)
            messagebox.showinfo("הצלחה", f"התרומה נקלטה: {btype}")
            self._refresh_stock()
            self.e_name.delete(0, tk.END); self.cb_type.set("")
        except Exception as e:
            messagebox.showerror("שגיאה", str(e))

    # ---------- Routine ----------
    def _build_routine_tab(self):
        req = ttk.Labelframe(self.tab_routine, text="בקשת ניפוק (שגרה)", style="Card.TLabelframe")
        req.pack(fill="x")

        self.cb_req_type = ttk.Combobox(req, values=BLOOD_TYPES, state="readonly", width=27)
        self.e_qty = ttk.Entry(req, width=10)

        ttk.Label(req, text="סוג דם נתרם (מקבל):").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.cb_req_type.grid(row=0, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(req, text="כמות מנות:").grid(row=0, column=2, sticky="e", padx=6, pady=6)
        self.e_qty.grid(row=0, column=3, sticky="w", padx=6, pady=6)

        ttk.Button(req, text="חשב המלצה", style="Accent.TButton", command=self._on_calc_plan)\
            .grid(row=0, column=4, sticky="w", padx=10)

        # תוצאות/המלצה
        res = ttk.Labelframe(self.tab_routine, text="המלצה לניפוק (לא מבוצע עד אישור)", style="Card.TLabelframe")
        res.pack(fill="both", expand=True, pady=(10, 0))

        top = ttk.Frame(res); top.pack(fill="x")
        self.lbl_status = ttk.Label(top, text="", style="H2.TLabel")
        self.lbl_status.pack(side="left")
        self.btn_apply = ttk.Button(top, text="נפק לפי ההמלצה", command=self._on_apply_plan, state="disabled")
        self.btn_apply.pack(side="right", padx=6)

        cols = ("donor", "available", "take", "note")
        self.tree_plan = ttk.Treeview(res, columns=cols, show="headings", height=14)
        for c, t in zip(cols, ["סוג תרומה", "קיים במלאי", "מומלץ לקחת", "הערה"]):
            self.tree_plan.heading(c, text=t)
            self.tree_plan.column(c, width=160, anchor="center")
        self.tree_plan.pack(fill="both", expand=True, pady=8)

        # צבעי מצב בטבלה
        self.tree_plan.tag_configure("primary", foreground=self.palette["ok"])     # התאמה מלאה
        self.tree_plan.tag_configure("alt", foreground="#0d47a1")                  # חלופה
        self.tree_plan.tag_configure("empty", foreground=self.palette["error"])    # אין מלאי

        info = ttk.Label(res, text="המערכת מדרגת חלופות לפי: התאמת סוג דם → זמינות גבוהה → פחות נדיר קודם.\n"
                                   "שימו לב: אין ניפוק אוטומטי — חייב אישור בלחיצה.",
                          wraplength=900)
        info.pack(anchor="w", padx=4)

        # state
        self._last_plan = None
        self._last_can_fulfill = False
        self._last_missing = 0

    def _on_calc_plan(self):
        btype = self.cb_req_type.get().strip()
        try:
            qty = int(self.e_qty.get().strip())
        except Exception:
            messagebox.showerror("שגיאה", "כמות מנות חייבת להיות מספר חיובי")
            return
        if not btype or qty <= 0:
            messagebox.showerror("שגיאה", "בחר סוג דם והכנס כמות חיובית")
            return

        plan, can_fulfill, missing = self.service.plan_routine_recommendation(btype, qty)
        self._last_plan = plan
        self._last_can_fulfill = can_fulfill
        self._last_missing = missing
        self._render_plan(btype, qty, plan, can_fulfill, missing)

    def _render_plan(self, recipient, qty, plan, can_fulfill, missing):
        for i in self.tree_plan.get_children():
            self.tree_plan.delete(i)

        if can_fulfill:
            self.lbl_status.config(text=f"ניתן לספק את הבקשה ({qty}) באמצעות התכנית המומלצת.", foreground=self.palette["ok"])
            self.btn_apply.config(text="נפק לפי ההמלצה", state="normal")
        else:
            self.lbl_status.config(text=f"חסרות {missing} מנות. ניתן לנפק חלקית לפי ההמלצה.", foreground=self.palette["warn"])
            self.btn_apply.config(text="נפק חלקית לפי ההמלצה", state="normal")

        for row in plan:
            donor = row["donor"]; available = row["available"]; take = row["take"]
            note = "התאמה מלאה" if donor == recipient else ("חלופה תואמת" if available > 0 else "אין מלאי")
            tag = "primary" if donor == recipient else ("alt" if available > 0 else "empty")
            self.tree_plan.insert("", "end", values=(donor, available, take, note), tags=(tag,))

    def _on_apply_plan(self):
        if not self._last_plan:
            return
        total = self.service.apply_plan(self._last_plan, mode="routine")
        if total == 0:
            messagebox.showwarning("אין מה לנפק", "לא קיימות מנות זמינות בהתאם לתכנית.")
        else:
            if self._last_can_fulfill:
                messagebox.showinfo("הושלם", f"נופקו {total} מנות לפי ההמלצה.")
            else:
                messagebox.showinfo("הושלם חלקית", f"נופקו {total} מנות (חסרות {self._last_missing}).")
        self._refresh_stock()
        self.btn_apply.config(state="disabled")
        self._last_plan = None

    # ---------- Emergency ----------
    def _build_emergency_tab(self):
        box = ttk.Labelframe(self.tab_emergency, text="ניפוק אר\"ן (O- בלבד)", style="Card.TLabelframe")
        box.pack(fill="x")

        self.lbl_on = ttk.Label(box, text="")
        self.lbl_on.grid(row=0, column=0, sticky="w", padx=8, pady=8)

        ttk.Button(box, text="נפק את כל מלאי O-", style="Danger.TButton", command=self._on_emergency)\
            .grid(row=0, column=1, sticky="e", padx=8, pady=8)

        info = ttk.Labelframe(self.tab_emergency, text="למה O-?", style="Card.TLabelframe")
        info.pack(fill="x", pady=(10, 0))
        ttk.Label(info, text="O- הוא התורם האוניברסלי — מתאים לכל סוגי הדם. במצב אר\"ן אין זמן לבדיקות תאימות, ולכן מנפיקים O- בלבד.",
                  wraplength=900).pack(anchor="w", padx=8, pady=8)

        self._update_on_label()

    def _update_on_label(self):
        count = service.db.count_available('O-')
        self.lbl_on.config(text=f"מלאי O- זמין: {count} מנות")

    def _on_emergency(self):
        count = service.db.count_available('O-')
        if count <= 0:
            messagebox.showerror("אין מלאי", "אין מלאי O- זמין לניפוק חירום")
            self._update_on_label()
            return
        if messagebox.askyesno("אישור חירום", f"האם לנפק את כל {count} מנות ה-O-?"):
            taken = self.service.emergency_issue_all_on()
            messagebox.showinfo("בוצע", f"נופקו {taken} מנות O- לחירום")
            self._refresh_stock()
            self._update_on_label()

    # ---------- Stock ----------
    def _build_stock_tab(self):
        frame = ttk.Frame(self.tab_stock)
        frame.pack(fill="both", expand=True)

        top = ttk.Frame(frame); top.pack(fill="x")
        ttk.Label(top, text="מלאי נוכחי", style="H2.TLabel").pack(side="left")
        ttk.Button(top, text="רענן", command=self._refresh_stock).pack(side="right")

        cols = ("type", "count", "pop")
        self.tree_stock = ttk.Treeview(frame, columns=cols, show="headings", height=16)
        self.tree_stock.heading("type", text="סוג דם")
        self.tree_stock.heading("count", text="כמות זמינה")
        self.tree_stock.heading("pop", text="אחוז באוכלוסייה")
        self.tree_stock.column("type", width=120, anchor="center")
        self.tree_stock.column("count", width=140, anchor="center")
        self.tree_stock.column("pop", width=160, anchor="center")

        # תיוג לפי מצב מלאי
        self.tree_stock.tag_configure("empty", foreground="#b71c1c")
        self.tree_stock.tag_configure("low", foreground="#e67e22")
        self.tree_stock.tag_configure("ok", foreground="#2e7d32")

        self.tree_stock.pack(fill="both", expand=True, pady=8)
        self._refresh_stock()

    def _refresh_stock(self):
        for i in self.tree_stock.get_children():
            self.tree_stock.delete(i)
        for bt in BLOOD_TYPES:
            cnt = service.db.count_available(bt)
            pop = POPULATION_PERCENT[bt]
            tag = "ok" if cnt >= 10 else ("low" if cnt > 0 else "empty")
            self.tree_stock.insert("", "end", values=(bt, cnt, f"{pop}%"), tags=(tag,))

if __name__ == "__main__":
    db = DB()
    service = Service(db)

    root = tk.Tk()
    # High-DPI (Windows) – לא חובה
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = App(root, service, theme_mode="dark")  # אפשר "light"
    root.protocol("WM_DELETE_WINDOW", lambda: (db.close(), root.destroy()))
    root.mainloop()
