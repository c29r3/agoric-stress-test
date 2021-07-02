# agoric-stress-test  
The purpose of this utility was to test the performance of validators in the Agoric `agorictest-16` test network  
The script sends transactions in multithreaded mode, from thousands of wallets. The main settings are in `config.ini`  

*This repository created for testing purposes only  
*For generating wallets and sending transcations I used [cosmospy](https://github.com/hukkinj1/cosmospy)

## Install  
```bash
git clone https://github.com/c29r3/agoric-stress-test.git \
&& cd agoric-stress-test \
&& pip3 install -r requirements
```
Download `keypairs.txt` via the link in the Agoric dashboard submission  
`curl -s <LINK_FROM_DASHBOARD> > keypairs.txt`  

## Run  
`python3 tx-stress-test.py`  

