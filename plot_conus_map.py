#Import packages & other scripts
import os, sys
import requests
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.io.shapereader import Reader
from cartopy.feature import ShapelyFeature

from cartopy_wrapper import Map
from color_gradient import Gradient

#========================================================================================================
# User-defined settings
#========================================================================================================

#Report date(s) to plot
plot_start_date = dt.datetime(2020,1,22)
plot_end_date = dt.datetime(2020,3,1)

#Use blue marble background for the map. "directory_path" string is ignored if setting==False.
# ** "directory_path" must be a folder with an image and an "images.json" file, in accordance with Cartopy's ax.background_img() function:
# ** https://scitools.org.uk/cartopy/docs/v0.15/matplotlib/geoaxes.html#cartopy.mpl.geoaxes.GeoAxes.background_img
# ** A Blue Marble image and directory are included in this repository.
background_image = {'setting': False,
                    'directory_path': "enter_full_directory_path_here"}

#Whether to save image or display. "directory_path" string is ignored if setting==False.
save_image = {'setting': False,
              'directory_path': "enter_full_directory_path_here"}

#What to plot (confirmed, deaths, recovered, ongoing, daily)
plot_type = "confirmed"

#========================================================================================================
# Get COVID-19 case data
#========================================================================================================

"""
COVID-19 case data is retrieved from John Hopkins CSSE:
https://github.com/CSSEGISandData/COVID-19
"""

#Avoid re-reading case data if it's already stored in memory
try:
    cases
except:
    print("--> Reading in COVID-19 case data from John Hopkins CSSE")

    #Construct list of dates with data available, through today
    start_date = dt.datetime(2020,1,22)
    iter_date = dt.datetime(2020,1,22)
    end_date = dt.datetime.today()
    dates = []
    while iter_date <= end_date:
        strdate = iter_date.strftime("%m-%d-%Y")
        url = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{strdate}.csv'
        request = requests.get(url)
        if request.status_code == 200: dates.append(iter_date)
        iter_date += dt.timedelta(hours=24)

    #US states list
    state_abbr = {
        'AL':'Alabama',
        'AK':'Alaska',
        'AZ':'Arizona',
        'AR':'Arkansas',
        'CA':'California',
        'CO':'Colorado',
        'CT':'Connecticut',
        'DE':'Delaware',
        'DC':'District of Columbia',
        'FL':'Florida',
        'GA':'Georgia',
        'HI':'Hawaii',
        'ID':'Idaho',
        'IL':'Illinois',
        'IN':'Indiana',
        'IA':'Iowa',
        'KS':'Kansas',
        'KY':'Kentucky',
        'LA':'Louisiana',
        'ME':'Maine',
        'MD':'Maryland',
        'MA':'Massachusetts',
        'MI':'Michigan',
        'MN':'Minnesota',
        'MS':'Mississippi',
        'MO':'Missouri',
        'MT':'Montana',
        'NE':'Nebraska',
        'NV':'Nevada',
        'NH':'New Hampshire',
        'NJ':'New Jersey',
        'NM':'New Mexico',
        'NY':'New York',
        'NC':'North Carolina',
        'ND':'North Dakota',
        'OH':'Ohio',
        'OK':'Oklahoma',
        'OR':'Oregon',
        'PA':'Pennsylvania',
        'RI':'Rhode Island',
        'SC':'South Carolina',
        'SD':'South Dakota',
        'TN':'Tennessee',
        'TX':'Texas',
        'UT':'Utah',
        'VT':'Vermont',
        'VA':'Virginia',
        'WA':'Washington',
        'WV':'West Virginia',
        'WI':'Wisconsin',
        'WY':'Wyoming',
    }

    #Create entry for each US state, along with Diamond Princess
    cases = {}
    inverse_state_abbr = {v: k for k, v in state_abbr.items()}
    for key in ['diamond princess'] + [key.lower() for key in inverse_state_abbr.keys()]:
        cases[key] = {'date':dates,
                        'confirmed':[0 for i in range(len(dates))],
                        'deaths':[0 for i in range(len(dates))],
                        'recovered':[0 for i in range(len(dates))],
                        'active':[0 for i in range(len(dates))],
                        'daily':[0 for i in range(len(dates))]}

    #Construct list of dates
    start_date = dates[0]
    end_date = dates[-1]
    while start_date <= end_date:

        #Read in CSV file
        strdate = start_date.strftime("%m-%d-%Y")
        url = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{strdate}.csv'
        df = pd.read_csv(url)
        df = df.fillna(0) #replace NaNs with zero

        #Isolate cases to only those in US
        df_us = df.loc[df["Country/Region"] == "US"]

        #Iterate through every US case
        for _,row in df_us.iterrows():

            #Get state/province name
            location  = row['Province/State']

            #Get index of date within list
            idx = dates.index(start_date)
            
            #Special handling for 2/21/2020
            if start_date.strftime("%Y%m%d") == "20200221":
                if "Lackland, TX" in location or "Travis, CA" in location or "Ashland, NE" in location:
                    location = location + "(Diamond Princess)"

            #Handle Diamond Princess cases separately
            if "Diamond Princess" in location:
                cases["diamond princess"]['confirmed'][idx] += int(row['Confirmed'])
                cases["diamond princess"]['deaths'][idx] += int(row['Deaths'])
                cases["diamond princess"]['recovered'][idx] += int(row['Recovered'])
                cases["diamond princess"]['active'][idx] += int(row['Confirmed']) - int(row['Recovered']) - int(row['Deaths'])
                if idx == 0:
                    cases["diamond princess"]['daily'][idx] = np.nan
                else:
                    cases["diamond princess"]['daily'][idx] = cases["diamond princess"]['confirmed'][idx] - cases["diamond princess"]['confirmed'][idx-1]
                
            #Otherwise, handle states
            else:
                #Handle state abbreviation vs. full state name
                if ',' in location:
                    abbr = (location.split(",")[1]).replace(" ","")
                    state = state_abbr.get(abbr)
                else:
                    state = str(location)

                #Add cases to entry for this state & day
                if state.lower() in cases.keys():
                    cases[state.lower()]['confirmed'][idx] += int(row['Confirmed'])
                    cases[state.lower()]['deaths'][idx] += int(row['Deaths'])
                    cases[state.lower()]['recovered'][idx] += int(row['Recovered'])
                    cases[state.lower()]['active'][idx] += int(row['Confirmed']) - int(row['Recovered']) - int(row['Deaths'])
                    if idx == 0:
                        cases[state.lower()]['daily'][idx] = np.nan
                    else:
                        cases[state.lower()]['daily'][idx] = cases[state.lower()]['confirmed'][idx] - cases[state.lower()]['confirmed'][idx-1]

        #Increment date by 1 day
        start_date += dt.timedelta(hours=24)

#========================================================================================================
# Handle map projection & geography
#========================================================================================================

#Create data colortable
max_val = 0.0
for key in [k for k in cases.keys() if k != "diamond princess"]:
    max_val = cases[key][plot_type][-1] if cases[key][plot_type][-1] > max_val else max_val

if plot_type == 'confirmed':
    if max_val < 40: max_val = 40
else:
    if max_val < 20: max_val = 20
color_obj = Gradient([['#FFFF00',1.0],['#EE7B51',int(max_val*0.3)]],
               [['#EE7B51',int(max_val*0.3)],['#B53079',int(max_val*0.7)]],
               [['#B53079',int(max_val*0.7)],['#070092',int(max_val*1.2)]])

#Create Cartopy projection
lon1 = -99.0
lat1 = 35.0
slat = 35.0
bound_n = 50.0
bound_s = 21.5
bound_w = -122.0
bound_e = -72.5
m = Map('LambertConformal',central_longitude=lon1,central_latitude=lat1,standard_parallels=[slat],res='h')
proj = m.proj

#Read in US states shapefile
fname = r'cb_2018_us_state_500k/cb_2018_us_state_500k.shp'
shp = Reader(fname)
print("--> Read in US states shapefile")

#Iterate through dates
while plot_start_date <= plot_end_date:
    
    #Update on current date
    print(f"------> Report date {plot_start_date}")
    
    #Create figure
    fig = plt.figure(figsize=(14,9),dpi=125)
    ax = plt.axes(projection=proj)
    ax.set_extent([bound_w,bound_e,bound_s,bound_n])
    print("--> Created matplotlib figure & map projection")

    #Draw map background
    if background_image['setting'] == True:
        print("--> Starting to read in blue marble image")
        os.environ["CARTOPY_USER_BACKGROUNDS"] = background_image['directory_path']
        ax.background_img(name='BM', resolution='low')
        background_image['alpha'] = 0.5
        print("--> Plotted blue marble image")
    else:
        background_image['alpha'] = 1.0

    #Draw geography
    m.drawstates()
    m.drawcoastlines()
    m.drawcountries()
    print("--> Plotted geographic & political boundaries")

    #========================================================================================================
    # Plot data
    #========================================================================================================

    #Iterate through all states
    total_cases = 0
    for record, state in zip(shp.records(), shp.geometries()):

        #Reference state name as a separate variable
        name = record.attributes['NAME']
        
        #Get state's case data for this date
        if name.lower() in cases.keys():
            idx = cases[name.lower()]['date'].index(plot_start_date)
            if plot_type not in ['confirmed','deaths','recovered','ongoing','daily']: plot_type = 'confirmed'
            case_number = cases[name.lower()][plot_type][idx]
            total_cases += case_number
        else:
            continue

        #Exclude states outside of CONUS & territories from map, but include in case count
        if name.lower() in ['alaska','hawaii','guam','puerto rico','commonwealth of the northern mariana islands',
                                                'american samoa','united states virgin islands']: continue

        #------------------------------------------------------------------------------------

        #Set background state color
        if case_number > 0:
            cmap = color_obj.get_cmap([case_number])
            facecolor = color_obj.colors[0]
        else:
            facecolor = '#eeeeee'

        #Draw states
        ax.add_geometries([state], ccrs.PlateCarree(), facecolor=facecolor, edgecolor='black', linewidth=0.5,
                          alpha=background_image['alpha'])

        #------------------------------------------------------------------------------------

        #Format case number as a string
        case_str = str(case_number)
        if case_number == 0: case_str = " - "

        #Label case number using state centroid
        centroid = state.centroid.bounds
        lon = centroid[0]; lat = centroid[1]

        #Adjust certain states to make plotting nicer
        if name == "Louisiana": lon = lon - 0.5
        if name == "Florida": lon = lon + 0.7
        if name == "California": lat = lat - 1.0
        if name == "Maryland":
            lon = lon - 0.1; lat = lat + 0.2
        if name == "Michigan":
            lon = lon + 0.5; lat = lat - 0.5
        if name in ['Delaware','Rhode Island']:
            lon = lon - 0.1

        #For some states, use arrows instead of direct labels
        state_transform = {
            'New Jersey':(2.0,-0.7),
            'Delaware':(2.5,-0.5),
            'Maryland':(3.2,-1.8),
            'Rhode Island':(1.5,-1.5),
            'District of Columbia':(3.0,-3.0),
        }
        if name in state_transform.keys():
            transform = ccrs.PlateCarree()._as_mpl_transform(ax)
            x_tr, y_tr = state_transform.get(name)
            ncolor = 'k' if background_image['alpha'] == 1 else 'w'
            ax.annotate(case_str,
                        xy=(lon,lat), xycoords=transform,
                        xytext=(lon+x_tr,lat+y_tr), 
                        fontweight='bold', ha='center', va='center', color=ncolor, fontsize=12,
                        arrowprops=dict(arrowstyle="->",
                                        shrinkA=0, shrinkB=0,
                                        connectionstyle="arc3", 
                                        color=ncolor),
                        transform=ccrs.PlateCarree())
        else:
            ax.text(lon, lat, case_str, color='k', fontsize=12,
                    fontweight='bold', ha='center', va='center', transform=ccrs.PlateCarree())

    #Add plot type and labels
    plot_name = {
        'confirmed':'Case Count',
        'deaths':'Death Count',
        'recovered':'Recovered Cases',
        'ongoing':'Ongoing Cases',
        'daily':'New Daily Cases'
    }
    plt.title(f"CONUS States COVID-19 {plot_name.get(plot_type)}",fontweight='bold',fontsize=18,loc='left')
    add_label = 'as of' if plot_type in ['ongoing','daily'] else 'through'
    plt.title(f"Cases {add_label} {plot_start_date.strftime('%d %B %Y')}",fontweight='bold',fontsize=14,loc='right')

    plt.text(0.99,0.01,'Data from John Hopkins CSSE:\nhttps://github.com/CSSEGISandData/COVID-19',
             ha='right',va='bottom',transform=ax.transAxes,fontsize=11,color='white',fontweight='bold')
    
    dp_cases = cases['diamond princess'][plot_type][idx]
    plt.text(0.01,0.01,f'Diamond Princess Cases: {dp_cases}\n\nTotal US Cases: {total_cases}\nTotal US Cases With Diamond Princess: {total_cases+dp_cases}',
             ha='left',va='bottom',transform=ax.transAxes,fontsize=11,color='w',fontweight='bold',bbox={'facecolor':'k', 'alpha':0.4, 'boxstyle':'round'})
    
    #Save image?
    if save_image['setting'] == True:
        savepath = os.path.join(save_image['directory_path'],f"{plot_type}_{plot_start_date.strftime('%Y%m%d')}.png")
        plt.savefig(savepath,bbox_inches='tight')
    else:
        plt.show()
    plt.close()
    
    #Increment date
    plot_start_date += dt.timedelta(hours=24)

#Alert script is done
print("Done!")
