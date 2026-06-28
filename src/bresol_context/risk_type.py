# src/bresol_context/risk_type.py

"""
Taxonomia central b-resol per a intake, classificació inicial i detecció
d'informació faltant.

Aquest fitxer és l'única font de veritat per a:
- BRESOL_RISK_TAXONOMY
- BRESOL_PHASE_2_CRITERIA

No crear cap altre fitxer duplicat tipus bresol_taxonomy.py.
"""


BRESOL_RISK_TAXONOMY = {
    "assetjament_escolar": {
        "label": "Bullying o assetjament escolar",
        "definition": (
            "Situació de violència entre iguals caracteritzada per conductes "
            "agressives intencionades, repetides en el temps i amb desequilibri "
            "de poder entre l'agressor i la víctima."
        ),
        "minimum_elements": [
            "conducta_agressiva_o_humiliant",
            "possible_victima_o_alumne_afectat",
            "repeticio_temporal",
            "desequilibri_poder",
            "intencionalitat",
        ],
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
            "Des de quan passa?",
            "Hi ha desequilibri de poder físic, social o psicològic?",
            "Hi ha intencionalitat de fer mal?",
            "Hi ha observadors, reforçadors o alumnes defensors?",
            "La víctima mostra por, evitació, patiment emocional o canvis conductuals?",
        ],
        "safe_identification_questions": [
            "En quin curs o grup passa aproximadament?",
            "En quin espai del centre passa amb més freqüència?",
            "En quin moment del dia acostuma a passar?",
            "Hi ha algun adult del centre que ho pugui observar sense exposar-te?",
        ],
        "avoid_questions": [
            "Dona'm el nom complet de la víctima.",
            "Qui són exactament els agressors?",
            "Per què no t'has defensat?",
            "Segur que no estàs exagerant?",
        ],
    },

    "ciberassetjament": {
        "label": "Cyberbullying o ciberassetjament",
        "definition": (
            "Qualsevol forma d'assetjament, burla o rebuig realitzada a través de mitjans digitals. "
            "Si el cas menciona WhatsApp, TikTok, xarxes socials, mòbils o internet, PRIORITZA SEMPRE aquesta categoria "
            "i NO UTILITZIS MAI assetjament_escolar. El medi digital mana per sobre de l'assetjament físic."
        ),
        "minimum_elements": [
            "canal_digital",
            "conducta_digital_lesiva",
            "possible_victima_o_alumne_afectat",
        ],
        "key_indicators": [
            "whatsapp",
            "instagram",
            "tiktok",
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
            "També passa presencialment dins del centre?",
        ],
        "safe_identification_questions": [
            "Saps en quin grup, curs o entorn digital passa?",
            "El contingut està en un grup de classe, xarxa social o xat privat?",
            "Hi ha alguna captura o pista que permeti localitzar la situació sense difondre-la?",
        ],
        "avoid_questions": [
            "Per què no has bloquejat aquesta persona?",
            "Per què no has esborrat l'aplicació?",
            "Envia les imatges a més gent perquè ho vegin.",
        ],
    },

    "conflicte_convivencia": {
        "label": "Conflictes de convivència",
        "definition": (
            "Situació d'agressió o conflicte entre alumnes que no és repetit ni estructural "
            "i on no existeix un desequilibri clar de poder."
        ),
        "minimum_elements": [
            "fet_concret",
            "context_del_fet",
            "alumnes_implicats_o_afectats",
        ],
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
        "safe_identification_questions": [
            "On ha passat el fet?",
            "Quan ha passat?",
            "Hi ha algun adult o alumne que ho hagi vist?",
        ],
        "avoid_questions": [
            "Qui té la culpa?",
            "Segur que no ha estat una broma?",
        ],
    },

    "pressio_grup": {
        "label": "Pressió de grup",
        "definition": (
            "Situació en què un alumne adopta conductes perjudicials per adaptar-se "
            "o obtenir acceptació social dins d'un grup. OBLIGATÒRIAMENT usa aquesta categoria si algú actua 'per agradar als grans', 'per entrar al grup' o és obligat a robar o fer trapelleries per ser acceptat."
        ),
        "minimum_elements": [
            "conducta_influenciada_pel_grup",
            "possible_alumne_afectat",
            "context_grupal",
        ],
        "key_indicators": [
            "por a l'exclusió social",
            "influència del grup",
            "lideratge del grup",
            "normalització de comportaments inadequats",
            "conductes que individualment no faria",
            "robar per ser acceptat",
            "agradar als més grans",
        ],
        "missing_info_questions": [
            "Hi ha pressió explícita o implícita del grup?",
            "L'alumne actua per evitar exclusió?",
            "Hi ha un lideratge grupal identificable?",
        ],
        "safe_identification_questions": [
            "En quin grup o context passa?",
            "Aquesta pressió passa a classe, al pati o fora del centre?",
        ],
        "avoid_questions": [
            "Per què no simplement dius que no?",
            "Per què segueixes amb aquest grup?",
        ],
    },

    "violencia_sexual": {
        "label": "Abús sexual, grooming o violència sexual",
        "definition": (
            "Activitat sexual imposada a un menor o situació de manipulació, coerció, "
            "engany o vulneració de la integritat sexual."
        ),
        "minimum_elements": [
            "tipus_situacio_sexual",
            "possible_menor_afectat",
            "risc_immediat",
            "adult_o_desequilibri_poder",
        ],
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
            "El menor està segur ara mateix?",
        ],
        "safe_identification_questions": [
            "Hi ha alguna manera segura d'identificar el canal o context on passa?",
            "La situació passa en línia, presencialment o en ambdós espais?",
            "Hi ha risc immediat o contacte amb una persona adulta?",
        ],
        "avoid_questions": [
            "Explica detalls íntims innecessaris.",
            "Per què vas enviar aquesta imatge?",
            "Per què no ho vas parar abans?",
        ],
    },

    "conducta_suicida": {
        "label": "Conducta suïcida",
        "definition": (
            "Pensaments o comportaments relacionats amb el desig de morir o posar fi "
            "a la pròpia vida."
        ),
        "minimum_elements": [
            "risc_immediat",
            "expressio_de_desesperanca_o_desig_de_morir",
            "alumne_acompanyat_o_seguretat_actual",
        ],
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
        "safe_identification_questions": [
            "L'alumne està segur ara mateix?",
            "Hi ha algun adult de confiança amb ell/a ara?",
            "Es pot avisar immediatament un responsable del centre?",
        ],
        "avoid_questions": [
            "Això ho dius de veritat?",
            "No diguis aquestes coses.",
            "Per què vols fer això?",
        ],
    },

    "tca": {
        "label": "Trastorns de la conducta alimentària",
        "definition": (
            "Alteracions greus en la relació amb el menjar, el pes corporal i la imatge "
            "corporal que poden afectar la salut física, emocional i social."
        ),
        "minimum_elements": [
            "conducta_alimentaria_observada",
            "possible_afectacio_fisica_o_emocional",
            "impacte_academic_social_o_emocional",
        ],
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
        "safe_identification_questions": [
            "Quins canvis s'han observat al centre?",
            "Hi ha afectació acadèmica, social o emocional observable?",
        ],
        "avoid_questions": [
            "Has menjat massa o massa poc?",
            "Quant peses?",
            "Per què fas això amb el menjar?",
        ],
    },

    "maltractament_infantil": {
        "label": "Maltractament infantil",
        "definition": (
            "Acció o omissió per part de cuidadors que provoca dany físic, emocional "
            "o psicològic al menor."
        ),
        "minimum_elements": [
            "indicador_de_dany_o_negligencia",
            "possible_menor_afectat",
            "context_familiar_o_cuidador",
            "risc_immediat",
        ],
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
            "Hi ha risc immediat per al menor?",
        ],
        "safe_identification_questions": [
            "Quins indicadors s'han observat al centre?",
            "Hi ha canvis recents de conducta, assistència o cura personal?",
            "El menor està segur quan surt del centre?",
        ],
        "avoid_questions": [
            "Els teus pares et fan mal?",
            "Segur que això és veritat?",
            "Per què no ho havies dit abans?",
        ],
    },

    "consum_substancies": {
        "label": "Consum de substàncies",
        "definition": (
            "Ús experimental, ocasional o habitual de substàncies psicoactives que afecten "
            "el desenvolupament físic, emocional o acadèmic de l'alumnat."
        ),
        "minimum_elements": [
            "substancia_detectada_o_sospitada",
            "lloc_o_context",
            "frequencia_o_tipus_consum",
            "afectacio_escolar_o_conductual",
        ],
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
        "safe_identification_questions": [
            "On s'ha detectat o sospitat el consum?",
            "En quin moment o espai passa?",
            "Hi ha altres alumnes implicats o afectats?",
        ],
        "avoid_questions": [
            "Digue'm qui consumeix exactament.",
            "Per què ho fas?",
        ],
    },

    "falta_greument_perjudicial": {
        "label": "Faltes greument perjudicials i vandalisme",
        "definition": (
            "Conductes que impliquen deteriorament, destrucció o ús inadequat intencionat "
            "d'espais, materials o propietats del centre o de l'entorn escolar. INCLOU explícitament vandalisme, trencar portes, fer pintades o rebentar extintors."
        ),
        "minimum_elements": [
            "dany_material_o_conducta_disruptiva",
            "context_del_fet",
            "puntual_o_repetit",
        ],
        "key_indicators": [
            "dany material voluntari",
            "vulneració de normes de convivència",
            "participació grupal",
            "impacte en el clima escolar",
            "desafiament",
            "conflictes amb autoritat",
            "canvis conductuals recents",
            "vandalisme",
            "trencar portes",
            "pintades despectives",
            "extintor",
        ],
        "missing_info_questions": [
            "És una acció puntual o repetida?",
            "Hi ha participació grupal?",
            "Hi ha conflicte amb l'autoritat?",
            "Pot ser expressió de malestar emocional?",
        ],
        "safe_identification_questions": [
            "On ha passat?",
            "Quan ha passat?",
            "Hi ha càmeres, testimonis o observacions del centre?",
        ],
        "avoid_questions": [
            "Qui ho ha fet exactament?",
            "Per què trenques coses?",
        ],
    },

    "conductes_odi_discriminacio": {
        "label": "Conductes d'odi i discriminació",
        "definition": (
            "Situació de discriminació, odi o rebuig per raó d'origen, ètnia, orientació sexual, "
            "identitat de gènere, religió o qualsevol altra condició personal o social."
        ),
        "minimum_elements": [
            "conducta_discriminatoria",
            "motiu_discriminacio",
            "possible_alumne_afectat",
        ],
        "key_indicators": [
            "insults racistes",
            "LGTBIfòbia",
            "homofòbia",
            "xenofòbia",
            "comentaris despectius per origen",
            "rebuig per creences",
            "exclusió per motius d'identitat",
        ],
        "missing_info_questions": [
            "Quin ha estat el motiu aparent de la discriminació?",
            "S'ha repetit en el temps o ha estat un fet aïllat?",
            "Hi ha altres alumnes que estiguin patint la mateixa situació?",
        ],
        "safe_identification_questions": [
            "A quin espai del centre acostuma a passar?",
            "Hi ha algun docent que ho hagi pogut presenciar?",
        ],
        "avoid_questions": [
            "Estàs segur que era amb aquesta intenció?",
            "Per què no els ignores?",
        ],
    },

    "violencies_masclistes": {
        "label": "Violències masclistes",
        "definition": (
            "Qualsevol tipus de violència, control, coacció o abús de poder exercit "
            "amb components de gènere sexistes, especialment cap a nenes o adolescents. INCLOU explícitament control de parella, prohibir sortir o amenaces de deixar-la."
        ),
        "minimum_elements": [
            "tipus_violencia_o_control",
            "possible_alumna_afectada",
            "context_de_la_relacio",
        ],
        "key_indicators": [
            "control de parella",
            "comentaris sexistes",
            "gelosia extrema",
            "cosificació",
            "violència de gènere",
            "revisió del mòbil",
            "aïllament de les amistats",
            "amenaces de deixar la parella",
            "prohibir vestir",
            "prohibir sortir de festa",
        ],
        "missing_info_questions": [
            "S'ha observat control sobre la manera de vestir, sortir o l'ús del mòbil?",
            "Tenen o han tingut una relació afectiva o de parella?",
            "L'alumna mostra por, canvis d'hàbits o aïllament?",
        ],
        "safe_identification_questions": [
            "Saps si això passa dins o fora de l'entorn escolar?",
            "Hi ha algun amic/amiga que ho hagi detectat?",
        ],
        "avoid_questions": [
            "Per què no el deixes?",
            "Segur que no ho fa per protegir-te?",
        ],
    },

    "autolesions": {
        "label": "Autolesions i autoagressió",
        "definition": (
            "Conductes d'autolesió física intencionada sovint per alleujar malestar emocional "
            "profund, amb o sense intenció suïcida explícita."
        ),
        "minimum_elements": [
            "conducta_autolesiva_observada",
            "risc_immediat",
            "estat_emocional",
        ],
        "key_indicators": [
            "talls",
            "cremades",
            "esgarrapades",
            "amagar parts del cos",
            "roba llarga a l'estiu",
            "malestar emocional intens",
            "aïllament brusc",
        ],
        "missing_info_questions": [
            "L'alumne està acompanyat i segur ara mateix?",
            "Hi ha indicis d'instruments lesius al seu abast?",
            "Ha expressat malestar emocional desbordant o dolor recentment?",
        ],
        "safe_identification_questions": [
            "Qui ha detectat les lesions i en quin context?",
            "S'ha activat ja algun professional de salut o el referent de benestar?",
        ],
        "avoid_questions": [
            "Per què et fas això?",
            "Vols cridar l'atenció?",
        ],
    },

    "general": {
        "label": "Situació general de convivència",
        "definition": "Situació sensible no classificada amb prou precisió.",
        "minimum_elements": [
            "descripcio_minima_dels_fets",
            "context_o_lloc",
            "persona_o_grup_afectat",
            "risc_immediat",
        ],
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
        "safe_identification_questions": [
            "Pots explicar què passa sense donar noms si no et sents segur/a?",
            "On i quan passa aproximadament?",
            "Hi ha alguna persona en risc ara mateix?",
        ],
        "avoid_questions": [
            "Dona'm tots els noms.",
            "Segur que és important?",
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
    "phase_questions": [
        "La situació ha escalat o s'ha agreujat recentment?",
        "Hi ha dany físic, amenaces o coaccions?",
        "Existeix possible abús, agressió o explotació?",
        "L'alumne/a manifesta por real o risc immediat?",
        "Hi ha conductes que podrien constituir delicte?",
        "Ja s'han aplicat mesures educatives sense millora?",
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
    "phase_actions": {
        "sense_indicis_delictius": (
            "Continuar intervenció educativa i seguiment dins del centre."
        ),
        "indicis_possibles": (
            "Informar l'equip directiu i activar protocols interns de protecció."
        ),
        "indicis_clars_activitat_delictiva": (
            "Contactar i formalitzar comunicació immediata amb el REVA segons el protocol vigent."
        ),
        "unknown": (
            "No es pot determinar la fase amb la informació disponible."
        ),
    },
}


def get_risk_config(risk_category: str) -> dict:
    """
    Retorna la configuració d'una categoria de risc.
    Si la categoria no existeix, retorna la categoria general.
    """
    return BRESOL_RISK_TAXONOMY.get(
        risk_category,
        BRESOL_RISK_TAXONOMY["general"],
    )


def get_all_risk_categories() -> list[str]:
    """
    Retorna totes les categories disponibles.
    """
    return list(BRESOL_RISK_TAXONOMY.keys())