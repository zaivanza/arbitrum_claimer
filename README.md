# arbitrum_claimer

Установка и запуск:
Linux/Mac
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py
```

Windows
```
pip install virtualenv
virtualenv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python main.py
```
в config.py можно поменять GAS_LIMIT_MIN, GAS_LIMIT_MAX и GAS_PRICE. 

gasLimit = рандомный для каждого кошелька от GAS_LIMIT_MIN до GAS_LIMIT_MAX.

нужно в файл wallets.csv добавить приватники и получателя. для этого иди в excel или гугл таблицы, первый столбец приватники, второй получатель и сохраняй файл как csv, добавляй файл в папку. 

ATTEMPTS - это кол-во попыток, то есть сколько раз мы отправим транзу на клейм и транзу на трансфер в случае фейлов. если ATTEMPTS = 5, значит мы сделаем 5 попыток.

настоятельно рекомендую сделать пару тестов на клейм, на трансфер с eth. для трансфера замени вызов функции transfer на transfer_eth. заменять в функции async def worker(wallet). кол-во эфира для трансфера настрой в config.py в переменной ETH_TRANSFER. сейчас выставлено 0.000001 eth, okx и бинанс такое кол-во точно примут.

-----

created by [ ноу гем ]. channel : https://t.me/hodlmodeth. [ code ] chat : https://t.me/code_hodlmodeth.
