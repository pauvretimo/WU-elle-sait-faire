---
title: "Elle sait faire"
description: "Challenge portant sur l'explotation de graines de courtes périodes d'un LFSR"
authors: ["Pauvretimo"]
publish_date: "2022-12-11"
tags : ["CRYPTO", "PROG"]
---

# Qu'est ce qu'un LFSR ?

Selon Wikipedia, un lfsr ou Linear-feedback shift register :
*est un dispositif électronique ou logiciel qui produit une suite de bits qui peut être vue comme une suite récurrente linéaire sur le corps fini F2 à 2 éléments (0 et 1). La notion a été généralisée à n'importe quel corps fini.*


De manière plus simple, c'est une fonction (ou un dispositif électronique) qui prend un nombre en entrée (sous forme de bits) et qui XOR certain des bits et ajoute le résultat au bout pour donner une suite s'apparentant à une suite aléatoire.
Elle est aléatoire en apparence mais à la facheuse tendance de faire des boucles, c'est cette propriété qui sera exploitée dans le cadre de ce challenge.


## Un peu de mathématiques :

Un LFSR idéal est un LFSR qui a une période égale à $2^l - 1$ tel que l est le nombre de bits en entrée du lfsr. 

C'est le cas si le polynôme de rétroaction linéaire est irréductible. (c.f. cours LFSR pour les 3A de l'ENSIBS), en des termes plus compréhensibles pour les néophytes, Tout LFSR peut se traduire mathématiquement par un polynôme et si ce polynôme peut se factoriser en de plus petits polynômes il est alors dit irréductible.

$x + 1$ est irréductible

$x^2 + x + 1$ est irréductible

mais $x^3 + 2x^2 + 2x + 1 = (x + 1)(x^2 + x + 1)$ ne l'est pas.

Dans notre cas, le polynôme est $x^9 + x^8 + x^6 + x + 1 = (x^2 + x + 1)(x^3 + x + 1)(x^4 + x + 1)$ et les boucles sont calculées en fonction des trois polynômes irréductibles. (pour plus de détailles mathématiques, allez voir [cet article](https://math.stackexchange.com/questions/872984/sequences-length-for-lfsr-when-polynomial-is-reducible).

## Revenons maintenant à notre challenge :


### Etude du LFSR

J'ai été gentil, j'ai donné les classes utilisées dans le chall au lieu du polynôme ou d'un schéma. On peut directement s'en servire afin de déterminer quelques petites choses.
```python
FLAG = "CATF{cec!_3st_un_exemp1e_de_fl4g_qui_n_est_m3me_pas_d3_la_b0nne_l0ngu3ur}"

class LFSR:

    def __init__(self, i):
        self.seed = self.gen_seed(i)
        self.state = self.seed

    def gen_seed(self, i):
        while i == None or i == 0:
            i = urandom(2)[0]
        seed = [int(x) for x in bin(i)[2:]]
        while len(seed) < 9:
            seed += [0]
        return seed[:9]

    def next(self):
        self.state = [(self.state[0] + self.state[5] + self.state[7] + self.state[8]) % 2] + self.state[:-1]


class getFlag:

    def __init__(self, FLAG):
        self.flag = FLAG.encode()

    def encrypt(self):
        l = LFSR(None)
        for k in range(urandom(1)[0]):
            l.next()

        encrypted_flag = b""
        for k in range(len(self.flag)):
            n = (-1)**l.state[0]
            key = ((n*sum([(2*l.state[x+1])**x for x in range(len(l.state[1:]))]))%255)
            encrypted_flag += (self.flag[k] ^ key).to_bytes(1, 'big')
            for i in range(urandom(1)[0]):
                l.next()
        return encrypted_flag
```


La classe du LFSR possède un paramètre afin d'initialiser à la graine voulue (exceptée 00...0 qui ne donne de toute façon que des 0). On remarque aussi qu'une graine de longueur 9 est nécessaire en entrée i.e. $2^9 = 512$ graines différentes sont possibles. Le programme optimal consiste à répertorier tous les états durant un cycle du LFSR et ainsi on ne parcours qu'une fois chaque cycle. Cependant, il n'y a que 512 graines ce qui permet de toutes les tester sans se poser trop de questions et ainsi d'avoir un code plus simple.
```python
def calc_periodes():

    periodes = []

    for graine in range(512):

        acc = []
        lfsr = LFSR(graine)

        while not(lfsr.state in acc):
            acc.append(lfsr.state)
            lfsr.next()

        periodes.append(len(acc))

    return periodes
```

Ensuite, on remarque qu'il existe un cycle de 3 graines, il nous suffit d'en trouver une pour pouvoir exploiter ce cycle.

```python
def calc_graine_faible(periodes):
    return periodes.index(3)
```

Depuis cette graine, on calcule les deux autres valeurs du LFSR.

```python
def calc_cycle_bits(graine):
    cycle = []
    lfsr = LFSR(graine)
    for k in range(3):
        cycle.append(lfsr.state)
        lfsr.next()
    return cycle
```

Et on traduit ce cycle de bits en cycle de clefs selon la méthode `encrypt` de la classe `getFlag`.

```python
def calc_cycle_clefs(cycle_bits):
        cycle_clefs = []
        for bits in cycle_bits:
            n = (-1)**bits[0]
            clef = ((n * sum([(2 * bits[x+1])**x for x in range(len(bits[1:]))])) % 255)
            cycle_clefs.append(clef)
        return cycle_clefs
```

### On déchiffre le flag

Il ne reste plus qu'à tester des flags jusqu'à ce qu'à en trouver un provenant d'une graine de cycle de péride 3.
Pour ce faire, comme on connait le format du flag (ici CATF{...}), on peut regarder si les 4 premières lettres déchiffrées avec nos clef trouvées précédemment comportent leur valeur initiale (respectivement "C" puis "A" puis "T" et enfin "F") 

```python
# Regarde si le flag provient d'une graine faible
def est_graine_faible(flag_chiffre, cycle_clefs):

    # On compare avec les 4 premier caractères connus : CATF
    correspondance = ""
    caractere = 0
    while caractere < 4:
        comparaison = correspondance
        dechiffre_char = b""

        # Regarde si le flag déchiffré avec les trois clefs connues donne
        # respectivement les lettres de CATF
        for clef in cycle_clefs:
            dechiffre_char = (flag_chiffre[caractere] ^ clef).to_bytes(1, 'big')

            try:
                if "CATF"[caractere] == dechiffre_char.decode():
                    correspondance += "CATF"[caractere]
            except:
                None

        # On continue que si il y a le bon caractère
        if correspondance == comparaison:
            caractere = 4
        else:
            caractere += 1

    # Renvoit True si début du flag est chiffré
    # avec une des trois bonnes graines
    return "CATF" == correspondance
```

Une fois le flag encodé de manière faible trouvé, il suffit d'afficher les différentes possibilités pour chaque caractère et le flag apparait !

```python
def affiche_flag(flag_chiffre, cycle_clefs):
    flag = []

    # On dechiffre les lettres une à une
    for lettre in flag_chiffre:
        possibilites = []

        # En donnant à chaque fois les trois possibilites
        for clef in cycle_clefs:
            possibilites.append(chr((lettre ^ clef)))
        flag.append(possibilites)
    return flag
```

Il restait une petite subtilité : le flag est mis sous forme de texte hexadécimal lorsqu'il est affiché sur la page web, il ne fallait donc pas décoder directement ce qui apparaissait mais bien penser de le convertire avant de traiter le flag chiffré.

Pour finir, il faut tester des flags jusqu'à ce qu'un que l'on puisse en déchiffrer un, voici une petite fonction permettant de faire des requètes à la page web et d'isoler un flag.

```python
import requests
import re

# fonction pour récupérer un flag depuis le site web :

def requete_flag():
    req = requests.get("http://cyberavent-elle-sait-faire.chals.io/flag").text

    # Isole le flag
    hex_flag = re.search(r"(?<=(<p>))(.*)(?=(<\/p>))", req).group()

    # converti le flag en bytes
    encrypted_flag = bytes.fromhex(hex_flag)

    return encrypted_flag
```

Et en appliquant les étapes précédentes on fini par avoir le flag.

```python
periodes = calc_periodes()

graine_faible = calc_graine_faible(periodes)

cycle_bits = calc_cycle_bits(graine_faible)

cycle_clefs = calc_cycle_clefs(cycle_bits)


print( f'''
La première graine faible est :     {graine_faible}

Elle donne le cycle de clefs :      {cycle_clefs}

Je lance la boucle d'identification d'une graine faible :
'''
)



est_faible = False
while not(est_faible):

    flag_chiffre = requete_flag()

    est_faible = est_graine_faible(flag_chiffre, cycle_clefs)

flag = affiche_flag(flag_chiffre, cycle_clefs)

print('Un flag chiffré avec une graine faible a été trouvé !')


print(f'''
Le flag a été trouvé ! Voici les différentes combinaisons :

{flag}
'''
```


## Le code en entier :
```python
from os import urandom

## On Fais tout d'abord quelques tests sur le code donné.

FLAG = "CATF{cec!_3st_un_exemp1e_de_fl4g_qui_n_est_m3me_pas_d3_la_b0nne_l0ngu3ur}"

class LFSR:

    def __init__(self, i):
        self.seed = self.gen_seed(i)
        self.state = self.seed

    def gen_seed(self, i):
        while i == None or i == 0:
            i = urandom(2)[0]
        seed = [int(x) for x in bin(i)[2:]]
        while len(seed) < 9:
            seed += [0]
        return seed[:9]

    def next(self):
        self.state = [(self.state[0] + self.state[5] + self.state[7] + self.state[8]) % 2] + self.state[:-1]


class getFlag:

    def __init__(self, FLAG):
        self.flag = FLAG.encode()

    def encrypt(self):
        l = LFSR(None)
        for k in range(urandom(1)[0]):
            l.next()

        encrypted_flag = b""
        for k in range(len(self.flag)):
            n = (-1)**l.state[0]
            key = ((n*sum([(2*l.state[x+1])**x for x in range(len(l.state[1:]))]))%255)
            encrypted_flag += (self.flag[k] ^ key).to_bytes(1, 'big')
            for i in range(urandom(1)[0]):
                l.next()
        return encrypted_flag

## On commence par calculer les temps des cycles de chaques graines (512 au total) :

def calc_periodes():

    periodes = []

    for graine in range(512):

        acc = []
        lfsr = LFSR(graine)

        while not(lfsr.state in acc):
            acc.append(lfsr.state)
            lfsr.next()

        periodes.append(len(acc))

    return periodes

## Après avoir remarqué les périodes de 3, on en cherche une :

def calc_graine_faible(periodes):
    return periodes.index(3)

## On calcul le cycle du LFSR :

def calc_cycle_bits(graine):
    cycle = []
    lfsr = LFSR(graine)
    for k in range(3):
        cycle.append(lfsr.state)
        lfsr.next()
    return cycle

## Puis on convertis le cycle de bits en cycle de clef suivant la fonction getFlag :

def calc_cycle_clefs(cycle_bits):
        cycle_clefs = []
        for bits in cycle_bits:
            n = (-1)**bits[0]
            clef = ((n * sum([(2 * bits[x+1])**x for x in range(len(bits[1:]))])) % 255)
            cycle_clefs.append(clef)
        return cycle_clefs

##  On regarde si un flag chiffré provient d'une des trois graines faibles :


# Regarde si le flag provient d'une graine faible
def est_graine_faible(flag_chiffre, cycle_clefs):

    # On compare avec les 4 premier caractères connus : CATF
    correspondance = ""
    caractere = 0
    while caractere < 4:
        comparaison = correspondance
        dechiffre_char = b""

        # Regarde si le flag déchiffré avec les trois clefs connues donne
        # respectivement les lettres de CATF
        for clef in cycle_clefs:
            dechiffre_char = (flag_chiffre[caractere] ^ clef).to_bytes(1, 'big')

            try:
                if "CATF"[caractere] == dechiffre_char.decode():
                    correspondance += "CATF"[caractere]
            except:
                None

        # On continue que si il y a le bon caractère
        if correspondance == comparaison:
            caractere = 4
        else:
            caractere += 1

    # Renvoit True si début du flag est chiffré
    # avec une des trois bonnes graines
    return "CATF" == correspondance


## On regarde toutes les possibilités du flag si il est chiffré avec un cycle de 3 :

def affiche_flag(flag_chiffre, cycle_clefs):
    flag = []

    # On dechiffre les lettres une à une
    for lettre in flag_chiffre:
        possibilites = []

        # En donnant à chaque fois les trois possibilites
        for clef in cycle_clefs:
            possibilites.append(chr((lettre ^ clef)))
        flag.append(possibilites)
    return flag


## On request un flag et on le décode :
import requests
import re

# fonction pour récupérer un flag depuis le site web :

def requete_flag():
    req = requests.get("http://cyberavent-elle-sait-faire.chals.io/flag").text

    # Isole le flag
    hex_flag = re.search(r"(?<=(<p>))(.*)(?=(<\/p>))", req).group()

    # converti le flag en bytes
    encrypted_flag = bytes.fromhex(hex_flag)

    return encrypted_flag


## On met tout bout à bout

periodes = calc_periodes()

graine_faible = calc_graine_faible(periodes)

cycle_bits = calc_cycle_bits(graine_faible)

cycle_clefs = calc_cycle_clefs(cycle_bits)


print( f'''
La première graine faible est :     {graine_faible}

Elle donne le cycle de clefs :      {cycle_clefs}

Je lance la boucle d'identification d'une graine faible :
'''
)



est_faible = False
while not(est_faible):

    flag_chiffre = requete_flag()

    est_faible = est_graine_faible(flag_chiffre, cycle_clefs)

flag = affiche_flag(flag_chiffre, cycle_clefs)

print('Un flag chiffré avec une graine faible a été trouvé !')


print(f'''
Le flag a été trouvé ! Voici les différentes combinaisons :

{flag}
'''
)

```
