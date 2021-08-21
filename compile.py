import smartpy as sp

Radiate = sp.io.import_script_from_url("file:contract.py").Radiate

sp.add_compilation_target(
    "Radiate",
    Radiate(
        admin = sp.address("tz1bKM4FRgAsGdDWzXs4o5HZdjBbLMbPBAA1")
    ),
    flags = [["default_record_layout", "comb"]]
)