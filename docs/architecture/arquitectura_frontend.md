# 9. Arquitectura del Frontend i Experiència d'Usuari (UX/UI)

L'arquitectura del sistema RAG es complementa amb una interfície d'usuari (desenvolupada en **Streamlit**) dissenyada específicament per fer de pont entre la complexitat del model d'Intel·ligència Artificial i la necessitat d'operativitat ràpida d'un docent davant d'una situació d'emergència. 

Aquesta capa de frontend no només actua com a "finestra" d'entrada, sinó que incorpora solucions d'enginyeria de software.

## 9.1. Gestió d'Estat i Aïllament de Context (Multi-xat)

Un dels reptes principals en sistemes RAG conversacionals és la **"contaminació de context"**: quan un mateix usuari consulta sobre dos casos diferents consecutivament, el motor d'IA pot barrejar les dades de l'Alerta A amb les de l'Alerta B en l'anàlisi de seguiment (*Standalone Query*).

Per mitigar aquest problema de manera robusta, l'arquitectura del frontend s'ha dissenyat sota un patró de **gestió d'estat aïllat**:
- S'ha abandonat la llista única d'historial per passar a una estructura basada en **diccionaris** (`st.session_state.chats`).
- El sistema permet gestionar fins a **3 fils de conversa paral·lels** (3 alertes diferents), cadascun amb el seu propi identificador únic (UUID), nom editable i historial de missatges tancat.
- Quan el docent envia una consulta, el frontend exclusivament passa al pipeline RAG la llista de missatges de la conversa *activa*. Això garanteix que el backend RAG (que és *stateless* o sense estat) operi en un entorn clínic i pur, evitant qualsevol risc de confusió entre casos de naturalesa dispar.

## 9.2. Avaluació i Tolerància a Fallades 

Per garantir la millora contínua i l'avaluació del rendiment del sistema (amb l'objectiu d'analitzar l'encert de les categories de risc detectades i la utilitat per part del docent), la interfície incorpora un **mòdul de feedback dinàmic**. Aquest mòdul està dissenyat amb criteris d'alta disponibilitat:

1. **Estructura de dades segures:** Es recopila la consulta original, la categoria de risc prevista pel sistema, i els 8 ítems de valoració del docent en un objecte JSON estructurat.


## 9.3. Compliment Legal i Protecció del Menor

Atès l'entorn altament sensible (protecció de la infància i aplicació de la normativa LOPIVI), la interfície està fortificada amb disseny orientat al risc:
- **Avís legal al docent:** La interfície mostra un text d'avís sempre al inici per subratllar que el sistema RAG és exclusivament una eina orientativa. Aquest avís allibera de responsabilitat tècnica a la plataforma, recordant explícitament que "la decisió final sobre les actuacions a seguir és responsabilitat del docent, l'equip directiu i els professionals competents del centre".
- **Avisos Contextuals en Pantalla:** El sistema guia visualment l'usuari (mitjançant requadres `st.info`) sobre com ha d'interactuar amb la plataforma, exigint la no-mescla de casos al mateix xat.

## 9.4. Accés Directe a Circuits Oficials

Per tal de reduir el temps de reacció en situacions crítiques, el frontend integra un sistema de lliurament dinàmic de documentació:
- Quan el sistema detecta que l'alerta assoleix la maduresa necessària i correspon a un criteri de risc específic (ex. *assetjament escolar*, *consum de substàncies*, etc.), la interfície renderitza automàticament un botó d'acció destacat.
- Aquest botó permet al docent descarregar directament el document **PDF del circuit d'actuació oficial** vinculat a aquell risc.
- **Control de redundància:** Per mantenir el xat net, l'aplicació utilitza variables d'estat per assegurar-se que **el botó de descàrrega es mostra únicament una vegada per cada xat**. D'aquesta manera, si el docent continua fent preguntes de seguiment dins la mateixa conversa, el botó ja no es repeteix, garantint una experiència d'usuari (UX) més fluida i menys invasiva.