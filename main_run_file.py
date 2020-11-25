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

#Crawls the data
from shuf_get import shuf_get_q
from vict_get import vict_get_q

#Strings manipulations (regex)
import re

#working directory
import os


#Set display for showing dataframes
pd.set_option('display.max_columns', 1000)
pd.set_option('display.max_rows', 1000)
pd.set_option('display.width', 1000)

#Set the working directory
# C:\Users\matan\Dropbox\bachelor's\Statistics\Data Mining\project/products_list
os.chdir("C:/Users/matan/Dropbox/bachelor's/Statistics/Data Mining/project")


#The Supermarkets We decided to use:
supermarkets = ["shufersal", "victory"]


#A function that calculates the percentage by which the product name string exists in the input
# i.e. the match of a b c, a b d c     is 1.0 (100%)
def perc_match(inp, prod_name):
    inp = inp.split()
    prod_name = prod_name.split()
    s = 0
    for w in inp:
        s += (w in prod_name)

    p = s/len(inp)
    return p



#A function that gets two rows of dataframes and decides if it's the same product
def same_prod(r1, r2, thresh):
    if min(perc_match(r1["Product Name"], r2["Product Name"]), perc_match(r2["Product Name"], r1["Product Name"])) < thresh:
        return False

    # #delete the word "units", delete spaces
    # r1["Quantity"] = str(r1["Quantity"]).replace("יחידות", "")
    # r1["Quantity"] = str(r1["Quantity"]).replace(" ", "")
    #
    # r2["Quantity"] = str(r2["Quantity"]).replace("יחידות", "")
    # r2["Quantity"] = str(r2["Quantity"]).replace(" ", "")

    s1 = re.sub('\D', '', r1["Quantity"])
    s2 = re.sub('\D', '', r2["Quantity"])


    if (s1 == s2):
        return True
    return False

def match_same_prod(shufersal, victory, threshold, match_needed):
    # Find same products in all supermarkets and take the cheapest
    same_indcs_shuf = []
    same_indcs_vic = []

    for i in range(shufersal.shape[0]):
        for j in range(victory.shape[0]):
            if same_prod(shufersal.loc[i], victory.loc[j], threshold):
                if shufersal.loc[i, "Prices"] > victory.loc[j, "Prices"]:
                    same_indcs_shuf.append(i)

                if shufersal.loc[i, "Prices"] < victory.loc[j, "Prices"]:
                    same_indcs_vic.append(j)

    #Take only items with percision of 70% or more and delete two same items (one from each supermarket)
    shufersal = shufersal.drop(same_indcs_shuf)
    shufersal = shufersal[shufersal["Match Perc"] >= match_needed]

    victory = victory.drop(same_indcs_vic)
    victory = victory[victory["Match Perc"] >= match_needed]

    return [shufersal, victory]


#A function that combines all products and for each item lets the user choose which one of the options he would like
#  to save given all the data he may have
def decide_products(shufersal, victory):
    df = pd.concat([shufersal, victory], ignore_index=True)
    itms = pd.unique(df["product"])

    for itm in itms:
        indx = -2
        current_prod = copy.deepcopy(df[df["product"] == itm])
        current_prod.sort_values(by=['Match Perc','Prices'], inplace=True, ascending=[False, True])

        # If there are more than 5 options- take the 5 that has the best match and lowest prices (to choose from
        if current_prod.shape[0] > 5:
            df = df.drop(current_prod.index[5:])
            current_prod = current_prod.head(5)


        while (any(indx == i for i in list(current_prod.index)) == False) and (indx != -1):
            print("Choose the product you want from this list by the index, if you don't want any- write any negative number\n")
            col_names_curr_prod = current_prod.columns
            current_prod.columns = ["מחיר", "כמות", "שם המוצר", "חיפוש", "רשת שיווק", "אחוז התאמה"]
            print(current_prod)
            current_prod.columns = col_names_curr_prod
            indx = input()
            if indx.isnumeric() and int(indx) >= 0:
                indx = int(indx)
            else:
                indx = -1

        if indx != -1:
            new_df = current_prod.drop(indx) #stay without the index you want
            df = df.drop(new_df.index) #delete the rows that aren't the index you want
        else:
            print("There is no such products with that index (of "+list(pd.unique(current_prod["product"]))[0]+")")
            df = df.drop(current_prod.index)

    shufersal = df[df["Super"] == "שופרסל"]
    victory = df[df["Super"] == "ויקטורי"]

    return [shufersal, victory]


#The main function of the program, this will call any other functions and code pieces
def main():
    print("Hello and Welcome to The Supermarket Comparison Program")
    path = "asn"
    while path == "asn":
        try:
            path = input("Please enter your path:\n")
            if path == "Matan Bendak":
                os.chdir("C:/Users/matan/Dropbox/bachelor's/Statistics/Data Mining/project")
            else:
                os.chdir(path)
        except:
            path = "asn"

    lst_of_strs = []
    inp_path = 0

    inp = input("Enter 'csv' if you wish to load you list from a file, otherwise press ENTER\n")
    if inp == "csv":
        while True:
            try:
                inp_path = input("Enter the path to your csv file with your list\n"
                                 "first column is the names of products, second column is the amounts as numbers\n")
                inp_path = inp_path.replace("\\", "/")

                if inp_path[-4:] != ".csv":
                    inp_path += ".csv"


                lst_of_strs = np.array(pd.read_csv(inp_path, header=None)[0])
                break
            except:
                print("The path isn't working, try again...\n")
                continue


    else:
        if inp == "":
            itm = input("Enter your items one each time with ENTER between any two items, press ENTER to finish\n")
            while itm != "":
                lst_of_strs.append(itm)
                itm = input()
        else:
            main()

    if len(lst_of_strs) == 0:
        print("There are no products\nProgram ended")
        return

    # markets initializations
    shufersal = []
    victory = []

    for query in lst_of_strs:
        shufersal.append(shuf_get_q(query))
        victory.append(vict_get_q(query))

    shufersal = pd.concat(shufersal, ignore_index=True)
    victory = pd.concat(victory, ignore_index=True)

    #Arrange the dataframes of the supermarkers in correct types, just in case
    shufersal["Prices"] = shufersal["Prices"].astype(float)
    shufersal["Quantity"] = shufersal["Quantity"].astype(str)
    shufersal["Product Name"] = shufersal["Product Name"].astype(str)
    shufersal["Match Perc"] = shufersal["Match Perc"].astype(float)



    victory["Prices"] = victory["Prices"].astype(float)
    victory["Quantity"] = victory["Quantity"].astype(str)
    victory["Product Name"] = victory["Product Name"].astype(str)
    victory["Match Perc"] = victory["Match Perc"].astype(float)

    #Delete items that exist in both supermarkets and have higher price and items which aren't a good match
    dfs_matched = match_same_prod(shufersal, victory, 0.75, 0.5)
    shufersal = dfs_matched[0]
    victory = dfs_matched[1]


    decision = decide_products(shufersal, victory)
    shufersal = decision[0]
    victory = decision[1]



    #Save the results so the user will be able to purchase his/her items in the relevant supermarket
    try:
        shufersal.to_csv("C:/Users/matan/Dropbox/bachelor's/Statistics/Data Mining/project/shuf_new.csv", encoding='utf-8-sig')
        victory.to_csv("C:/Users/matan/Dropbox/bachelor's/Statistics/Data Mining/project/vic_new.csv", encoding='utf-8-sig')

    except:
        print("Unable to save the file, Please make sure the previous file is closed\n"
              "for now the results will be displayed here") #just to use except... no real need

    #Print it as well
    col_names = shufersal.columns
    hebrew_col_names = ["מחיר", "כמות", "שם מוצר", "חיפוש", "סופרמרקט", "אחוז דיוק"]
    shufersal.columns = hebrew_col_names
    victory.columns = hebrew_col_names

    print("Your products from Shufersal are:")
    print(shufersal.to_string())
    print()
    print("Your products from Victory are:")
    print(victory.to_string())
    shufersal.columns = col_names
    victory.columns = col_names

    total_price  = 0
    if inp_path != 0:
        prods_amounts = pd.read_csv(inp_path, header=None, names = ["product", "amount"])
        shufersal = pd.merge(left=shufersal, right=prods_amounts, left_on="product", right_on="product")

        total_price = sum(shufersal["Prices"]*shufersal["amount"])
        print("The total price you will pay in Shufersal is: ", total_price)

        total_price = 0
        victory = pd.merge(left=victory, right=prods_amounts, left_on="product", right_on="product")
        total_price = sum(victory["Prices"] * victory["amount"])
        print("The total price you will pay in Victory is: ", total_price)


    else:
        print("\nFor each product choose it's amount:\n")

        #Shufersal
        total_price_shuf = 0
        itms = list(pd.unique(shufersal["product"]))
        for itm in itms:
            prods_amount = float(input(str(itm) + "\n"))
            while prods_amount < 0:
                print("Negative amounts aren't valid, Please try again:\n")
                prods_amount = float(input(str(itm) + "\n"))

            pr = float(shufersal[shufersal["product"] == itm]["Prices"])
            total_price_shuf += round(float(prods_amount*pr), 2)



        #Victory
        total_price_vic = 0
        itms = list(pd.unique(victory["product"]))
        for itm in itms:
            prods_amount = float(input(str(itm) + "\n"))
            while prods_amount < 0:
                print("Negative amounts aren't valid, Please try again:\n")
                prods_amount = float(input(str(itm) + "\n"))

            pr = victory[victory["product"] == itm]["Prices"]
            total_price_vic += round(float(prods_amount*pr), 2)

        print()
        print("The total price you will pay in Shufersal is: ", total_price_shuf)
        print("The total price you will pay in Victory is: ", total_price_vic)
        print()
        print("The total payment is: ", total_price_shuf+total_price_vic)

main()

