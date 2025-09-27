from PyQt6 import QtWidgets, QtCore
from .db import get_conn
from .logic import add_donor, check_inventory, extract_emergency_o_neg, extract_surgery, suggest_alternative
from .auth import verify_password
from .logic import add_donor, check_inventory, extract_emergency_o_neg, extract_surgery
from .reports import export_donations_pdf, export_audit_pdf


class LoginWindow(QtWidgets.QWidget):
    authed = QtCore.pyqtSignal(str, str)  # username, role

    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
        self.setWindowTitle("BECS Login")
        layout = QtWidgets.QFormLayout(self)
        self.user = QtWidgets.QLineEdit()
        self.passw = QtWidgets.QLineEdit()
        self.passw.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        btn = QtWidgets.QPushButton("Login")
        self.msg = QtWidgets.QLabel("")
        layout.addRow("Username:", self.user)
        layout.addRow("Password:", self.passw)
        layout.addRow(btn)
        layout.addRow(self.msg)
        btn.clicked.connect(self.do_login)

    def do_login(self):
        u = self.user.text().strip()
        p = self.passw.text()
        if not u or not p:
            self.msg.setText("Enter username and password.")
            return
        with get_conn(self.db_path) as conn:
            row = conn.execute(
                "SELECT password_hash, role FROM users WHERE username = ?",
                (u,)
            ).fetchone()
            if row and verify_password(p, row["password_hash"]):
                role = (row.get("role") if isinstance(row, dict) else "user") or "user"
                self.msg.setText("OK")
                self.authed.emit(u, role)
            else:
                self.msg.setText("Wrong username/password.")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, db_path: str, username: str, role: str):
        super().__init__()
        self.db_path = db_path
        self.username = username
        self.role = (role or "user").lower()
        self.setWindowTitle(f"BECS — {username} ({self.role})")

        self.tabs = QtWidgets.QTabWidget()
        if self.role != "student":
            self.tabs.addTab(self._donation_tab(), "Donations")
        self.tabs.addTab(self._inventory_tab(), "Inventory")
        if self.role != "student":
            self.tabs.addTab(self._extract_tab(), "Extraction")
        self.tabs.addTab(self._audit_tab(), "Audit Log")
        self.setCentralWidget(self.tabs)
        self.resize(980, 640)

    def _donation_tab(self):
        w = QtWidgets.QWidget()
        f = QtWidgets.QFormLayout(w)
        self.fn = QtWidgets.QLineEdit()
        self.ln = QtWidgets.QLineEdit()
        self.pid = QtWidgets.QLineEdit()
        self.bt = QtWidgets.QComboBox()
        self.bt.addItems(["A+","A-","B+","B-","AB+","AB-","O+","O-"])
        btn = QtWidgets.QPushButton("Add Donation")
        export_btn = QtWidgets.QPushButton("Export Donations (PDF)")
        self.dmsg = QtWidgets.QLabel("")
        f.addRow("First name:", self.fn)
        f.addRow("Last name:", self.ln)
        f.addRow("ID/Passport:", self.pid)
        f.addRow("Blood type:", self.bt)
        f.addRow(btn)
        f.addRow(export_btn)
        f.addRow(self.dmsg)
        btn.clicked.connect(self._add_donation)
        export_btn.clicked.connect(self._export_donations)
        return w

    def _add_donation(self):
        fn, ln, pid, bt = (
            self.fn.text().strip(),
            self.ln.text().strip(),
            self.pid.text().strip(),
            self.bt.currentText(),
        )
        if not (fn and ln and pid):
            self.dmsg.setText("All fields are required.")
            return
        with get_conn(self.db_path) as conn:
            did = add_donor(conn, fn, ln, pid, bt, actor=self.username)
            self.dmsg.setText(f"Donation #{did} saved.")
            self.fn.clear(); self.ln.clear(); self.pid.clear()

    def _export_donations(self):
        include_pii = (self.role != "student")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Donations PDF", "donations.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        with get_conn(self.db_path) as conn:
            if include_pii:
                rows = list(conn.execute(
                    "SELECT id, first_name, last_name, pid, blood_type, donated_at "
                    "FROM donations ORDER BY id ASC"
                ))
            else:
                rows = list(conn.execute(
                    "SELECT id, blood_type, donated_at FROM donations ORDER BY id ASC"
                ))
                # normalize keys for exporter
                for r in rows:
                    r.setdefault("first_name",""); r.setdefault("last_name",""); r.setdefault("pid","")
        try:
            export_donations_pdf(rows, path, include_pii=include_pii)
            self.dmsg.setText(f"Donations exported → {path}")
        except Exception as e:
            self.dmsg.setText(f"Export failed: {e}")

    def _inventory_tab(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        row = QtWidgets.QHBoxLayout()
        self.recipient = QtWidgets.QComboBox()
        self.recipient.addItems(["A+","A-","B+","B-","AB+","AB-","O+","O-"])
        btn = QtWidgets.QPushButton("Check")
        row.addWidget(QtWidgets.QLabel("Recipient type:"))
        row.addWidget(self.recipient); row.addWidget(btn)
        self.inventory_list = QtWidgets.QListWidget()
        v.addLayout(row); v.addWidget(self.inventory_list)
        btn.clicked.connect(self._do_check)
        return w

    def _do_check(self):
        self.inventory_list.clear()
        rbt = self.recipient.currentText()
        with get_conn(self.db_path) as conn:
            rows = check_inventory(conn, rbt)
        for bt, count in rows:
            self.inventory_list.addItem(f"{bt}: {count} units")

    def _extract_tab(self):
        w = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(w)
        # Emergency O-
        grid.addWidget(QtWidgets.QLabel("Emergency (O-) units:"), 0, 0)
        self.em_units = QtWidgets.QSpinBox(); self.em_units.setRange(1, 999)
        grid.addWidget(self.em_units, 0, 1)
        btn1 = QtWidgets.QPushButton("Extract O-")
        grid.addWidget(btn1, 0, 2)
        self.em_msg = QtWidgets.QLabel("")
        grid.addWidget(self.em_msg, 1, 0, 1, 3)

        # Surgery
        grid.addWidget(QtWidgets.QLabel("Surgery for recipient type:"), 2, 0)
        self.surg_rec = QtWidgets.QComboBox(); self.surg_rec.addItems(["A+","A-","B+","B-","AB+","AB-","O+","O-"])
        grid.addWidget(self.surg_rec, 2, 1)
        grid.addWidget(QtWidgets.QLabel("Units:"), 3, 0)
        self.surg_units = QtWidgets.QSpinBox(); self.surg_units.setRange(1, 999)
        grid.addWidget(self.surg_units, 3, 1)
        btn2 = QtWidgets.QPushButton("Extract for Surgery")
        grid.addWidget(btn2, 3, 2)
        self.surg_msg = QtWidgets.QLabel("")
        grid.addWidget(self.surg_msg, 4, 0, 1, 3)

        btn1.clicked.connect(self._do_emergency)
        btn2.clicked.connect(self._do_surgery)
        return w

    def _do_emergency(self):
        units = int(self.em_units.value())
        with get_conn(self.db_path) as conn:
            got = extract_emergency_o_neg(conn, units, actor=self.username)
        self.em_msg.setText(f"Extracted {got} O- units.")

    def _do_surgery(self):
        rbt = self.surg_rec.currentText()
        units = int(self.surg_units.value())       

        with get_conn(self.db_path) as conn:
                 # rarity-aware alternative suggestion
             alt = None
        try:
            from .logic import suggest_alternative
            alt = suggest_alternative(conn, rbt)
        except Exception:
            pass

        if alt and self.role != "student":
            QtWidgets.QMessageBox.information(
                self, "Suggestion",
                f"No stock for {rbt}. Suggested compatible alternative (rarity-aware): {alt}"
            )

        result = extract_surgery(conn, rbt, units, actor=self.username)

        if result:
             parts = [f"{bt}:{n}" for bt, n in result.items()]
             self.surg_msg.setText("Extracted → " + ", ".join(parts))
        else:
            if alt:
                self.surg_msg.setText(f"No units extracted (shortfall logged). Suggested alt: {alt}")
            else:
                self.surg_msg.setText("No units extracted (shortfall logged).")

    def _audit_tab(self):
        w = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(w)
        self.audit_table = QtWidgets.QTableWidget(0, 6)
        self.audit_table.setHorizontalHeaderLabels(["id","at","actor","action","entity","entity_id"])
        self.audit_table.horizontalHeader().setStretchLastSection(True)

        # Buttons row
        btn_row = QtWidgets.QHBoxLayout()
        btn_refresh = QtWidgets.QPushButton("Refresh Audit Log")
        btn_export = QtWidgets.QPushButton("Export Audit (PDF)")
        btn_row.addWidget(btn_refresh)
        btn_row.addWidget(btn_export)
        btn_row.addStretch(1)

        v.addLayout(btn_row)
        v.addWidget(self.audit_table)

        btn_refresh.clicked.connect(self._refresh_audit)
        btn_export.clicked.connect(self._export_audit)
        return w

    def _refresh_audit(self):
        with get_conn(self.db_path) as conn:
            rows = list(conn.execute(
                "SELECT id, at, actor, action, entity, entity_id "
                "FROM audit_log ORDER BY id DESC LIMIT 500"
            ))
        self.audit_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, key in enumerate(["id","at","actor","action","entity","entity_id"]):
                val = row[key] if row[key] is not None else ""
                item = QtWidgets.QTableWidgetItem(str(val))
                self.audit_table.setItem(r, c, item)

    def _export_audit(self):
        redact = (self.role == "student")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Audit PDF", "audit_log.pdf", "PDF Files (*.pdf)"
        )
        if not path:
            return
        with get_conn(self.db_path) as conn:
            rows = list(conn.execute(
                "SELECT id, at, actor, action, entity, entity_id, details_json "
                "FROM audit_log ORDER BY id ASC"
            ))
        try:
            export_audit_pdf(rows, path, redact_details=redact)
            QtWidgets.QMessageBox.information(self, "Export", f"Audit exported → {path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export failed", str(e))
