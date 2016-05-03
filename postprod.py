#!/bin/python
import os, sys, re, glob
import datetime
from datetime import timedelta
import urllib.request

## To test the script (to not write files or convert them) you can set DEBUG to True
DEBUG = True

## Configs ##
audiofiles_folder = "/home/dennis/Audio" # without "/" at the end

# 1. shortcut, 2. filename/broadcast
broadcasts = {
              'll': 'linuxlounge',
              'pt': 'primetime',
              'ff': 'faldriansfeierabend'
             }
etherpad_url = "http://pad.theradio.cc/p"
## End Configs ##

## Set the date

input_year = input("Jahr? (z.B. 2016, fuer heutiges Datum einfach <ENTER>) > ")
day = ''
if input_year == "":
    year = datetime.date.today().year
    month = datetime.date.today().strftime('%m')
    day = datetime.date.today().strftime('%d')
else:
    while day == '':
        input_month = input("Monat? (z.B. 04) > ")
        input_day = input("Tag? (z.B. 19) > ")
        year = input_year
        month = input_month
        day = input_day

print("\033[1m# Datum: %s.%s.%s\033[0m" % (day, month, year))


## Find idjc files

audiofiles = glob.glob(audiofiles_folder + '/*.*')
flacfile = []
listfile = []
for filename in audiofiles:
    list = re.findall(r"idjc\.\[%s\-%s\-%s\]\[\d\d\:\d\d\:\d\d\]\.\d\d\.cue$" % (year, month, day), filename)
    if list != []:
        listfile = list[0]
    flac = re.findall(r"idjc\.\[%s\-%s\-%s\]\[\d\d\:\d\d\:\d\d\]\.\d\d\.flac$" % (year, month, day), filename)
    if flac != []:
        flacfile = flac[0]

if flacfile and listfile:
    print("\033[1m# FLAC-Datei gefunden: %s\033[0m" % flacfile)
    print("\033[1m# Playlist-Datei gefunden: %s\033[0m" % listfile)
elif flacfile == []:
    print("[ERR] FLAC-Datei nicht gefunden \n\n Folgende Dateien sind vorhanden:")
    for audiofile in audiofiles:
        print(audiofile)
    sys.exit()
elif listfile == []:
    sys.exit("[ERR] Playlist-Datei nicht gefunden")


## Set broadcast

broadcast = ""
while broadcast == "":
    input_broadcast = input("Sendung? " + str(broadcasts.keys()) + " > ")
    try:
        broadcast = str(broadcasts[input_broadcast])
    except:
        pass

## Set episode number

input_number = input("Folgenzahl? (z.B. 197) > ")

newfilename = str(year) + str(month) + str(day) + '_' + broadcast + input_number
if DEBUG == False:
    os.system("opusenc %s/%s.flac %s/%s.opus" % (audiofiles_folder, newfilename, audiofiles_folder, newfilename))
    #os.system("mv %s/%s %s/%s.flac" % (audiofiles_folder, flacfile, audiofiles_folder, newfilename))
print("\033[1m# FLAC-Datei umgewandelt \n# von '%s'\n# zu \033[0m\n%s/%s.opus" % (flacfile, audiofiles_folder, newfilename ))

## Convert .cue-file to .psc-file

cue_file = open(audiofiles_folder + "/" + listfile, "r")
cue_content = cue_file.readlines()
pre_psc_content = []
item_title = ""
item_timecode = ""
for line in cue_content:
    got_timecode = re.findall(r'(?<=   INDEX 01 ).*(?=\r)', line)
    if got_timecode and re.findall(r'^\d\d:\d\d:\d\d$', got_timecode[0]):
        item_timecode = "00:" + got_timecode[0] + "0"
    elif got_timecode:
        item_timecode = got_timecode[0][1:] + "." + got_timecode[0][:2] + "0"
       
    got_title = re.findall(r'(?<=   TITLE \").*(?=\")', line)
    if got_title:
        item_title = got_title[0]
    if item_timecode:
        pre_psc_content.append(item_timecode + " " + item_title)

# Every item should only be twice in the list (beginning and ending)

psc_content = []
last_line = ""
last_title = ""
for line in pre_psc_content:
    title = re.findall(r'(<=\d\d:\d\d\:\d\d\.\d\d\d\ )*', line)
    if last_line != line and title != last_title:
        psc_content.append(line)
    last_line = line
    last_title = title

if DEBUG == False:
    with open(audiofiles_folder + "/" + newfilename + ".psc", "w") as psc_file:
        psc_file.write('\n'.join(psc_content))

print("\033[1m# Playlist-Datei umgewandelt \n# von '%s'\n# zu\033[0m\n%s/%s.psc" % (listfile, audiofiles_folder, newfilename))


## Get shownotes from etherpad

pad_id = ''
while pad_id == '':
    pad_id = input("\033[1mEtherpad: Pad ID? (z.B. LL220) > \033[0m")

pad_url = etherpad_url + "/" + pad_id + "/export/txt"
with urllib.request.urlopen(pad_url) as ep_content:
    ep_content = ep_content.read().decode('utf-8')
    print('\n\033[1m––– Content of %s –––\033[0m' % (pad_url))
    for line in ep_content.split("\n"):
        if not re.match(r"\s+.*", line):
            print(line)
    print('\033[1m––– End –––\033[0m\n')
