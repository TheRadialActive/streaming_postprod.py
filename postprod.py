#!/bin/python
import os, sys, re, glob
import datetime
from datetime import timedelta
import urllib.request
from argparse import ArgumentParser

ms = sys.modules[__name__]

## To test the script (to not write files or convert them) you can set DEBUG to True
ms.DEBUG = False

## Configs ##
audiofiles_folder = "/home/dennis/Audio" # without "/" at the end

# 1. shortcut, 2. filename/broadcast
broadcasts = {
              'll': 'linuxlounge',
              'pt': 'primetime',
              'ff': 'faldriansfeierabend'
             }
audiofiles_url = "https://rec.theradio.cc/auphonic" # without "/" at the end
audioformats = ['.mp3', '.ogg', '.opus']
etherpad_url = "http://pad.theradio.cc/p" # without "/" at the end
## End Configs ##


## Set the date
def auto_date():
    ms.year = datetime.date.today().year
    ms.month = datetime.date.today().strftime('%m')
    ms.day = datetime.date.today().strftime('%d')

def set_date():
    auto_date()
    input_year = input("Jahr? (z.B. %s, fuer heutiges Datum einfach <ENTER>) > " % ms.year)
    if input_year == "":
        print("\033[1m# Generiertes Datum: %s.%s.%s\033[0m" % (ms.day, ms.month, ms.year))
    else:
        input_day = ""
        while input_day == '':
            input_month = input("Monat? (z.B. %s) > " % ms.month)
            input_day = input("Tag? (z.B. %s) > " % ms.day)
            ms.year = input_year
            ms.month = input_month
            ms.day = input_day
        print("\033[1m# Datum: %s.%s.%s\033[0m" % (ms.day, ms.month, ms.year))


## Find idjc files
def find_idjc_files(opt_audiofiles):
    audiofiles = glob.glob(opt_audiofiles + '/*.*')
    ms.flacfile = []
    ms.listfile = []
    for filename in audiofiles:
        list = re.findall(r"idjc\.\[%s\-%s\-%s\]\[\d\d\:\d\d\:\d\d\]\.\d\d\.cue$" % (ms.year, ms.month, ms.day), filename)
        if list != []:
            ms.listfile = list[0]
        flac = re.findall(r"idjc\.\[%s\-%s\-%s\]\[\d\d\:\d\d\:\d\d\]\.\d\d\.flac$" % (ms.year, ms.month, ms.day), filename)
        if flac != []:
            ms.flacfile = flac[0]

    if ms.flacfile and ms.listfile:
        print("\033[1m# FLAC-Datei gefunden: %s\n# Playlist-Datei gefunden: %s\033[0m" % (ms.flacfile, ms.listfile))
    elif ms.flacfile == []:
        print("\033[1m# [ERR] FLAC-Datei nicht gefunden \n\n Folgende Dateien sind vorhanden:\033[0m")
        for audiofile in audiofiles:
            print(audiofile)
        sys.exit()
    elif ms.listfile == []:
        sys.exit("\033[1m# [ERR] Playlist-Datei nicht gefunden\033[0m")


## Set broadcast
def set_broadcast(broadcast):
    broadcast_arg = broadcast
    while broadcast == "":
        broadcast_list_str = ""
        for key in broadcasts.keys():
            broadcast_list_str = broadcast_list_str + key + ", "
        broadcast = input("Sendung? (" + broadcast_list_str + ") > ")
    try:
        broadcast_name = str(broadcasts[broadcast])
        print("\033[1m# Sendung %s ausgewählt\033[0m" % broadcast_name)
        return broadcast_name
    except:
        pass


## Set episode number
def rename_audiofiles(dir, broadcast_name, epi_no):
    if dir == '':
        dir = audiofiles_folder
    if broadcast_name == '':
        broadcast_name = set_broadcast('')
    if epi_no == '':
        epi_no = input("Folgenzahl? (z.B. 225) > ")

    ms.newfilename = str(year) + str(month) + str(day) + '_' + broadcast_name + epi_no
    if ms.DEBUG == False:
        os.system("cp %s/%s %s/%s.flac" % (dir, flacfile, dir, ms.newfilename))
        os.system("opusenc %s/%s.flac %s/%s.opus" % (dir, ms.newfilename, dir, ms.newfilename))
    else:
        print("dir: %s, newfilename: %s, flacfile: %s, broadcast_name: %s, epi_no: %s" % (dir, ms.newfilename, flacfile, broadcast_name, epi_no))
    print("\033[1m# FLAC-Datei umgewandelt \n# von '%s'\n# zu %s/%s.opus\033[0m" % (ms.flacfile, dir, ms.newfilename ))


## Convert .cue-file to .psc-file
def convert_cue_psc(dir, **args):
    if args:
        cue_file = open(args["cue_filepath"], "r")
    else:
        cue_file = open(dir + "/" + ms.listfile, "r")
    cue_content = cue_file.readlines()
    pre_psc_content = []
    item_title = ""
    item_timecode = ""
    for line in cue_content:
        got_timecode = re.findall(r'(?<=    INDEX 01 ).*', line)
        if got_timecode and re.match(r'^(?P<minutes>\d\d):(?P<seconds>\d\d):(?P<millisec>\d\d)$', got_timecode[0]):
            timecode_re = re.match(r'^(?P<minutes>\d\d):(?P<seconds>\d\d):(?P<millisec>\d\d)$', got_timecode[0])
            tc_h = str(int(timecode_re.group('minutes'))//60).zfill(2)
            tc_min = str(int(timecode_re.group('minutes'))%60).zfill(2)
            tc_sec = timecode_re.group('seconds')
            tc_ms = timecode_re.group('millisec')
            item_timecode = tc_h + ":" + tc_min + ":" + tc_sec + "." + tc_ms + "0"
        elif got_timecode:
            item_timecode = got_timecode[0][1:] + "." + got_timecode[0][:2] + "0"

        got_title = re.findall(r'(?<=   TITLE \").*(?=\")', line)
        if got_title:
            item_title = got_title[0]
        if item_timecode:
            pre_psc_content.append(item_timecode + " " + item_title)

    if not pre_psc_content:
        sys.stderr.write("\033[1m# [ERR] Keine Timecode gefunden\033[0m")
        sys.exit()

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

    if ms.DEBUG == False and args == False:
        with open(dir + "/" + ms.newfilename + ".psc", "w") as psc_file:
            psc_file.write('\n'.join(psc_content))
        print("\033[1m# Playlist-Datei umgewandelt \n# von '%s'\n# zu %s/%s.psc\033[0m" % (listfile, dir, ms.newfilename))
    elif args:
        psc_filepath = str(args["cue_filepath"]) + ".psc"
        with open(psc_filepath, "w") as psc_file:
            psc_file.write('\n'.join(psc_content))
        print("\033[1m# Playlist-Datei umgewandelt \n# von '%s'\n# zu %s\033[0m" % (str(args["cue_filepath"]), psc_filepath))
    else:
        print("\033[1m# DEBUG: Playlist-Datei umgewandelt \n# von '%s'\n# zu %s/%s.psc\033[0m" % (listfile, dir, ms.newfilename))


## Get shownotes from etherpad
# print audio urls
def print_audio_urls(audio_url):
    if not audio_url:
        audio_url = ms.audiofiles_url
    print("\033[1mLinks der Audiodateien:\033[0m")
    for audioformat in audioformats:
        print(audio_url + '/' + ms.newfilename + audioformat)

def get_shownotes_ep(pad_link):
    pad_link_arg = pad_link
    while pad_link == '':
        pad_id = input("\033[1mEtherpad Lite ID? ('%s/<?>') > \033[0m" % etherpad_url)
        pad_link = etherpad_url + "/" + pad_id
    pad_txt_url = pad_link + "/export/txt"
    with urllib.request.urlopen(pad_txt_url) as ep_content:
        ep_content = ep_content.read().decode('utf-8')
        new_ep_content = ""
        for line in ep_content.split("\n"):
            if not re.match(r"^\s+\/\/.*$", line):
                line = re.sub(r"^(.*)\*\ ", "* ", line)
                new_ep_content = new_ep_content + line + "\n"
        if not pad_link_arg == "":
            sys.stdout.write(new_ep_content)
        else:
            print('\n\033[1m––– Content of %s –––\033[0m' % (pad_txt_url))
            print(new_ep_content)
            print('\033[1m––– End –––\033[0m\n')


## Create command line options
ap = ArgumentParser(description="Convert your idjc files to opus, rename audio files, convert cue to psc files and get shownotes from an etherpad lite instance")
if __name__ == '__main__':
    ap.add_argument("-d", "--default", help="Default order of output", action="store_true")
    ap.add_argument("-D", "--debug", help="Debug mode. Doesn't convert files.", action="store_true", default=ms.DEBUG)
    ap.add_argument("-sn", "--shownotes", help="Import markdown shownotes from Etherpad Lite link", default="")
    ap.add_argument("-epid", "--etherpadid", help="Import markdown shownotes from Etherpad Lite ID", default="")
    ap.add_argument("-no", "--episodeno", help="Number of the episode", default="")
    ap.add_argument("-dir", "--audiodir", help="Directory of audiofiles from idjc.", default=audiofiles_folder)
    ap.add_argument("-u", "--audiourl", help="Custom audiourls.", default=audiofiles_url)
    ap.add_argument("-idjc", "--idjc", help="Check if there are idjc files via date", action="store_true")
    ap.add_argument("-b", "--broadcast", help="Set the name of the broadcast", default='')
    ap.add_argument("-r", "--rename", help="Rename the idjc-files", action="store_true")
    ap.add_argument("-ccm", "--convcm", help="Convert .cue- to .psc chaptermark files")
    args = ap.parse_args()

    ms.DEBUG = args.debug

    if args.default:
        set_date()
        find_idjc_files(args.audiodir)
        rename_audiofiles(args.audiodir, args.broadcast, args.episodeno)
        convert_cue_psc(args.audiodir)
        print_audio_urls(args.audiourl)
        if args.etherpadid:
            get_shownotes_ep(etherpad_url + "/" + args.etherpadid)
        elif args.shownotes:
            get_shownotes_ep(args.shownotes)
        else:
            get_shownotes_ep('')
    elif args.etherpadid:
        get_shownotes_ep(etherpad_url + "/" + args.etherpadid)
    elif args.shownotes:
        get_shownotes_ep(args.shownotes)
    elif args.idjc:
        set_date()
        find_idjc_files(args.audiodir)
    elif args.convcm:
        convert_cue_psc(args.audiodir, cue_filepath=args.convcm)
    else:
        ap.print_help()
