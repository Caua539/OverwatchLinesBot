#!/bin/python


import json
import requests
import os

from uuid import uuid4
from shutil import rmtree
from pony.orm import *
from pydub import AudioSegment


""" Module that find the best game response from a given text"""

from OW_lines_DBManager import Personagem, Clip


with open('config.json') as config_file:
    CONFIGURATION = json.load(config_file)


@db_session
def get_responses(query, specific_hero):
    
    if query is None or query is '':
        print(">>>Empty query<<<")
        return None
    
    result = []
    
    folderid = uuid4()

    if specific_hero is not None:
        bd_query = select((c.personagem.nome, c.texto, c.url) for c in Clip if
                          specific_hero.lower() == c.personagem.nome.lower() and query.lower() in
                          c.texto.lower()).order_by(raw_sql('RANDOM()'))[:5]

        if bd_query is not None and bd_query != []:
            hero = bd_query[0][0]

            for each in bd_query:
                text = each[1]
                url = each[2]
                single_response = {'Character': hero,'Text': text, 'URL': url}
                result.append(single_response)
            
            result = ogg_to_mp3(result, folderid)
            return result
        else:
            result = None
            return result
    else:
        bd_query = select((c.personagem.nome, c.texto, c.url) for c in Clip if query.lower() in 
                           c.texto.lower()).order_by(raw_sql('RANDOM()'))[:10]
        
        if bd_query is not None and bd_query != []:
            for each in bd_query:
                hero = each[0]
                text = each[1]
                url = each[2]
                single_response = {'Character': hero, 'Text': text, 'URL': url}
                result.append(single_response)

            result = ogg_to_mp3(result, folderid)
            return result
        else:
            result = None
            return result


def ogg_to_mp3(result, folderid):
    
    direc = "gamequotes.mooo.com/{}".format(folderid)
    os.makedirs(direc+"/Original")
        
    for i, each in enumerate(result):
        url = each["URL"]
        file_path = direc+"/Original/audio_0{}.{}".format(i+1, url[-3:])
        local_file = open(file_path,'wb')
        local_file.write(requests.get(url).content)
        local_file.close()
        
        mp3_file = AudioSegment.from_file(file_path, url[-3:])
    
        file_path = direc+"/audio_0{}.ogg".format(i+1)
        mp3_file.export(file_path, format = "ogg", codec = "libopus")
    
        
        
        result[i]['URL'] = "http://"+file_path
        
    return result
            

