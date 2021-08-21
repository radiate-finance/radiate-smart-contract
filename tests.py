import smartpy as sp

Radiate = sp.io.import_script_from_url("file:smart_contracts/contract.py").Radiate

@sp.add_test(name = "Radiate", is_default = True)
def test():
    scenario = sp.test_scenario()
    scenario.add_flag("default_record_layout", "comb")
    scenario.h1("Radiate Contract")
    scenario.table_of_contents()

    # Creating test accounts
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    shwetal = sp.test_account("shwetal")
    anshit = sp.test_account("anshit")

    scenario.h2("Initialise the contract")
    c1 = Radiate()
    
    scenario += c1

    # scenario.h2("Creating first stream")
    # c1.createStream(                           # todo
    #     ratePerSecond = 1,
    #     startTime = 200,
    #     stopTime = 500,
    #     receiver = bob,
    #     tokenAddress = 
    # ).run(sender = alice)

    # scenario.h2("Creating second stream")
    # c1.createStream(                           # todo
    #     ratePerSecond = 2,
    #     startTime = ,
    #     stopTime = ,
    #     receiver = anshit,
    #     tokenAddress = 
    # ).run(sender = shwetal)

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



