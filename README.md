# Big Data Practical Exam

## XKCD Search Engine

### 1. Ziel des Projekts
Ziel des Projektes ist es eine durchsuchbare Datenbank für XKCD-Comics aufzubauen. Dafür werden die öffentlich verfügbaren Daten der XKCD-API automatisiert heruntergeladen, in einem Hadoop Distributed File System (HDFS) gespeichert, mit Apache Spark verarbeitet und anschließend in eine PostgreSQL-Datenbank übertragen.

Die aufbereiteten Daten werden anschließend durch eine FastAPI-Anwendung bereitgestellt. Ein React-Frontend ermöglicht es dann dem Nutzer, die gespeicherten Comics über eine Volltextsuche zu durchsuchen und die Ergebnisse anzuzeigen.

Somit besteht der vollständige Datenfulls aus den folgenden Komponenten:
XKCD API -> HDFS Raw Layer -> PySpark Transformation -> HDFS Final Layer -> PostgreSQL -> FastAPI -> React Frontend

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


### 4. Load - Export nach PostgreSQL



### 5. PostgreSQL - Datenbank

### 6. Backend - FastAPI

### 7. Frontend

### 8. Komponenten des Workflows


### 9. Ablauf der Pipeline

### 10. Ergebnis