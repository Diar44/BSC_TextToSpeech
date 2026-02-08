# Speechmatics Livecaptions
Dieses Projekt ist im Rahmen der Bachelorarbeit "Modernizing Websites" von Diar entstanden.
Es basiert auf dem [Speechmatics Real-time Javascript SDK](https://docs.speechmatics.com/sdk/real-time-javascript-sdk)
und übernimmt einen Livestream, der von Speechmatics in Echtzeit transkribiert wird.

## Systemanforderungen
Um das Projekt zu starten, muss [NodeJS](https://nodejs.org/en) und [FFmpeg](https://www.ffmpeg.org/) installiert sein.

## Installation
`.env.local` als Kopie der `.env`-Datei erstellen und dort den ApiKey von Speechmatics
einfügen und den Streaminglink eingeben.

Beispiel:
```
apiKey = "<KEY>"
streamLink = "rtmp://localhost/live/transcode1080_live"
filePath = "/mnt/c/WowzaContent/" // Ordner, wo die Transcript-Dateien zwischengespeichert werden
language = "de"
targetLanguages = "en,it" // Wichtig: mit "," teilen zur richtigen Spracherkennung; Nur benötigt bei Übersetzung in eine andere Sprache
maxDelay = 1 // Zum einstellen vom Delay von der Transkription
languageBreakWait = 1000 // Zu langer übersetzter Text wird in der mitte gebrochen und die Zeit zum warten zum anzeigen von der zweiten Hälfte vom Text (1000 = 1 Sekunde)
translationMaxLength = 30 // die maximale länge des Textes für die übersetzung kann variable definiert werden. 1 ... ein Buchstabe.
```

Dann die Libraries installieren

```
npm install
```


## Ausführung
Für die normale ausführung mittels .env.local Standarddaten in Linux Shell:

```
  node speechmatics.js
```
In Kürze sollte dann in der Console in laufenden Abständen die Untertitelung angezeigt werden.

### Für eine erweiterte Ausführung und direkte veränderung der Daten mittels Command

Beispiel:

```
  node speechmatics.js --streamLink=rtmp://fms3.braintrust.at/liveloop/eve_speechmatics --filePath=/mnt/c/FH/ --language=de
```

Wichtig es muss vor der Eingabe eines von diesen Werten angegeben werden mit einem '=' damit er es richtig greift.

```
--apiKey, --streamLink, --filePath, --language, --targetLanguages, --maxDelay, --languageBreakWait
```

## Troubleshooting

### Fehlermeldung "ffmpeg error: Error: spawn ffmpeg ENOENT"
Prüfen ob FFmpeg installiert ist. `ffmpeg` muss für den aktuellen User ausführbar sein.

### Log
Es existiert auch ein Logfile im gleichen verzeichnis wie die textfiles.
