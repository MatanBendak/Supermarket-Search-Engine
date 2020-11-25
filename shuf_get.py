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


#Fix the spans of shufersal to be good strings
def fix_spans_shufersal(spn):
    spn = str(spn)
    return spn[6:len(spn)-7]

#Check if the item is a product of promotion
def is_product_shufersal(prod):
    print(len(prod.contents))
    for cont in prod.contents:
        # print(len(cont))
        for sub_c in cont:
            # print((str(sub_c)))
            # print("product_images" in str(sub_c))
            #     return True
            if "promotion_characteristics_images" in str(sub_c):
                print("a promotion, not a product")
            else:
                return True

# A function that calculates the percentage by which the product name string exists in the input
# i.e. the match of a b c, a b d c     is 1.0 (100%)
def perc_match(inp, prod_name):
    inp = inp.split()
    prod_name = prod_name.split()

    s = 0
    for w in inp:
        s += (w in prod_name)
    p = s / len(inp)
    return p

#For a given tag, return the string in it
def extract_text_from_tag(tag):
    st = ""
    tag = str(tag)
    if len(tag) < 2:
        return ""
    start = False

    for i in range(1, len(tag)):
        if tag[i - 1] == ">":
            start = True
        if start == True and tag[i] != "<":
            st += tag[i]
        if tag[i] == "<":
            start = False
    return st


#Crawl prices
def get_prices_shuf(soup):
    raw_prices = soup.find_all(class_='price')
    prices = ''
    for child in raw_prices:
        prices += (child.find(class_='number').get_text())

    prices = prices.split()
    new_prices = []

    for i in range(len(prices)):
        if len(prices[i]) <= 5: #Delete unwanted short strings from the list
            new_prices.append(prices[i])

    return new_prices


#Crawl product names
def get_prod_name(soup):
    raw_text_prod = soup.find_all('div', {"class": "text"})
    raw_text_prod = [extract_text_from_tag(p.contents[1]) for p in raw_text_prod if len(p.contents) > 1]

    text_prod = []
    for p in raw_text_prod:
        if len(p) > 0:
            text_prod.append(p)

        text_prod = [p.replace("-", " ") for p in text_prod]

    return text_prod


#Get the names with mutagim and weights
def get_names_shuf(soup):
    raw_names = soup.find_all(class_='smallText')

    names = []
    for child in raw_names:
        tmp = child.find_all("span")
        if len(tmp) > 0:
            if len(tmp) == 1:
                names.append(([fix_spans_shufersal(tmp[0])]))
            else:
                names.append([fix_spans_shufersal(tmp[0]), fix_spans_shufersal(tmp[1])])

    return names


#Get the weights
def get_weights_shuf(names):
    return [sub[0] for sub in names]

#Get the mutagim names
def get_mutagim_shuf(names):
    mutagim = []

    for sub in names:
        if len(sub) > 1:
            mutagim.append(sub[1])

    return mutagim


#Get the normalized prices from the web
def get_norm_prices_shuf(soup):

    raw_norm_price = soup.find_all(class_="smallText")
    norm_prices = []
    for p in raw_norm_price:
        c = p.contents[0]
        c = str(c)
        if len(c) > 0:
            c = c.split()
            c = " ".join(c)
        if len(c) > 14:
            norm_prices.append(c)

    norm_prices = norm_prices[1:]
    norm_prices = [float(pr.split()[0]) for pr in norm_prices]

    return norm_prices


def shuf_get_q(query):
    shufersal = []
    # Constracting http query
    url = 'https://www.shufersal.co.il/online/search?q=' + query
    search_page = requests.get(url)
    soup = BeautifulSoup(search_page.content, 'html.parser')

    #Define maximum amount of items by the number appears in the website of the current search
    max_items = '(0)'
    max_items = soup.select('span[id^=searchResults_count_label]')[0].text
    max_items = ("".join(max_items.split()))
    max_items = max_items.replace(",", "")
    max_items = int(max_items[1:len(max_items) - 1])


    #Crawl prices
    new_prices = get_prices_shuf(soup)

    #Crawl product names
    text_prod = get_prod_name(soup)


    #Crawl the names in the website with the weights to get the weights and Mutagim
    names = get_names_shuf(soup)

    #Crawl the weights
    weights = get_weights_shuf(names)

    # #Crawl the Mutagim
    # mutagim = get_mutagim_shuf(names)


    # #Crawl the normalized prices
    # norm_prices = get_norm_prices_shuf(soup)


    #use max 20 items of each product (less if there are less), take the first ones
    real_len = min(len(new_prices), len(weights), len(text_prod), 20)

    new_prices = new_prices[:real_len]

    weights = weights[:real_len]
    # text_prod = delete_unwanted_names(text_prod)
    text_prod = text_prod[:real_len]
    match = [perc_match(query, text_prod[i]) for i in range(real_len)]

    #Create the DataFrame
    tmp = pd.DataFrame({"Prices": new_prices, "Quantity": weights, "Product Name": text_prod,
                        "product": list(np.repeat(query, len(weights))),
                        "Super": list(np.repeat(["שופרסל"], len(weights))),
                        "Match Perc": match})

    return tmp
