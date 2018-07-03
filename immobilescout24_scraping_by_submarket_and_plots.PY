# -*- coding: utf-8 -*-
"""
# Web Scrapper for IMMOBILIENSCOUT24.DE
# Start date: 2018 03 07 evening
"""

# Import modules and packages
import requests, re
import numpy as np
import pandas as pd
import datetime
from bs4 import BeautifulSoup

# :::::::::::::::: READ URL FILE : BEGIN :::::::::::::::::
def readURLs():
    import os
    
    directory = os.path.join(os.getcwd())
        
    df = pd.read_excel('submarkets.xlsx')
    print(df)
    d_urls = df.to_dict()
    return d_urls
# URL file is done right now!
        
d_urls = readURLs()

# :::::::::::: MAIN BODY OF SCRAPPER : BEGIN :::::::::::::
def startScrapping(d_urls):
    
    for submarket in range(0, len(d_urls["URL"]), 1):
        # ::::::::::::: DATA PREPARATION FUNCTIONS :::::::::::::::
        # Get HTML code for the main page
        # base_url = "https://www.immobilienscout24.de/gewerbe-flaechen/de/hamburg/hamburg/buero-mieten/"
        base_url = d_urls["URL"][submarket]
        
        print('\nBase URL for a market {} \n {} \n:'.format(d_urls["Submarket"][submarket], 
              base_url))
        
        r = requests.get(base_url)
        c = r.content
        soup = BeautifulSoup(c, "html.parser")
        
        # SELF FUNCTIONS AND PROCEDURES ---------------------------------------
        # Getting the number of pages
        def getPages(soup):
            return soup.find_all("span", {"class":"pg-item"})[len(soup.find_all("span", {"class":"pg-item"}))-1].text
        
        # Getting full list of URLs
        def getURLs(base_url, number):
            #print(number, type(number))
            listofURLs = []      # List where all our URLs will be store
            for page in range(0, number, 1):
                 listofURLs.append(base_url + "seite/" + str(page + 1) + "/")
            return listofURLs
        
        # Dive inside the page of property
        def insidePage(url):
            
            try:
                print('--: {}'.format(url))
                r = requests.get(url)
                c = r.content
                soup = BeautifulSoup(c, "html.parser")
                
                try:
                    built_year = soup.find("dd", {"class":"is24qa-letzte-modernisierungsanierung grid-item three-fifths"}).text
                    #print("*** last renovation: " + built_year + " ***")
                except:
                    if "Baujahr".upper() in str(soup).upper():
                        try:
                            built_year = soup.find("dd", {"class":"is24qa-baujahr grid-item three-fifths"}).text
                        except:
                            built_year = 0
                    else:
                        built_year = 0
            except:
                print('!!! The internal page can not be read !!!')
                built_year = 0
            
            return built_year
        
        # Change Date Format: for making it suitable for generating graphs on Data visualization part
        def changeDateFormat():
            today_value = str(datetime.datetime.now()).split(" ")[0]
            my_year = today_value.split('-')[0]
            my_month = today_value.split('-')[1]
            my_day = today_value.split('-')[2]
            
            new_date = my_month + "/" + my_day + "/" + my_year
            
            if new_date[0] == "0":
                new_date = new_date[1:]
                
            if "/0" in new_date:
                new_date = new_date.replace("/0", "/")
            
            return new_date        
        #----------------------------------------------------------------------
        
        # Start gathering URLs!
        URLs = getURLs(base_url, int(getPages(soup)))
        
        # ::::::::::::: GETTING THE DATA ::::::::::::::::::::::::::
        # Check if element has a number
        def num_there(s):
            return any(i.isdigit() for i in s)
        
        all_properties = []  # All properties will be stored in the list of dictionaries
        error_msg = "Not found"
        
        today_is = changeDateFormat()
        
        # Go through the pages!
        for page in range(0, int(getPages(soup)), 1):                       # Default: for page in range(0, int(getPages(soup)), 1):
            print(URLs[page])
            
            r_inside = requests.get(URLs[page])
            c_inside = r_inside.content
            souping = BeautifulSoup(c_inside, "html.parser")
            blocks = souping.find_all("div", {"class":"real-estate-card"})  # HTML blocks of properties in search page
            nop = len(blocks)    # nop - Number Of Properites (per one page)
            record = {}          # The data of property will be storage in a dictionary as always
            
            print("Page: ", page)
            
            # Go through the properties in a page!
            for property in range(0, nop, 1):
                sizeTrue = False   
                priceTrue = False
                
                #print(blocks[property])
                
                # Get title of a property
                try:
                    title = blocks[property].find("div", {"class":"real-estate-title"}).text
                except:
                    title = error_msg
                
                # Get address
                try:
                    address = blocks[property].find("p", {"class":"spec-address"}).text
                    if "," in address:
                        part_1 = address.split(",")[0]
                        part_2 = address.split(",")[1]
                        
                        address = part_2 + ", " + part_1
                except:
                    address = error_msg
                    
                # Get price
                try:
                    price = blocks[property].find("span", {"class":"inner-value"}).text
                except:
                    price = error_msg
                    
                # Get Min. price and Max price fro price variable
                if "–" in price:
                    price_max = price.split("–")[1].replace("€", "").replace(".", "").replace(",",".")
                    price_min = price.split("–")[0].replace(".", "").replace(",",".")
                    priceTrue = True
                elif num_there(price):
                    price_max = price.replace("€", "").replace(".", "").replace(",",".")
                    price_min = price.replace("€", "").replace(".", "").replace(",",".")
                    priceTrue = True
                else:
                    price_max = price_min = price = error_msg
                    
                # Get size
                try:
                    size = blocks[property].find("div", {"class":"spec-arealine-area"}).text.split("m²")[0]
                except:
                    size = error_msg
                    
                # Get Min. size and Max size
                if "–" in size:
                    size_max = size.split("–")[1].replace(".", "").replace(",",".")
                    size_min = size.split("–")[0].replace(".", "").replace(",",".")
                    sizeTrue = True
                elif num_there(price):
                    size_max = size.replace(".", "").replace(",",".")
                    size_min = size.replace(".", "").replace(",",".")
                    sizeTrue = True
                else:
                    size_max = size_min = size = error_msg   
                
                # Calculate Price per Min. Size AND Price per MaxSize
                if sizeTrue and priceTrue:
                    try:
                        price_Min_s = float(price_min) / float(size_min)
                        price_Max_s = float(price_max) / float(size_max)
                    except:
                        price_Min_s = 0
                        price_Max_s = 0  
                else:
                    price_Min_s = 0
                    price_Max_s = 0
                    
                # Get URL
                my_url = str(blocks[property]("a", href = True)[0]).split('href="')[1].split('"')[0]
                    
                #Get block for SPECIAL FEATURES
                sf = str(blocks[property].find("div", {"class":"special-features"}))       # From this point we will looking for special features (sf)
                
                # Checking for lift >>>
                if "lift.svg" in sf:
                    lift = "Y"
                else:
                    lift = "N"
                    
                # Checking for disabled people
                if "barrierFree.svg" in sf:
                    d_people = "Y"
                else:
                    d_people = "N"
                    
                # Checking for Internet
                if "Wiring.svg" in sf:
                    internet = "Y"
                else:
                    internet = "N"
                    
                # Checking for air conditioning
                if "airConditioning.svg" in sf:
                    airC = "Y"
                else:
                    airC = "N"
                    
                # Checking for kitcher
                if "kitchen.svg" in sf:
                    kitchen = "Y"
                else:
                    kitchen = "N"
                    
                # Checking for Non-Commision
                if "Provisionsfrei *" in sf:
                    noComm = "Y"
                else:
                    noComm = "N"
                    
                # Checking for type of office
                if "Büro" in sf:
                    typeOffice = "Büro"
                elif "Praxis" in sf:
                    typeOffice = "Praxis"
                elif "Loft" in sf:
                    typeOffice = "Loft"
                else:
                    typeOffice = error_msg
                    
                # Checking for built year
                b_year = insidePage(my_url)
                    
                # Put data into a dictionary
                record["Submarket"] = d_urls["Submarket"][submarket] 
                record["Title"] = title
                record["Address"] = address
                record["Built year"] = b_year
                record["Price"] = price
                record["Price max."] = price_max
                record["Price min."] = price_min
                record["Price per max. size"] = round(price_Max_s, 2)
                record["Price per min. size"] = round(price_Min_s, 2)
                record["Size"] = size
                record["Size max."] = size_max
                record["Size min."] = size_min
                record["SF: Lift"] = lift
                record["SF: Disabled persons"] = d_people
                record["SF: Internet"] = internet
                record["SF: Air cond."] = airC
                record["SF: Kitchen"] = kitchen
                record["SF: No commissions"] = noComm
                record["Type"] = typeOffice
                record["URL"] = my_url
                record["Timestamp"] = today_is
            
                #print("-------------------------")
                all_properties.append(dict(record))
        # <----------------- Finishing scrapping ::::::::::
        print("Finished.")
                
        # Save data to file : start
        def writeToFile(DF, filename):
            import time, datetime, os
            from datetime import date 
            
            directory = os.path.join(os.getcwd())
            
            os.chdir(directory)
            timeNow = str(datetime.datetime.now()).replace(":","-")[:-10]
            DF.to_excel("immobilienscout24.de " + filename + " " + timeNow + ".xls")
            return None
        # Save data to file : end <--------------        
        
        # Save data to the Pandas DataFrame
        df = pd.DataFrame(all_properties)
        df = df[["Submarket", "Title", "Built year", "Address", "Type", "Price", "Price min.", "Price max.", "Price per min. size", "Price per max. size", "Size", "Size min.", "Size max.", "SF: Lift", "SF: Disabled persons", "SF: Internet", "SF: Air cond.", "SF: Kitchen", "SF: No commissions", "URL", "Timestamp"]]
        
        # Save DataFrame to CSV file in current workspace directory
        writeToFile(df, d_urls["Submarket"][submarket])
    
    print("{} : this submarket is done.".format(d_urls["Submarket"][submarket]))
    print(" ")
    
    return None
#------------------------------------------------------------------------------
# :::::::::::::::::::::::: SCENARION FOR SCRAPPER :::::::::::::::::::::::::::::
#------------------------------------------------------------------------------
# 01 - read all source urls to dictionary that will be passed to the algorithm
d_urls = readURLs()
# 02 - passing all urls to the algorithm
startScrapping(d_urls)

#------------------------------------------------------------------------------
# :::::::::::::::::::::::: DATA VISUALIZATION PART ::::::::::::::::::::::::::::
#------------------------------------------------------------------------------
# Import modules and packages
import numpy as np        # If haven't been imported before this part
import pandas as pd       # If haven't been imported before this part
import csv
import os
import matplotlib.pyplot as plt
import seaborn as sns

# ::::::::::::::::::::::::::::::: READING CSV :::::::::::::::::::::::::::::::::
# :::::::::::::::::::::::::::::::: FUNCTIONS ::::::::::::::::::::::::::::::::::
# Read a single CSV
def readCSV(my_csv):
    
    # Function for data noise removing from the array (remove marginal data by set threshold)
    def removeDataNoise(df):
        threshold = 0.2
        df = df.loc[df["Price per max. size"] > df["Price per max. size"].max() * (threshold/2)]
        df = df.loc[df["Price per max. size"] < df["Price per max. size"].max() - df["Price per max. size"].max() * (threshold/2)]
        
        df_without_noise = df
        return df_without_noise
    # Function closed <------------------------------
    
    # Function that filter properties by built year or last reconstruction year
    def filterByYear(df):
        for row in range(0, len(df), 1):
            try:
                df.iat[row, df.columns.get_loc("Built year")] = int(df.iat[row, df.columns.get_loc("Built year")])
                #print("Successful: ", df.iat[row, df.columns.get_loc("Built year")])
            except:
                #print("Not successful: ", df.iat[row, df.columns.get_loc("Built year")])
                df.iat[row, df.columns.get_loc("Built year")] = 0
        
        df = df.loc[df["Built year"] > 1990]
        df_filtered = df
        return df_filtered
    # Function closed <------------------------------
    
    df = pd.read_csv(my_csv)
    
    X = df[["Submarket", "Built year", "Price max.", "Price per max. size", "Size max.", "Timestamp"]]
    print("L_before:", len(X["Price per max. size"]))

    # Make some basic calculations if neeeded!
    X = removeDataNoise(X)
    X = filterByYear(X)
    
    
    print("L_after:", len(X["Price per max. size"]))
    print(X["Price per max. size"].describe())
    print(X["Price per max. size"].max())
    
    print(X)
    
    print("-------------------------")
    return X
    # Function closed <-------------------------------------------------------
    
# ::::::::::::::::: READING CSV FILES FROM DIRECTORY ::::::::::::::::::::::::::
# BEGIN WITH THIS ------------------------------------------------------------>
# Read all CSV from work directory
directory = os.path.join(os.getcwd())

l = []   # List of DataFrames after data noise removal

for root, dirs, files in os.walk(directory):
    for file in files:
        if file.endswith(".csv"):
            f = open(file, 'r')
            print(file)
            
            X_opened = readCSV(file)
            l.append(X_opened.reset_index())
            
            # perform some calculation could be performing here!
            
            f.close()

# :::::::::::::::::::::::::: DATA RESHAPING PART ::::::::::::::::::::::::::::::
# Join all dataframes into only one right here right now!
def joinDFs(list_of_dfs):
    
    new_l = []
    
    for this_array in range(0, len(l), 1):
        for array_row in range(0, len(l[this_array]), 1):
            
            new_l.append(dict(l[this_array].ix[array_row]))
    
    df = pd.DataFrame(new_l)
    
    return df
# Function made it's job. <--------------------------

my_db = joinDFs(l)[["Submarket", "Built year", "Price max.", "Price per max. size", "Size max.", "Timestamp"]].reset_index()

# ::::::::::::::::::::DATA VISUALIZATION BEGINS HERE! :::::::::::::::::::::::::
# Import packages and modules for data visualization
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid", palette="pastel", color_codes=True)

# :::::::::::::::::::::: Plot the TIMELINE with Prices ::::::::::::::::::::::::

# DRAW A NESTED BOXPLOT :::::::::::::::::::::::::::::::::::::::::::::::::::::::
# (https://seaborn.pydata.org/examples/grouped_boxplot.html)
fig, ax = plt.subplots()
fig.set_size_inches(11.7, 8.27)
#g = sns.boxplot(x = "Submarket", y = "Price per max. size", data = my_db, palette = "Blues", fliersize = 7, whis = 1.5, 
#                saturation = 0.1, hue_order = "Price per max. size")

g = sns.boxplot(x = "Submarket", y = "Price per max. size", data = my_db, palette = "Blues", fliersize = 7, whis = 1.5, 
                saturation = 0.1, hue = "Timestamp")

plt.xticks(rotation = 90)
g.set_xlabel("Submarkets of Dusseldorf", fontsize = 16)
g.set_ylabel("Price per square meter (€)", fontsize = 16)
g.tick_params(labelsize = 14)

medians = my_db.groupby(['Submarket'])['Price per max. size'].median().values
median_labels = [str(np.round(s, 2)) for s in medians]
pos = range(len(medians))
for tick,label in zip(pos,ax.get_xticklabels()):
    ax.text(pos[tick] + 0.1, medians[tick] + 10, median_labels[tick], 
            horizontalalignment='center', size=10, color='black', weight='semibold', ha = "left")

maxs = my_db.groupby(['Submarket'])['Price per max. size'].max().values
maxs_labels = [str(np.round(s, 2)) for s in maxs]
    
means = my_db.groupby(['Submarket'])['Price per max. size'].mean().values
means_labels = [str(np.round(s, 2)) for s in means]

pos = range(len(medians))
for tick, label in zip(pos,ax.get_xticklabels()):
    ax.text(pos[tick], ((maxs[tick] + maxs[tick] * 0.10) /2.5) + 25, means_labels[tick], 
            horizontalalignment='center', size=10, color='green', weight='semibold', ha = "center")
    
      
# Second attempt ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# Explanation: https://stackoverflow.com/questions/39228121/how-to-plot-dates-on-the-x-axis-using-seaborn-or-matplotlib
import seaborn as sns

my_db["Timestamp"] = pd.to_datetime(my_db["Timestamp"], errors = "coerce", box = False)

my_db["timepoint"] = 0.0
for row in range(0, len(my_db), 1):
    my_db.iat[row, my_db.columns.get_loc("timepoint")] = float(str(my_db.iat[row,my_db.columns.get_loc("Timestamp")]).split(" ")[0].replace("-", ""))

my_db2 = my_db.groupby(["Submarket", "timepoint"])["Price per max. size"].mean().reset_index()
my_db2["Unit"] = 0

"""my_index = 0
for row in range(0, len(my_db2), 1):
    if row == 0:
        my_db2.iat[row, my_db2.columns.get_loc("Unit")] = float(my_index)
    elif row > 0 and my_db2.iat[row, my_db2.columns.get_loc("Submarket")] == my_db2.iat[row - 1, my_db2.columns.get_loc("Submarket")]:
        my_index = my_index + 1
        my_db2.iat[row, my_db2.columns.get_loc("Unit")] = float(my_index)
    else:
        my_index = 0
        my_db2.iat[row, my_db2.columns.get_loc("Unit")] = float(my_index)"""
    
sns.set(style="darkgrid")

fig, ax = plt.subplots()
fig.set_size_inches(11, 7)

g = sns.tsplot(data=my_db2, time="timepoint",
           value="Price per max. size", 
           unit = "Unit", 
           condition="Submarket",
           legend = True,
           ci = "sd",
           color = sns.color_palette("cubehelix", 14))
g.tick_params(labelsize = 12)

"""
# -----------------------------------------------------------------------------
# DRAW A VIOLINPLOTS WITH OBSERVATIONS
# (https://seaborn.pydata.org/examples/grouped_boxplot.html)
fig, ax = plt.subplots()
fig.set_size_inches(11.7, 8.27)
g = sns.violinplot(x = "Submarket", y = "Price per max. size", data = my_db, palette = "Blues", inner = "points")
plt.xticks(rotation = 90)
g.set_xlabel("Submarkets of Dusseldorf", fontsize = 16)
g.set_ylabel("Price per square meter (€)", fontsize = 16)
g.tick_params(labelsize = 14)

medians = my_db.groupby(['Submarket'])['Price per max. size'].median().values
median_labels = [str(np.round(s, 2)) for s in medians]
pos = range(len(medians))
for tick,label in zip(pos,ax.get_xticklabels()):
    ax.text(pos[tick] + 0.1, medians[tick] + 10, median_labels[tick], 
            horizontalalignment='center', size=15, color='black', weight='semibold', ha = "left")
    
means = my_db.groupby(['Submarket'])['Price per max. size'].mean().values
means_labels = [str(np.round(s, 2)) for s in means]

maxs = my_db.groupby(['Submarket'])['Price per max. size'].max().values
maxs_labels = [str(np.round(s, 2)) for s in maxs]

pos = range(len(medians))
for tick, label in zip(pos,ax.get_xticklabels()):
    ax.text(pos[tick], ((maxs[tick] + maxs[tick] * 0.35) /2) + 25, means_labels[tick], 
            horizontalalignment='center', size=14, color='green', weight='semibold', ha = "center")
    
# GET AMOUNT OF PROPERTIES PER EACH SUBMARKET
counts = my_db.groupby(['Submarket'])["index"].count().to_dict()
print(counts)
# This part is not finished yet

# TIMELINE CHART BASED ON BUILT YEAR AND LAST RENOVATION YEAR
# (https://seaborn.pydata.org/examples/kde_joyplot.html)
xx = my_db["Built year"].as_matrix()

# Generate label axis
labels = []
for item in range(0, len(my_db), 1):
    labels.append(my_db.iat[item, my_db.columns.get_loc("Submarket")])
    
print(len(labels), type(labels))
g = np.tile(labels, 1)
print(len(g))

# Joing xx and g to a new DataFrame
df_xx_g = pd.DataFrame(dict(x=xx, g=g))

# Initialize the FacetGrid object
pal = sns.cubehelix_palette(10, rot=-.25, light=.7)
g = sns.FacetGrid(df_xx_g, row="g", hue="g", aspect=20, size=.6, palette=["#450F76", "#614B75", "#935BC7", "#352048"])

# Draw the densities in a few steps
g.map(sns.kdeplot, "x", clip_on=False, shade=True, alpha=1, lw=0.1, bw=.2)
g.map(sns.kdeplot, "x", clip_on=False, color="w", lw=2, bw=.2)
g.map(plt.axhline, y=0, lw=2, clip_on=False)

# Define and use a simple function to label the plot in axes coordinates
def label(x, color, label):
    ax = plt.gca()
    ax.text(1.0, .8, label, fontweight="bold", color=color, 
            ha="right", va="center", transform=ax.transAxes)
    
g.map(label, "x")

# Set the subplots to overlap
g.fig.subplots_adjust(hspace=+0.1555)

# Remove axes details that don't play will with overlap
g.set_titles("")
g.set(yticks=[])
g.despine(bottom=True, left=True)"""

gammas = sns.load_dataset("gammas")
ax = sns.tsplot(time="timepoint", value="BOLD signal",
                 unit="subject", condition="ROI",
                 data=gammas)

def changeDateFormat():
    from datetime import datetime
    
    today_value = str(datetime.datetime.now()).split(" ")[0]
    my_year = today_value.split('-')[0]
    my_month = today_value.split('-')[1]
    my_day = today_value.split('-')[2]
    
    new_date = my_month + "/" + my_day + "/" + my_year
    return new_date

print(changeDateFormat())
    