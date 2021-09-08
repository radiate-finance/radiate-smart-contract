import smartpy as sp

Radiate = sp.io.import_script_from_url("file:smart_contracts/contract.py").Radiate

FA12_module = sp.io.import_script_from_url("file:FA12.py")
FA12 = FA12_module.FA12
FA12_config = FA12_module.FA12_config

FA2_module = sp.io.import_script_from_url("file:FA2.py")
FA2 = FA2_module.FA2
FA2_config = FA2_module.FA2_config

sp.add_compilation_target(
    "plenty",
    FA12(
        admin = sp.address("tz1f85LjxaHfWfPuNtZFg1aVBiaAkVnVnKsH"),
        config              = FA12_config(support_upgradable_metadata = True),
        token_metadata      = {
            "": "ipfs://QmaKjuYmhKkAhDufNyzEdgH2xUWzySzGQM6YkEnrnDd7te"
        },
    )
)

sp.add_compilation_target(
    "kusd",
    FA12(
        admin = sp.address("tz1f85LjxaHfWfPuNtZFg1aVBiaAkVnVnKsH"),
        config              = FA12_config(support_upgradable_metadata = True),
        token_metadata      = {
            "": "ipfs://QmVnHvxjWfYFwfGCco2Lx9C8j2i3HvPzUXCRdKCtcFhvhU"
        },
    )
)

sp.add_compilation_target(
    "FA2_tokens",
    FA2(
        config = FA2_config(non_fungible = False),
        metadata = sp.utils.metadata_of_url("ipfs://QmPUbXWsHji1aSoomix7dXj1veBrnqXtjfTzWyt73R1Mkj"),
        admin = sp.address("tz1f85LjxaHfWfPuNtZFg1aVBiaAkVnVnKsH")
    )
)


sp.add_compilation_target(
    "Radiate",
    Radiate(admin = sp.address("tz1f85LjxaHfWfPuNtZFg1aVBiaAkVnVnKsH")),
    flags = [["default_record_layout", "comb"]]
)