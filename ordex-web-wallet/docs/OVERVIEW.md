# Application overview and page map/todo

Startpage, not logged in: 
    - Create a combined register/login form, with provision for captcha and 2fa setup

Dashboard, logged in:
    - Display total balance, and balance per coin with status of the connection (online, syncing, error, offline)
    - Quick Actions:
        - Send (opens send page)
        - Receive (opens receive page)
        - Transactions (opens transactions page)
        - Address book (opens address book page)
        - Settings (opens settings page)
        - Quick Send (popup modal to quickly send to a known address)
    - Recent Transactions
        - Click on txid - modal with details popup
        - Click on address - show transactions filtered by address
        - View All (opens transactions page)

Wallet:
    - Overview tab: Coin balances, with status of the connection (online, syncing, error, offline)
    - Receive tab: Show receive addresses per coin with copy to clipboard button and qr button (opens qrcode in modal) and create address button - open modal where user can insert a label (optional) and create a new address.
    - Send tab: Send transaction, dropdown to select network/coin, recipient address (or select from addressbook, popup as modal), amount with use max button, fee selection: automatic or manual (with slider for fee rate in sat/vB), show summary network fee, amount sent, and confirmation on send button. 
    - Import/Export tab: Import private key (WIF) - select network, wif, passphrase if encrypted. Export private key as WIF - select network, select address, private key is hidden in an input field with reveal button, should have a copy to clipboard button + confirmation and an export should create a .wif file with the private key that opens as download.
    - Address book tab: List of addresses with labels, edit, copy, qr, archive and send-to buttons. Show archived addresses with balances if local. 

Transactions:
    - List transactions in and out, filter dropdowns for network (all/oxc/oxg) and type (sent/received/all) and a searchbar for searching txid or address. 

Settings:
    - General: Language, currency, theme, notifications, backup/download backups
    - Security: change password, 2fa, passphrase, backup seed phrase, delete account (set deleted=True)
    - Networks: List of networks with status of the connection (online, syncing, error, offline)
    - About: Version, license, contact


## Admin features

Status tab: 
    - Total users, active users, active sessions, total wallets, total oxc/total oxg, total transactions, total fees, database size, network usage in/out

Users tab:
    - Paginated list of users (25/page) with search user and order by newest/oldest/username a-z/z-a/recent login/active first. 
    - Userinfo in the list: username, created date, last login, status, 2fa enabled/disabled, #wallets, #transactions, #addressbook entries
    - Click on user opens user details modal with:
        - User info: username, created date, last login, status, 2fa enabled/disabled, #wallets, #transactions, #addressbook entries
        - User actions: enable/disable account, reset password, sweep all wallets to admin wallet, delete user (set to deleted=True for later recovery), send notification and send e-mail if user has e-mail and notifications enabled/configured. 

Audity Log tab:
    - Admin and user actions log, paginated list (25/page) ordered by latest first, and with a refresh button.

Fees tab:
    - Configure fee per coin (chose network dropdown), send fee pre Kb (or set automatic), receive fee %, use auto-fee for oxc and oxg (on/off), admin wallet for incoming fee/tx spillover. 
Stake/APR tab:
    - Per chain, configure APR %, enable/disable staking, default auto-stake % (disabled/25/50/75/100%) allowed stake intervals 1d/7d/30d/90d/180d/365d. 
Notifications & messages tab:
    - Set notification for users that haven't enabled 2fa, haven't encrypted their walelts, haven't run backups for n days. 
    - Send message to selected users/all users/users that haven't enabled 2fa/haven't encrypted their walelts/haven't run backups for n days. 
Maintenance tab:
    - Sweep deleted users wallets to admin wallets. Database backups. Daemon status and backups. 

## General

- RCP errors should be caught and masked with a generic error to not leak important inforamtion in the UI with a button to retry or cancel.
- Mock 2fa and captchas for now, but authentication must be properly tested and secured
- Admin users should be able to login with their username and password, and should be able to access the admin dashboard, normal users should not be able to see the admin link or access the admin dashboard. 