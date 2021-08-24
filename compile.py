import smartpy as sp

Radiate = sp.io.import_script_from_url("file:smart_contracts/contract.py").Radiate

sp.add_compilation_target(
    "Radiate",
    Radiate(),
    flags = [["default_record_layout", "comb"]]
)