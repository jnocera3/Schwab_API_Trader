# Schwab API Trader
## Overview

schwab_trader.py is designed to interact with Schwab's Trader APIs. An account will need to be setup [here](https://developer.schwab.com/) in order to interface the API with your Schwab account(s). [This reddit guide](https://www.reddit.com/r/Schwab/comments/1c2ioe1/the_unofficial_guide_to_charles_schwabs_trader/) is the best place to start with getting your developer account setup and getting the needed authentication tokens.

Once you have the keys and tokens, schwab_trader.py can be used to:

- Update your access token
- Get a hash for your account numbers
- Get your account balance
- Get real-time stock or option chain quotes
- Run a trading algorithm to sell naked call options
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

### Get Account Balance

To get your current brokerage account balance, run this command:

```
python schwab_trader.py -get_balance
```

The current balance will be output to a file named schwab_brokerage_balance.csv

The code defaults to getting your brokerage account balance. If you'd like your IRA or any other account balance run this:

```
python schwab_trader.py -get_balance -account_type ira
```

This will output your current IRA account balance to a file name schwab_ira_balance.csv.

The account type option should match one of the account types listed in schwab_config.ini.

### Get a Quote

To get a quote, run this command:

```
python schwab_trader.py -get_quote $STOCK_SYMBOL
```

where $STOCK_SYMBOL is the ticker of the ETF or stock you want to get a quote for. For example to get a quote for SPY:

```
python schwab_trader.py -get_quote SPY
```

This will output the current price, high of the day, low of the day and the resistance level:

```
SPY quotes valid at 2025-09-11 13:22:37:
Current Price:     657.325
High of Day:       657.8
Low of Day:        653.59
Resistance Level:  657.8
```

A file named $STOCK_SYMBOL_max.txt is used to track the all-time high or a resistance level of your choice. If the latest high of the day is greater than the current value in $STOCK_SYMBOL_max.txt then the value in the file will be updated with the high of the day.

In the example for SPY, the SPY_max.txt file will store the resistance level.

### Range Trade a Stock or ETF

To range trade a stock or ETF, first setup an option file with the settings for range trading. The file name should be:

```
schwab_$STOCK_SYMBOL_range_trade.ini
```

where $STOCK_SYMBOL is the ticker of the ETF or stock you want to range trade. An example is provided in this repo for TMF:

```
schwab_TMF_range_trade.ini
```

The first 3 header lines will need to be set:

```
Shares of $STOCK_SYMBOL to trade: 10
Max shares of $STOCK_SYMBOL to own: 560
Ticker to Buy/Sell for Buying Power: BIL
```

On the first line enter the number of shares you want to trade per trade. On the second line enter the maximum number of shares you want to own. On the third line enter an ETF to use for storing cash to provide buying power for your trades. BIL (1-3 month T-Bill ETF) is a good one to use.

On the remaining lines:

```
Num Shares, Buy Price, Sell Price
10, 39.01, 39.81
20, 38.91, 39.71
30, 38.81, 39.61
40, 38.71, 39.51
50, 38.61, 39.41
60, 38.51, 39.31
70, 38.41, 39.21
80, 38.31, 39.11
.., ....., .....
560, 33.51, 34.31
```

Enter the number of shares to own, the buy price and the sell price at each share count. In the example above, if the shares price falls to 38.41, 70 shares of the position will be bought. The count will stay at 70 until the price moves. The code will automatically enter a limit buy order for 10 shares at 38.31 and a limit sell order for 10 shares at 39.21. If the price moves down to 38.31, an additional 10 shares will be purchased. If the price moves up to 39.21, 10 shares will be sold. After each trade is executed new buy and sell orders will be placed based on the current share count.

The script:

```
range_trade_setup.py
```

can be used to print out the shares to own, the buy price and the sell price which can then be easily copied and pasted into the option file.

Once your option file is setup, you can run the code to range trade:

```
python schwab_trader.py -range_trade $STOCK_SYMBOL
```

Example for TMF:

```
python schwab_trader.py -range_trade TMF
```

Ideally, set the code to run once per minute throughout the trading day. Since the access token expires after 30 minutes, it's important that you make sure to update it throughout the trading day. Here are sample cron entries for updating the access tokens:

```
# Update Schwab Tokens every 20 minutes on trading days
20,40 9 * * 1-5 cd /home/user/schwab; python schwab_trader.py -get_tokens > schwab_trader_get_tokens.out 2>&1
00,20,40 10-15 * * 1-5 cd /home/user/schwab; python schwab_trader.py -get_tokens > schwab_trader_get_tokens.out 2>&1
00 16 * * 1-5 cd /home/user/schwab; python schwab_trader.py -get_tokens > schwab_trader_get_tokens.out 2>&1
```

and here are sample cron entries for running range trading throughout the day:

```
# Run code to range trade TMF, checking every minute of the trading day
30 9 * * 1-5 sleep 15; yyyymmdd=`date +\%Y\%m\%d`; hhmm=`date +\%H\%M`; cd /home/user/schwab; mkdir -p TMF/$yyyymmdd > /dev/null; python schwab_trader.py -range_trade TMF -account_type ira > TMF/$yyyymmdd/schwab_trader_range_trade.$hhmm.out 2>&1
31-59 9 * * 1-5 sleep 15; yyyymmdd=`date +\%Y\%m\%d`; hhmm=`date +\%H\%M`; cd /home/user/schwab; python schwab_trader.py -range_trade TMF -account_type ira > TMF/$yyyymmdd/schwab_trader_range_trade.$hhmm.out 2>&1
00-59 10-15 * * 1-5 sleep 15; yyyymmdd=`date +\%Y\%m\%d`; hhmm=`date +\%H\%M`; cd /home/user/schwab; python schwab_trader.py -range_trade TMF -account_type ira > TMF/$yyyymmdd/schwab_trader_range_trade.$hhmm.out 2>&1
```

In the example above, the first entry creates a dated directory for storing the output. This will provide a log of the day's trading. The account_type option is optional. If not specified, trades will be placed in your brokerage account. In the example above, trades are being placed in an IRA account.

### Sell Call Options in a Stock or ETF

To sell naked call options in a stock or ETF, first setup an option file with the settings for selling call options. The file name should be:

```
schwab_$STOCK_SYMBOL_sell_call_options.ini
```

where $STOCK_SYMBOL is the ticker of the ETF or stock you want to sell call options in. An example is provided in this repo for SPY:

```
schwab_SPY_sell_call_options.ini
```

Here's a description of the settings:

```
limit_price: Target price to sell to open an option contract for
min_limit_price: Minimum price to use when searching for a contract to sell
transition_time: Time in HHMM to transition to trading options for the next day
num_contracts: Number of contracts to sell to open per trade
max_contracts: Maximum number of contracts to own in account
```

Example option file for SPY:

```
limit_price: 0.17
min_limit_price: 0.14
transition_time: 1230
num_contracts: 3
max_contracts: 15
```

**How these settings are used in the code:**

Before 12:30 pm local time, the code will place orders for the current day. After 12:30 pm local time, the code will place orders for the next day.

The code will get option quotes for either the current day or the next trading day depending on the transition time. It will find the contract that has a bid price >= 0.14. The code will place an order to sell to open 3 contracts of SPY at 0.17 or at the ask price if the contract's ask price is > 0.17.

The number of new contracts to sell to open will not be allowed to exceed the max_contracts settings. For example, if your account already owns 15 contracts, then no new orders will be placed. If your account owns 13 contracts, your next order will be to sell to open 2 contracts.

**How does the code manage positions:**

Once an order is filled, the code will automatically place a buy to close order for 0.01 on the new position. The code will also place a new order at a strike price one point higher from the strike price that was filled. The new order will be placed for the current day if the current time is before the transition time or for the next trading day if the current time is after the transition time. After 4:09 pm ET, the code will automatically attempt to close any remaining open positions for the current trading day.

**How does the code handle stops:**

If the current price hits the strike price of an open position, then the position is immediately closed and rolled to a new position. The rolling depends on the time of day. If the current time is before the transition time, then the position is rolled to an option at the next highest strike price and one additional contract is sold to open. For example:

```
Current position:
3 647 Current Day calls

Current price:
647.10

Action:
Buy to Close 3 647 Current Day calls
Sell to Open 4 648 Current Day calls
```

If the current time is after the transition time, then the position is rolled to a contract for the next day at a premium that is at least as much as the cost of closing the position. For example:

```
Current position:
3 647 Current Day calls

Current price:
647.10

Action:
Buy to Close 3 647 Current Day calls at 0.65
Sell to Open 4 649 Next Trading Day calls at 0.70
```

In this example, it is assumed the position is closed for 0.65. The code will automatically loop through the options for the next day and find the one that provides at least as much premium as the cost of closing the current position. In this example, it is assumed that the 649 options were found.

When rolling positions, the number of contracts to sell to open will still be limited by the max_contracts setting.

Once your option file is setup, you can run the code to sell to open call options:

```
python schwab_trader.py -sell_call_options $STOCK_SYMBOL
```

Example for SPY:

```
python schwab_trader.py -sell_call_options SPY
```

There is also a percent_threshold option which can be set to determine the distance from the resistance level in which call options will be sold.

A file named $STOCK_SYMBOL_max.txt is used to track the all-time high or a resistance level of your choice. If the latest high of the day is greater than the current value in $STOCK_SYMBOL_max.txt then the value in the file will be updated with the high of the day.

Example of setting a percent threshold option:

```
python schwab_trader.py -sell_call_options SPY -percent_threshold 3.0
```

These options will sell calls in SPY as long as the current price is within 3% of the value in the SPY_max.txt file. If the percent_threshold option is not set, then a default of 1.5% is used.

Another feature of the code is that it reduces the number of contracts to sell to open as the price moves further away from the resistance level. For example, if you are set to sell to open 3 contracts per trade and the percent threshold is set to 3% then the code will:

- Sell 3 contracts if the price is within 1% of the resistance level
- Sell 2 contracts if the price is within 1%-2% of the resistance level
- Sell 1 contract if the price is within 2%-3% of the resistance level
- Not place any orders if the price is >3% from the resistance level

If you don't want to use the feature that reduces contracts to sell to open, then set the percent_threshold to a high number such that the price will always be well within the threshold.

Ideally, the code should be set to run once per minute throughout the trading day. Since the access token expires after 30 minutes, it's important that you make sure to update it throughout the trading day. Here are sample cron entries for updating the access tokens:

```
# Update Schwab Tokens every 20 minutes on trading days
20,40 9 * * 1-5 cd /home/user/schwab; python schwab_trader.py -get_tokens > schwab_trader_get_tokens.out 2>&1
00,20,40 10-15 * * 1-5 cd /home/user/schwab; python schwab_trader.py -get_tokens > schwab_trader_get_tokens.out 2>&1
00 16 * * 1-5 cd /home/user/schwab; python schwab_trader.py -get_tokens > schwab_trader_get_tokens.out 2>&1
```

and here are sample cron entries for selling call options throughout the day:

```
# Run code to sell SPY call options every minute of the trading day
30 9 * * 1-5 sleep 30; yyyymmdd=`date +\%Y\%m\%d`; hhmm=`date +\%H\%M`; cd /home/user/schwab; mkdir -p SPY/$yyyymmdd > /dev/null; python schwab_trader.py -sell_call_options SPY > SPY/$yyyymmdd/schwab_trader_sell_call_options.$hhmm.out 2>&1
31-59 9 * * 1-5 sleep 30; yyyymmdd=`date +\%Y\%m\%d`; hhmm=`date +\%H\%M`; cd /home/user/schwab; python schwab_trader.py -sell_call_options SPY > SPY/$yyyymmdd/schwab_trader_sell_call_options.$hhmm.out 2>&1
00-59 10-15 * * 1-5 sleep 30; yyyymmdd=`date +\%Y\%m\%d`; hhmm=`date +\%H\%M`; cd /home/user/schwab; python schwab_trader.py -sell_call_options SPY > SPY/$yyyymmdd/schwab_trader_sell_call_options.$hhmm.out 2>&1
00-14 16 * * 1-5 sleep 30; yyyymmdd=`date +\%Y\%m\%d`; hhmm=`date +\%H\%M`; cd /home/user/schwab; python schwab_trader.py -sell_call_options SPY > SPY/$yyyymmdd/schwab_trader_sell_call_options.$hhmm.out 2>&1
```

In the example above, the first entry creates a dated directory for storing the output. This will provide a log of the day's trading.
