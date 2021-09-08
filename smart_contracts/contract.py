import smartpy as sp

TokenType = sp.TVariant(
    tez = sp.TUnit,
    FA12 = sp.TAddress,
    FA2 = sp.TRecord(
        tokenAddress = sp.TAddress,
        tokenId = sp.TNat
    )
)

class Radiate(sp.Contract):
    def __init__(self, admin):
        self.init(
            nextStreamId = sp.nat(0),
            admin = admin,
            rewards = sp.nat(0),
            streams = sp.big_map(
                tkey = sp.TNat, 
                tvalue = sp.TRecord(
                    deposit = sp.TNat,
                    ratePerSecond = sp.TNat,
                    remainingBalance = sp.TNat,
                    startTime = sp.TTimestamp,
                    stopTime = sp.TTimestamp,
                    receiver = sp.TAddress,
                    sender = sp.TAddress,
                    token = TokenType
                )
            ),
            metadata = sp.utils.metadata_of_url("ipfs://QmZcjtDZVGenfkHG321UfhPKEn7saKVQJJabiDEnKmNEB7")
        )

    @sp.entry_point(name = "default")
    def ep(self):
        self.data.rewards += sp.utils.mutez_to_nat(sp.amount)
        pass

    def checkStartTime(self, startTime):
        sp.verify(startTime > sp.now, message = "START_TIME_LESS_THAN_CURRENT_TIME")

    def checkStopTime(self, startTime, stopTime):
        sp.verify(stopTime > startTime, message = "STOP_TIME_LESS_THAN_START_TIME")

    @sp.sub_entry_point
    def getDeposit(self, params):
        sp.verify(params.stopTime >= params.startTime)
        duration = sp.as_nat(params.stopTime - params.startTime)
        sp.result(duration * params.ratePerSecond)

    def checkValidReceiver(self, receiver, sender):
        sp.verify(receiver != sender, message = "INVALID_RECEIVER")

    @sp.entry_point
    def delegate(self, baker):
        sp.verify(sp.sender == self.data.admin)
        sp.verify(sp.amount == sp.mutez(0))
        sp.set_delegate(baker)

    @sp.entry_point
    def collect_management_rewards(self, params):
        sp.verify(sp.sender == self.data.admin)
        sp.verify(params.amount <= self.data.rewards)
        sp.send(params.address, sp.utils.nat_to_mutez(params.amount))
        self.data.rewards = sp.as_nat(self.data.rewards - params.amount)
    
    @sp.sub_entry_point
    def timeDifference(self, streamId):
        stream = self.data.streams[streamId]

        sp.if (sp.now < stream.startTime):
            sp.result(sp.as_nat(0))
        sp.else:
            sp.if (stream.stopTime > sp.now):
                sp.result(sp.as_nat(sp.now - stream.startTime))
            sp.else:
                sp.result(sp.as_nat(stream.stopTime - stream.startTime))


    @sp.sub_entry_point
    def balanceOfReceiver(self, params):  
        stream = self.data.streams[params.streamId]

        receiverBalance = params.timeDifference * stream.ratePerSecond

        sp.if stream.remainingBalance < stream.deposit:
            withdrawalAmount = sp.as_nat(stream.deposit - stream.remainingBalance)
            receiverBalance = sp.as_nat(receiverBalance - withdrawalAmount)

        sp.result(receiverBalance)


    def checkRequester(self, streamId):
        sp.verify((sp.sender == self.data.streams[streamId].receiver), message = "NOT_RECEIVER")

    @sp.entry_point
    def createStream(self, params):
        sp.set_type(params, sp.TRecord(
            ratePerSecond = sp.TNat,
            startTime = sp.TTimestamp,
            stopTime = sp.TTimestamp,
            receiver = sp.TAddress,
            token = TokenType
        ))

        self.checkStartTime(params.startTime)
        self.checkStopTime(params.startTime, params.stopTime)
        self.checkValidReceiver(params.receiver, sp.sender)

        deposit = sp.local("deposit", self.getDeposit(sp.record(
                    startTime = params.startTime, 
                    stopTime = params.stopTime, 
                    ratePerSecond =  params.ratePerSecond
                )
            )
        )

        # transfer tokens
        with params.token.match_cases() as arg:
            with arg.match("tez") as unit:
                sp.verify(sp.amount == sp.utils.nat_to_mutez(deposit.value), message = "INVALID_TEZ")

            with arg.match("FA12") as FA12_token:
                data_type = sp.TRecord(
                    from_ = sp.TAddress,
                    to_ = sp.TAddress,
                    value = sp.TNat
                ).layout(("from_ as from", ("to_ as to", "value")))

                c = sp.contract(data_type, FA12_token, "transfer").open_some()

                data_to_be_sent = sp.record(
                    from_ = sp.sender,
                    to_ = sp.self_address,
                    value = deposit.value
                )

                sp.transfer(data_to_be_sent, sp.mutez(0), c)

            with arg.match("FA2") as FA2_token:
                data_type = sp.TList(
                    sp.TRecord(
                        from_ = sp.TAddress, 
                        txs = sp.TList(
                            sp.TRecord(
                                amount = sp.TNat,
                                to_ = sp.TAddress,
                                token_id = sp.TNat
                            ).layout(("to_", ("token_id", "amount")))
                        )
                    ).layout(("from_", "txs"))
                )

                c = sp.contract(data_type, FA2_token.tokenAddress, "transfer").open_some()

                data_to_be_sent = sp.list(
                    [
                        sp.record(
                            from_ = sp.sender, 
                            txs = sp.list(
                                [
                                    sp.record(
                                        amount = deposit.value,
                                        to_ = sp.self_address, 
                                        token_id = FA2_token.tokenId
                                    )
                                ]
                            )
                        )
                    ]
                )
                sp.transfer(data_to_be_sent, sp.mutez(0), c)


        self.data.streams[self.data.nextStreamId] = sp.record(
            deposit = deposit.value,
            ratePerSecond = params.ratePerSecond,
            remainingBalance = deposit.value,
            startTime = params.startTime,
            stopTime = params.stopTime,
            receiver = params.receiver,
            sender = sp.sender,
            token = params.token,
        )

        self.data.nextStreamId = self.data.nextStreamId + 1

    @sp.entry_point
    def withdraw(self, params):

        sp.set_type(params, sp.TRecord(
            streamId = sp.TNat,
            amount = sp.TNat
        ))

        self.checkRequester(params.streamId)
        sp.verify(params.amount > 0, message = "AMOUNT_LESS_THAN_ZERO")   

        stream = self.data.streams[params.streamId]
        timeDiff = self.timeDifference(params.streamId)

        sp.verify(timeDiff > 0, message = "DURATION_0")

        # balance should be greater than requested amount
        balance = self.balanceOfReceiver(sp.record(streamId = params.streamId, timeDifference = timeDiff))
        sp.verify(balance >= params.amount, message = "EXCEEDING_AMOUNT")
        
        stream.remainingBalance = sp.as_nat(stream.remainingBalance - params.amount)

        # token transfer
        with self.data.streams[params.streamId].token.match_cases() as arg:
            with arg.match("tez") as unit:
                sp.send(sp.sender, sp.utils.nat_to_mutez(params.amount), message = "WITHDRAWAL")

                sp.if stream.remainingBalance == 0:
                    reward = sp.local("reward", sp.utils.mutez_to_nat(sp.split_tokens(sp.utils.nat_to_mutez(self.data.rewards), stream.deposit, sp.utils.mutez_to_nat(sp.balance) * 4)))
                    sp.send(stream.sender, sp.utils.nat_to_mutez(reward.value), message = "YIELD_REWARDS")
                    sp.send(stream.receiver, sp.utils.nat_to_mutez(reward.value), message = "YIELD_REWARDS")
                    self.data.rewards = sp.as_nat(self.data.rewards - (reward.value * 2))
                sp.else:
                    pass

            with arg.match("FA12") as FA12_token:
                data_type = sp.TRecord(
                    from_ = sp.TAddress,
                    to_ = sp.TAddress,
                    value = sp.TNat
                ).layout(("from_ as from", ("to_ as to", "value")))

                c = sp.contract(data_type, FA12_token, "transfer").open_some()

                data_to_be_sent = sp.record(
                    from_ = sp.self_address, 
                    to_ = sp.sender, 
                    value = params.amount
                )

                sp.transfer(data_to_be_sent, sp.mutez(0), c)

            with arg.match("FA2") as FA2_token:
                data_type = sp.TList(
                    sp.TRecord(
                        from_ = sp.TAddress, 
                        txs = sp.TList(
                            sp.TRecord(
                                amount = sp.TNat, 
                                to_ = sp.TAddress,
                                token_id = sp.TNat
                            ).layout(("to_", ("token_id", "amount")))
                        )
                    ).layout(("from_", "txs"))
                )

                c = sp.contract(data_type, FA2_token.tokenAddress, "transfer").open_some()

                data_to_be_sent = sp.list(
                    [
                        sp.record(
                            from_ = sp.self_address, 
                            txs = sp.list(
                                [
                                    sp.record(
                                        amount = params.amount, 
                                        to_ = sp.sender, 
                                        token_id = FA2_token.tokenId
                                    )
                                ]
                            )
                        )
                    ]
                )
                sp.transfer(data_to_be_sent, sp.mutez(0), c)

        # if remaining balance becomes 0 then delete stream
        sp.if stream.remainingBalance == 0:
            del stream


    @sp.entry_point
    def cancelStream(self, params):

        sp.set_type(params, sp.TRecord(
            streamId = sp.TNat,
        ))
    
        sp.verify(
            (sp.sender == self.data.streams[params.streamId].sender) | (sp.sender == self.data.streams[params.streamId].receiver)
        )

        timeDiff = self.timeDifference(params.streamId)

        receiverBalance = self.balanceOfReceiver(sp.record(
                streamId = params.streamId, 
                timeDifference = timeDiff
            )
        )
        senderBalance = sp.as_nat(self.data.streams[params.streamId].remainingBalance - receiverBalance)

        stream = self.data.streams[params.streamId]

        # token transfer
        with self.data.streams[params.streamId].token.match_cases() as arg:
            with arg.match("tez") as unit:
                sp.send(self.data.streams[params.streamId].sender, sp.utils.nat_to_mutez(senderBalance), message = "CANCELLED")
                
                sp.if receiverBalance != 0:
                    sp.send(self.data.streams[params.streamId].receiver, sp.utils.nat_to_mutez(receiverBalance), message = "CANCELLED")

            with arg.match("FA12") as FA12_token:
                data_type = sp.TRecord(
                    from_ = sp.TAddress,
                    to_ = sp.TAddress,
                    value = sp.TNat
                ).layout(("from_ as from", ("to_ as to", "value")))

                c = sp.contract(data_type, FA12_token, "transfer").open_some()

                data_to_be_sent = sp.record(          # sending to sender
                    from_ = sp.self_address,
                    to_ = self.data.streams[params.streamId].sender,
                    value = senderBalance
                )
                sp.transfer(data_to_be_sent, sp.mutez(0), c)

                data_to_be_sent_receiver = sp.record(       # sending to receiver
                    from_ = sp.self_address,
                    to_ = self.data.streams[params.streamId].receiver,
                    value = receiverBalance
                )
                sp.transfer(data_to_be_sent_receiver, sp.mutez(0), c)

            with arg.match("FA2") as FA2_token:
                data_type = sp.TList(
                    sp.TRecord(
                        from_ = sp.TAddress, 
                        txs = sp.TList(
                            sp.TRecord(amount = sp.TNat,
                                to_ = sp.TAddress,
                                token_id = sp.TNat
                            ).layout(("to_", ("token_id", "amount")))
                        )
                    ).layout(("from_", "txs"))
                )

                c = sp.contract(data_type, FA2_token.tokenAddress, "transfer").open_some()

                data_to_be_sent = sp.list(   # for sender
                    [
                        sp.record(
                            from_ = sp.self_address, 
                            txs = sp.list(
                                [
                                    sp.record(
                                        amount = senderBalance,
                                        to_ = self.data.streams[params.streamId].sender,
                                        token_id = FA2_token.tokenId
                                    )
                                ]
                            )
                        )
                    ]
                )
                sp.transfer(data_to_be_sent, sp.mutez(0), c)

                data_to_be_sent_receiver = sp.list(      # for receiver
                    [       
                        sp.record(
                            from_ = sp.self_address, 
                            txs = sp.list(
                                [
                                    sp.record(
                                        amount = receiverBalance,
                                        to_ = self.data.streams[params.streamId].receiver,
                                        token_id = FA2_token.tokenId
                                    )
                                ]
                            )
                        )
                    ]
                )
                sp.transfer(data_to_be_sent_receiver, sp.mutez(0), c)

        del self.data.streams[params.streamId]