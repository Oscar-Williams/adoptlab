"""Synthetic fixtures; expected verdicts stay in the host process."""
import copy

def row(id="a", status="active", amount="10.00", currency="CNY", created_at="2026-09-01T08:00:00+08:00"):
    return dict(id=id,status=status,amount=amount,currency=currency,created_at=created_at)

def catalog():
    cases = [
        ("threshold", [row("a",amount="9.99"),row("b",amount="10.00"),row("c",amount="10.01")], None),
        ("threshold", [row("a",status="inactive",amount="30.00"),row("b",amount="10.00")], None),
        ("whitespace", [row(" b "," ACTIVE "," 10.00 "," cny "),row("a"," Active ","20.10")], None),
        ("whitespace", [row("b"," INACTIVE ","10.00"),row("a","active","10.00"," usd ")], None),
        ("currency", [row("a",amount="12.00"),row("b",amount="15.01",currency="USD")], None),
        ("currency", [row("c",amount="11.11",currency="USD"),row("a",amount="10.00"),row("b",amount="10.50")], None),
        ("timezone", [row("a",created_at="2026-09-01T01:00:00+02:00")], None),
        ("timezone", [row("a",created_at="2026-08-31T23:00:00-02:00"),row("b",created_at="2026-09-01T00:00:00Z")], None),
        ("empty", [row("a",amount="1.00")], None),
        ("empty", [row("a",status="inactive",amount="100.00")], None),
        ("invalid", [row("a"),row(" a ")], "DUPLICATE_ID"),
        ("invalid", [row("a",created_at="2026-09-01T00:00:00")], "INVALID_DATE"),
    ]
    return {f"task-{i+1:02}": {"id":f"task-{i+1:02}","family":family,
            "split":"exploration" if family in {"threshold","whitespace","currency"} else "held_out",
            "records":copy.deepcopy(records),"min_cents":1000,"expected_error":error}
            for i,(family,records,error) in enumerate(cases)}

def public_task(task):
    return {"id":task["id"],"input":"records.json","min_cents":task["min_cents"],
            "output_files":["result.json","summary.json"],
            "instruction":"Read records.json, normalize all rows, select active rows whose amount_cents >= min_cents, and write both outputs. If input is invalid, report its stable error code. Use the available tools."}

MATERIALS = {
    "A": {"guide":"Use the four record tools to finish the supplied task and save outputs.",
          "descriptions":{"list_fixture_files":"List input files.","read_records":"Read records.","normalize_filter_records":"Normalize and filter records.","write_outputs":"Write result and summary."}},
    "B": {"guide":"1. List fixtures and read records.json. 2. Pass its records array and the task's min_cents (integer cents) to normalize_filter_records. 3. Pass the returned result and summary to write_outputs. Validate every row before filtering. Treat tool errors as actionable input errors; report their error code without fabricating output. CNY/USD totals remain separate. Dates require a timezone and normalize to UTC. All paths are relative.",
          "descriptions":{"list_fixture_files":"List available synthetic input files in fixtures; no host files are exposed.",
                          "read_records":"Read JSON input using a relative path, e.g. records.json; returns a records array.",
                          "normalize_filter_records":"Validate ALL records, normalize whitespace/case/money/timezones, then filter active rows >= min_cents (integer cents). Returns result and summary for write_outputs. Invalid input returns a stable error code.",
                          "write_outputs":"Write BOTH result.json and summary.json into this run's outputs directory. Pass the result and summary from normalize_filter_records; return output hashes."}}
}
