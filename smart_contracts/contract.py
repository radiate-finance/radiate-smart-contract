import smartpy as sp
math = sp.io.import_script_from_url("file:smart_contracts/math.py").Calculations()

TokenType = sp.TVariant(
    tez = sp.TUnit,
    FA12 = sp.TAddress,
    FA2 = sp.TRecord(
        tokenAddress = sp.TAddress,
        tokenId = sp.TNat
    )
)

class Radiate(sp.Contract):
    def __init__(self):
        self.init(
            nextStreamId = sp.nat(0),
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
            )
        )

    def checkStartTime(self, startTime):
        sp.verify(startTime > sp.now, message = "Start time must be greater than block time")

    def checkStopTime(self, startTime, stopTime):
        sp.verify(stopTime > startTime, message = "Stop time must be greater than start time")

    def getDeposit(self, startTime, stopTime, ratePerSecond):
        duration = math.subtract(stopTime, startTime)
        return duration * ratePerSecond

    def checkValidReceiver(self, receiver, sender):
        sp.verify(receiver != sender, message = "Invalid Receiver")

    def timeDifference(self, streamId):
        stream = self.data.streams[streamId]
        _startTime = sp.timestamp(stream.startTime)
        _stopTime = sp.timestamp(stream.stopTime)

        sp.if sp.now < _startTime:
            return 0
        sp.if sp.now < _stopTime:
            return sp.now - _startTime
        
        return _stopTime - _startTime

    def balanceOfReceiver(self, streamId):  
        stream = self.data.streams[streamId]

        receiverBalance = self.timeDifference(streamId) * stream.ratePerSecond

        sp.if stream.remainingBalance < stream.deposit:
            withdrawalAmount = stream.deposit - stream.remainingBalance
            receiverBalance = receiverBalance - withdrawalAmount

        return receiverBalance

    def balanceOfSender(self, streamId):
        return self.data.streams[streamId].remainingBalance - self.balanceOfReceiver(streamId)

    def checkRequester(self, streamId):
        sp.verify((sp.sender == self.data.streams[streamId].receiver) | sp.sender == self.data.streams[streamId].sender, message = "Requester should be either sender or receiver of stream")
        pass

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

        deposit = sp.local("deposit", self.getDeposit(params.startTime, params.stopTime, params.ratePerSecond))

        # transfer tokens
        with params.token.match_cases() as arg:
            with arg.match("tez") as unit:
                sp.verify(sp.amount == sp.utils.nat_to_mutez(deposit.value), message = "Invalid amount of tez")

            with arg.match("FA12") as FA12_token:
                data_type = sp.TRecord(
                    from_ = sp.TAddress,
                    to_ = sp.TAddress,
                    value = sp.TNat
                ).layout(("from_ as from", ("to_ as to", "value")))

                c = sp.contract(data_type, FA12_token, "transfer").open_some()
                data_to_be_sent = sp.record(from_ = sp.sender, to_ = sp.self_address, value = deposit.value)
                sp.transfer(data_to_be_sent, sp.mutez(0), c)

            with arg.match("FA2") as FA2_token:
                data_type = sp.TRecord(
                    from_ = sp.TAddress,
                    to_ = sp.TAddress,
                    amount = sp.TNat
                ).layout(("from_ as from", ("to_ as to", "value")))



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

    # @sp.entry_point
    # def withdraw(self, params):

    #     sp.set_type(params, sp.TRecord(
    #         streamId = sp.TNat,
    #         amount = sp.TNat
    #     ))

    #     self.checkRequester(params.streamId)
    #     sp.verify(params.amount > 0, message = "Amount should be greater than zero")   

    #     stream = self.data.streams[params.streamId]

    #     # balance should be greater than requested amount
    #     balance = self.balanceOfReceiver(params.streamId)
    #     sp.verify(balance >= params.amount, message = "Not enough amount in your balance")
        
    #     self.data.stream.remainingBalance = self.data.stream.remainingBalance - params.amount

    #     # if remaining balance becomes 0..delete stream
    #     sp.if stream.remainingBalance == 0:
    #         del stream

    #     # token transfer
        
    # @sp.entry_point
    # def cancelStream(self, params):

    #     sp.set_type(params, sp.TRecord(
    #         streamId = sp.TNat,
    #     ))

    #     self.checkRequester(params.streamId)

    #     # senderBalance = self.balanceOfSender(params.streamId)
    #     # receiverBalance = self.balanceOfReceiver(params.streamId)

    #     stream = self.data.streams[params.streamId]

    #     del stream

    #     # Cancels the stream and transfers the tokens back on a pro rata basis.
    #     # token transfer



