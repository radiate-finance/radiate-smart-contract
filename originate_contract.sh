# ./originate-contract.sh <path to compiled output>
SMARTPY=~/smartpy-cli/SmartPy.sh
RPC=https://granadanet.smartpy.io
# RPC=https://api.tez.ie/rpc/mainnet

echo "Originate Contract..."
echo "[INFO] - Using code" $1/*contract.tz
echo "[INFO] - Using storage" $1/*storage.tz

if [ -z "$2" ]
    then
        echo "Using default private key"
        $SMARTPY originate-contract --code $1/*contract.tz --storage $1/*storage.tz --rpc $RPC
    else
        $SMARTPY originate-contract --code $1/*contract.tz --storage $1/*storage.tz --rpc $RPC --private-key $2
fi



echo "Done."