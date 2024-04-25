import networkx as nx
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from itertools import permutations, combinations
import json
import requests
from datetime import datetime


def main():
    
    # currencies/rates data
    currencies = {
        "aave": "aave", 
        "avalanche-2": "avax", 
        "bitcoin-cash": "bch", 
        "basic-attention-token": "bat", 
        "litecoin": "ltc", 
        "ethereum": "eth", 
        "bitcoin": "btc",
        "curve-dao-token": "crv",
        "polkadot": "dot",
        "the-graph": "grt",
        "chainlink": "link",
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

    # save path of json file
    exchange_rates_json_file_path = "./data/json_data/exchange_rates.json"

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
            
    # current directory
    curr_dir = os.path.dirname(__file__)
    graph_visual_file = curr_dir + "\graph_visual.png"
    edges_file = curr_dir + "\edges.txt"

    # create graph object
    g = nx.DiGraph()
    edges = []
    i = 0

    # go through currency combinations and append them to edges
    for i, c1 in enumerate(currencies):
        for j, c2 in enumerate(currencies):
            # if c1 and c2 are not the same and the rate to convert is not None (both to and from possibilities)
            if i != j and rates[i][j] is not None and rates[j][i] is not None:
                edges.append((c1, c2, rates[i][j]))
                # print("adding edge:", c1, c2, rates[i][j])

                # write currency pair to text file (csv) with currency_pair_YYYY.MM.DD:HH.MM.txt as the file name
                now = datetime.now()
                name_1 = f"./data/currency_pair_data/currency_pair_"
                name_2 = now.strftime("%Y.%m.%d-%H.%M.txt")
                file_name = name_1 + name_2
                text = f"{c1},{c2},{rates[i][j]},"

                # write the currency pair data to the csv txt file
                with open(file_name, "a") as csv_file:
                    csv_file.write(text + "\n")

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

    # iterate through all the possible combinations nodes 
    for n1, n2 in combinations(g.nodes, 2):
        print("All paths from", n1, "to", n2, "-------------------------------------------------------------")

        # for each path in all simple paths, calculate the weight to and from...
        for path in nx.all_simple_paths(g, source=n1, target=n2):
            
            path_weight_to = 1.0
            # calculating the path weight from the first currency to the second
            for i in range(len(path) - 1):
                path_weight_to *= g[path[i]][path[i + 1]]["weight"]

            # print the path along with the weight
            print("Path to", path, path_weight_to)
            # append path weight to to the list

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


main()
