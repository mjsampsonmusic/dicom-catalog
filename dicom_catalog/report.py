"""Data-quality checks over the catalog."""

QUERIES = {
    "counts_by_modality": """
        SELECT sc.modality, COUNT(DISTINCT se.id) AS sessions, COUNT(DISTINCT sc.id) AS scans,
               COUNT(i.id) AS instances
        FROM scan sc JOIN session se ON se.id = sc.session_id
        LEFT JOIN instance i ON i.scan_id = sc.id
        GROUP BY sc.modality ORDER BY sc.modality""",
    # Series whose InstanceNumbers are not a contiguous 1..N run (likely a partial transfer)
    "incomplete_scans": """
        SELECT sc.series_instance_uid, COUNT(i.id) AS instances, MAX(i.instance_number) AS max_number
        FROM scan sc JOIN instance i ON i.scan_id = sc.id
        GROUP BY sc.id HAVING MAX(i.instance_number) <> COUNT(i.id)
        ORDER BY sc.series_instance_uid""",
    "duplicate_files": """
        SELECT sha256, COUNT(*) AS copies FROM instance GROUP BY sha256 HAVING COUNT(*) > 1""",
    "missing_study_date": """
        SELECT study_instance_uid FROM session WHERE study_date IS NULL""",
}


def run_report(conn) -> dict[str, list[tuple]]:
    out = {}
    with conn.cursor() as cur:
        for name, sql in QUERIES.items():
            cur.execute(sql)
            out[name] = cur.fetchall()
    return out
