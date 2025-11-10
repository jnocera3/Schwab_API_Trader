#!/usr/bin/python
import requests
import os
import sys
import base64
import configparser
import argparse
import datetime
import time
import holidays
import json
import math

# START FUNCTIONS

# Function to get tokens for API
def get_tokens(endpoint: str, token_file: str, config_file: str):

    #Read in variables from configuration files
    config = configparser.ConfigParser()
    config.read(config_file)
    app_key = config.get("myvars", "app_key")
    app_secret = config.get("myvars", "app_secret")
    config = configparser.ConfigParser()
    config.read(token_file)
    refresh_token = config.get("myvars", "refresh_token")

    #Define payload and headers
    payload = {"grant_type":"refresh_token",
               "refresh_token":refresh_token}
    headers = {
             "Authorization": f'Basic {base64.b64encode(f"{app_key}:{app_secret}".encode()).decode()}',
             "Content-Type": "application/x-www-form-urlencoded"}

    #Make request for new token
    content = requests.post(url = endpoint, headers = headers, data = payload)

    #Convert json to a dictionary
    auth = content.json()
    print (auth)
    print ("Access Token: " + auth["access_token"])
    print ("Refresh Token: " + auth["refresh_token"])

    #Define name of temporary token file
    token_temp = token_file + ".tmp"

    #Open temporary token file and write out new tokens
    auth_out = open(token_temp,"w+")
    auth_out.write('[myvars]\n')
    auth_out.write('refresh_token: ' + str(auth["refresh_token"]) + '\n')
    auth_out.write('access_token: ' + str(auth["access_token"]) + '\n')
    auth_out.close()

    #Move token file to final name
    os.rename(token_temp,token_file)


# Function to get values from a config file
def get_config_value(config_file: str, config_string: str):

    #Read variables from input file
    config = configparser.ConfigParser()
    config.read(config_file)
    return config.get("myvars", config_string)


# Function to get account hashes
def get_account_hashes(endpoint: str, access_token: str):

    # Define headers for request
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Make request to get account info
    content = requests.get(url = endpoint, headers = headers)

    # Open account hashes in JSON format
    print(json.dumps(content.json(),indent=4))


# Function to read settings from a config file
def read_settings(config_file: str):

    #Read variables from input file
    config = configparser.ConfigParser()
    config.read(config_file)
    return float(config.get("myvars", "limit_price")), float(config.get("myvars", "min_limit_price")), int(config.get("myvars", "transition_time")), int(config.get("myvars", "num_contracts")), int(config.get("myvars", "max_contracts"))


# Function to read range trade settings from a file
def read_settings_range_trade(option_file: str):

    # Initialize trade ranges dictionary
    trade_ranges = {}

    # Read variables from input file
    with open(option_file, 'r') as file:
        shares = int(file.readline().split(':')[1])
        max_shares = int(file.readline().split(':')[1])
        buying_power_ticker = file.readline().split(':')[1].strip()
        next(file)
        for line in file.readlines():
            trade_ranges[int(line.split(',')[0])] = [float(line.split(',')[1]), float(line.split(',')[2])]
    return shares, max_shares, buying_power_ticker, trade_ranges


# Function to get account balance
def get_account_info(endpoint: str, access_token: str, info_type: str, ticker="None", assetType=["OPTION"]):

    # Define headers for request
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Make request to get account info
    content = requests.get(url = endpoint, headers = headers)

    # Convert json to a dictionary
    if info_type == "balance":
        return content.json()['aggregatedBalance']['currentLiquidationValue']
    elif info_type == "positions":
        # Create dictionary for positions
        positions = {}
        #print(json.dumps(content.json()['securitiesAccount']['positions'],indent=4))
        #print(json.dumps(content.json(),indent=4))
        if assetType[0] == "OPTION":
            for pos in content.json()['securitiesAccount']['positions']:
                if pos['instrument']['assetType'].upper() == 'OPTION' and pos['instrument']['underlyingSymbol'].upper() == ticker:
                    symbol = pos['instrument']['symbol']
                    positions[symbol] = [int(pos['shortQuantity']), round(float(pos['marketValue'])*0.01,3)]
            return positions
        else:
            for pos in content.json()['securitiesAccount']['positions']:
                if pos['instrument']['assetType'].upper() == 'COLLECTIVE_INVESTMENT' and (pos['instrument']['symbol'] == ticker or pos['instrument']['symbol'] == assetType[1]):
                    symbol = pos['instrument']['symbol']
                    positions[symbol] = int(pos['longQuantity'])
            buying_power = float(content.json()['securitiesAccount']['projectedBalances']['availableFunds'])
            return buying_power, positions

# Function to get quote
def get_quote(endpoint: str, access_token: str, ticker: str, quote_type="stock"):

    # Define headers for request
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Make request to get account info
    content = requests.get(url = endpoint, headers = headers)

    # Convert json to a dictionary
    if quote_type == "stock":
        return round((float(content.json()[ticker]['quote']['bidPrice'])+float(content.json()[ticker]['quote']['askPrice']))*0.5,3), float(content.json()[ticker]['quote']['highPrice']), float(content.json()[ticker]['quote']['lowPrice'])
    elif quote_type == "option":
        quotes = {}
        for exp_date in content.json()['callExpDateMap']:
            for strike_price in content.json()['callExpDateMap'][exp_date]:
                # Extract option symbol
                symbol = content.json()['callExpDateMap'][exp_date][strike_price][0]['symbol']
                # Compute limit price to pay for option as average of "ask" and "mark"
                quotes[symbol] = [content.json()['callExpDateMap'][exp_date][strike_price][0]["bid"], content.json()['callExpDateMap'][exp_date][strike_price][0]["ask"]]
               
        return quotes

# Function to get current orders
def get_orders(endpoint: str, access_token: str, order_date: str, status: str, assetType="OPTION"):

    # Define headers for request
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Add start and end time to endpoint
    endpoint = endpoint + "?fromEnteredTime=" + order_date + "T04:00:00.000Z&toEnteredTime=" + order_date + "T23:00:00.000Z"

    # Make request to get account info
    content = requests.get(url = endpoint, headers = headers)

    # Initialize orders dictionary
    orders = {}

    # Loop through orders
    for order in content.json():
        #print(json.dumps(order,indent=4))
        # Store order status requested
        if order["status"].upper() == status and order["orderLegCollection"][0]["orderLegType"].upper() == assetType:
            # Store order
            orders[order["orderId"]] = [order["orderLegCollection"][0]["instrument"]["symbol"], order["orderLegCollection"][0]["instruction"], int(order["quantity"]), float(order["price"])]

    # Return the orders
    return orders

# Function to cancel an order
def cancel_order(endpoint: str, access_token: str, order_id: str):

    # Define headers for request
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Add start and end time to endpoint
    endpoint = endpoint + "/" + order_id

    # Make request to delete to cancel the order
    content = requests.delete(url = endpoint, headers = headers)

    #Return status code
    return content.status_code

# Function to place and order
def place_order(
    endpoint,
    access_token,
    symbol,
    order_type,
    instruction,
    quantity,
    order_leg_type,
    asset_type,
    position_effect,
    leg_id=0,
    price=None,
    session="NORMAL",
    duration="DAY",
    complex_order_strategy_type="NONE",
    tax_lot_method="FIFO",
    order_strategy_type="SINGLE",
    special_instructions="NONE"
):

    order_payload = {
        "price": price,
        "session": session,
        "duration": duration,
        "orderType": order_type,
        "complexOrderStrategyType": complex_order_strategy_type,
        "quantity": quantity,
        "taxLotMethod": tax_lot_method,
        "orderLegCollection": [
            {
                "orderLegType": order_leg_type,
                "legId": leg_id,
                "instrument": {
                    "symbol": symbol,
                    "assetType": asset_type,
                },
                "instruction": instruction,
                "positionEffect": position_effect,
                "quantity": quantity,
            }
        ],
        "orderStrategyType": order_strategy_type,
    }

#   Add special instructions if provided
    if special_instructions != "NONE":
        order_payload["specialInstruction"] = special_instructions

    # Define headers for request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "accept": "*/*",
        "Content-Type": "application/json"
    }

    # Make request to get account info
    content = requests.post(url = endpoint, headers = headers, data = json.dumps(order_payload))
    return content.status_code

# Function to resistance level high and update it, if necessary
def get_resistance_level(max_file: str, highofday: float):

    # Attempt to read current MAX from file
    if os.path.exists(max_file):
        with open(max_file, 'r') as file:
            resistance_level = float(file.readline())
    else:
        resistance_level = 0.0

    # Check to see if new resistence level set
    if highofday > resistance_level:
        resistance_level = highofday
        with open(max_file, 'w') as file:
            file.write(str(resistance_level) + "\n")

    # Return the resistence level
    return resistance_level

# Function to get list of holidays for years input
def get_holidays(years: list):

    return holidays.financial_holidays('NYSE', years=years)


# END FUNCTIONS

# BEGIN MAIN CODE

# Define endpoints
trading_endpoint = r"https://api.schwabapi.com/trader/v1"
marketdata_endpoint = r"https://api.schwabapi.com/marketdata/v1"
token_endpoint = r"https://api.schwabapi.com/v1/oauth/token"

# Define configuration file containing access token
token_file = "schwab_tokens.ini"

# Define configuation file containing hash of account numbers
config_file = "schwab_config.ini"

# Argument Parsing
parser = argparse.ArgumentParser()

# Read in arguments
parser.add_argument("-get_tokens","--get_tokens", action='store_true', help='Get an updated access token.')
parser.add_argument("-get_account_hashes","--get_account_hashes", action='store_true', help='Get hash value for all accounts returned in JSON format.')
parser.add_argument("-get_balance","--get_balance", action='store_true', help='Get current account balance. Use account_type option to set the account. Default is brokerage.')
parser.add_argument("-account_type","--account_type", required=False, default="brokerage", help='Account type to grab balance or place trades for. Options are ira or brokerage. Default is brokerage.')
parser.add_argument("-get_quote","--get_quote", required=False, default="None", help='Ticker Symbol to get quote for. Result will be stored in ${TickerSymbol}.csv. Default is None (No quote requested).')
parser.add_argument("-sell_call_options","--sell_call_options", required=False, default="None", help='Ticker Symbol to sell call options for. Default is None. If set, this will automatically get a quote for the ticker. A threshold for %% from resistance level can be set with the -percent_threshold option. The default threshold is 1.5%%. Option file schwab_$ticker_sell_call_options.ini is required.')
parser.add_argument("-percent_threshold","--percent_threshold", required=False, default=1.5, help='Percent threshold from resistance level in which options trading is allowed. If outside this threshold, no new option trades will be placed. Default is 1.5.')
parser.add_argument("-range_trade","--range_trade", required=False, default="None", help='Ticker Symbol to range trade for. Default is None. Option file schwab_$ticker_range_trade.ini with settings for trading is required.')

# Parse the input
args = parser.parse_args()

# Check to see if new token should be grabbed
if args.get_tokens:

    # Get updated tokens
    get_tokens(token_endpoint, token_file, config_file)

# Make sure account type is all lower case
account_type = args.account_type.lower()

# Get latest access token
access_token = get_config_value(token_file, "access_token")

# Check to see if account hashes should be grabbed
if args.get_account_hashes:

    # Define endpint for getting account hashes
    endpoint = trading_endpoint + "/accounts/accountNumbers"

    # Get account hashes
    get_account_hashes(endpoint, access_token)

# Check to see if account balance is requested.
if args.get_balance:

    # Get current date
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")

    # Get account type hash
    account_hash = get_config_value(config_file, account_type)

    # Define endpoint for account balance
    endpoint = trading_endpoint + "/accounts/" + account_hash

    # Get account balance
    account_balance = get_account_info(endpoint, access_token, "balance")

    # Write out account balance
    print(account_type + " account balance:")
    print(str(timestamp) + ", " + str(account_balance))

    # Define name of file to output balance to
    balance_file = "schwab_" + account_type + "_balance.csv"

    # Append account balance to a file
    balance_out = open(balance_file,"a")
    balance_out.write(str(timestamp) + ", " + str(account_balance) + "\n")
    balance_out.close()

# Set ticker to use for quote and/or options trading
if args.sell_call_options != "None":
    ticker = args.sell_call_options
elif args.get_quote != "None": 
    ticker = args.get_quote
else:
    ticker = "None"

# Check to see if quote requested.
if ticker != "None":

    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Defined endpoint for quote
    endpoint = marketdata_endpoint + "/quotes?symbols=" + ticker + "&fields=quote&indicative=false"

    # Get quote
    current, highofday, lowofday = get_quote(endpoint, access_token, ticker)

    # Define name of file containing resistence level
    max_file = ticker + "_max.txt"

    # Get resistance level
    resistance_level = get_resistance_level(max_file, highofday)

    # Informational Print
    print(ticker + " quotes valid at " + timestamp + ":")
    print("Current Price:     " + str(current))
    print("High of Day:       " + str(highofday))
    print("Low of Day:        " + str(lowofday))
    print("Resistance Level:  " + str(resistance_level))

# Check for range trading
if args.range_trade != "None":

    # Define file containing settings for range trading
    settings_file = "schwab_" + args.range_trade + "_range_trade.ini"

    # Check to make sure settings file is present
    if not os.path.exists(settings_file):
        print("Option file: " + settings_file + " does not exist. Exiting")
        sys.exit(1)

    # Read variables from settings file
    trade_shares, max_shares, buying_power_ticker, trade_ranges = read_settings_range_trade(settings_file)

    # Define current day, trading day and set year to pull holidays for
    current_yyyymmdd = datetime.datetime.now().strftime("%Y%m%d")
    this_year = current_yyyymmdd[0:4]
    year_list = [this_year]
    current_trading_day = current_yyyymmdd[0:4] + "-" + current_yyyymmdd[4:6] + "-" + current_yyyymmdd[6:8]

    # Call function to get list of holidays for this year and next year
    holiday_dates = get_holidays(year_list)

    # Check if current day is a holiday
    if datetime.datetime.now() in holiday_dates:
        print("Today is a market holiday. No trading today. Exiting")
        sys.exit(1)

    # Get account type hash
    account_hash = get_config_value(config_file, account_type)

    # Define endpoint for orders
    orders_endpoint = trading_endpoint + "/accounts/" + account_hash + "/orders"

    # Get all current open orders
    current_open_orders = get_orders(orders_endpoint, access_token, current_trading_day, "WORKING", "EQUITY")

    # Define endpoint for account positions
    account_endpoint = trading_endpoint + "/accounts/" + account_hash + "?fields=positions"

    # Get list of current stock positions
    buying_power, account_positions = get_account_info(account_endpoint, access_token, "positions", args.range_trade, ["stock", buying_power_ticker])
    print("Account Buying Power: " + str(buying_power))
    if buying_power_ticker not in account_positions:
        account_positions[buying_power_ticker] = 0
    if args.range_trade not in account_positions:
        account_positions[args.range_trade] = 0
    print(buying_power_ticker + " shares owned: " + str(account_positions[buying_power_ticker]))
    print(args.range_trade + " shares owned: " + str(account_positions[args.range_trade]))

    # Defined endpoint for quote
    quote_endpoint = marketdata_endpoint + "/quotes?symbols=" + args.range_trade + "&fields=quote&indicative=false"
    # Get latest quote for range trade ticker
    current, highofday, lowofday = get_quote(quote_endpoint, access_token, args.range_trade)
    print(args.range_trade + " Current Price: " + str(current))
    print(args.range_trade + " High of Day:   " + str(highofday))
    print(args.range_trade + " Low of Day:    " + str(lowofday))

    # Construct orders to place based on current share count
    orders = {}
    if account_positions[args.range_trade] == 0:
        # Buy Order Only
        max_shares_to_own = max_shares
        for shares in trade_ranges:
            if current >= trade_ranges[shares][0]:
                max_shares_to_own = shares - trade_shares
                break
        if max_shares_to_own > trade_shares:
            orders[0] = [args.range_trade, "BUY", max_shares_to_own, trade_ranges[max_shares_to_own][0]]
        else:
            orders[0] = [args.range_trade, "BUY", trade_shares, trade_ranges[account_positions[args.range_trade] + trade_shares][0]]
        num_orders = 1
    elif account_positions[args.range_trade] >= max_shares:
        # Sell Order Only
        max_shares_to_own = 0
        for shares in trade_ranges:
            if current <= trade_ranges[shares][1]:
                max_shares_to_own = shares + trade_shares
        max_shares_to_trade = max_shares - max_shares_to_own
        if max_shares_to_trade > trade_shares:
            if max_shares_to_own == 0:
                orders[0] = [args.range_trade, "SELL", max_shares_to_trade, trade_ranges[trade_shares][1]]
            else: 
                orders[0] = [args.range_trade, "SELL", max_shares_to_trade, trade_ranges[max_shares_to_own][1]]
        else:
            orders[0] = [args.range_trade, "SELL", trade_shares, trade_ranges[max_shares][1]]
        num_orders = 1
    else:
        # Sell Order
        max_shares_to_own = 0
        for shares in trade_ranges:
            if current <= trade_ranges[shares][1]:
                max_shares_to_own = shares + trade_shares
        max_shares_to_trade = account_positions[args.range_trade] - max_shares_to_own
        if max_shares_to_trade > trade_shares:
            if max_shares_to_own == 0:
                orders[0] = [args.range_trade, "SELL", max_shares_to_trade, trade_ranges[trade_shares][1]]
            else:
                orders[0] = [args.range_trade, "SELL", max_shares_to_trade, trade_ranges[max_shares_to_own][1]]
        else:
            orders[0] = [args.range_trade, "SELL", trade_shares, trade_ranges[account_positions[args.range_trade]][1]]
        # Buy Order
        max_shares_to_own = max_shares
        for shares in trade_ranges:
            if current >= trade_ranges[shares][0]:
                 max_shares_to_own = shares - trade_shares
                 break
        max_shares_to_trade = max_shares_to_own - account_positions[args.range_trade]
        if max_shares_to_trade > trade_shares:
            orders[1] = [args.range_trade, "BUY", max_shares_to_trade, trade_ranges[max_shares_to_own][0]]
        else:
            orders[1] = [args.range_trade, "BUY", trade_shares, trade_ranges[account_positions[args.range_trade] + trade_shares][0]]
        num_orders = 2

    # Write out current open orders, if any
    if current_open_orders:
        print ("\nCurrent Open Orders:")
        for current_order in current_open_orders:
            print("\nOrder ID: " + str(current_order))
            print("Symbol: " + current_open_orders[current_order][0])
            print("Instruction: " + current_open_orders[current_order][1])
            print("#Shares: " + str(current_open_orders[current_order][2]))
            print("Price: " + str(current_open_orders[current_order][3]))
            # Loop over orders to place
            for order in range(num_orders):
                # Delete order to place if already in place
                if order in orders:
                    if orders[order][0] == current_open_orders[current_order][0] and orders[order][1] == current_open_orders[current_order][1] and orders[order][2] == current_open_orders[current_order][2] and math.isclose(orders[order][3],current_open_orders[current_order][3]):
                        del orders[order]

    # Loop over orders to place
    for order in orders:
        # Check on order type
        # BUY order
        if orders[order][1] == "BUY":
            # Cancel any buy orders that are currently in place
            for current_order in current_open_orders:
                # Check for matching buy order
                if orders[order][0] == current_open_orders[current_order][0] and orders[order][1] == current_open_orders[current_order][1] and orders[order][2] == current_open_orders[current_order][2]:
                    order_status = cancel_order(orders_endpoint,access_token,str(current_order))
                    # Check order status
                    if order_status == 200:
                        print ("Canceled previous " + orders[order][1] + " order for: " + orders[order][0] + " successfully\n")
                    else:
                        print ("FAILED to cancel previous " + orders[order][1] + " order for: " + orders[order][0] + "\n")
            # Compute needed buying power
            needed_buying_power = float(orders[order][2]) * orders[order][3] - buying_power
            # Defined endpoint for quote
            quote_endpoint = marketdata_endpoint + "/quotes?symbols=" + buying_power_ticker + "&fields=quote&indicative=false"
            # Get latest quote for buying power ticker
            current, highofday, lowofday = get_quote(quote_endpoint, access_token, buying_power_ticker)
            # Compute number of shares needed to sell to raise buying power
            if needed_buying_power > 0.0:
                sell_shares = int(needed_buying_power / highofday) + 1
                # Place market order to sell to raise buying power
                print ("Placing market order to sell " + str(sell_shares) + " shares of " + buying_power_ticker)
                order_status = place_order(
                               endpoint=orders_endpoint,
                               access_token=access_token,
                               symbol=buying_power_ticker, 
                               order_type="MARKET", 
                               instruction="SELL", 
                               quantity=sell_shares,
                               order_leg_type="EQUITY",
                               asset_type="EQUITY",
                               position_effect="CLOSING")
                # Check order status
                if order_status == 201:
                    print ("Order successfully placed to sell " + str(sell_shares) + " shares of " + buying_power_ticker)
                    # Compute needed buying power to buy shares
                    needed_buying_power = float(orders[order][2]) * orders[order][3]
                    # Loop to see if order has been filled and buying power has increased
                    for i in range(7):
                        print("Sleeping 5 seconds. Waiting for market order to be filled")
                        time.sleep(5)
                        buying_power, account_positions = get_account_info(account_endpoint, access_token, "positions", args.range_trade, ["stock", buying_power_ticker])
                        if buying_power >= needed_buying_power:
                            print ("Order to sell " + str(sell_shares) + " shares of " + buying_power_ticker + " has been filled. \nPlacing order to buy " + str(orders[order][2]) + " shares of " + orders[order][0] + " at limit price of " + str(orders[order][3]))
                            order_status = place_order(
                                           endpoint=orders_endpoint,
                                           access_token=access_token,
                                           symbol=orders[order][0],
                                           order_type="LIMIT", 
                                           instruction=orders[order][1],
                                           quantity=orders[order][2],
                                           order_leg_type="EQUITY",
                                           asset_type="EQUITY",
                                           position_effect="OPENING",
                                           price=orders[order][3],
                                           special_instructions="ALL_OR_NONE")
                            # Check order status
                            if order_status == 201:
                                print ("Order successfully placed to buy " + str(orders[order][2]) + " shares of " + orders[order][0] + " at limit price of " + str(orders[order][3]))
                            else:
                                print ("FAILED to place order to buy " + str(orders[order][2]) + " shares of " + orders[order][0] + " at limit price of " + str(orders[order][3]))
                            # Exit from loop
                            break
                else:
                    print ("FAILED to place order to sell " + str(sell_shares) + " shares of " + buying_power_ticker)
            else:
                print ("Placing order to buy " + str(orders[order][2]) + " shares of " + orders[order][0] + " at limit price of " + str(orders[order][3]))
                order_status = place_order(
                               endpoint=orders_endpoint,
                               access_token=access_token,
                               symbol=orders[order][0],
                               order_type="LIMIT", 
                               instruction=orders[order][1],
                               quantity=orders[order][2],
                               order_leg_type="EQUITY",
                               asset_type="EQUITY",
                               position_effect="OPENING",
                               price=orders[order][3],
                               special_instructions="ALL_OR_NONE")
                # Check order status
                if order_status == 201:
                    print ("Order successfully placed to buy " + str(orders[order][2]) + " shares of " + orders[order][0] + " at limit price of " + str(orders[order][3]))
                else:
                    print ("FAILED to place order to buy " + str(orders[order][2]) + " shares of " + orders[order][0] + " at limit price of " + str(orders[order][3]))

        # SELL order
        elif orders[order][1] == "SELL":
            print ("Placing order to sell " + str(orders[order][2]) + " shares of " + orders[order][0] + " at limit price of " + str(orders[order][3]))
            order_status = place_order(
                           endpoint=orders_endpoint,
                           access_token=access_token,
                           symbol=orders[order][0],
                           order_type="LIMIT", 
                           instruction=orders[order][1],
                           quantity=orders[order][2],
                           order_leg_type="EQUITY",
                           asset_type="EQUITY",
                           position_effect="OPENING",
                           price=orders[order][3],
                           special_instructions="ALL_OR_NONE")
            # Check order status
            if order_status == 201:
                print ("Order successfully placed to sell " + str(orders[order][2]) + " shares of " + orders[order][0] + " at limit price of " + str(orders[order][3]))
            else:
                print ("FAILED to place order to sell " + str(orders[order][2]) + " shares of " + orders[order][0] + " at limit price of " + str(orders[order][3]))

    # Get current time, HHMM
    hhmm = int(datetime.datetime.now().strftime("%H%M"))

    # At end of trading day, use any remaining buying power to buy shares of BIL.
    if hhmm == 1559:
        # Get latest buying power
        buying_power, account_positions = get_account_info(account_endpoint, access_token, "positions", args.range_trade, ["stock", buying_power_ticker])
        print("\nLatest Account Buying Power: " + str(buying_power))
        # Defined endpoint for quote
        quote_endpoint = marketdata_endpoint + "/quotes?symbols=" + buying_power_ticker + "&fields=quote&indicative=false"
        # Get latest quote for buying power ticker
        current, highofday, lowofday = get_quote(quote_endpoint, access_token, buying_power_ticker)
        print(buying_power_ticker + " latest quote: " + str(current))
        # Compute number of shares to buy
        buy_shares = int(buying_power / highofday)
        if buy_shares > 0:
            # Place market order to buy shares
            print ("Placing market order to buy " + str(buy_shares) + " shares of " + buying_power_ticker)
            order_status = place_order(
                           endpoint=orders_endpoint,
                           access_token=access_token,
                           symbol=buying_power_ticker, 
                           order_type="MARKET", 
                           instruction="BUY", 
                           quantity=buy_shares,
                           order_leg_type="EQUITY",
                           asset_type="EQUITY",
                           position_effect="OPENING")
            # Check order status
            if order_status == 201:
                print ("Order successfully placed to buy " + str(buy_shares) + " shares of " + buying_power_ticker)
            else:
                print ("FAILED to place order to buy " + str(buy_shares) + " shares of " + buying_power_ticker)


# Check for options trading
if args.sell_call_options != "None":

    # Define file containing settings for selling call options
    settings_file = "schwab_" + ticker + "_sell_call_options.ini"

    # Check to make sure settings file is present
    if not os.path.exists(settings_file):
        print("Option file: " + settings_file + " does not exist. Exiting")
        sys.exit(1)

    # Read variables from settings file
    trade_price, min_trade_price, transition_time, trade_contracts, max_contracts = read_settings(settings_file)

    # Set years to pull holidays for. Handle holidays beginning in the new year
    this_year = datetime.datetime.now().strftime("%Y")
    next_year = (datetime.datetime.now() + datetime.timedelta(days=10)).strftime("%Y")
    year_list = [this_year, next_year]

    # Call function to get list of holidays for this year and next year
    holiday_dates = get_holidays(year_list)

    # Check if current day is a holiday
    if datetime.datetime.now() in holiday_dates:
        print("Today is a market holiday. No trading today. Exiting")
        sys.exit(1)
    else:
        current_trading_day = datetime.datetime.now().strftime("%Y-%m-%d")

    # Check day of week and set next trading day
    if datetime.datetime.now().weekday() == 4:
        next_trading_day = datetime.datetime.now() + datetime.timedelta(days=3)
    else:
        next_trading_day = datetime.datetime.now() + datetime.timedelta(days=1)

    # Check if the next trading day is a holiday
    if next_trading_day in holiday_dates:
        # Push ahead to next trading day
        if next_trading_day.weekday() == 4:
            next_trading_day = next_trading_day + datetime.timedelta(days=3)
        else:
            next_trading_day = next_trading_day + datetime.timedelta(days=1)

    # Convert next trading day into a string
    next_trading_day = next_trading_day.strftime("%Y-%m-%d")

    # Define current and next trading day in yyyymmdd and yymmdd format
    current_parts = current_trading_day.split("-")
    current_yyyymmdd = current_parts[0] + current_parts[1] + current_parts[2]
    current_yymmdd = current_yyyymmdd[2:]
    next_parts = next_trading_day.split("-")
    next_yymmdd = next_parts[0][2:] + next_parts[1] + next_parts[2]

    # Create directory to store logs, if it doesn't exist
    os.makedirs(ticker + "/" + current_yyyymmdd, exist_ok=True)

    # Define path to order log file
    order_log = ticker + "/" + current_yyyymmdd + "/orders.json"

    # Read order log if it exists
    if os.path.exists(order_log):
        with open(order_log, "r") as file:
            stored_orders = json.load(file)
    else:
        stored_orders = {}

    # Defined endpoint for options quotes
    endpoint = marketdata_endpoint + "/chains?symbol=" + ticker + "&contractType=CALL&strikeCount=24&fromDate=" + current_trading_day + "&toDate=" + next_trading_day

    # Get call options quotes
    option_quotes = get_quote(endpoint, access_token, ticker, "option")
    #print(option_quotes)

    # Compute % below resistance level
    percent_below = ((resistance_level - current) / resistance_level) * 100.0
    print("%Below Resistance: " + str(round(percent_below,3)) + "\n")

    # Set flag for selling call options
    if percent_below <= float(args.percent_threshold):
        options_trading = True
    else:
        options_trading = False

    # Adjust number of contracts to trade based on how close to resistance level
    trade_level_one = float(args.percent_threshold) * 0.3333333
    trade_level_two = float(args.percent_threshold) * 0.6666667
    # Reduce contracts by 1/3
    if percent_below > trade_level_one and percent_below <= trade_level_two:
        trade_contracts = int(float(trade_contracts) * 0.66) + 1
    elif percent_below > trade_level_two and percent_below <= float(args.percent_threshold):
        trade_contracts = int(float(trade_contracts) * 0.33) + 1
    elif percent_below > float(args.percent_threshold):
        trade_contracts = 0

    # Get current time, HHMM
    hhmm = int(datetime.datetime.now().strftime("%H%M"))

    # Get account type hash
    account_hash = get_config_value(config_file, account_type)

    # Define endpoint for account positions
    endpoint = trading_endpoint + "/accounts/" + account_hash + "?fields=positions"

    # Get list of current options positions
    account_positions = get_account_info(endpoint, access_token, "positions", ticker)
    #print(account_positions)

    # Initialize total contracts open or with orders in place to zero
    total_contracts = 0

    # Define endpoint for orders
    orders_endpoint = trading_endpoint + "/accounts/" + account_hash + "/orders"

    # Get all current open orders
    current_open_orders = get_orders(orders_endpoint, access_token, current_trading_day, "WORKING")

    # Write out current open orders, if any
    if current_open_orders:
        print ("Current Open Orders:")
        for order in current_open_orders:
            print("Order ID: " + str(order))
            print("Symbol: (" + current_open_orders[order][0] + ")")
            print("Instruction: " + current_open_orders[order][1])
            print("#Contracts: " + str(current_open_orders[order][2]))
            # Add contracts to total contracts if order still open
            for symbol in stored_orders:
                if symbol == current_open_orders[order][0] and stored_orders[symbol][0] == current_open_orders[order][1] and stored_orders[symbol][1] == current_open_orders[order][2] and stored_orders[symbol][2] == "WORKING":
                    total_contracts = total_contracts + current_open_orders[order][2]

    # Loop over current positions and total up number of contracts in play
    for key in account_positions:
        # Add contracts to total contracts
        total_contracts = total_contracts + account_positions[key][0]

    # Loop over current positions and check if any should be closed
    for key in account_positions:
        # Extract out strike price
        strike_price = float(key.split()[1][9:12])
        # Extract out expiration date
        expiration_date = key.split()[1][0:6]
        # Compute current market price for option contract
        option_market_price = (-1.0 * account_positions[key][1]) / account_positions[key][0]
        # Write out info on option contract
        print ("\n" + ticker + " Option Position Info:")
        print ("Symbol: (" + key + ")")
        print ("Expiration Date: " + expiration_date)
        print ("Strike Price: " + str(strike_price))
        print ("#Contracts: " + str(account_positions[key][0]))
        print ("Market Price: " + str(round(option_market_price,3)))
        if key in option_quotes:
            print ("Bid Price: " + str(option_quotes[key][0]))
            print ("Ask Price: " + str(option_quotes[key][1]) + "\n")
        else:
            print ("")
        # Close option position, if strike price exceeded or option about to expire
        if current > strike_price or (current_yymmdd == expiration_date and hhmm >= 1610):
            # Loop over current open orders
            for order in current_open_orders:
                if current_open_orders[order][0] == key and current_open_orders[order][1] == "BUY_TO_CLOSE":
                    order_status = cancel_order(orders_endpoint,access_token,str(order))
                    # Check order status
                    if order_status == 200:
                        print ("Canceled previous order for: (" + key + ") successfully\n")
                    else:
                        print ("FAILED to cancel previous order for (" + key + ")\n")
            # Set limit price to close option
            limit_price = round(option_quotes[key][1] - 0.33 * (option_quotes[key][1] - option_quotes[key][0]),2)
            # Output what position is being closed
            print ("Placing order to buy to close: (" + key + ") at limit price of " + str(limit_price))
            order_status = place_order(
                           endpoint=orders_endpoint,
                           access_token=access_token,
                           symbol=key, 
                           order_type="LIMIT", 
                           instruction="BUY_TO_CLOSE", 
                           quantity=account_positions[key][0],
                           order_leg_type="OPTION",
                           asset_type="OPTION",
                           position_effect="CLOSING",
                           price=limit_price)
            # Check order status
            if order_status == 201:
                print ("Order successfully placed to buy to close: (" + key + ")")
                # If stopped out, check to see if order can be rolled to next strike price
                if current > strike_price:
                    # Compute contracts available
                    contract_avail = max_contracts - total_contracts - 1
                    # Check on number of contracts available
                    if contract_avail <= 0:
                        # Attempt to cancel any existing SELL_TO_OPEN orders 
                        # to free up contracts for trading
                        # Loop over current open orders
                        for order in current_open_orders:
                            # Check for SELL_TO_OPEN orders
                            if current_open_orders[order][1] == "SELL_TO_OPEN":
                                # Loop over stored orders to find matching order
                                for symbol in stored_orders:
                                    if symbol == current_open_orders[order][0] and stored_orders[symbol][0] == current_open_orders[order][1] and stored_orders[symbol][1] == current_open_orders[order][2] and stored_orders[symbol][2] == "WORKING":
                                        # Cancel order
                                        order_status = cancel_order(orders_endpoint,access_token,str(order))
                                        # Check order status
                                        if order_status == 200:
                                            print ("Canceled order for: (" + symbol + ") successfully\n")
                                            # Switch stored order status to CANCELED
                                            stored_orders[symbol][2] = "CANCELED"
                                            # Reduce the total number of contracts
                                            total_contracts = total_contracts - current_open_orders[order][2]
                                            # Update contracts available
                                            contract_avail = max_contracts - total_contracts - 1
                                        else:
                                            print ("FAILED to cancel for: (" + symbol + ")\n")
                    # Try to increment number of contracts by one
                    if contract_avail > 0:
                        roll_trade_contracts = account_positions[key][0] + 1
                        # Increment total contracts by one
                        total_contracts = total_contracts + 1
                    else:
                        roll_trade_contracts = account_positions[key][0]
                    # Initialize filled order flag to False
                    close_order_filled = False
                    # Loop to see if order to close has been filled
                    for i in range(7):
                        print("Sleeping 5 seconds. Waiting for buy to close order to be filled")
                        time.sleep(5)
                        # Get filled orders
                        current_filled_orders = get_orders(orders_endpoint, access_token, current_trading_day, "FILLED")
                        # Loop over orders
                        for order in current_filled_orders:
                            # Check to see if order has been filled
                            if current_filled_orders[order][0] == key and current_filled_orders[order][1] == "BUY_TO_CLOSE" and current_filled_orders[order][2] == account_positions[key][0]:
                                print ("Order to buy to close: (" + key + ") has been filled. Rolling option to next strike price above current price")
                                # Set strike price to trade
                                new_strike = int(current) + 1
                                # Place new order based on time of day
                                if hhmm > transition_time:
                                    # Trade next day
                                    # Find strike that provides at least as much premium as was closed
                                    for strike in range(new_strike+10, new_strike-1, -1):
                                        trade_symbol = key[0:6] + next_yymmdd + key[12:15] + str(strike) + key[18:]
                                        if option_quotes[trade_symbol][0] >= limit_price:
                                            break
                                else:
                                    # Trade same day that was closed
                                    trade_symbol = key[0:15] + str(new_strike) + key[18:]
                                # Set initial limit price to roll option
                                limit_price = round(option_quotes[trade_symbol][1] + 0.33 * (option_quotes[trade_symbol][1] - option_quotes[trade_symbol][0]),2)
                                # Output what order is being placed
                                print ("Placing order to sell to open " + str(roll_trade_contracts) + " contracts of : (" + trade_symbol + ") at limit price of " + str(limit_price))
                                order_status = place_order(
                                               endpoint=orders_endpoint,
                                               access_token=access_token,
                                               symbol=trade_symbol, 
                                               order_type="LIMIT", 
                                               instruction="SELL_TO_OPEN", 
                                               quantity=roll_trade_contracts,
                                               order_leg_type="OPTION",
                                               asset_type="OPTION",
                                               position_effect="OPENING",
                                               price=limit_price)
                                # Check order status
                                if order_status == 201:
                                    print ("Order successfully placed to sell to open: (" + trade_symbol + ")")
                                else:
                                    print ("FAILED to place order to sell to open: (" + trade_symbol + ")")
                                # Initialize filled order flag to False
                                open_order_filled = False
                                # Loop to see if order to roll has been filled
                                for i in range(5):
                                    print("Sleeping 2 seconds. Waiting for sell to open order to be filled")
                                    time.sleep(2)
                                    # Get filled orders
                                    current_filled_orders = get_orders(orders_endpoint, access_token, current_trading_day, "FILLED")
                                    # Loop over filled orders
                                    for fill_order in current_filled_orders:
                                        # Check to see if order has been filled
                                        if current_filled_orders[fill_order][0] == trade_symbol and current_filled_orders[fill_order][1] == "SELL_TO_OPEN" and current_filled_orders[fill_order][2] == roll_trade_contracts:
                                            print ("Order to sell to open: (" + trade_symbol + ") has been filled.")
                                            open_order_filled = True
                                    # If order has been filled exit loop
                                    if open_order_filled:
                                        break
                                    else:
                                        # Get all current open orders
                                        current_open_orders = get_orders(orders_endpoint, access_token, current_trading_day, "WORKING")
                                        # Loop over current open orders
                                        for open_order in current_open_orders:
                                            if current_open_orders[open_order][0] == trade_symbol and current_open_orders[open_order][1] == "SELL_TO_OPEN":
                                                order_status = cancel_order(orders_endpoint,access_token,str(open_order))
                                                # Check order status
                                                if order_status == 200:
                                                    print ("Canceled previous order for: (" + trade_symbol + ") successfully\n")
                                                    # Set limit price to one cent lower
                                                    limit_price = round(limit_price - 0.01,2)
                                                    # Output what order is being placed
                                                    print ("Placing order to sell to open " + str(roll_trade_contracts) + " contracts of : (" + trade_symbol + ") at limit price of " + str(limit_price))
                                                    order_status = place_order(
                                                                   endpoint=orders_endpoint,
                                                                   access_token=access_token,
                                                                   symbol=trade_symbol, 
                                                                   order_type="LIMIT", 
                                                                   instruction="SELL_TO_OPEN", 
                                                                   quantity=roll_trade_contracts,
                                                                   order_leg_type="OPTION",
                                                                   asset_type="OPTION",
                                                                   position_effect="OPENING",
                                                                   price=limit_price)
                                                    # Check order status
                                                    if order_status == 201:
                                                        print ("Order successfully placed to sell to open: (" + trade_symbol + ")")
                                                    else:
                                                        print ("FAILED to place order to sell to open: (" + trade_symbol + ")")
                                                else:
                                                    print ("FAILED to cancel previous order for (" + trade_symbol + ")\n")
                                # Write out message if order not filled
                                if not open_order_filled:
                                    print ("Order to sell to open: (" + trade_symbol + ") not filled.")
                                # Set close order filled to True
                                close_order_filled = True
                        # If order has been filled exit loop
                        if close_order_filled:
                            break
                    # Write out message if order not filled
                    if not close_order_filled:
                        print ("Order to buy to close: (" + key + ") not filled.")

            else:
                print ("FAILED to place order to buy to close: (" + key + ")")

    # Cancel any current open orders for today's contracts if past the transition time
    if hhmm > transition_time:
        # Loop over current open orders
        for order in current_open_orders:
            # Check for matching date
            if current_yymmdd == current_open_orders[order][0].split()[1][0:6] and current_open_orders[order][1] == "SELL_TO_OPEN":
                # Loop over stored orders to find matching order
                for symbol in stored_orders:
                    if symbol == current_open_orders[order][0] and stored_orders[symbol][0] == current_open_orders[order][1] and stored_orders[symbol][1] == current_open_orders[order][2] and stored_orders[symbol][2] == "WORKING":
                        # Cancel order
                        order_status = cancel_order(orders_endpoint,access_token,str(order))
                        # Check order status
                        if order_status == 200:
                            print ("Canceled order for: (" + symbol + ") successfully\n")
                            # Switch stored order status to CANCELED
                            stored_orders[symbol][2] = "CANCELED"
                            # Reduce the total number of contracts
                            total_contracts = total_contracts - current_open_orders[order][2]
                        else:
                            print ("FAILED to cancel for: (" + symbol + ")\n")

    # Write out total number of contracts in play
    print ("Total Contracts: " + str(total_contracts))

    # Compute difference between max_contracts and total contracts
    contract_diff = max_contracts - total_contracts

    # Update number of contracts to trade, if necessary
    if contract_diff <= 0:
        # Turn off ability to add additional positions
        options_trading = False
    elif contract_diff < trade_contracts:
        trade_contracts = contract_diff

    # Check whether to continue with trading or not
    if options_trading:
        print ("\n%Below Resistance <= Threshold Value of " + str(float(args.percent_threshold)) + ". Will attempt to add options positions.\n")

        # Initialize trade symbol to None
        trade_symbol = "None"

        # Get all current filled orders
        current_filled_orders = get_orders(orders_endpoint, access_token, current_trading_day, "FILLED")

        # Write out current filled orders, if any
        if current_filled_orders:
            print ("Current Filled Orders:")
            for order in current_filled_orders:
                print("Order ID: " + str(order))
                print("Symbol: (" + current_filled_orders[order][0] + ")")
                print("Instruction: " + current_filled_orders[order][1])
                print("#Contracts: " + str(current_filled_orders[order][2]))
                # Check to see if any of today's orders have been filled
                for symbol in stored_orders:
                    if symbol == current_filled_orders[order][0] and stored_orders[symbol][0] == current_filled_orders[order][1] and stored_orders[symbol][1] == current_filled_orders[order][2] and stored_orders[symbol][2] == "WORKING":
                        # Switch stored order status to FILLED
                        stored_orders[symbol][2] = "FILLED"
                        # Output what position is being closed
                        print ("Placing order to buy to close: (" + symbol + ") at limit price of 0.01")
                        # Place limit order to close position at limit price of 0.01
                        order_status = place_order(
                                       endpoint=orders_endpoint,
                                       access_token=access_token,
                                       symbol=symbol, 
                                       order_type="LIMIT", 
                                       instruction="BUY_TO_CLOSE", 
                                       quantity=stored_orders[symbol][1],
                                       order_leg_type="OPTION",
                                       asset_type="OPTION",
                                       position_effect="CLOSING",
                                       price=0.01,
                                       duration="GOOD_TILL_CANCEL")
                        # Check order status
                        if order_status == 201:
                            print ("Order successfully placed to buy to close: (" + symbol + ")")
                        else:
                            print ("FAILED to place order to buy to close: (" + symbol + ")")
                        # Place new order based on time of day
                        if hhmm > transition_time:
                            # Trade next day
                            # Loop over option quotes
                            for symbol in sorted(option_quotes):
                                # Check for matching date
                                if next_yymmdd == symbol.split()[1][0:6] and option_quotes[symbol][1] <= min_trade_price:
                                    # Set symbol to trade
                                    trade_symbol = symbol
                                    # Exit loop
                                    break
                        else:
                            # Trade current day
                            # Increment strike price by one
                            new_strike = int(symbol[15:18]) + 1
                            trade_symbol = symbol[0:15] + str(new_strike) + symbol[18:]

        # Initialize new_trade to True
        new_trade = True
        # Check to see if new order should be placed
        if trade_symbol == "None":
            # Set trade date based on whether trading current day or next day
            if hhmm > transition_time:
                trade_date = next_yymmdd
            else:
                trade_date = current_yymmdd
            # Check to see if trade already made for this day
            for symbol in stored_orders:
                # If matching date found, exit loop
                if trade_date == symbol.split()[1][0:6]:
                    new_trade = False
                    break
            # Set trade symbol if new trade should be placed
            if new_trade:
                for symbol in sorted(option_quotes):
                    # Check for matching date
                    if trade_date == symbol.split()[1][0:6] and option_quotes[symbol][0] >= min_trade_price:
                        # Set symbol to trade
                        trade_symbol = symbol

        # Place order if symbol found
        if trade_symbol != "None":
            # Set limit price for order
            if option_quotes[trade_symbol][1] > trade_price:
                limit_price = option_quotes[trade_symbol][1]
            else:
                limit_price = trade_price
            #limit_price = 2.00
            # Output what order is being placed
            print ("Placing order to sell to open " + str(trade_contracts) + " contracts of : (" + trade_symbol + ") at limit price of " + str(limit_price))
            order_status = place_order(
                           endpoint=orders_endpoint,
                           access_token=access_token,
                           symbol=trade_symbol, 
                           order_type="LIMIT", 
                           instruction="SELL_TO_OPEN", 
                           quantity=trade_contracts,
                           order_leg_type="OPTION",
                           asset_type="OPTION",
                           position_effect="OPENING",
                           price=limit_price)
            # Check order status
            if order_status == 201:
                print ("Order successfully placed to sell to open: (" + trade_symbol + ")")
                # Add order to stored orders as status WORKING
                stored_orders[trade_symbol] = ["SELL_TO_OPEN", trade_contracts, "WORKING"]
            else:
                print ("FAILED to place order to sell to open: (" + trade_symbol + ")")

    else:
        print ("\nWill not attempt to add options positions. Will only check on closing existing positions")
        if contract_diff <= 0:
            print("Total contracts in place: " + str(total_contracts) + " >= max contracts to trade: " + str(max_contracts) + ".")
        else:
            print ("\n%Below Resistance > Threshold Value of " + str(float(args.percent_threshold)) + ".")

    # Write any stored orders to order log
    with open(order_log, "w") as file:
        json.dump(stored_orders, file, indent=4)
