#!/usr/bin/env python

import tkinter as tk
from tkinter import ttk
from tkinter import Menu
import paho.mqtt.client as mqtt
import logging
import json
from datetime import datetime, timedelta
from time import strftime
import time, threading
import os
import csv
import requests  # for the openweather API fetch
from PIL import ImageTk, Image
import urllib.request
import io


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

# Set up lists for the workstations names representing their place in the room
row1 = ['OptiPlex-07', 'OptiPlex-08', 'OptiPlex-10', 'OptiPlex-17']
row2 = ['hp-pd-753', 'hp-pd-744', 'hp-pd-754', 'hp-pd-739', 'hp-pd-745', 'hp-pd-747', 'hp-pd-743', 'hp-pd-742', 'hp-pd-752', 'hp-pd-738']
row3 = []
row4 = ['hp-pd-749', 'hp-pd-748', 'hp-pd-741', 'hp-pd-740', 'hp-pd-736', 'hp-pd-746', 'hp-pd-755', 'hp-pd-751', 'hp-pd-737', 'hp-pd-750']
rowList = [row1, row2, row3, row4]

# OpenWeather variables
api_key = "f8f4f22707725e97b37a0edacc2f226c"
lat = '43.1769'
lon = '-70.8868'

rosterPath = "./"
os.chdir(rosterPath)
theFiles = [f for f in os.listdir() if os.path.isfile(f)]


#
### COLORS
green = '#008800'
ltgreen = '#abfaa9'
dkgreen = '#152614'
tangerine = '#ef8a17'
green2 = '#47af60'
offRed = '#ef2917'
### FONTS
font1 = ("Helvetica", "14", "bold")   # was 14
font2 = ("Times", "14", "bold italic")# same
font3 = ("Courier", "30", "bold") # was 30
font4 = ("Courier", "12", "bold") # was ?
font5 = ("Courier", "18", "bold") # was 18


### INSTANTIATE WINDOW ###
window = tk.Tk()
window.title('Dashboard v1')
window_width = '1800'
window_height = '750'
window.geometry(f'{window_width}x{window_height}')
# window.attributes('-fullscreen', True)  # makes tkinter full screen; comment out above
bdVar_outer = 5


# MenuBar section
menubar = Menu(window)
window.config(menu=menubar)
filemenu = Menu(menubar)
menubar.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="Exit", command=window.quit)

# The layout uses 3 frames; top, middle, bottom
frameTop = tk.Frame(window, bg=green2, bd=bdVar_outer, relief='sunken')  # I had width and heights assigned
frameTop.pack(fill='x'  )
frameMiddle = tk.Frame(window, bg=green)                      # but they dont do anything
frameMiddle.pack()
frameBottom = tk.Frame(window, bg=green2, bd=bdVar_outer, relief='sunken')
frameBottom.pack(fill = 'both', anchor='s')

logging.debug("")
# topLabel = tk.Label(frameTop, text="This is the ToP", width=50, height=5).pack()
timeLabel = tk.Label(frameTop, font=("Courier", 30, 'bold'), bg=green, fg="white", bd =30)
timeLabel.grid(row =0, column=1)
# the clock function itself is at the bottom
# it needs to launch functions that have to be defined first


# WEATHER LABELS
weatherLabel = tk.Label(frameTop, text="the weather", bd=15, font=font3)
weatherLabel.grid(row=0, column=2)

weatherIconLabel = tk.Label(frameTop, image="")
weatherIconLabel.grid(row=0, column=3)

weatherTempLabel = tk.Label(frameTop, text='temp', bd=15, font=font3)
weatherTempLabel.grid(row=0, column=4)

weatherWindSpeedLabel = tk.Label(frameTop, text='wind speed', bd=15, font=font4)
weatherWindSpeedLabel.grid(row=0, column=5)

weatherWindGustLabel = tk.Label(frameTop, text='wind gust', bd=15, font=font4)
weatherWindGustLabel.grid(row=0, column=6)

weatherFeelsLikeLabel = tk.Label(frameTop, text='feels like', bd=15, font=font5)
weatherFeelsLikeLabel.grid(row=0, column=7)


# FRAME MIDDLE
#  This allows for easier changes. h, w, bd
xPad = 0
bdVar = 5
widthVar = round((int(window_width))/200)
heightVar = round((int(window_height))/300)  # this doesn't seem to be doing anything, or at least it does not control the height
bgVar = green


class workstation:
    def __init__(self, parent, row, column, hostname):
        self.parent = parent
        self.hostname = hostname
        self.row = row
        self.column = column

        logging.debug("Workstation class called:  %s, %s, %s"  % (row, column, hostname))

        # create the host frame in the middle frame
        self.frame = tk.Frame(frameMiddle, width=widthVar, height=heightVar, bd=bdVar, relief='raised')
        self.frame.grid(row=row, column=column, padx=xPad, pady=(0))
        logging.debug("created the host frame")

        # create hostname label
        self.hostnameLabel = tk.Label(self.frame, width=widthVar, height=1, text=hostname, font = font1, padx=15)
        self.hostnameLabel.pack()
        logging.debug("Where's the host label??? %s" %(hostname))

        # create username label and add to dictionary
        self.nameLabel = tk.Label(self.frame, width=widthVar, height=2, font=font2, fg='blue')
        self.nameLabel.pack()

        # create timestamp object
        self.timestamp = datetime.now()
        self.timestamp_sys = datetime.now()

# testFrame = workstation(frameMiddle, 1, 7, 'testhost')
# print(testFrame.hostname, testFrame.row, testFrame.column)

# Roster Frame
frameMiddle_roster = tk.Frame(frameMiddle, width=50, bd=5, relief='groove')
frameMiddle_roster.grid(row=0, column=10, rowspan=4, sticky='NS')
# begin forming the drop down menuSelection by creating a StringVar that will hold the selection
menuSelection = tk.StringVar()
menuSelection.set("Select A Class")
# create a list of options/classes to choose from
options_list = ["ProgI","ProgII", "IntroG", "IntroW"]
dropDown = tk.OptionMenu(frameMiddle_roster, menuSelection, *options_list)
dropDown.pack()
# and  you need a submit button
submitButton = tk.Button(frameMiddle_roster, text='Submit', command= lambda:getSelection(menuSelection.get()))
submitButton.pack()
# TextBox Configuration
# inherits height and width; has scrollbars
textBox = tk.Text(frameMiddle_roster, width=200)
S = tk.Scrollbar(frameMiddle_roster)
S.pack(side=tk.RIGHT, fill=tk.Y)
textBox.pack(side=tk.LEFT, fill=tk.Y)
S.config(command=textBox.yview)
textBox.config(yscrollcommand=S.set)
textBox.insert(tk.END, 'data goes here')

### OpenWeather API Call
def getWeather(api_key, lat, lon):
    base_url = "http://api.openweathermap.org/data/2.5/weather?units=imperial&"
    complete_url = base_url + "appid=" + api_key + "&lat=" + lat + "&lon=" + lon
    response = requests.get(complete_url)
    x = response.json()

    if x['cod'] != "404":
        y = x["main"]
        current_temperature = str(y['temp']) + 'F'
        current_pressure = y['pressure']
        current_humidity = y['humidity']
        z = x['weather']
        weather_description = z[0]['description']
        weather_icon = z[0]['icon']
        wind_speed = x['wind']['speed']
        try:
            wind_gust = x['wind']['gust']
        except:
            wind_gust = '0 '
        feels_like = y['feels_like']
        print(f"The weather is {str(weather_description)}  AND THE WEATHER ICON IS {weather_icon}: wind_speed: {wind_speed}, Feels Like: {feels_like}")
    else:
        print("weather broken")
        weather_description = 'broken'
    return weather_description, weather_icon, current_temperature, wind_speed, wind_gust, feels_like

### OpenWeather icon pull
def getWeatherIcon(iconID):
    iconBaseURL = 'http://openweathermap.org/img/wn/'
    size = '@2x.png'
    url = iconBaseURL + iconID + size
    logging.debug('The URL is: %s', url)

    with urllib.request.urlopen(url) as u:
        raw_data = u.read()
    image = Image.open(io.BytesIO(raw_data))
    weatherIcon = ImageTk.PhotoImage(image)
    print(f'weatherIcon type is {type(weatherIcon)}')
    # return weatherIcon # this object should be a png
    # instead of returning, lets try to update the label here
    weatherIconLabel.configure(image = weatherIcon)
    weatherIconLabel.image=weatherIcon


# Create the username from fname and lname
# also packs other data into the return
def makeUserName(row):
    # print(f'makeUserName type of row: {type(row)}')
    course = row['Course']
    fname = row['First Name']
    lname = row['Last Name']
    if (len(row['Last Name']) < 5):  # do we need more letters from the fname?
        nfl = 6 - len(lname)  # number of first letters
        username = (f'{fname[0:nfl]}{lname[0:5]}').lower()
    else:
        username = (f'{fname[0]}{lname[0:5]}').lower()
        # row['username'] = userName
    # print(course, fname, lname, username)
    return course, fname, lname, username

# this opens a csv file and adds entris to the list
def getStudents(csvFile, list):
    with open(csvFile) as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        lineCount = 0
        for row in csv_reader:
            list.append(makeUserName(row))

# This is the beginning of the roster process
# theFiles is created at the top, then we loop for csv files and send them off
listOfStudents = []          # initialize a list to pass in to the function
for fileName in theFiles:    # loop through the csv files
    if fileName[-3:] == 'csv':
        getStudents(fileName, listOfStudents)


classDict = {'ProgI':'921250-1', 'ProgII':'922251-1', 'IntroG':'990225-1 INTRO PROGRAM', 'IntroW':'990225-2 INTRO PROGRAM'}
# classDict = {'ProgI':'921250-1', 'ProgII':'922251-1', 'IntroG':'990228-1 INTRO PROGRAM', 'IntroW':'990228-2 INTRO PROGRAM'}

activeRosterList = []
def getSelection(selection):
    global activeRosterList
    activeRosterList = []
    textBox['state'] = 'normal'
    textBox.delete("1.0", "end")

    for record in listOfStudents:
        if record[0][0:8] == classDict[selection][0:8]:
            activeRosterList.append(record)
            textBox.insert('end', f'{record[1]} {record[2]}\n')
    textBox['state'] = 'disabled'

# called from processMessage, to see if the username is in the activeRosterList
def removeName(name):
    logging.debug('Remove %s', name)
    for idx, entry in enumerate(activeRosterList):
        # print(idx, entry[-1])
        if name[0:5] == entry[-1][0:5]:
            activeRosterList.pop(idx)
            textBox['state'] = 'normal'
            textBox.delete("1.0", "end")
            for item in activeRosterList:
                textBox.insert('end', f'{item[1]} {item[2]}\n')
            textBox['state'] = 'disabled'



# Stuff in the Bottom Frame
bottomLabel = tk.Label(frameBottom, text='this is the bottom label, with lttle config').pack(fill='both')
exitButton = tk.Button(frameBottom, text='Exit', padx=10, pady=5, command=window.quit).pack()


frameMiddle.grid_columnconfigure(10, weight=1)
# The middle frame has a frame for each workstation.
# These are all in frame middle, the host and user frames will be in each of these
# iterate throught the row files and create
objectDict = {}
for ridx, row in enumerate(rowList):    # ridx = row index
    for hidx, host in enumerate(row):   # hidx = host index
        objectDict[host] = workstation(frameMiddle, ridx, hidx, host)


# Refresh Button
def refreshHosts():
    for hostName in objectDict:
        objectDict[hostName].nameLabel.config(text = '')
refreshButton = tk.Button(frameBottom, text='Refresh', padx=10, pady=5, command=refreshHosts).pack()

# I generated multiple time objects to simplify testing
# and may use them in the future for other checks
sec1 = timedelta(seconds=1)
sec10 = timedelta(seconds=10)
sec30 = timedelta(seconds=30)
sec45 = timedelta(seconds=45)
min1 = timedelta(minutes=1)
min5 = timedelta(minutes=5)

# called periodically by the clock to see if users are stale
def checkUser(now):
    logging.debug("CheckUser:  yup, and this")
    # print(f'CheckUser: Now is {now} and is of type {type(now)}')  # amateurish debugging
    for host in objectDict:
        if (now - (objectDict[host].timestamp)) > sec30:
            objectDict[host].nameLabel.config(text = '', fg='red')
        if (now - (objectDict[host].timestamp_sys)) > min1:
            objectDict[host].hostnameLabel.config(fg='red')

# MQTT Section
def on_connect(client, userdata, flags, rc):
    logging.info("OnConnect:  Connected with result code {0}".format(str(rc)))
    # client.subscribe("IamAlive")
    client.subscribe([("IamAlive",0), ("IamAlive-sys",0)])
    # that worked, but I wasn't ready for inconsistant values

def on_message(client, userdata, msg):
    # window.update()  # this will do away with mainloop updating only on messages
    message = msg.payload.decode("utf-8")
    topic = msg.topic
    values = json.loads(msg.payload)
    hostName = values["hostname"]
    logging.debug("OnMessage: hostName: %s, topic: %s, values: %s", hostName, topic, values)
    if topic == 'IamAlive':
        process_message(values)
    elif topic == 'IamAlive-sys':
        process_message_sys(values)


# i thought i would be slick and move this up the page
# but dependencies above, duh
def process_message_sys(values):
    logging.debug("ProcessMessage_Sys: hostname: %s\n", values["hostname"])
    hostName = values["hostname"]
    objectDict[hostName].hostnameLabel.config(fg='green')
    objectDict[hostName].timestamp_sys = datetime.now()

# This is for user messages
def process_message(values):
    # values is a dict
    hostName = values["hostname"]
    userName = values["username"]
    logging.debug("ProcessMessage: hostname: %s  username: %s", hostName, userName)
    objectDict[hostName].nameLabel.config(text = userName, fg='blue')
    objectDict[hostName].timestamp = datetime.now()
    removeName(userName)
    # print(f'ProcessMessage:  {objectDict}')


def on_disconnect(client, userdata, rc=0):
    logging.debug("Disconnected result code " + str(rc))
    client.loop_stop()


client = mqtt.Client("iamalivedash")
client.on_connect = on_connect
client.on_message = on_message
client.connect('10.1.10.8', 1883)
client.loop_start()

# timeHack is just an index that I am using to trigger events
# that don't need to happen every second
timeHack = 0
timeHack2 = 0
def digitalclock():
   global timeHack
   global timeHack2
   text_input = strftime("%H:%M:%S")
   timeLabel.config(text=text_input)
   timeHack = timeHack + 1
   if timeHack > 50:
       checkUser(datetime.now())
#       match datetime.now().strftime('%H:%M'):

   if timeHack2 == 0:
       print("############################################################## getWeather ###################################")
       weatherReturn, weatherIconID, weatherTemp, windSpeed, windGust, feelsLike =  getWeather(api_key, lat, lon)
       print(f'Type is {type(weatherReturn)} and the value is {weatherReturn} #### the type of icon is {type(weatherIconID)} and the temperature is {weatherTemp}')
       weatherLabel.config(text = weatherReturn)
       weatherTempLabel.config(text = f'{weatherTemp}\u00B0')
       weatherWindSpeedLabel.config(text = f'Wind Speed\n{windSpeed}mph')
       weatherWindGustLabel.config(text = f'Gusts to\n{windGust}mph')
       weatherFeelsLikeLabel.config(text = f'Feels Like\n{feelsLike}\u00B0F')


       # was going to try and update here, but going up to the function instead.
       # theWeatherIcon = getWeatherIcon(weatherIconID)
       # print(f'theWeatherIcon type is {type(theWeatherIcon)}')
       # weatherIconLabel.config(img = theWeatherIcon)

       getWeatherIcon(weatherIconID)

   timeHack2 = timeHack2 + 1
   if timeHack2 > 60:
       timeHack2 = 0
   timeLabel.after(200, digitalclock)


digitalclock()
window.mainloop()
