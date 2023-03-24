from config import *

# ждем блок, return true
def waitBlock():
    web3 = Web3(Web3.HTTPProvider(RPC))
    
    while True:
        try:
            contract = web3.eth.contract(
                address=web3.to_checksum_address(L1BLOCK_CONTRACT), abi=L1BLOCK
            )
            time.sleep(0.1)
            block = contract.functions.getL1BlockNumber().call()
            cprint(f'eth_block : {block}', "white")  # можно убрать чтобы не спамило

            if block >= CLAIM_BLOCK: 
                break
        except Exception as error:
            cprint(f"waitBlock() : {error}", "red")
            time.sleep(0.5)
            web3 = Web3(Web3.HTTPProvider(get_arbitrum_endpoint()))

    return True

# Инициализируем состояние
def getInitializedData():
    web3 = Web3(Web3.HTTPProvider(get_arbitrum_endpoint()))

    wallets = []

    with open(CSV_FILE) as f:
        reader = csv.reader(f)

        for private_key, recepient in reader:

            # time.sleep(0.3)
            while True:
                try:
                    amount_to_transfer = getArbitrumClaimableTokensFromOnchain(web3, private_key)
                    break
                except Exception as error: 
                    cprint(f"getArbitrumClaimableTokensFromOnchain() : {private_key} | {error}", "red")
                    web3 = Web3(Web3.HTTPProvider(get_arbitrum_endpoint()))

            # cprint(amount_to_transfer, 'blue')
            cprint(
                f"{web3.eth.account.from_key(private_key).address} | {decimalToInt(amount_to_transfer, 18)}",
                "green",
            )

            if amount_to_transfer > 0:
                wallets.append(
                    {
                        "private_key": private_key,
                        "recepient": recepient,
                        "amount_to_transfer": amount_to_transfer - 10,  # Вычитаем копейку
                    }
                )
    return wallets

# смотрим баланс ARB, чтобы отправить на биржи
def getArbitrumClaimableTokensFromOnchain(web3, private_key):

    account = web3.eth.account.from_key(private_key)
    address = account.address
    contract = web3.eth.contract(
        address=web3.to_checksum_address(CLAIMER_CONTRACT), abi=CLAIMER_ABI
    )

    return contract.functions.claimableTokens(
        web3.to_checksum_address(address)
    ).call()

# проверяем статус транзакции
async def checkStatusTx(web3, tx_hash):

    while True:
        try:
            status_ = await web3.eth.get_transaction_receipt(tx_hash)
            status = status_["status"]
            break
        except:
            None

    return status

# клеймим
async def claimer(web3, privatekey):

    try:

        contract = web3.eth.contract(
            address=Web3.to_checksum_address(CLAIMER_CONTRACT), abi=CLAIMER_ABI
        )
        account = web3.eth.account.from_key(privatekey)
        address = account.address

        retry = 0

        while True:

            if retry != ATTEMPTS:

                nonce = await web3.eth.get_transaction_count(address)
                gasLimit = random.randint(GAS_LIMIT_MIN, GAS_LIMIT_MAX) 

                contract_txn = await contract.functions.claim().build_transaction(
                    {
                        "from": address,
                        "gas": gasLimit,
                        "gasPrice": GAS_PRICE,
                        "nonce": nonce,
                    }
                )

                signed_txn = web3.eth.account.sign_transaction(
                    contract_txn, private_key=privatekey
                )
                tx_hash = await web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                hash_ = web3.to_hex(tx_hash)
                status_tx = await checkStatusTx(web3, hash_)

                # нужно поменять на 1 , пока что 0 чтобы не слать бесконечно транзы
                if status_tx == 1:
                    cprint(f"\n>>> claim : https://arbiscan.io/tx/{hash_}", "green")
                    break
                else: 
                    cprint(f"\n>>> not claim, try again : {address}", "yellow")
                    time.sleep(0.5)

                retry += 1

            else : break

        except Exception as error:

            cprint(f'{privatekey} | claimer() : {error}', 'red')
            web3 = Web3(AsyncHTTPProvider(get_arbitrum_endpoint()),modules={"eth": (AsyncEth,)},middlewares=[])
            return await claimer(web3, privatekey)

# отправляем арб на биржи
async def transfer(web3, privatekey, amount_to_transfer, to_address):

    try:
            
        token_contract = web3.eth.contract(
            address=Web3.to_checksum_address(ARB_CONTRACT), abi=ERC20_ABI
        )
        account = web3.eth.account.from_key(privatekey)
        address = account.address

        retry = 0
        while True:

            if retry != ATTEMPTS:

                nonce = await web3.eth.get_transaction_count(address)
                gasLimit = random.randint(GAS_LIMIT_MIN, GAS_LIMIT_MAX) 

                contract_txn = await token_contract.functions.transfer(
                    Web3.to_checksum_address(to_address), int(amount_to_transfer)
                ).build_transaction(
                    {
                        "chainId": 42161,
                        "gasPrice": GAS_PRICE,
                        "gas": gasLimit,
                        "nonce": nonce,
                    }
                )

                tx_signed = web3.eth.account.sign_transaction(contract_txn, privatekey)
                tx_hash = await web3.eth.send_raw_transaction(tx_signed.rawTransaction)
                hash_ = web3.to_hex(tx_hash)
                status_tx = await checkStatusTx(web3, hash_)

                # нужно поменять на 1 , пока что 0 чтобы не слать бесконечно транзы
                if status_tx == 1:
                    cprint(f"\n>>> transfer : https://arbiscan.io/tx/{hash_}", "green")
                    break
                else: 
                    cprint(f"\n>>> not transfer, try again : {address}", "yellow")
                    time.sleep(0.5)

                retry += 1

            else : break

    except Exception as error:
        cprint(f'{privatekey} | transfer() : {error}', 'red')
        web3 = Web3(AsyncHTTPProvider(get_arbitrum_endpoint()),modules={"eth": (AsyncEth,)},middlewares=[])
        return await transfer(web3, privatekey, amount_to_transfer, to_address)


# для теста отправка эфира
async def transfer_eth(web3, privatekey, amount_to_transfer, to_address):

    try:

        account = web3.eth.account.from_key(privatekey)
        address = account.address

        while True:
            nonce = await web3.eth.get_transaction_count(address)
            gasLimit = random.randint(GAS_LIMIT_MIN, GAS_LIMIT_MAX) 

            contract_txn = {
                    'chainId': 42161,
                    'gasPrice': GAS_PRICE,
                    'gas': gasLimit,
                    'nonce': nonce,
                    'to': Web3.to_checksum_address(to_address),
                    'value': ETH_TRANSFER
                }

            tx_signed = web3.eth.account.sign_transaction(contract_txn, privatekey)
            tx_hash = await web3.eth.send_raw_transaction(tx_signed.rawTransaction)
            hash_ = web3.to_hex(tx_hash)
            status_tx = await checkStatusTx(web3, hash_)

            # нужно поменять на 1 , пока что 0 чтобы не слать бесконечно транзы
            if status_tx == 1:
                cprint(f"\n>>> transfer : https://arbiscan.io/tx/{hash_}", "green")
                break

    except Exception as error:
        cprint(f'{privatekey} | transfer_eth() : {error}', 'red')
        web3 = Web3(AsyncHTTPProvider(get_arbitrum_endpoint()),modules={"eth": (AsyncEth,)},middlewares=[])
        return await transfer(web3, privatekey, amount_to_transfer, to_address)

# асинхронный воркер
async def worker(wallet):

    while True:
        try:
            web3 = Web3(
                AsyncHTTPProvider(get_arbitrum_endpoint()),
                modules={"eth": (AsyncEth,)},
                middlewares=[],
            )
            break
        except: None

    await claimer(web3, wallet["private_key"])
    await transfer(
        web3, wallet["private_key"], wallet["amount_to_transfer"], wallet["recepient"]
    )

async def main():
    start = float(time.perf_counter())
    tasks = [worker(wallet) for wallet in wallets]
    await asyncio.gather(*tasks)
    fin = round((time.perf_counter() - start), 1)
    cprint(f'result : {fin} sec', 'blue')


if __name__ == "__main__":

    # Инициализируем состояние (чекаем балансы кошельков)
    wallets = getInitializedData()
    print("Initialization completed successfully")

    # Ждем блок
    block_ = waitBlock()

    # для теста раскомментируй это, тогда не будет ждать блок
    # block_ = True 

    if block_ == True:

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        loop.close()
