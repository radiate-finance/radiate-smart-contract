import smartpy as sp

Radiate = sp.io.import_script_from_url("file:smart_contracts/contract.py").Radiate

FA12_module = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA1.2.py")
FA12 = FA12_module.FA12
FA12_config = FA12_module.FA12_config

FA2_module = sp.io.import_script_from_url("https://smartpy.io/dev/templates/FA2.py")
FA2 = FA2_module.FA2
FA2_config = FA2_module.FA2_config


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
    user1 = sp.test_account("user1")
    user2 = sp.test_account("user2")

    scenario.h2("Initialise the Radiate contract")
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

    scenario.h2("Initialise FA2 contract")

    c3 = FA2(
        config = FA2_config(non_fungible = False),
        metadata = sp.utils.metadata_of_url("https://example.com"),
        admin = admin
    )

    scenario += c3

######################################### tez begins here #####################################

    scenario.h2("Creating first stream")
    c1.createStream(                           
        ratePerSecond = sp.nat(10),
        startTime = sp.timestamp(1729622656),
        stopTime = sp.timestamp(1829622656),
        receiver = user2.address,
        token = sp.variant("tez", sp.unit)
    ).run(sender = alice, amount = sp.mutez(1000000000))

    scenario.h2("The failing withdraw case")
    c1.withdraw(
        streamId = 0,
        amount = 10
    ).run(sender = user2.address, now = sp.timestamp(100), valid = False)

    scenario.h2("Cancelling stream, tez")
    c1.cancelStream(
        streamId = 0
    ).run(sender = alice, now = sp.timestamp(1729622654))

    scenario.h2("Withdrawing from stream of tez")
    c1.withdraw(
    streamId = 0,
    amount = 10
    ).run(sender = user2.address, now = sp.timestamp(1759622656))

    scenario.h2("Withdraw before stopTime")
    c1.withdraw(
    streamId = 0,
    amount = 10
    ).run(sender = user2.address, now = sp.timestamp(1819622656))

    scenario.h2("To test if withdrawal works after stopTime")
    c1.withdraw(
    streamId = 0,
    amount = 10
    ).run(sender = user2.address, now = sp.timestamp(1929622656))


    ######################################### FA1.2 begins here #####################################

    scenario.h2("Creating second stream for FA1.2 token")
    scenario.h3("Failing case, before minting")
    c1.createStream(                           
        ratePerSecond = sp.nat(100),
        startTime = sp.timestamp(500),
        stopTime = sp.timestamp(1000),
        receiver = user2.address,
        token = sp.variant("FA12", c2.address)
    ).run(sender = user1.address, valid = False)

    c2.mint(address = user1.address, value = 60000).run(sender = admin)   #minting
    c2.approve(spender = c1.address, value = 50000).run(sender = user1)   #approving

    scenario.h2("Creating stream for FA1.2 after minting")
    c1.createStream(                           
        ratePerSecond = sp.nat(100),
        startTime = sp.timestamp(500),
        stopTime = sp.timestamp(1000),
        receiver = user2.address,
        token = sp.variant("FA12", c2.address)
    ).run(sender = user1, now = sp.timestamp(300))

    scenario.h2("Withdraw from stream, FA1.2")

    scenario.h3("Withdrawing before start of stream")
    c1.withdraw(
        streamId = 1,
        amount = 10
    ).run(sender = user2, now = sp.timestamp(100), valid = False)

    scenario.h3("Withdrawing after start, before stop time")
    c1.withdraw(
        streamId = 1,
        amount = 10
    ).run(sender = user2, now = sp.timestamp(700))

    # scenario.h3("Withdraw at stop time")
    # c1.withdraw(
    #     streamId = 1,
    #     amount = 10
    # ).run(sender = user2, now = sp.timestamp(1000))

    # scenario.h3("Withdraw after stop time")
    # c1.withdraw(
    #     streamId = 1,
    #     amount = 10
    # ).run(sender = user2, now = sp.timestamp(1200))

    scenario.h2("Cancelling stream, FA1.2")
    c1.cancelStream(
        streamId = 1
    ).run(sender = user1, now = sp.timestamp(900))

    ######################################### FA2 begins here #####################################

    scenario.h2("Create stream for FA2, failing case")
    c1.createStream(                           
        ratePerSecond = sp.nat(100),
        startTime = sp.timestamp(500),
        stopTime = sp.timestamp(1200),
        receiver = user2.address,
        token = sp.variant("FA2", sp.record(tokenAddress = c3.address, tokenId = 0))
    ).run(sender = user1, valid = False)

    scenario.h2("mint tokens")
    tok0_md = FA2.make_metadata(
        name = "The Token Zero",
        decimals = 18,
        symbol= "TK0" 
    )

    c3.mint(
        address = user1.address,
        amount = 100000,
        metadata = tok0_md,
        token_id = 0
    ).run(sender = admin)

    scenario.h2("Update operators")
    c3.update_operators(
        [
            sp.variant("add_operator", c3.operator_param.make(
                owner = user1.address,
                operator = c1.address,
                token_id = 0
            ))
        ]
    ).run(sender = admin)

    scenario.h2("create stream for FA2, after minting and updating operators")
    c1.createStream(                           
        ratePerSecond = sp.nat(100),
        startTime = sp.timestamp(500),
        stopTime = sp.timestamp(1200),
        receiver = user2.address,
        token = sp.variant("FA2", sp.record(tokenAddress = c3.address, tokenId = 0))
    ).run(sender = user1, now = sp.timestamp(400))

    scenario.h2("Withdraw from stream, FA2")

    scenario.h3("Withdrawing before start of stream")
    c1.withdraw(
        streamId = 2,
        amount = 10
    ).run(sender = user2, now = sp.timestamp(100), valid = False)

    scenario.h3("Withdrawing after start, before stop time")
    c1.withdraw(
        streamId = 2,
        amount = 10
    ).run(sender = user2, now = sp.timestamp(700))

    # scenario.h3("Withdraw at stop time")
    # c1.withdraw(
    #     streamId = 2,
    #     amount = 10
    # ).run(sender = user2, now = sp.timestamp(1200))

    # scenario.h3("Withdraw after stop time")
    # c1.withdraw(
    #     streamId = 2,
    #     amount = 10
    # ).run(sender = user2, now = sp.timestamp(1500))

    scenario.h2("Cancelling stream, FA2")
    c1.cancelStream(
        streamId = 2
    ).run(sender = user1, now = sp.timestamp(900))

    




