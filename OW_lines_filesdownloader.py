#!/usr/bin/env python
# -*- coding: utf-8 -*-
#pylint: disable=locally-disabled

import re
import requests
import os
import progressbar
import json

from OW_lines_DBManager import Clip, Personagem
from bs4 import BeautifulSoup
from pony.orm import *
from pydub import AudioSegment
from slugify import slugify
from urllib.parse import unquote

##############################################################################################################
#Carregando o DATABASE

db = Database("sqlite", 'DATABASE/botbd.db', create_db=True)

db.generate_mapping(create_tables=True)

###############################################################################################################
#Web Scraping
def webscrap(url):
    
    page = requests.get(url)
    
    soup = BeautifulSoup(page.content, 'html.parser')
    
    data = []
    table = soup.findAll('table', attrs={'class': 'wikitable'})
    for each in table:
        rows = each.find_all('tr')
    
        for row in rows:
            ili = []
            cols = row.find_all('td')
            for ele in cols:
                if 'https:' in ele.text.strip():
                    audios = ele.find_all('audio')
                    if len(audios) > 1:
                        ele = '\n'.join(item.get('src') for item in audios)
                    else:
                        ele = ele.audio.get('src').strip()

                else:
                    ele = ele.text.strip()
                ili.append(ele)
            itemlist = [ele for ele in ili if ele]
                        
            data.append(itemlist)
    return data

###############################################################################################################
#Formatação dos resultados obtidos e gravação numa lista

def listMaker(data, hero):
    
    count = 0
    finalList = []
    regexLang = re.compile(r'\n\n\n')
    regexLang2 = re.compile(r'\n')
    for each in data:
        if len(each) > 2:
            each[0] = each[1]
            each[1] = each[2]
            del each[2]
    
        if any("https://" in s for s in each) is False:
            continue
        
        if "\n\n\n" in each[0]:
            each[0] = re.sub(regexLang, ' - ', each[0])

        if "\n" in each[0] and "English" in each[0]:
            each[0] = re.sub(regexLang2, ' - ', each[0])
    
        for i, s in enumerate(each):
            if "\n" in s:
                line1, line2, *extra = s.split("\n")
                if ("{}:".format(hero)) in unquote(line1) or ("{}_-_".format(hero)) in unquote(line1):
                    each[i] = line1
                elif ("{}:".format(hero)) in unquote(line2) or ("{}_-_".format(hero)) in unquote(line2):
                    each[i] = line2

        dicy = {}
        dicy["Line"] = each[0].strip()
        dicy["URL"] = each[1]

        finalList.append(dicy)
        count += 1
        
    print ("FILES COUNT: {}".format(count))

    return finalList


###############################################################################################################
# Download dos arquivos

def file_download(filelist, hero):
    
    direc = "DOWNLOAD/{}".format(hero)
    os.makedirs(direc+"/original")

    herolower = '{}_-_'.format(slugify(hero.lower()))
    regex_patt = r'[^-a-z0-9_.]+'
    fileversion = "%04d" % filename_version(hero)
    print (fileversion)

    j = 0
    bar = progressbar.ProgressBar(max_value=len(filelist))
    print ("FILE DOWNLOAD START...\n")
    
    for i, item in enumerate(filelist):
        j += 1
        url = item["URL"]

        filename = requests.utils.unquote(url.split('/')[-1])
        filename = slugify(filename, regex_pattern = regex_patt)
        if herolower not in filename:
            filename = herolower+filename
        file_path = direc + "/original/{}".format(filename)

        #print("\n{} :....................{}".format(item["URL"], file_path))

        local_file = open(file_path, 'wb')
        local_file.write(requests.get(url).content)
        local_file.close()
        
        mp3_file = AudioSegment.from_file(file_path, url[-3:])

        export_filename = "/{}--{}.mp3".format(filename.replace(filename[-4:], ''), fileversion)
        export_path =  direc + export_filename
        
        mp3_file.export(export_path, format="mp3")
        
        file_size = os.stat(export_path).st_size / 1024
        
        if file_size < 8:
            #print("\n{}".format(item["Line"]))
            
            #print("ORIGINAL SMALL FILE: %.2f" % file_size)
    
            mp3_file = AudioSegment.from_file(file_path, url[-3:])
            if file_size < 4.2:
                silence = AudioSegment.silent(duration=600, frame_rate=192000)
            else:
                silence = AudioSegment.silent(duration=500, frame_rate=192000)
            mp3_file = mp3_file + silence
            
            os.remove(export_path)
            
            export_filename = "/{}--{}.mp3".format(filename.replace(filename[-4:], ''), fileversion)
            export_path =  direc + export_filename
        
            mp3_file.export(export_path, format="mp3")
            
            file_size = os.stat(export_path).st_size / 1024
            
            #print ("MP3 FILE SIZE: %.2f\n" % file_size)
            

        filelist[i]["URL"] = "http://gamequotes.mooo.com/overwatch/{}".format(hero) + export_filename
        bar.update(j)
    print (" FILE DOWNLOAD END.\n")
    return filelist
    

    
def filename_version(hero):
    
    jsonfile = "AUXI/fileversion.json"
    dicy = {}
    if os.path.exists(jsonfile):   
        with open(jsonfile, "r+") as fp:
            dicy = json.load(fp)
        os.remove(jsonfile)
        
    if hero in dicy.keys():
        dicy[hero] += 1
    else:
        dicy[hero] = 1
    
    with open(jsonfile, 'w') as fp:   
        json.dump(dicy, fp, indent=4)

    
    return dicy[hero]
        

###############################################################################################################
#Inserção no banco

@db_session
def get_id():  #pega o último id de fala adicionado
    num = Clip.get(id=max(d.id for d in Clip))
    if num is None:
        id_pos = 0
    else:
        id_pos = num.id

    print("CURRENT ID: {}".format(id_pos))
    return id_pos

@db_session
def dbInsert(ID, hero, dbfuel):
    charac = Personagem(nome=hero, origem='overwatch')
    commit()
    for item in dbfuel:
        ID += 1
        line = item["Line"]
        file_url = item["URL"]
        clip = Clip(id=ID, texto=line, url=file_url, personagem=hero)
        commit()


def main():
    print ("SCRIPT START...")
    hero = "Reinhardt"
    data = webscrap("https://overwatch.gamepedia.com/Reinhardt/Quotes")
    #for item in data:
        #print (item)
    filelist = listMaker(data, hero)
    dbFuel = file_download(filelist, hero)
    print("DB INSERT START...")
    ID = get_id()
    dbInsert(ID, hero, dbFuel)
    print ("DB INSERT END.\n")
    get_id()

    print("END.\n")
    
if __name__ == '__main__':
    main()