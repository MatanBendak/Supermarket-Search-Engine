# Import libraries
#Web Crawling
import requests
import urllib.request
from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep

#Data Manipulations
import pandas as pd
import numpy as np
import copy
import collections


def get_names_vic(soup):
    spans = soup.find_all('span',  {'class': 'Prefix'})
    prod_names = [span.contents[0] for span in spans]
    prod_names = [p.replace("-", " ") for p in prod_names]
    return prod_names

def get_prices_vic(soup):
    spans = soup.find_all('span', {'class': 'Price'})

    offers = soup.find_all('span', {'class': 'Offer'})
    offers_available = has_offer(soup)

    prices = []
    off_ind = 0

    for i in range(len(spans)):
        if offers_available[i] == True:
            if "Coin" in str(offers[off_ind]):
                prices.append(offers[off_ind].contents[1])
                off_ind += 1
            else:
                off_ind += 1
                prices.append(spans[i].contents[1].split()[0])
        else:
            prices.append(spans[i].contents[1].split()[0])
    return prices

def get_norm_prices_vic(soup):
    spans = soup.find_all('span', {'class': 'BeforeOffer'})
    norm_prices = [float(str(s.contents[1]).split()[0]) for s in spans]
    return norm_prices


def has_offer(soup):
    spans = soup.find_all('span', {'class': ["PPU"]})
    offers_exists = []

    for s in spans:
        for itm in s.contents:
            if "AfterOffer" in str(itm):
                offers_exists.append(True)
                break
        else:
            offers_exists.append(False)

    return offers_exists

def perc_match(inp, prod_name):
    inp = inp.split()
    prod_name = prod_name.split()

    s = 0
    for w in inp:
        s += (w in prod_name)
    p = s / len(inp)
    return p


def get_weights_vic(soup):
    spans = soup.find_all('span', {'class': 'Suffix'})

    weights = []
    for s in spans:
        try:
            weights.append(str(s.contents[0])[1:-1])
        except:
            weights.append("")

    return weights


def vict_get_q(query):
    url = "http://www.victoryonline.co.il/Shopping/FindProducts.aspx?Query=" + query
    search_page = requests.get(url)
    soup = BeautifulSoup(search_page.content, 'html.parser')

    prices = get_prices_vic(soup)


    # Get the product names of the current query (item)
    prod_names = get_names_vic(soup)

    # #Get the normalized price of the products for the current query (before any offer, no mivtzaim
    # norm_prices = get_norm_prices_vic(soup)

    #Get the weights of the products
    weights = get_weights_vic(soup)

    # use max 20 items of each product (less if there are less), take the first ones
    real_len = min(len(prices), len(weights), len(prod_names), 20)

    prices = prices[:real_len]
    weights = weights[:real_len]
    prod_names = prod_names[:real_len]

    match = [perc_match(query, prod_names[i]) for i in range(real_len)]

    # Create the DataFrame
    tmp = pd.DataFrame({"Prices": prices, "Quantity": weights, "Product Name": prod_names,
                        "product": list(np.repeat(query, len(weights))),
                        "Super": list(np.repeat(["ויקטורי"], len(weights))),
                        "Match Perc": match})

    return tmp
