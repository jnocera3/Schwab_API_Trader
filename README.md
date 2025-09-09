# Schwab API Trader
## Overview

schwab_trader.py is designed to interact with Schwab's Trader APIs. An account will need to be setup [here](https://developer.schwab.com/) in order to interface the API with your Schwab account(s). [This reddit guide](https://www.reddit.com/r/Schwab/comments/1c2ioe1/the_unofficial_guide_to_charles_schwabs_trader/) is the best place to start with getting your developer account setup and getting the needed authentication tokens.

Once you have the keys and tokens, schwab_trader.py can be used to:

- Update your access token
- Get a hash for your account numbers
- Get your account balance
- Get real-time stock or option chain quotes
- Run a trading algorithm to sell naked call options in real-time
- Run a trading algorithm to range trade

## Installation

```
git clone https://github.com/jnocera3/Schwab_API_Trader.git
```

## Dependencies
```
pip install configparser
pip install argparse
pip install holidays
```

## Running the code
```
python schwab_trader.py -h
usage: schwab_trader.py [-h] [-get_tokens] [-get_account_hashes] [-get_balance]
                        [-account_type ACCOUNT_TYPE] [-get_quote GET_QUOTE]
                        [-sell_call_options SELL_CALL_OPTIONS]
                        [-percent_threshold PERCENT_THRESHOLD] [-range_trade RANGE_TRADE]

options:
  -h, --help            show this help message and exit
  -get_tokens, --get_tokens
                        Get an updated access token.
  -get_account_hashes, --get_account_hashes
                        Get hash value for all accounts returned in JSON format.
  -get_balance, --get_balance
                        Get current account balance. Use account_type option to set the
                        account. Default is brokerage.
  -account_type ACCOUNT_TYPE, --account_type ACCOUNT_TYPE
                        Account type to grab balance or place trades for. Options are ira or
                        brokerage. Default is brokerage.
  -get_quote GET_QUOTE, --get_quote GET_QUOTE
                        Ticker Symbol to get quote for. Result will be stored in
                        ${TickerSymbol}.csv. Default is None (No quote requested).
  -sell_call_options SELL_CALL_OPTIONS, --sell_call_options SELL_CALL_OPTIONS
                        Ticker Symbol to sell call options for. Default is None. If set, this
                        will automatically get a quote for the ticker. A threshold for % from
                        resistance level can be set with the -percent_threshold option. The
                        default threshold is 1.5%. Option file
                        schwab_$ticker_sell_call_options.ini is required.
  -percent_threshold PERCENT_THRESHOLD, --percent_threshold PERCENT_THRESHOLD
                        Percent threshold from resistance level in which options trading is
                        allowed. If outside this threshold, no new option trades will be
                        placed. Default is 1.5.
  -range_trade RANGE_TRADE, --range_trade RANGE_TRADE
                        Ticker Symbol to range trade for. Default is None. Option file
                        schwab_$ticker_range_trade.ini with settings for trading is required.
```

In order to access the API, first add your Schwab Developer App Key and Secret to schwab_config.ini:

```
app_key: App Key for your APP on developer.schwab.com
app_secret: Secret for your APP on developer.schwab.com
```

Next, add your refresh token to schwab_tokens.ini:
```
refresh_token: Your Refresh Token
```

[Consult the reddit guide](https://www.reddit.com/r/Schwab/comments/1c2ioe1/the_unofficial_guide_to_charles_schwabs_trader/) for the code to use to get your refresh token. The refresh token expires after 7 days, so once per week you will need to manually update your refresh token.

Once you have the refresh token, then you can run:

```
python schwab_trader.py -get_tokens
```

This will get your access token and automatically write it to schwab_tokens.ini. The access torken expires in 30 minutes, so you will want to run:

```
python schwab_trader.py -get_tokens
```

periodically to update your access token before it expires. This is most important if you will be accessing the API throughout the trading day.

Once you have your app_key and app_secret set in schwab_config.ini and your refresh and access tokens set in schwab_tokens.ini, then you can run:

```
python schwab_trader.py -get_account_hashes
```

to get your account hashes

Add the hashes for any account you want to access to schwab_config.ini.
```
brokerage: Hash of brokerage account number
```
