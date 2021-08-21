import smartpy as sp

Radiate = sp.io.import_script_from_url("file:smart_contracts/contract.py").Radiate
FA12 = sp.io.import_script_from_url("file:FA12.py").FA12
# FA12_config = sp.io.import_script_from_url("file:FA12.py").FA12_config

class FA12_config:
    def __init__(
        self,
        support_upgradable_metadata         = False,
        use_token_metadata_offchain_view    = True,
    ):
        self.support_upgradable_metadata = support_upgradable_metadata
        # Whether the contract metadata can be upgradable or not.
        # When True a new entrypoint `change_metadata` will be added.

        self.use_token_metadata_offchain_view = use_token_metadata_offchain_view
        # Include offchain view for accessing the token metadata (requires TZIP-016 contract metadata)

@sp.add_test(name = "Radiate", is_default = True)
def test():
    scenario = sp.test_scenario()
    scenario.add_flag("default_record_layout", "comb")
    scenario.h1("Radiate Contract")
    scenario.table_of_contents()

    # Creating test accounts
    admin = sp.test_account("admin").address
    alice = sp.test_account("alice").address
    bob = sp.test_account("bob").address
    shwetal = sp.test_account("shwetal").address
    anshit = sp.test_account("anshit").address

    scenario.h2("Initialise the contract")
    c1 = Radiate()
    scenario += c1

    token_metadata = {
        "decimals"    : "18",               # Mandatory by the spec
        "name"        : "Test FA1.2 Token",   # Recommended
        "symbol"      : "MGT",              # Recommended
        # Extra fields
        "icon"        : 'https://smartpy.io/static/img/logo-only.svg'
    }
    contract_metadata = {
        "" : "ipfs://QmaiAUj1FFNGYTu8rLBjc3eeN9cSKwaF8EGMBNDmhzPNFd",
    }

    scenario.h2("Initialise FA1.2 contract")
    c2 = FA12(
            admin,
            config              = FA12_config(support_upgradable_metadata = True),
            token_metadata      = token_metadata,
            contract_metadata   = contract_metadata
        )
    scenario += c2

    scenario.h2("Creating first stream")
    c1.createStream(                           # todo
        ratePerSecond = sp.nat(10),
        startTime = sp.timestamp(200),
        stopTime = sp.timestamp(500),
        receiver = bob,
        token = sp.variant("tez", sp.unit)
    ).run(sender = alice, amount = sp.mutez(3000))

    scenario.h2("Creating second stream")
    c1.createStream(                           # todo
        ratePerSecond = sp.nat(100),
        startTime = sp.timestamp(500),
        stopTime = sp.timestamp(1000),
        receiver = anshit,
        token = sp.variant("FA12", c2.address)
    ).run(sender = shwetal, valid = False)

    c2.mint(address = shwetal, value = 60000).run(sender = admin)
    c2.approve(spender = c1.address, value = 50000).run(sender = shwetal)

    c1.createStream(                           # todo
        ratePerSecond = sp.nat(100),
        startTime = sp.timestamp(500),
        stopTime = sp.timestamp(1000),
        receiver = anshit,
        token = sp.variant("FA12", c2.address)
    ).run(sender = shwetal)

    # scenario.h2("Withdraw little amount from first stream")
    # c1.withdraw(
    #     streamId = 0,
    #     amount = 10
    # )

    # scenario.h2("Withdraw left out amount from first stream")
    # c1.withdraw(
    #     streamId = 0,
    #     amount = 10
    # )

    # scenario.h2("Withdraw from second stream") # withdraw complete amount in one go
    # c1.withdraw(
    #     streamId = 1,
    #     amount = 100
    # )

    # scenario.h2("Cancel second stream")
    # c1.cancelStream(
    #     streamId = 1
    # )



