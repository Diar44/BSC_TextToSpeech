import fs from 'fs';
import { RealtimeClient } from "@speechmatics/real-time-client";
import { spawn } from 'child_process';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const currentDate = new Date();
const client = new RealtimeClient();
let finalText = '';
let finalTextLanguage = '';
let transcriptFile = 'transcript_'+currentDate.getDate()+(currentDate.getMonth()+1)+currentDate.getFullYear();
let startTime = 0;
let languages = {};

//Standardwerte vorbereiten von .env
let config = {
    apiKey: process.env.apiKey,
    targetLanguage: process.env.targetLanguages,
    language: process.env.language,
    streamLink: process.env.streamLink,
    filePath: process.env.filePath,
    maxDelay: parseFloat(process.env.maxDelay) || 4,
    languageBreakWait: parseFloat(process.env.languageBreakWait) || 1000,
    translationMaxLength: process.env.translationMaxLength,
};

//Mit übergabewerten falls vorhanden ersetzen
const args = process.argv.slice(2);
args.forEach(arg  => {
    let [key, value] = arg.split('=');
    key = key.replace("--","");
    if (config.hasOwnProperty(key)) {
        config[key] = value;
    }
});

if (!config.apiKey) {
    logging("[ERROR] No ApiKey!");
    console.log("[ERROR] No ApiKey!");
}

transcribeRealTimeStream();

async function transcribeRealTimeStream() {
    logging("[INFO] Transkription wird gestartet.");

    console.log("Connected: Starting transcription!");

    const jwt = await fetchJWT();

    if(config.targetLanguage === ""){
        await client.start(jwt, {
            transcription_config: {
                language: config.language,
                enable_partials: true,
                operating_point: 'enhanced',
                max_delay: config.maxDelay,
            },
        });
    }else{
        const targetLanguages = config.targetLanguage.split(',');

        await client.start(jwt, {
            transcription_config: {
                language: config.language,
                enable_partials: true,
                operating_point: 'enhanced',
                max_delay: config.maxDelay,
            },
            translation_config: {
                target_languages: targetLanguages,
            },
        });
    }

    // rtmp Stream wird mittels ffmpeg zu einer wav umgebaut damit wir es an Speechmatics senden können
    function startFFmpeg() {
        const ffmpeg = spawn('ffmpeg', [
            '-i', config.streamLink,
            '-f', 'wav',
            '-ar', '16000',
            '-c:a', 'pcm_s16le',
            '-fflags', 'nobuffer',
            '-flags', 'low_delay',
            'pipe:1',
        ]);

        ffmpeg.stdout.on('data', (data) => {
            client.sendAudio(data);
        });

        ffmpeg.stderr.on('data', () => {});

        //Es wird 3 Sekunden gewartet und dann wieder versucht
        ffmpeg.on('close', (code) => {
            logging("[ERROR] Fehler mit dem Stream. Es wird versucht, eine neue Verbindung aufzubauen.");
            console.log(`Fehler mit dem Stream. Es wird versucht, eine neue Verbindung aufzubauen. (${code})`);
            setTimeout(() => {
                console.log("FFMPEG wird neugestartet.");
                startFFmpeg();
            }, 3000);
        });

        ffmpeg.on('error', (err) => {
            console.error('Failed to start ffmpeg:', err);
        });
    }

    startFFmpeg();
}

// Zum aufbauen der verbindung und senden vom API Key 
async function fetchJWT() {
    const resp = await fetch('https://mp.speechmatics.com/v1/api_keys?type=rt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${config.apiKey}`,
        },
        body: JSON.stringify({
            ttl: 3600,
        }),
    });
    if (!resp.ok) {
        throw new Error('Bad response from API', { cause: resp });
    }
    return (await resp.json()).key_value;
}

// Hier werden der response vom Server bearbeitet
client.addEventListener('receiveMessage', ({ data }) => {
    //Für die Normale Transcription von der eingabesprache
    if (data.message === 'AddTranscript') {
        const time = new Date().getTime();
        const text = data.metadata.transcript;

        if(finalText === "") startTime = time;

        finalText = finalText + text;

        if(finalText.length > 40){
            finalText = checkStringForAnnotation(finalText)
            console.log(config.language +':' + finalText);
            fs.appendFile(config.filePath + 'ontextdata.txt', finalText + "\n", (err) => {
                if (err) throw err;
            });
            writeJsonFile(startTime,time,finalText);
            finalText = "";
        }
    }

    //Für die übersetzung in einer anderen sprache
    if (data.message === 'AddTranslation') {
        const language = data.language;
        const translations = data.results[0].content;
        const time = new Date().getTime();

        
        if(finalTextLanguage === "") languages["startime_"+language] = time;

        finalTextLanguage = translations;

        if (finalTextLanguage.length > config.translationMaxLength) { //Wenn der Text zulange ist wird er in der Mitte geteilt und angezeigt
            const midpoint = Math.floor(finalTextLanguage.length / 2);

            // Teilweise Aufteilung an Wortgrenze (nicht mitten im Wort trennen)
            let splitIndex = finalTextLanguage.lastIndexOf(' ', midpoint);
            if (splitIndex === -1) splitIndex = midpoint;

            let firstHalf = finalTextLanguage.slice(0, splitIndex).trim();
            let secondHalf = finalTextLanguage.slice(splitIndex).trim();

            console.log(`${language}: firstHalf: ${firstHalf}`);
            firstHalf = checkStringForAnnotation(firstHalf)
            fs.appendFile(config.filePath + 'ontextdata_'+language+'.txt', firstHalf + "\n", (err) => {
                if (err) throw err;
            });

            writeJsonFile(languages["startime_"+language],time,firstHalf,language);

            setTimeout(() => {
                console.log(`${language}: secondHalf: ${secondHalf}`);
                secondHalf = checkStringForAnnotation(secondHalf)
                fs.appendFile(config.filePath + 'ontextdata_'+language+'.txt', secondHalf + "\n", (err) => {
                    if (err) throw err;
                });
                writeJsonFile(time,time + config.languageBreakWait,secondHalf,language);

            }, config.languageBreakWait);
        }else{
            console.log(`${language}: ${finalTextLanguage}`);
            fs.appendFile(config.filePath + 'ontextdata_'+language+'.txt', finalTextLanguage + "\n", (err) => {
                if (err) throw err;
            });
            writeJsonFile(languages["startime_"+language],time + 1000,finalTextLanguage,language);
        }

        finalTextLanguage = "";
    }
});

// Loggen für Errors oder Messages
function logging(message){
    const logFile = `${config.filePath}log${currentDate.getDate()}${currentDate.getMonth()+1}${currentDate.getFullYear()}.txt`;
    const time = new Date().toLocaleTimeString('de-DE');
    fs.appendFile(logFile, `${message} | ${time}\n`, (err) => {
        if (err) console.error("Fehler beim Loggen:", err);
    });
}

// Schreibt ein JsonFile für das vtt File im späteren verlauf
function writeJsonFile(startTime, endTime, data,language = ""){
    let jsonData = JSON.stringify({ startTime: startTime, endTime: endTime , data: data});
    fs.appendFile(config.filePath + transcriptFile + language +'.json', jsonData , (err) => {
        if (err) throw err;
    });
}

// Entfernt alle . , ? ! aus den ersten 5 Zeichen
function checkStringForAnnotation(text) {
    const firstFive = text.slice(0, 5);
    if (/[.,?!]/.test(firstFive)) {
        const cleaned = firstFive.replace(/[.,?!]/g, '') + text.slice(5);
        return cleaned;
    }
    return text;
}