from typing import Iterable, Dict, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import json

def _sanitize_details(details_json: Optional[str]) -> str:
    if not details_json:
        return ""
    try:
        data = json.loads(details_json)
    except Exception:
        return ""
    for k in ["first_name", "last_name", "pid"]:
        if k in data:
            data[k] = "REDACTED"
    return json.dumps(data, ensure_ascii=False)

def export_donations_pdf(rows: Iterable[Dict[str, Any]], pdf_path: str, include_pii: bool = True):
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm,
                            leftMargin=1.3*cm, rightMargin=1.3*cm)
    styles = getSampleStyleSheet()
    story = [Paragraph("BECS — Donations Report", styles["Title"]), Spacer(1, 0.3*cm)]

    headers = (["ID","First Name","Last Name","ID/Passport","Blood Type","Donated At"]
               if include_pii else ["ID","Donor","Blood Type","Donated At"])
    data = [headers]
    for r in rows:
        if include_pii:
            data.append([r.get("id",""), r.get("first_name",""), r.get("last_name",""),
                         r.get("pid",""), r.get("blood_type",""), r.get("donated_at","")])
        else:
            data.append([r.get("id",""), "Anon", r.get("blood_type",""), r.get("donated_at","")])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey), ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),9),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE")
    ]))
    story.append(table)
    doc.build(story)

def export_audit_pdf(rows: Iterable[Dict[str, Any]], pdf_path: str, redact_details: bool = False):
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm,
                            leftMargin=1.0*cm, rightMargin=1.0*cm)
    styles = getSampleStyleSheet()
    story = [Paragraph("BECS — Audit Log", styles["Title"]), Spacer(1, 0.3*cm)]

    headers = ["ID","Timestamp","Actor","Action","Entity","Entity ID","Details"]
    data = [headers]
    for r in rows:
        details = r.get("details_json")
        if redact_details:
            details = _sanitize_details(details)
        else:
            try:
                details = json.dumps(json.loads(details) if details else {}, ensure_ascii=False)
            except Exception:
                details = ""
        data.append([r.get("id",""), r.get("at",""), r.get("actor",""), r.get("action",""),
                     r.get("entity",""), r.get("entity_id",""), details])

    table = Table(data, repeatRows=1,
                  colWidths=[1.2*cm,3.3*cm,2.0*cm,2.5*cm,2.0*cm,1.6*cm,7.0*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.lightgrey), ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("FONTSIZE",(0,0),(-1,-1),8),
        ("VALIGN",(0,0),(-1,-1),"TOP")
    ]))
    story.append(table)
    doc.build(story)
