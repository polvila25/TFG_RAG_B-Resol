# 9. Arquitectura del Frontend i Experiència d'Usuari (UX/UI)

L'arquitectura del sistema RAG es complementa amb una interfície d'usuari (desenvolupada en **Streamlit**) dissenyada específicament per fer de pont entre la complexitat del model d'Intel·ligència Artificial i la necessitat d'operativitat ràpida d'un docent davant d'una situació d'emergència. 

Aquesta capa de frontend no només actua com a "finestra" d'entrada, sinó que incorpora solucions d'enginyeria de software per garantir l'aïllament de dades, la seguretat de l'avaluació i el compliment legal.

## 9.1. Gestió d'Estat i Aïllament de Context (Multi-xat)

Un dels reptes principals en sistemes RAG conversacionals és la **"contaminació de context"**: quan un mateix usuari consulta sobre dos casos diferents consecutivament, el motor d'IA pot barrejar les dades de l'Alerta A amb les de l'Alerta B en l'anàlisi de seguiment (*Standalone Query*).

Per mitigar aquest problema de manera robusta, l'arquitectura del frontend s'ha dissenyat sota un patró de **gestió d'estat aïllat**:
- S'ha abandonat la llista única d'historial per passar a una estructura basada en **diccionaris** (`st.session_state.chats`).
- El sistema permet gestionar fins a **3 fils de conversa paral·lels** (3 alertes diferents), cadascun amb el seu propi identificador únic (UUID), nom editable i historial de missatges tancat.
- Quan el docent envia una consulta, el frontend exclusivament passa al pipeline RAG la llista de missatges de la conversa *activa*. Això garanteix que el backend RAG (que és *stateless* o sense estat) operi en un entorn clínic i pur, evitant qualsevol risc de confusió entre casos de naturalesa dispar.

## 9.2. Telemetria, Avaluació i Tolerància a Fallades (Fault Tolerance)

Per garantir la millora contínua i l'avaluació del rendiment del sistema (amb l'objectiu d'analitzar l'encert de les categories de risc detectades i la utilitat per part del docent), la interfície incorpora un **mòdul de feedback dinàmic**. Aquest mòdul està dissenyat amb criteris d'alta disponibilitat:

1. **Estructura de dades segures:** Es recopila la consulta original, la categoria de risc prevista pel sistema, i els 8 ítems de valoració del docent en un objecte JSON estructurat.
2. **Limitació de càrrega:** Les cadenes de text llargues (com la resposta generada) es trunquen automàticament a 4000 caràcters abans d'iniciar l'enviament per evitar excepcions de quota a les APIs externes.
3. **Fallback Local (Tolerància a Fallades):** El sistema implementa una doble estratègia d'emmagatzematge. Intenta enviar les dades al full de càlcul al núvol (**Google Sheets**) mitjançant credencials d'API segures. Tanmateix, preveient possibles caigudes de xarxa, talls de servei de Google o errors de certificats, el sistema guarda prèviament la valoració de manera silenciosa en un fitxer `feedback_log.jsonl` local. Això garanteix un 0% de pèrdua de dades d'avaluació.

## 9.3. Compliment Legal i Protecció del Menor

Atès l'entorn altament sensible (protecció de la infància i aplicació de la normativa LOPIVI), la interfície està fortificada amb disseny orientat al risc:
- **Disclaimer Legal Estàtic:** La interfície mostra formularis i avisos visuals dissenyats per subratllar que el sistema RAG és exclusivament una eina orientativa. Aquest "disclaimer" allibera de responsabilitat tècnica a la plataforma, recordant explícitament que "la decisió final sobre les actuacions a seguir és responsabilitat del docent, l'equip directiu i els professionals competents del centre".
- **Avisos Contextuals en Pantalla:** El sistema guia visualment l'usuari (mitjançant requadres `st.info`) sobre com ha d'interactuar amb la plataforma, exigint la no-mescla de casos al mateix xat per no desvirtuar el tractament segur de la identitat del menor o l'anonimat de qui denuncia la situació.
