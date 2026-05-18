# src/bresol_context/risk_type.py

BRESOL_RISK_TAXONOMY = {
    "assetjament_escolar": {
        "label": "Bullying o assetjament escolar",
        "definition": (
            "Situació de violència entre iguals caracteritzada per conductes "
            "agressives intencionades, repetides en el temps i amb desequilibri "
            "de poder entre l'agressor i la víctima."
        ),
        "key_indicators": [
            "repetició de conductes",
            "intencionalitat de fer mal",
            "desequilibri de poder",
            "existència de rols diferenciats",
            "agressor",
            "víctima",
            "observadors",
            "insults",
            "humiliacions",
            "exclusió social",
            "difusió de rumors",
            "assetjament psicològic",
            "amenaces",
            "intimidació",
        ],
        "missing_info_questions": [
            "Els fets s'han repetit en el temps?",
            "Hi ha desequilibri de poder físic, social o psicològic?",
            "Hi ha intencionalitat de fer mal?",
            "Hi ha observadors, reforçadors o alumnes defensors?",
            "La víctima mostra por, evitació, patiment emocional o canvis conductuals?",
        ],
    },

    "ciberassetjament": {
        "label": "Cyberbullying o ciberassetjament",
        "definition": (
            "Forma d'assetjament entre iguals realitzada a través de mitjans digitals "
            "que permet la difusió ràpida i continuada del dany."
        ),
        "key_indicators": [
            "xarxes socials",
            "missatgeria",
            "videojocs online",
            "anonimat",
            "persistència del contingut",
            "difusió massiva",
            "dificultat de desconnexió",
            "insults digitals",
            "amenaces digitals",
            "difusió d'imatges sense consentiment",
            "perfils falsos",
            "exclusió digital",
            "ridiculització pública",
        ],
        "missing_info_questions": [
            "A través de quin canal digital s'ha produït?",
            "Hi ha captures, missatges o evidències digitals?",
            "El contingut s'ha difós a altres alumnes?",
            "La situació és puntual o repetida?",
            "La víctima pot desconnectar o el contingut continua actiu?",
        ],
    },

    "violencia_puntual": {
        "label": "Violència puntual",
        "definition": (
            "Situació d'agressió o conflicte entre alumnes que no és repetit ni estructural "
            "i on no existeix un desequilibri clar de poder."
        ),
        "key_indicators": [
            "fet aïllat",
            "conflicte concret",
            "impulsivitat",
            "possibilitat de reconciliació",
            "no hi ha rol estable de víctima i agressor",
        ],
        "missing_info_questions": [
            "És un fet aïllat o s'ha repetit?",
            "Hi ha desequilibri de poder?",
            "Hi ha por, evitació o patiment sostingut?",
            "Hi ha antecedents entre els alumnes implicats?",
        ],
    },

    "pressio_grup": {
        "label": "Pressió de grup",
        "definition": (
            "Situació en què un alumne adopta conductes perjudicials per adaptar-se "
            "o obtenir acceptació social dins d'un grup."
        ),
        "key_indicators": [
            "por a l'exclusió social",
            "influència del grup",
            "lideratge del grup",
            "normalització de comportaments inadequats",
            "conductes que individualment no faria",
        ],
        "missing_info_questions": [
            "Hi ha pressió explícita o implícita del grup?",
            "L'alumne actua per evitar exclusió?",
            "Hi ha un lideratge grupal identificable?",
        ],
    },

    "violencia_sexual": {
        "label": "Abús sexual, grooming o violència sexual",
        "definition": (
            "Activitat sexual imposada a un menor o situació de manipulació, coerció, "
            "engany o vulneració de la integritat sexual."
        ),
        "key_indicators": [
            "abús sexual",
            "grooming",
            "imatges íntimes",
            "contacte sexual",
            "exhibicionisme",
            "coacció",
            "xantatge",
            "secretisme amb el mòbil",
            "sexualització progressiva",
            "petició d'imatges íntimes",
        ],
        "missing_info_questions": [
            "Hi ha una persona adulta implicada?",
            "Hi ha petició o difusió d'imatges íntimes?",
            "Hi ha coerció, xantatge o amenaces?",
            "Hi ha risc immediat per al menor?",
        ],
    },

    "conducta_suicida": {
        "label": "Conducta suïcida",
        "definition": (
            "Pensaments o comportaments relacionats amb el desig de morir o posar fi "
            "a la pròpia vida."
        ),
        "key_indicators": [
            "ideació suïcida",
            "desig de morir",
            "desesperança",
            "planificació",
            "intents previs",
            "conductes d'acomiadament",
            "risc elevat",
        ],
        "missing_info_questions": [
            "Hi ha risc immediat?",
            "Ha expressat un pla concret?",
            "Hi ha intents previs?",
            "L'alumne està acompanyat i segur ara mateix?",
            "S'ha informat un adult responsable o servei competent?",
        ],
    },

    "tca": {
        "label": "Trastorns de la conducta alimentària",
        "definition": (
            "Alteracions greus en la relació amb el menjar, el pes corporal i la imatge "
            "corporal que poden afectar la salut física, emocional i social."
        ),
        "key_indicators": [
            "preocupació pel pes",
            "imatge corporal",
            "restricció alimentària",
            "afartaments",
            "conductes compensatòries",
            "vòmits",
            "laxants",
            "exercici excessiu",
            "baixa autoestima",
            "ocultació d'hàbits alimentaris",
        ],
        "missing_info_questions": [
            "Hi ha restricció alimentària?",
            "Hi ha vòmits, laxants o exercici excessiu?",
            "Hi ha pèrdua de pes o preocupació intensa pel cos?",
            "Hi ha impacte acadèmic, social o emocional?",
        ],
    },

    "maltractament_infantil": {
        "label": "Maltractament infantil",
        "definition": (
            "Acció o omissió per part de cuidadors que provoca dany físic, emocional "
            "o psicològic al menor."
        ),
        "key_indicators": [
            "maltractament físic",
            "maltractament emocional",
            "negligència parental",
            "lesions inexplicades",
            "por als adults",
            "canvis conductuals sobtats",
            "falta d'atencions bàsiques",
            "absentisme escolar",
            "higiene inadequada",
        ],
        "missing_info_questions": [
            "Hi ha lesions o indicadors físics?",
            "Hi ha negligència o desatenció continuada?",
            "Hi ha por als adults o canvis conductuals sobtats?",
            "La situació es produeix a l'entorn familiar?",
        ],
    },

    "consum_substancies": {
        "label": "Consum de substàncies",
        "definition": (
            "Ús experimental, ocasional o habitual de substàncies psicoactives que afecten "
            "el desenvolupament físic, emocional o acadèmic de l'alumnat."
        ),
        "key_indicators": [
            "alcohol",
            "drogues",
            "cànnabis",
            "vapeig",
            "canvis bruscos de conducta",
            "baix rendiment escolar",
            "desinhibició",
            "irritabilitat",
            "influència del grup d'iguals",
            "conductes de risc associades",
        ],
        "missing_info_questions": [
            "Quina substància s'ha detectat o sospitat?",
            "Ha passat dins o fora del centre?",
            "És un consum puntual, ocasional o habitual?",
            "Hi ha afectació conductual o acadèmica?",
            "Hi ha altres alumnes implicats?",
        ],
    },

    "vandalisme": {
        "label": "Vandalisme i conductes disruptives associades",
        "definition": (
            "Conductes que impliquen deteriorament, destrucció o ús inadequat intencionat "
            "d'espais, materials o propietats del centre o de l'entorn escolar."
        ),
        "key_indicators": [
            "dany material voluntari",
            "vulneració de normes de convivència",
            "participació grupal",
            "impacte en el clima escolar",
            "desafiament",
            "conflictes amb autoritat",
            "canvis conductuals recents",
        ],
        "missing_info_questions": [
            "És una acció puntual o repetida?",
            "Hi ha participació grupal?",
            "Hi ha conflicte amb l'autoritat?",
            "Pot ser expressió de malestar emocional?",
        ],
    },

    "general": {
        "label": "Situació general de convivència",
        "definition": "Situació sensible no classificada amb prou precisió.",
        "key_indicators": [
            "conflicte",
            "convivència",
            "malestar",
            "situació educativa",
        ],
        "missing_info_questions": [
            "Què ha passat exactament?",
            "Quan ha passat?",
            "On ha passat?",
            "Hi ha repetició?",
            "Hi ha risc físic o emocional?",
        ],
    },
}


BRESOL_PHASE_2_CRITERIA = {
    "assessment_dimensions": [
        "evolució temporal de la situació",
        "intensitat o gravetat dels fets descrits",
        "existència de risc per a la integritat física o emocional del menor",
        "possible vulneració de drets del menor",
        "presència d'indicis d'activitat delictiva",
        "mesures educatives prèvies sense millora",
    ],
    "possible_crime_indicators": [
        "agressions físiques greus",
        "abús sexual o grooming",
        "violència de gènere",
        "maltractament o negligència greu",
        "amenaces greus o coaccions",
        "difusió de contingut íntim sense consentiment",
        "conductes autolesives amb risc vital",
        "extorsió o xantatge",
    ],
    "phase_levels": [
        "sense_indicis_delictius",
        "indicis_possibles",
        "indicis_clars_activitat_delictiva",
        "unknown",
    ],
}