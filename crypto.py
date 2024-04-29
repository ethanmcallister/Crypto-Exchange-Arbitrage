import networkx as nx
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from itertools import permutations, combinations
import json
import requests
from datetime import datetime
import alpaca_trade_api as api
import csv

BASE_URL = "https://paper-api.alpaca.markets"
KEY_ID = "PK914CBGHAJZBKQP8NMK"
SECRET_KEY = "3hDTujilOcjR1r2DhWB4Y6lP9AxMGkvIcNfLOBdd"


def make_alpaca_orders(path_list):

    # initialize the alpaca api
    alpaca = api.REST(key_id=KEY_ID, secret_key=SECRET_KEY, base_url=BASE_URL)

    usd_symbols = []
    
    # create purchase history list to be returned
    purchase_history = []
    
    # concatenate full symbol with USD at end
    for curr in path_list:
        symbol = curr.upper() + 'USD'
        usd_symbols.append(symbol)

        # buy and sell from each currency in the arbitrage chain
    for i in range(len(usd_symbols)):

        # order data
        symbol = usd_symbols[i]
        qty = '1'
        side = 'buy'
        type = 'market'
        time_in_force = 'gtc'

        # buy crypto
        order = alpaca.submit_order(symbol=symbol, qty=qty, side=side, type=type, time_in_force=time_in_force)
        print(f"buying {usd_symbols[i]}")
        purchase_history.append(f"buying {usd_symbols[i]}")

        # sell cypto
        side = 'sell'
        order = alpaca.submit_order(symbol=symbol, qty=qty, side=side, type=type, time_in_force=time_in_force)
        print(f"selling {usd_symbols[i]}\n")
        purchase_history.append(f"selling {usd_symbols[i]}")

    # account/account balance
    account = alpaca.get_account()
    account_cash = float(account.cash)
    print(f"\nBalance: {account_cash}")
    
    return purchase_history, account_cash


def main():
    
    # currencies/rates data (I removed polkadot and chainlink because placing their orders didn't seem to work with alpaca)
    currencies = {
        "aave": "aave", 
        "avalanche-2": "avax", 
        "bitcoin-cash": "bch", 
        "basic-attention-token": "bat", 
        "litecoin": "ltc", 
        "ethereum": "eth", 
        "bitcoin": "btc",
        "curve-dao-token": "crv",
        # "polkadot": "dot",
        "the-graph": "grt",
        # "chainlink": "link",
        "maker": "mkr",
        "shiba-inu": "shib",
        "uniswap": "uni",
        "tezos": "xtz"
        }

    # build url
    url1 = "https://api.coingecko.com/api/v3/simple/price?ids="
    url2 = "&vs_currencies="

    curr_string = "" 
    curr_id_string = ""
    counter = len(currencies)
    # create url to show all currency exchange rates
    for curr in currencies:
        curr_id = currencies[curr]

        if counter == 1:
            curr_string += curr
            curr_id_string += curr_id
        else:
            curr_string += curr + ","
            curr_id_string += curr_id + ","
            counter -= 1

    url = url1 + curr_string + url2 + curr_id_string  # url string built here

    request = requests.get(url)  # request data from api
    exchange_rates_dict = json.loads(request.text)  # load json as string into python dictionary

    # current directory
    curr_dir = os.path.dirname(__file__)
    
    # save path of json file
    exchange_rates_json_file_path = curr_dir + "/data/json_data/exchange_rates.json"

    # dump the dictionary into the json file
    with open(exchange_rates_json_file_path, "w") as json_file:
        json.dump(exchange_rates_dict, json_file)

    # create rates 2-D list to be used to store the exchange rates
    rates = []
    key_error = False
    # for loop that iterates through each currency
    for c1 in currencies:
        rate_row = []
        for c2 in currencies:

            # try and except block so that if a key doesn't exist during the dictionary traversal,
            # (cardano), it will leave an None value
            try:
                rate = exchange_rates_dict[c1][currencies[c2]]

                rate_row.append(rate)
            # if KeyError occurs, append None as the value since it doesn't exist
            except KeyError:
                rate = None
                rate_row.append(rate)
                key_error = True
        
        # append the rate_row to the rates list
        rates.append(rate_row)
            
    graph_visual_file = curr_dir + "/graph_visual.png"
    edges_file = curr_dir + "/edges.txt"

    # create graph object
    g = nx.DiGraph()
    edges = []
    csv_data = []
    i = 0

    # go through currency combinations and append them to edges
    for i, c1 in enumerate(currencies):
        for j, c2 in enumerate(currencies):
            # if c1 and c2 are not the same and the rate to convert is not None (both to and from possibilities)
            if i != j and rates[i][j] is not None and rates[j][i] is not None:
                edges.append((c1, c2, rates[i][j]))
                # print("adding edge:", c1, c2, rates[i][j])

                # write currency pair to csv with currency_pair_YYYY.MM.DD:HH.MM.txt as the file name
                now = datetime.now()
                name_1 = curr_dir + "/data/currency_pair_data/currency_pair_"
                name_2 = now.strftime("%Y.%m.%d-%H.%M.csv")
                file_name = name_1 + name_2
                line = [c1, c2, rates[i][j]]
                csv_data.append(line)

    # write the currency pair data to the csv txt file
    with open(file_name, "w", newline='') as csv_file:
        writer = csv.writer(csv_file)
        
        for row in csv_data:
            writer.writerow(row)

    g.add_weighted_edges_from(edges)
    print()

    # save graph as image
    pos = nx.circular_layout(g)
    nx.draw_networkx(g, pos)
    labels = nx.get_edge_attributes(g, "weight")
    nx.draw_networkx_edge_labels(g, pos, edge_labels=labels)

    plt.savefig(graph_visual_file)

    # graph traversal
    
    # create weight factor dictionary
    weight_factor_dict = {}
    results_dict = {}

    # iterate through all the possible permutations nodes 
    for n1, n2 in permutations(g.nodes, 2):
        print("All paths from", n1, "to", n2, "-------------------------------------------------------------")
        results_dict_key = f"{n1}-->{n2}"
        results_dict[results_dict_key] = {}
        
        # keep track of path number
        path_count = 1

        # for each path in all simple paths, calculate the weight to and from...
        for path in nx.all_simple_paths(g, source=n1, target=n2):

            path_weight_to = 1.0
            # calculating the path weight from the first currency to the second
            for i in range(len(path) - 1):
                path_weight_to *= g[path[i]][path[i + 1]]["weight"]

            # print the path along with the weight
            print("Path to", path, path_weight_to)
            
            # append this path/weight tuple to the results dictionary
            results_dict[results_dict_key][f"Path to ({path_count})"] = (path, path_weight_to)

            # before reversing, create a copy of the path list
            to_list = [] + path

            # reversing the path
            path.reverse()

            path_weight_from = 1.0
            # calculating the path weight from the second currency back to the firsst
            for i in range(len(path) - 1):
                path_weight_from *= g[path[i]][path[i + 1]]["weight"]

            # print the path along with the weight
            print("Path from", path, path_weight_from)
            
            # append this path/weight tuple to the results dictionary
            results_dict[results_dict_key][f"Path from ({path_count})"] = (path, path_weight_from)

            # calculate the weight factor of the to/from path and print it
            weight_factor = path_weight_to * path_weight_from
            print("Weight Factor:", weight_factor)

            # create tuple with the path to and reversed path, set it to the key.
            # set the value to the weight factor, add it to the dictionary
            key = []
            key.append(to_list)
            key.append(path)
            key_tuple = tuple(map(tuple, key))

            weight_factor_dict[key_tuple] = weight_factor
            
            # increment path count
            path_count += 1
    
        print("---------------------------------------------------------------------------------------------")

    print()
    print()

    # find the min weight factor from the dictionary and save the key and value
    min_weight_factor_key = min(weight_factor_dict, key=weight_factor_dict.get)
    min_weight_factor_value = weight_factor_dict[min_weight_factor_key]

    # find the max weight factor from the dictionary and save the key and value
    max_weight_factor_key = max(weight_factor_dict, key=weight_factor_dict.get)
    max_weight_factor_value = weight_factor_dict[max_weight_factor_key]

    # print the smallest paths weight factor
    print("Smallest Paths weight factor:", min_weight_factor_value)
    print("Paths:", list(min_weight_factor_key[0]), list(min_weight_factor_key[1]))

    # print the greathest paths weight factor
    print("Greatest Paths weight factor:", max_weight_factor_value)
    print("Paths:", list(max_weight_factor_key[0]), list(max_weight_factor_key[1]))
    
    # create results dictionary final results key
    results_dict_results_key = "Final Results"
    results_dict[results_dict_results_key] = {}
    
    # add smallest and greatest paths/weight factors to final results
    results_dict[results_dict_results_key]["Smallest Path"] = (list(min_weight_factor_key[0]), list(min_weight_factor_key[1]), min_weight_factor_value)
    results_dict[results_dict_results_key]["Greatest Path"] = (list(max_weight_factor_key[0]), list(max_weight_factor_key[1]), max_weight_factor_value)

    # iterate through list of max_weight_factor_key, see if each item is in currencies, if so set each item to be the value
    greatest_wf_path = [currencies[symbol] for symbol in list(max_weight_factor_key[0])]

    # if the max_weight_factor_value is greater than 1, make crypto orders with alpaca
    if max_weight_factor_value > 1:
        print()  # add space for terminal formatting
        purchase_history_list, alpaca_balance = make_alpaca_orders(greatest_wf_path)
    
    # add purchase history and balance to results dictionary
    purchases_key = "Purchases"
    balance_key = "Balance"
    results_dict[purchases_key] = purchase_history_list
    results_dict[balance_key] = alpaca_balance
    
    # save path of json file
    results_json_file_path = curr_dir + "/results.json"

    # dump the dictionary into the json file
    with open(results_json_file_path, "w") as json_file:
        json.dump(results_dict, json_file) 


main()
