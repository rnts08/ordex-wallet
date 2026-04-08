# OrdexWallet

A custodial web wallet for ordexnetwork built to run with docker in your own network.

## Wallet Features

Landing page with dashboard showing assets in both networks, fetch price values from configured exchanges (nestex default), balance over time, recent transactions and news from the ordexnetwork homepage with direct links to github, explorer, pool, swap, staking, discord and other relevant information.

Wallet functionality:
- On first start - create or import wallet (private key)
- Wallet overview with total balance and latest transactions
- Create new/view receiving addresses
- Create new/view sending addresses
- Transactions (list + view details)
- Backup/restore wallet, verify & sign message

System Functionality:
- Automated backups
- System stats (disk usage, network usage)
- RPC console
- System audit log

##

Architecture

    [docker/linux]
        |
    [Flask Backend/API] <---> [html/js/css frontend]
        |
        |
      [RPC]
[ordexcoind/ordexgoldd daemons]

## Notes
* Autogenerate config for the deamons with randomized password for communication with the RPC daemons on first start. 
* Input validation on all input fields to verify correct values

