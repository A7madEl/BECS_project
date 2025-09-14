# file: service.py
import re, json
from typing import Tuple, List, Dict
from db import DB
from constants import BLOOD_TYPES, COMPATIBILITY, POPULATION_PERCENT, parse_ddmmyyyy_or_iso, iso_now

class Service:
    def __init__(self, db: DB, actor: str = "operator"):
        self.db = db
        self.actor = actor  # אפשר בעתיד לחבר למסך לוגין

    @staticmethod
    def valid_id9(s: str) -> bool:
        return bool(re.fullmatch(r"\d{9}", (s or "").strip()))

    def audit(self, action: str, entity: str, entity_id: str | None, details: dict):
        self.db.add_audit(
            ts=iso_now(),
            actor=self.actor,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details_json=json.dumps(details, ensure_ascii=False)
        )

    # ----- Intake -----
    def intake(self, donor_id: str, donor_name: str, blood_type: str, date_str: str):
        if blood_type not in BLOOD_TYPES:
            raise ValueError("סוג דם לא חוקי")
        if not self.valid_id9(donor_id):
            raise ValueError('ת"ז חייבת להיות 9 ספרות')
        donation_iso = parse_ddmmyyyy_or_iso(date_str)
        new_id = self.db.add_donation(donor_id.strip(), donor_name.strip(), blood_type, donation_iso)
        # audit
        self.audit("INTAKE", "donations", str(new_id), {
            "donor_id": donor_id, "donor_name": donor_name,
            "blood_type": blood_type, "donation_date": donation_iso
        })

    # ----- Routine recommendation (no execution) -----
    def plan_routine_recommendation(self, recipient_type: str, quantity: int
                                    ) -> Tuple[List[Dict], bool, int]:
        need = int(quantity)
        plan = []

        # 1) requested type
        avail_req = self.db.count_available(recipient_type)
        take_req = min(avail_req, need)
        plan.append({"donor": recipient_type, "available": avail_req, "take": take_req})
        need -= take_req

        # 2) alternatives
        if need > 0:
            compatible = [d for d in BLOOD_TYPES if recipient_type in COMPATIBILITY[d] and d != recipient_type]
            donors_sorted = sorted(
                compatible,
                key=lambda bt: (self.db.count_available(bt), POPULATION_PERCENT.get(bt, 0)),
                reverse=True
            )
            for donor_bt in donors_sorted:
                if need <= 0:
                    break
                avail = self.db.count_available(donor_bt)
                take = min(avail, need)
                plan.append({"donor": donor_bt, "available": avail, "take": take})
                need -= take

        can_fulfill = (need == 0)
        missing = max(0, need)

        # audit (אופציונלי אך מומלץ)
        self.audit("PLAN_ROUTINE", "dispensations", None, {
            "recipient": recipient_type, "requested_qty": quantity,
            "can_fulfill": can_fulfill, "missing": missing, "plan": plan
        })

        return plan, can_fulfill, missing

    # ----- Apply plan (execute) -----
    def apply_plan(self, plan: List[Dict], mode: str = "routine") -> int:
        total_issued = 0
        for row in plan:
            donor = row["donor"]
            take = int(row.get("take", 0))
            if take <= 0:
                continue
            ids = self.db.available_ids(donor, take)
            taken = self.db.mark_dispensed_ids(ids, mode=mode)
            if taken > 0:
                self.db.log_dispensation(donor, taken, mode=mode)
                total_issued += taken
                # audit per donor-type taken
                self.audit("ISSUE_ROUTINE" if mode == "routine" else "ISSUE_EMERGENCY",
                           "dispensations", None, {"donor_type": donor, "taken": taken, "mode": mode})
        return total_issued

    # ----- Emergency O- all -----
    def emergency_issue_all_on(self) -> int:
        count = self.db.count_available('O-')
        if count <= 0:
            return 0
        ids = self.db.available_ids('O-', count)
        taken = self.db.mark_dispensed_ids(ids, mode="emergency")
        if taken > 0:
            self.db.log_dispensation('O-', taken, mode="emergency")
            # audit
            self.audit("ISSUE_EMERGENCY", "dispensations", None, {"donor_type": "O-", "taken": taken})
        return taken
