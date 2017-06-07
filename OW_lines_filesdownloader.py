#!/usr/bin/env python
# -*- coding: utf-8 -*-
#pylint: disable=locally-disabled

import re
import requests
import os
import progressbar

from OW_lines_DBManager import Clip, Personagem
from bs4 import BeautifulSoup
from pony.orm import *
from pydub import AudioSegment
from slugify import slugify

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
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            data.append([ele for ele in cols if ele])
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
                if ("{}:".format(hero)) in line1 or (":{}_".format(hero)) in line1:
                    each[i] = line1
                elif ("{}:".format(hero)) in line2 or (":{}_".format(hero)) in line2:
                    each[i] = line2

        dicy = {}
        dicy["Line"] = each[0].strip()
        dicy["URL"] = each[1]
        finalList.append(dicy)
        count += 1
        
    print ("FILES COUNT: {}".format(count))
    print ("RECOVERING URLs...")
    bar = progressbar.ProgressBar(max_value=len(finalList))
    j = 0
    for i, item in enumerate(finalList):
        j += 1
        url = item["URL"]
        if "\n" in url:
            continue
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        
        for div_obj in soup.find_all("div"):
            if div_obj.has_attr("class") and div_obj["class"][0] == "fullMedia":
                finalList[i]["URL"] = div_obj.a.get('href')
        bar.update(j)
    print ("URLs RECOVERED.\n")
    return finalList


###############################################################################################################
# Download dos arquivos

def file_download(filelist, hero):
    
    direc = "DOWNLOAD/{}".format(hero)
    os.makedirs(direc+"/original")
    regex_patt = r'[^-a-z0-9_.]+'

    j = 0
    bar = progressbar.ProgressBar(max_value=len(filelist))
    print ("FILE DOWNLOAD START...\n")
    for i, item in enumerate(filelist):
        j += 1
        url = item["URL"]

        filename = requests.utils.unquote(url.split('/')[-1])
        filename = slugify(filename, regex_pattern = regex_patt)
        file_path = direc + "/original/{}".format(filename)
        
        local_file = open(file_path, 'wb')
        local_file.write(requests.get(url).content)
        local_file.close()

        mp3_file = AudioSegment.from_file(file_path, url[-3:])

        filename = "/{}.mp3".format(filename.replace(filename[-4:], ''))
        file_path =  direc + filename
        
        mp3_file.export(file_path, format="mp3")

        filelist[i]["URL"] = "http://gamequotes.mooo.com/overwatch/{}".format(hero) + filename
        bar.update(j)
    print (" FILE DOWNLOAD END.\n")
    return filelist



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
    hero = "Ana"
    data = webscrap("https://overwatch.gamepedia.com/Ana/Quotes")

    filelist = listMaker(data, hero)
    dbFuel = file_download(filelist, hero)
    print("DB INSERT START...")
    ID = get_id()
    #dbInsert(ID, hero, dbFuel)
    print ("DB INSERT END.\n")
    get_id()

    print("END.\n")
    
if __name__ == '__main__':
    main()