from cosmospy import Transaction
import configparser
import requests
from requests import RequestException, Timeout
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import random
import time

headers = {"accept": "application/json", "Content-Type": "application/json"}


def req_get(url: str):
    try:
        req = requests.get(url=url, headers=headers, timeout=5)
        # print(req.text)
        if req.status_code == 200:
            return req.json()

    except (RequestException, Timeout) as reqErrs:
        if verbose == "yes":
            print(f'req_get ERR: {reqErrs} {url}')


def get_addr_balance(addr: str, provider: str):
    d = ""
    try:
        d = req_get(f'{provider}/bank/balances/{addr}')
        if "amount" in str(d):
            return int(d["result"][0]["amount"])
        else:
            return 0
    except Exception as addr_balancer_err:
        print("get_addr_balance", d, addr_balancer_err)


def get_addr_info(addr: str, provider: str):
    try:
        """:returns sequence: int, account_number: int, balance: int"""
        d = req_get(f'{provider}/auth/accounts/{addr}')
        balance = get_addr_balance(addr, provider)
        acc_num = 0
        seq     = 0
        if "sequence" in str(d):
            seq = int(d["result"]["value"]["sequence"])
        else:
            seq = 0

        if "account_number" in str(d):
            acc_num = int(d["result"]["value"]["account_number"])
        else:
            acc_num = 0
        return seq, acc_num, balance

    except Exception as Err11:
        print("get_addr_info err", Err11)


def gen_transaction(recipients_lst: list, priv_key: bytes, amount_lst: list, fee: int, sequence: int, account_num: int,
                    gas: int = 999999999):

    tx = Transaction(
        privkey=priv_key,
        account_num=account_num,
        sequence=sequence,
        fee=fee,
        gas=gas,
        memo=memo_,
        fee_denom=denom,
        hrp=bech32_prefix_,
        chain_id=chain_id,
        sync_mode="sync",
    )

    if len(recipients_lst) != len(amount_lst):
        raise Exception("ERROR: recipients_lst and amount_lst lengths not equal")

    # print(f'Got {len(recipients_lst)} recipients')

    for i, addr in enumerate(recipients_lst):
        # print(f'{i+1}\\{len(recipients_lst)} {addr} amount: {amount_lst[i]} {denom}')
        tx.add_transfer(recipient=recipients_lst[i], amount=amount_lst[i], denom=denom)
    return tx


def send_trxs(transactions_str: str, provider: str) -> str:
    try:
        req = requests.post(url=provider + "/txs", data=transactions_str, headers=headers)
        # print(req.status_code)
        return req.text

    except (RequestException, Timeout) as reqErrs:
        if verbose == "yes":
            print(f'send_trxs ERR {provider}: {reqErrs}')


def read_keypairs():
    print(f'Reading file {keypairs_file}...')
    addrs = []
    privs = []
    with open(keypairs_file, 'r') as csv_file:
        csv_reader = csv_file.read()
        data_lst = csv_reader.split("\n")

    for line in data_lst:
        if line == "":
            continue
        line = line.split(";")
        addr = line[0]
        priv = line[1]
        addrs.append(addr)
        privs.append(priv)

    print(f'Found {len(data_lst)} lines in file {keypairs_file}')
    return addrs, privs


def main():
    prov = random.choice(rpc_providers)
    rand_index = random.randint(0, random_accs)
    address = addresses[rand_index]
    priv = bytes.fromhex(private_keys[rand_index])
    addr_lst = [address] * int(tx_num)
    sequence, account_num, balance = get_addr_info(addr=address, provider=prov)

    if verbose == "yes":
        print(f'{address} nonce: {sequence}')
    txs = gen_transaction(recipients_lst=addr_lst, amount_lst=amount_lst, priv_key=priv,
                          sequence=sequence, account_num=account_num, fee=tx_fee)
    pushable_tx = txs.get_pushable()
    result = send_trxs(pushable_tx, provider=prov)
    transaction_hash = json.loads(result)["txhash"]
    if verbose == "yes":
        print(f'{sequence} | {account_num} | {balance}')
        print(f"http://161.97.153.219:26657/tx?hash=0x{transaction_hash}&prove=true")
        print(result)


# check if config exists
if Path("config.ini").is_file():
    print('Config found')
else:
    print('Config not found')
    exit()

c = configparser.ConfigParser()
c.read("config.ini")
c = c["DEFAULT"]

# Load data from config
keypairs_file = str(c["keypairs_file"])
rpc_providers = str(c["rpc_providers"]).split(",")
tx_num        = int(c["tx_num"])
threads       = int(c["threads"])
verbose       = str(c["verbose"])
chain_id      = str(c["chain_id"])
denom         = str(c["denomination"])
bech32_prefix_ = str(c["bech32_prefix"])
tx_fee        = int(c["tx_fee"])


# check if keyfile exists
if Path(keypairs_file).is_file() is False:
    print(f'File with private keys and addresses not fount: {keypairs_file}')
    exit(1)
addresses, private_keys = read_keypairs()
random_accs = len(addresses)
print(f'Loaded {len(addresses)} keypairs')
amount_lst = [1] * int(tx_num)
memo_ = "c29r3" * 51

# thread pool loop
while True:
    with ThreadPoolExecutor(max_workers=threads) as executor:
        [executor.submit(lambda: main()) for i in range(threads)]
        time.sleep(1)
