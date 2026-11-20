# Big Data Practical Exam - XKCD Search Engine

## Information zur KI Nutzung
| Werkzeug | Beschreibung der Nutzung |
| --- | --- |
| ChatGPT | Recherche und Unterstützung bei der Informationsaufbereitung |
| ChatGPT Codex | Unterstützung bei Fehleranalyse, Fehlerbehebung und Dokumentation |

## Demo

### 1. Alle Dienste starten
```powershell
docker compose --profile web --profile airflow up -d --build
```


Damit werden HDFS, PostgreSQL, Airflow, das FastAPI-Backend und das React-Frontend gestartet. Die ETL-Pipeline startet erst durch das manuelle Auslösen des DAGs.


### 2. Bei Airflow anmelden
Airflow unter ```http://localhost:8080``` öffnen.

Benutzername: `admin`
passwort: automatisch erzeugt => auslesen
```powershell
docker compose exec airflow python -c "import json; print(json.load(open('/opt/airflow/simple_auth_manager_passwords.json.generated'))['admin'])"
```

Falls Airflow noch nicht bereit ist, die Startlogs prüfen:

```powershell
docker compose logs --tail 100 airflow
```


### 3. Datenpipeline starten
In der Airflow-Oberfläche:
1. Den DAG `xkcd_pipeline` öffnen
2. Den DAG ggf. aktivieren
3. Über **Trigger DAG** durchlauf starten.

Airflow führt die folgenden Schritte automatisch nacheinander aus:
``download -> import_hdfs -> transform -> export_postgres -> merge_comics`

Der Download lädt alle Comics von ID 1 bis zur aktuell höchsten ID
(`XKCD_END_ID=0` in `docker-compose.yml`). Bereits lokal vorhandene Comics
werden übersprungen; nicht vorhandene IDs (HTTP 404) werden protokolliert.

### 4. Suchfunktion
Im Frontend `http://localhost:3000` können jetzt suchen durchgeführt werden.

Andere Oberflächen:
* Airflow: `http://localhost:8080`
* API-Dokumentation: `http://localhost:8000/docs`
* HDFS NameNode: `http://localhost:9870`


### 5. Demo beenden
```powershell
docker compose --profile web --profile airflow down
```






## DOKU

### 1. Ziel des Projekts
Ziel des Projektes ist es eine durchsuchbare Datenbank für XKCD-Comics aufzubauen. Dafür werden die öffentlich verfügbaren Daten der XKCD-API automatisiert heruntergeladen, in einem Hadoop Distributed File System (HDFS) gespeichert, mit Apache Spark verarbeitet und anschließend in eine PostgreSQL-Datenbank übertragen.

Die aufbereiteten Daten werden anschließend durch eine FastAPI-Anwendung bereitgestellt. Ein React-Frontend ermöglicht es dann dem Nutzer, die gespeicherten Comics über eine Volltextsuche zu durchsuchen und die Ergebnisse anzuzeigen.

Somit besteht der vollständige Datenfluss aus den folgenden Komponenten:
XKCD API -> lokale JSON-Dateien -> HDFS Raw Layer -> PySpark Transformation -> HDFS Final Layer -> PostgreSQL -> FastAPI -> React Frontend

### 2. Datenquelle
Als Datenquelle wird die öffetnliche JSON-Schnittstelle von XKCD verwendet.

Diese bietet die möglichkeit, jedes Comic über folgende Request abzurufen.

```
https://xkcd.com/{id}/info.0.json
```


Das daraus zurückbekommene JSON-Dokument enthält unteranderem diese Informationen:

* Comic-ID
* Title
* sicherer Titel (safe_title)
* Erscheinungsdatum
* Alternativtext (alt)
* Transcript
* URL zum Comic-Bild

Aufgrund der tatsache, dass die API selbst keinen Endpunkt zum Abruf aller Comics bereitstellt, müssen die einzelnen Comics anhand ihrer Comic-IDs nacheinander abgefragt werden.

### 3. ETL-Workflow
#### 3.1 Extract - Herunterladen der XKCD-Daten
Im ersten Schritt des ETL-Workflows werden die Comic-Daten über die öffentliche XKCD-API abgerufen und zunächst lokal unter `data/raw/<Jahr>/<ID>.json` gespeichert. Erst der separate Task `import_hdfs` kopiert diese Dateien in den HDFS Raw Layer.

Da die XKCD-API selbst keinen Endpunkt zum Abrufen aller Comics bereitstellt, wird der Download durch die fortlaufenden Comic-IDs realisiert.

Dabei kann die höchste verfügbare Comic-ID über den folgenden Endpunkt ermittelt werden:
```
https://xkcd.com/info.0.json
```

Der Download erfolgt dabei mithilfe eines Python-Skripts, welches dabei die folgenden Schritte ausführt:
1. Ermitteln der aktuell höchsten Comic-ID
2. Iterieren über sämtliche Comic-IDs.
3. Abrufen der zugehörigen JSON-Dokumente über HTTP-GET-Requests.
4. Überprüfen der HTTP-Antworten und Behandlung möglicher Fehler .
5. Speichern der erfolgreich abgerufenen JSON-Dokumente unter `data/raw/<Jahr>/`.

Da nicht sichergestellt ist, das jede Comic-ID existiert, werden die HTTP-404-Antworten im skript berücksichtigt. Die aufgetretenen Fehlerhaften Requests, werden dabei Protokoliert und können im späteren verlauf nachvollzogen werden.


Speicherung im HDFS Raw Layer
Der Task `import_hdfs` kopiert die lokal heruntergeladenen JSON-Dokumente in den HDFS Raw Layer. Er wartet dafür auf einen aktiven DataNode und das Ende des HDFS Safe Mode. Somit können die ursprünglichen Daten erhalten bleiben und bei Bedarf erneut verarbeitet werden.
Die Speicherung erfolgt im anschluss anhand des Erscheinungsjahrs der einzelnen Comics.
Eine Beispielhafte Verzeichnisstruktur könnte dabei folgender maßen aussehen:
```
/user/hadoop/xkcd/
└── raw/
    ├── 2024/
    │   ├── 2990.json
    │   └── ...
    ├── 2023/
    │   └── ...
    └── 2018/
        ├── 2054.json
        └── ...
```
Das jeweilige Erscheindungsjahr wird dabei aus dem Feld 'year' des jeweiligen JSON-Dokuemnts extrahiert.

#### 3.2 Transform - Verarbeitung mit Apache Spark
Im dritten DAG-Task (`transform`) werden die gespeicherten Rohdaten von Apache Spark und dessen Python Schnittstelle PySpark verarbeitet.
Ziel bei dieser Transformation ist es, die ursprünglichen JSON-Dokumente in eine bereinigte und strukturierte Form zu übersetzen, die im späteren verlauf für die Volltextsuche verwendet werden kann.

Für diesen Schritt weden die JSON-Dateien aus dem Raw Layer eingelesen und in einen Spark DataFrame umgewandelt.

Die Transformation umfasst dabei die folgenden Schritte:
1. Auswahl relevanter Attribute: Aus den JSON-Dokumenten werden die für die Suche und Darstellung benötigten Informationen extrahiert.
2. Datentypkonvertierung: Comic-ID sowie `year`, `month` und `day` werden in Ganzzahlen umgewandelt. Ein separates Datumsfeld wird nicht erzeugt.
3. Datenbereinigung: Fehlende oder leere Werte werden behandelt, um eine konsistete Datenstruktur sicherzustellen.
4. Deduplizierung: Mögliche doppelte Einträge werden durch die eindeutige Comic-ID identifiziert und entfernt.
5. Anreicherung: Auf basis der Comic-ID wird die URL zur jeweiligen XKCD-Webseite generiert.


##### 3.2.1 Datenmodell des Final Layers 
Nach der Transformation enthält jeder Comic einen strukturierten Datensatz mit den folgenden Attributen:

| Attribute | Datentyp | Beschreibung |
| --- | --- | --- |
| id | Integer | Endeutige Comic-ID |
| title | String | Titel des Comics |
| safe_title | String  | Bereinigter Titel |
| year, month, day | Integer | Bestandteile des Erscheinungsdatums |
| search_text | String | Kleingeschriebener Suchtext aus Titel, Alternativtext und Transkript |
| alt | String | Alternativtext |
| transcript | String | Transkript des Comics |
| image_url | String | URL des Comic-Bildes |
| comic_url | String | URL zur XKCD-Webseite |

Diese bereitstellung eines einheitlichen Datenmodells, vereinfacht die spätere übertragung in die PostgreSQL-Datenbank.

##### 3.2.2 Speicherung im HDFS Final Layer 
Die aufbereiteten Daten werden naschließend im Final Layer von HDFS gespeichert.
Hierfür wird das Dateiformat von Apache Parquet verwendet. Dieses ermöglicht eine kompakte Speicherung und eine effiziente Verarbeitung durch Apache Spark.

Eine beispielhafte struktur:
```
/user/hadoop/xkcd/
├── raw/
│   ├── 2018/
│   ├── 2019/
│   └── ...
└── final/
    ├── part-00000-....snappy.parquet
    ├── part-00001-....snappy.parquet
    └── ...
```
Die Trennung zwischen Raw und Final Layer ermöglicht es, die ursprünglichen JSON-Dokumente unabhängig von den transformierten Daten aufzubewahren.

### 4. Load - Export nach PostgreSQL
Im letzten Schritt des ETL-Prozesses werden die Transformierten Comic-Daten aus dem HDFS Final Layer in eine PostgreSQL-Datenbank überführt.

PostgreSQL dient hierbei als Endnutzer-Datenbank und ermöglicht einen effizienten Zugriff auf die aufbereiteten Daten durch die FastAPI-Anwendung.

Die Übertragung erfolgt hierbei mithilfe von Apache Spark über eine JDBC-Verbindung zur PostgreSQL-Datenbank.

Die Comic-ID dient hierbei als eindeutiger Identifikator, sodass doppelte Datensätze verhindert werden können.
Für die spätere Volltextsuche wird in der PostgreSQL Datenbank ein entsprechender Suchindex angelegt. Dieser berücksichtigt die textuellen Attribute 'title', 'alt' und 'transcript'.

Die Daten können somit direkt in der Datenbank durchsucht werden, ohne dass FastAPI erst sämtliche Comics laden und selbst durchsuchen muss.




### 5. PostgreSQL - Datenbank
Für die persistente Speicherung und Bereitstellung der aufbereiteten Comic-Daten wird die relationale Datenbank PostgreSQL verwendet.

Die Datenbank dient dabei als Schnittstelle zwischen dem ETL-Workflow und der späteren Webanwendung. Die HDFS wird zur Speicherung der Rohdaten und der transformierten Daten verwendet, PostgreSQL verwendet hingegen einen effizienten Zugriff auf die einzelnen Comics.

#### 5.1 Datenbankschema
Die Datenbank enthält eine Tabelle comics, in welcher die aufbereiteten Informationen der XKCD-Comics gespeichert werden. 
Die struktur orientiert sich dabei an dem zuvor definierten Datenmodell des HDFS Final Layer.

```
CREATE TABLE comics (
    id INTEGER PRIMARY KEY,
    title TEXT,
    safe_title TEXT,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    alt TEXT,
    transcript TEXT,
    image_url TEXT,
    comic_url TEXT,
    search_text TEXT
);
```

Die Comic-ID wird dabei als Primärschlüssel verwendet, da dieses jeden Comic eindeutig identifiziert.

#### 5.2 Volltextsuche 
Um eine effiziente Suche innerhalb der gespeicherten Comics zu ermöglichen, wird die integrierte Volltextsuche von PostgreSQL verwendet.

Dabei werden die textuellen Attribute 'title', 'alt' und 'transcript' zu einem durchsuchbaren Text zusammengefasst.

Diese Suchinformationen werden anschließend mithilfe der PostgreSQL-Funktion to_tsvector() aufbereitet. Im weiteren verlauf wird ein GIN-Index erstellt, welcher die suche innerhalb der Textattribute beschleunigt.

```
CREATE INDEX idx_comics_search
ON comics
USING GIN (
    to_tsvector(
        'english',
        coalesce(search_text, '')
    )
);
```

Die Suche erfolgt somit durch eine SQL-Abfrage, welche die eingegebenen Suchbegrife mit den indexierten Textinformationen vergleicht.

Somit können auch größere Datenbestände effizient durchsucht werden, ohne sämtliche Datensätze einzeln inenrhalb der Anwendung verarbeiten zu müssen.


### 6. Backend - FastAPI
Um die Kommunikation zwischen React-Frontend und PostgreSQL-Datenbank zu ermöglichen, wird eine REST-API mit hilfe des Python Framworks FastAPI bereitgestellt.

Das Backend übernimmt hierbei die Verarbeitung der Suchanfrage und stellt die entsprechenden Ergebnisse über HTTP-Endpunkte bereit.

Somit kann eine Trennung zwischen Darstellung der Daten im Frontend und dem Zugriff auf die Datenbank sichergestellt.


#### 6.1 REST-API
Die FastAPI-Anwendung stellt einen Endpunkt zur Suche nach XKCD-Comics bereit.
Eine beispielhafte HTTP-Request:
```
GET /api/comics/search?q=data
``` 

Der übergebene Parameter q enthält hierbei den Suchbegriff des Nutzers.
Nach dem die Suchanfrage eingegangen ist, führt das Backend folgende Schritte aus:
1. Extraktion des Suchbegriffes aus der HTTP-Request
2. Validierung und Verarbeitung des übergebenen Suchbegriffes
3. Durchführung einer Volltextsuche innerhalb der PostgreSQL-Datenbank
4. Aufbereitung der gefundenen Datensätze.
5. Rückgabe der Suchergebnisse als JSON-Dokument.

Die eigentliche Volltextsuche wird hierbei durch PostgreSQL durchgeführt. FastAPI übernimmt lediglich die Kommunikation zwischen der Datenbank und dem Frontend.

#### 6.2 Rückgabe der Suchergebnisse 
Die in der Volltextsuche gefundenen Comics werden in einem JSON-Format an das Frontend zurückgegeben.
Die Antwort enthält `query`, `page`, `limit`, `total` und die Liste `results`. Jeder Treffer enthält `id`, `title`, `alt`, `image_url`, `comic_url`, `year`, `month`, `day` und `relevance`.

Weitere Endpunkte:

| Endpunkt | Zweck |
| --- | --- |
| `GET /api/health` | Prüft die Datenbankverbindung |
| `GET /api/comics/search?q=data&page=1&limit=20` | Volltextsuche mit Seitennavigation |
| `GET /api/comics/{comic_id}` | Einzelnen Comic abrufen; 404 bei fehlender ID |


### 7. Frontend - React
Für die Benutzeroberfläche für die XKCD Search Engine wird die JavaScript Bibliothek React verwendet.
Das Frontend ermöglicht es dabei dem Nutzer, die gespeicherten XKCD-Comics mithilfe einer Suchfunktion zu durchsuche un die gefundenen Comics direkt anzuzeigen.

#### 7.1 Suchfunktion
Die oberfläche stellt dem Nutzer ein Eingabefeld bereit, über welches dieser einen beliebigen Suchbegriff eingeben kann. Nach Absenden der Suchanfrage, wird eine HTTP-Anfrage an die Fast-API Anwendung gesendet. 
Das Frontend führt dabei folgenden Schritte aus:
1. Annahme des Suchbegriffs
2. Übermitteln des Suchbegriffs an die REST-API
3. Empfangen der Suchergebnisse im JSON-Format.
4. Verarbeitung der empfangenen Daten
5. Darstellung der gefundenen Comics.

#### 7.2 Darstellung der Suchergebnisse
Die gefundenen Comics werden innerhalb der Benutzeroberfläche als einzelnes Ergebniss dargestellt.
Dabei werden unteranderem diese Informationen angezeigt:
* Titel des Comics
* Bild des Comics
* Erscheinungsdatum
* Alternativtext
* Link zur ursprünglichen XKCD-Webseite


### 8. Komponenten des Workflows

Die XKCD Search Engine besteht aus mehreren Komponenten, welche gemeinsam die automatisierte Verarbeitung und Bereitstellung der Comic Daten ermöglichen. 

| Komponente | Technologie | Aufgabe | 
| --- | --- | --- |
| Datenquelle | XKCD API | Bereitstellung der ursprünglichen Comic-Daten |
| Datenextraktion | Python | Automatisierter Download der JSON-Dokumente |
| Raw Layer | Hadoop HDFS | Speicherung der ursprünglichen JSON-Daten |
| Transformation | Apache Spark / PySpark | Bereinigung und Strukturierung der Comic-Daten |
| Final Layer | Hadoop HDFS / Parquet | Speicherung der transformierten Daten |
| Datenbankexport | Spark JDBC | Übertragung der Daten nach PostgreSQL |
| Datenbank | PostgreSQL | Persistente Speicherung und Volltextsuche |
| Backend | FastAPI | Bereitstellung der REST-Schnittstelle |
| Frontend | React | Benutzeroberfläche zur Suche und Darstellung |
| Orchestrierung | Apache Airflow | Automatisierte Ausführung des ETL-Workflows |

### 9. Ablauf der Pipeline
Der ETL-Workflow wurde mithilfe von Apache Airflow automatisiert. Airflow ermöglicht es hierbei die Definition und Ausführung einzelner Verarbeitungsschritte sowie deren Zeitlichen und logischen Abhängigkeiten.

#### 9.1 Aufbau des Airflow-DAGs
Die Pipeline wird in mehreren aufeinanderfolgende Tasks aufgeteilt.

| Task | Beschreibung |
| --- | --- | 
| extract_xkcd | Herunterladen der Comic-Daten über die XKCD-API |
| transform_xkcd | Verarbeitung und Bereinigung der Rohdaten mit PySpark |
| load_postgresql | Übertragung der aufbereiteten Daten in die PostgreSQL-Datenbank |

Diese Tasks werden dabei in einer festgelegten Reihenfolge ausgeführt:

extract_xkcd -> transform_xkcd -> load_postgresql

