
from pony.orm import *



########################################################################################################################
#Criação do Schema do DB

db = Database("sqlite", 'DATABASE/botbd.db', create_db=True)


class Personagem(db.Entity):
    nome = PrimaryKey(str)
    origem = Required(str)
    clips = Set('Clip')


class Clip(db.Entity):
    id = PrimaryKey(int, auto=True)
    texto = Required(str)
    url = Required(str)
    personagem = Required(Personagem)


db.generate_mapping(create_tables=True)

########################################################################################################################
#Popular o DB e funções auxiliares
@db_session
def get_id():  #pega o último id de fala adicionado
    num = Clip.get(id=max(d.id for d in Clip))
    if num is None:
        id_pos = 0
    else:
        id_pos = num.id

    print(id_pos)
    return id_pos

@db_session
def check_double(hero):
    hlist = select(p.nome for p in Personagem)
    for nome in hlist:
        if nome == hero:
            return True
        else:
            continue
    return False





