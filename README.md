# CGSSBeatmap2TW5
A python script that helps extracting CGSS's beatmap to TW5 format, which is used by tempest-wave.

## Usage
1. Install python
1. Pull `/sdcard/Android/data/deleste_folder..../files/a` to your PC.
1. run `file * | SQL > dbs.txt` in the `a` folder(pulled)
1. run `python extractor.py a/ a/extracted/ < a/dbs.txt` in the parent directory of the extracted `a`.
1. move the largest file and the smallest file from `a/dbs` to outer folder. The largest is the main.db.
1. Prepare wav files.
1. run `python dbExtractor.py a/extracted/ main.db wav_folder/`
1. The script will create a lot of folders named after the song's names.
