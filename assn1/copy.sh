echo "Make sure directory ~/cs334/assn1 exists in your moat"
if [ "$1" == "" ]; then
    echo "Specify username for moat"
else
    cp client.py client
    scp client "$1"@moat.cs.uab.edu:cs334/assn1
    rm client
fi