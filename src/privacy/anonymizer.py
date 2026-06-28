import re
from typing import List, Dict
import spacy


# ==============================================================================
# LLISTES DE NOMS PROPIS CATALANS I CASTELLANS (Font de veritat per detecció)
# ==============================================================================
# Noms comuns que un docent podria mencionar en una alerta.
# És molt més fiable que una regex de "majúscules" perquè evita falsos positius
# amb paraules com "Protocol", "Circuit", "Decret", "Institut", etc.

NOMS_MASCULINS = {
    "Pol", "Marc", "Arnau", "Jan", "Nil", "Biel", "Pau", "Joan", "Oriol", "Àlex",
    "Guillem", "Roger", "Aleix", "Jordi", "Pere", "Adrià", "Eric", "Ferran", "Xavier",
    "Sergi", "David", "Daniel", "Carlos", "Pablo", "Alejandro", "Javier", "Miguel",
    "Diego", "Hugo", "Mario", "Raúl", "Sergio", "Pedro", "Alberto", "Roberto",
    "Andrés", "Manuel", "Antonio", "Francisco", "Fernando", "Rafael", "Luis",
    "Enric", "Josep", "Francesc", "Martí", "Bernat", "Albert", "Víctor", "Ivan",
    "Mohamed", "Ahmed", "Omar", "Ali", "Yousef", "Adam", "Leo", "Luca", "Iker",
    "Joel", "Àngel", "Gerard", "Eloi", "Miquel", "Roc", "Bruno", "Tomàs",
    "Andrea", "Nikita", "Luca",  # Noms masculins que acaben en 'a'
}

NOMS_FEMENINS = {
    "Marta", "Maria", "Laia", "Jana", "Noa", "Júlia", "Aina", "Carla", "Emma",
    "Ona", "Ariadna", "Paula", "Laura", "Sara", "Anna", "Clara", "Núria", "Alba",
    "Montse", "Montserrat", "Meritxell", "Neus", "Gemma", "Roser", "Mireia",
    "Sofía", "Lucía", "Elena", "Andrea", "Carmen", "Isabel", "Ana", "Raquel",
    "Cristina", "Patricia", "Beatriz", "Silvia", "Pilar", "Rosa", "Teresa",
    "Nour", "Fatima", "Amina", "Aisha", "Salma", "Leila", "Yasmin",
    "Mar", "Berta", "Bruna", "Cloe", "Gala", "Abril", "Martina", "Valentina",
    "Carlota", "Mariona", "Blanca", "Helena", "Irene", "Eva", "Lola",
}

# Combinació per cerca ràpida
TOTS_ELS_NOMS = NOMS_MASCULINS | NOMS_FEMENINS


class Anonymizer:
    """
    Sistema d'anonimització per garantir la LOPIVI i el RGPD.
    
    Detecta i substitueix dades personals reals (noms d'alumnes, telèfons, DNI/NIE)
    per tokens genèrics abans que viatgin a cap API externa (Gemini).
    Permet des-anonimitzar la resposta final per mostrar-la al docent.
    
    IMPORTANT: NO anonimitza edats, cursos ni context educatiu, ja que
    aquesta informació és essencial perquè el triatge RAG funcioni correctament.
    """
    
    def __init__(self):
        self.mapping: Dict[str, str] = {}         # {token: original}
        self.reverse_mapping: Dict[str, str] = {}  # {original: token}
        self.counter = {
            "ALUMNE": 1,
            "ALUMNA": 1,
            "EMAIL": 1,
            "TEL": 1,
            "DNI": 1,
        }
        try:
            # Model lleuger de spaCy en català per detectar noms per context
            self.nlp = spacy.load("ca_core_news_sm")
        except Exception as e:
            print(f"Avís: Model spaCy 'ca_core_news_sm' no carregat. La capa 2 d'anonimització (NLP) estarà desactivada. Error: {e}")
            self.nlp = None

    def _get_or_create_token(self, original: str, category: str) -> str:
        """Retorna el token existent per a un original, o en crea un de nou."""
        if original in self.reverse_mapping:
            return self.reverse_mapping[original]
        
        token = f"[{category}_{self.counter[category]}]"
        self.mapping[token] = original
        self.reverse_mapping[original] = token
        self.counter[category] += 1
        return token

    def anonymize(self, text: str) -> str:
        """
        Anonimitza un text substituint dades personals per tokens genèrics.
        
        Ordre de detecció (important per evitar col·lisions):
        1. Emails (contenen @ que no apareix en noms)
        2. Telèfons (seqüències numèriques llargues)
        3. DNI/NIE (seqüència alfanumèrica específica)
        4. Noms propis (basats en la llista de noms catalans/castellans)
        """
        if not text:
            return ""

        # Força la conversió a string natiu de Python (soluciona l'error TextAccessor de Langchain)
        anonymized = str(text)

        # ── 1. EMAILS ──────────────────────────────────────────────
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        for match in re.finditer(email_pattern, anonymized):
            original = match.group(0)
            token = self._get_or_create_token(original, "EMAIL")
            anonymized = anonymized.replace(original, token)

        # ── 2. TELÈFONS (Espanya) ─────────────────────────────────
        # Cobreix: 612345678, 612 345 678, 612-345-678, +34 612345678
        phone_pattern = (
            r'\b(?:\+34[\s.-]?)?'        # Prefix opcional +34
            r'[6789]\d{2}[\s.-]?'         # Primers 3 dígits (mòbil o fix)
            r'\d{3}[\s.-]?'               # Dígits centrals
            r'\d{3}\b'                    # Últims 3 dígits
        )
        for match in re.finditer(phone_pattern, anonymized):
            original = match.group(0)
            token = self._get_or_create_token(original, "TEL")
            anonymized = anonymized.replace(original, token)

        # ── 3. DNI / NIE ──────────────────────────────────────────
        # DNI: 12345678A | NIE: X1234567A, Y1234567B
        dni_pattern = r'\b[XYZxyz]?\d{7,8}[A-Za-z]\b'
        for match in re.finditer(dni_pattern, anonymized):
            original = match.group(0)
            token = self._get_or_create_token(original, "DNI")
            anonymized = anonymized.replace(original, token)

        # ── 4. NOMS PROPIS (Basats en llista) ─────────────────────
        # Busquem paraules que coincideixin amb la llista de noms reals.
        # Això evita falsos positius amb "Protocol", "Decret", "Institut", etc.
        word_pattern = r'\b([A-ZÀ-Ÿa-zà-ÿ]+)\b'
        for match in re.finditer(word_pattern, anonymized):
            word = match.group(1)
            # Normalitzem la primera lletra a majúscula per comparar
            word_normalized = word.capitalize()
            
            if word_normalized in NOMS_MASCULINS:
                token = self._get_or_create_token(word, "ALUMNE")
                anonymized = re.sub(r'\b' + re.escape(word) + r'\b', token, anonymized)
            elif word_normalized in NOMS_FEMENINS:
                token = self._get_or_create_token(word, "ALUMNA")
                anonymized = re.sub(r'\b' + re.escape(word) + r'\b', token, anonymized)

        # ── 5. DETECCIÓ AVANÇADA NER (spaCy) ──────────────────────
        # Segona capa: llegeix la frase i busca entitats "PER" (Persona) que 
        # hagin escapat al diccionari de noms.
        if self.nlp:
            doc = self.nlp(anonymized)
            for ent in doc.ents:
                if ent.label_ == "PER":
                    ent_text = ent.text
                    # Assegurem que no sobre-anonimitzem tokens existents (ex. [ALUMNE_1])
                    if "[" not in ent_text and "]" not in ent_text:
                        token = self._get_or_create_token(ent_text, "ALUMNE")
                        anonymized = re.sub(r'\b' + re.escape(ent_text) + r'\b', token, anonymized)

        return anonymized

    def deanonymize(self, text: str) -> str:
        """Reverteix l'anonimització substituint els tokens pels valors originals."""
        if not text:
            return text

        result = text
        # Ordenem per longitud descendent per evitar reemplaçaments parcials
        # (ex. [ALUMNE_10] no ha de ser reemplaçat parcialment per [ALUMNE_1])
        for token in sorted(self.mapping.keys(), key=len, reverse=True):
            result = result.replace(token, self.mapping[token])
        return result

    def anonymize_chat_history(self, chat_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Anonimitza tot l'historial del xat perquè els noms dels missatges
        anteriors tampoc viatgin a l'API de Gemini (al Condense Query).
        """
        if not chat_history:
            return chat_history
        
        anonymized_history = []
        for msg in chat_history:
            anonymized_msg = dict(msg)  # Còpia per no mutar l'original
            if "content" in anonymized_msg:
                anonymized_msg["content"] = self.anonymize(anonymized_msg["content"])
            anonymized_history.append(anonymized_msg)
        return anonymized_history
