"""Year-end rollover — carry PY figures and confirmed mappings to next FY."""

from __future__ import annotations
from pathlib import Path
import shutil
from datetime import datetime


def rollover_project(src_path: Path, dest_path: Path,
                     new_fy: str, settings_db) -> Path:
    """
    Clone src project to dest, advance FY, carry closing → opening balances,
    and transfer confirmed ledger mappings.
    """
    if dest_path.exists():
        raise FileExistsError(f"Destination project already exists: {dest_path}")

    shutil.copy2(src_path, dest_path)

    from ..data.project_db import ProjectDB
    db = ProjectDB(dest_path)
    db.connect()

    # Update FY
    db.set_meta("financial_year", new_fy)
    db.set_meta("created_at", datetime.now().isoformat())
    db.set_meta("is_locked", "0")
    db.set_meta("is_finalized", "0")
    db.set_meta("rolled_from", str(src_path))

    # Shift CY figures → PY, zero out CY
    db._conn.execute("""
        UPDATE raw_tb SET
          py_net  = cy_net,
          cy_debit = 0, cy_credit = 0, cy_net = 0
    """)

    # Carry PPE closing → opening
    db._conn.execute("""
        UPDATE ppe SET
          gross_op  = gross_op + additions - disposals,
          additions = 0, disposals = 0,
          dep_op    = dep_op + dep_charge - dep_disposal,
          dep_charge = 0, dep_disposal = 0,
          nbv_py    = gross_op + additions - disposals - dep_op - dep_charge + dep_disposal,
          it_wdv_op = it_wdv_cl,
          it_dep    = 0, it_wdv_cl = 0
    """)

    # Reset overrides and note_data
    db._conn.execute("DELETE FROM fs_overrides")
    db._conn.execute("DELETE FROM note_data")
    db._conn.execute("DELETE FROM adjustments")
    db._conn.execute("DELETE FROM audit_log")

    # Re-confirm mappings (wtb already has them; just reset confidence source)
    db._conn.execute("""
        UPDATE wtb SET
          confidence = 1.0,
          confidence_source = 'LEARNED',
          cy_net = 0,
          py_net = cy_net
    """)
    db._conn.commit()
    db.log("ROLLOVER", f"Rolled from {src_path.name} to FY {new_fy}")
    db.close()

    # Carry mappings to global learned_mappings
    src_db = ProjectDB(src_path)
    src_db.connect()
    entity_type = src_db.get_meta("entity_type") or ""
    rows = src_db._conn.execute(
        "SELECT r.ledger_name, w.mapping_code FROM wtb w "
        "JOIN raw_tb r ON r.id = w.raw_tb_id "
        "WHERE w.is_confirmed=1 AND w.mapping_code IS NOT NULL"
    ).fetchall()
    for row in rows:
        settings_db.learn(row[0], entity_type, row[1])
    src_db.close()

    return dest_path
