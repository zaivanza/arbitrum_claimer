from web3 import Web3, AsyncHTTPProvider
from termcolor import cprint
import time
import json
import random
import decimal
import requests
import csv
from web3.eth import AsyncEth
import asyncio
import aiohttp

'''

1. смотрим сколько мы можем сминтить
2. ждем блок
3. отправляем транзы на минт, если фейл, повторяем снова 
4. если выполнено, делаем трансфер, также проверяем на фейл

'''

# добавляем сюда рпс
RPC_ARBITRUM = [
    'https://rpc.ankr.com/arbitrum',
    'https://1rpc.io/arb',
]

RPC               = 'https://rpc.ankr.com/arbitrum'
RPC_ETH           = 'https://rpc.ankr.com/eth'

ARB_CONTRACT      = '0x912CE59144191C1204E64559FE8253a0e49E6548' # arb token
CLAIMER_CONTRACT  = '0x67a24CE4321aB3aF51c2D0a4801c3E111D88C9d9'
L1BLOCK_CONTRACT  = '0x842eC2c7D803033Edf55E478F461FC547Bc54EB2'
CLAIM_BLOCK       = 16890400 # ethereum

GAS_LIMIT_MIN     = 1200000
GAS_LIMIT_MAX     = 1500000
GAS_PRICE         = 100000000 * 100 # = 10 gwei сейчас
ATTEMPTS          = 5 # кол-во попыток отправить транзу (клейм / трансфер)


outfile = ''

with open(f"{outfile}erc20.json", "r") as file:
    ERC20_ABI = json.load(file)

with open(f"{outfile}TokenDistributor.json", "r") as file:
    CLAIMER_ABI = json.load(file)

with open(f"{outfile}L1Block.json", "r") as file:
    L1BLOCK = json.load(file)

CSV_FILE = f"{outfile}wallets.csv"


def intToDecimal(qty, decimal):
    return int(qty * int("".join(["1"] + ["0"]*decimal)))

def decimalToInt(qty, decimal):
    return qty/ int("".join((["1"]+ ["0"]*decimal)))

ETH_TRANSFER = intToDecimal(0.000001, 18) # для теста

class Arbitrum:
    def __init__(self):
        self.endpoints_array = RPC_ARBITRUM
        self.last_endpoint = ''

    def get_endpoint(self):
        if self.last_endpoint == '':
            self.last_endpoint = self.endpoints_array[0]
            return self.last_endpoint
        else:
            if (self.endpoints_array.index(
                    self.last_endpoint) + 1) > len(self.endpoints_array) - 1:
                self.last_endpoint = self.endpoints_array[0]
                return self.endpoints_array[0]

            self.last_endpoint = self.endpoints_array[self.endpoints_array.index(
                self.last_endpoint) + 1]
            return self.last_endpoint

arbitrum_instance = Arbitrum()
def get_arbitrum_endpoint():
    return arbitrum_instance.get_endpoint()


