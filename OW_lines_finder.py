#!/bin/python


import json
import requests

from pony.orm import *


""" Module that find the best game response from a given text"""

from OW_lines_DBManager import Personagem, Clip


with open('config.json') as config_file:
    CONFIGURATION = json.load(config_file)


@db_session
def get_responses(query, specific_hero):
    
    result = []

    if specific_hero is not None:
        bd_query = select((c.personagem.nome, c.texto, c.url) for c in Clip if
                          specific_hero.lower() in c.personagem.nome.lower() and query.lower() in
                          c.texto.lower()).order_by(raw_sql('RANDOM()'))[:5]

        if bd_query is not None and bd_query != []:
            hero = bd_query[0][0]

            for each in bd_query:
                text = each[1]
                url = each[2]
                single_response = {'Character': hero,'Text': text, 'URL': url}
                result.append(single_response)
            
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

            return result
        else:
            result = None
            return result

            

