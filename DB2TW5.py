# dbExtractor.py -- extracts music and beatmaps from db to folders
# usage : python dbExtractor.py folder_with_beatmap_dbs/ maindb folder_with_wav_files/
# Disclaimer : I didn't reverse engineer the app.
# This script actually can automatically place mp3 files in the corresponding folders of each beatmap folders.
# folder_with_wave_files contains : song_XXXX.wav  files.
# maindb is a db which is the largest in the "a" folder.
# folder_with_beatmap_dbs contains the database files from the "a" folder.
# you must play at least once to get the beatmap of the song.
 
import sqlite3
import os
import sys
import json
import csv
import io
from collections import OrderedDict
import subprocess
from pydub import AudioSegment

def getColor(circletype):
    return {
        1: [255,0,0,255],
        2: [0,255,0,255],
        3: [255,255,0,255],
        4: [255,255,255,255]    
    } [circletype]

def getColorType(circletype):
    return {
        1: 'cute',
        2: 'cool',
        3: 'passion',
        4: 'all'
    }[circletype]


def getMusicNumber(filename):
    filename = filename.replace("musicscores/m", "")
    return int(filename.split("/")[0])


def getDifficulty(filename):
    return int(filename.split(".")[-2].split("/")[-1].split("_")[-1])


def getTW5Difficulty(difficulty):
    return {
        1: 1,
        2: 1,
        3: 2,
        4: 3,
        5: 4,
        101: 4,
        11: 1,
        12: 2
    }[difficulty]


def getTW5Mode(typea):
    return {
        1: 0,   # 1 in dele is normal note
        2: 1,   # 2 in dele is long note
        3: 2    # 3 in dele is slide note
        # 100 : 0
        # 91 : 0
    }[typea]


def getTW5Flick(status):
    return {
        0: 0,
        1: 1,
        2: 2
    }[status]


difficulty_name = {'1': 'easy', '2': 'normal', '3': 'pro', '4': 'hard',
                   '5': 'apex', '11': 'light', '12': 'trick', '101': 'apex2'}

folder = sys.argv[1]
maindb = sys.argv[2]
songsFolder = sys.argv[3]
mainconn = sqlite3.connect(maindb)
mainc = mainconn.cursor()
files = os.listdir(folder)
for fil in files:
    
    filename = folder+fil
    print("processing ", filename)
    conn = sqlite3.connect(filename)
    c = conn.cursor()
    c.execute('SELECT * FROM blobs')
    all_rows = c.fetchall()
    music_number = -1
    for row in all_rows:
        csvfilename = row[0]
        # print(csvfilename)
        #folder_name = ' '
        if music_number == -1:
            music_number = getMusicNumber(csvfilename)
            # query the music info from the main db
            mainc.execute(
                'SELECT music_data_id FROM live_data WHERE id = '+str(music_number))
            music_data_id = mainc.fetchone()[0]
            # query the music info using the music_data_id
            mainc.execute(
                'SELECT * FROM music_data WHERE id = ' + str(music_data_id))
            music_info = mainc.fetchone()
            music_name = music_info[1]
            bpm = music_info[2]
            composer = music_info[3]
            lyricist = music_info[4]
            sound_offset = music_info[5]
            sound_length = music_info[6]
            mainc.execute('SELECT circle_type FROM live_data WHERE id = '+str(music_number))
            circleType = mainc.fetchone()[0]
            colorName = getColorType(circleType)
            color = getColor(circleType)
            # ignore name_sort and kana names
            # sanitize 
            folder_name = music_name.replace(u"\\n", u' ')
            folder_name = folder_name.replace(u"/", u'-')
            folder_name = folder_name.replace(u"\\", u'-')
            folder_name = folder_name.replace(u"%", u' percent ')
            folder_name = folder_name.replace(u"?", u'_!')
            folder_name = folder_name.replace(u"*", u'★')
            folder_name = folder_name.replace(u":", u'=')
            folder_name = folder_name.replace(u"|", u'!')
            folder_name = folder_name.replace(u"\"", u'``')
            folder_name = folder_name.replace(u"<", u'⟨')
            folder_name = folder_name.replace(u">", u'⟩')
            folder_name = folder_name.replace(u'.',u'·')
            # print(folder_name)          
            try:
                os.makedirs(folder_name)
            except FileExistsError:
                print("Waring: appending color name")
                folder_name = folder_name+'_'+colorName
                os.makedirs(folder_name)     
            print(music_number, music_data_id, music_name, folder_name)
            musicoutPath = os.path.join(os.getcwd(),os.path.join(folder_name,folder_name+'.mp3'))
            musicinPath = os.path.join(songsFolder,'song_'+'%04d'%music_data_id+'.wav')
            print(musicinPath)
            print(musicoutPath)
            #AudioSegment.from_wav(musicinPath).export(musicoutPath,format='mp3',codec='libmp3lame')

            
        if "cyalume" in csvfilename or "lyrics" in csvfilename or "2dchara" in csvfilename or "_analyzer.bytes" in csvfilename:
            continue
        # 메타데이터를 읽어들입니다.
        # "version":2,
        # "metadata":
        # [
        #   "level": the difficulty,
        #   "artist":"Query_from the db",
        #   "mapper":"Deresute official",
        #   "density":30
        # ],
        
        difficulty = getDifficulty(csvfilename)
        outfilename = folder_name+'/'+folder_name + \
            '_'+difficulty_name[str(difficulty)]+'.tw5'
        mainc.execute('SELECT level_vocal FROM live_detail WHERE live_data_id = ' +
                      str(music_number)+' and difficulty_type = '+str(difficulty))
        density = mainc.fetchone()[0]
        print(density)
        twData = OrderedDict()
        twData["version"] = 2
        twData["metadata"] = {"level": getTW5Difficulty(
            difficulty), 'artist': composer+'+'+lyricist, "mapper": "official", "density": density, "bpm": [bpm]}
        print(outfilename)
        csvdata = row[1].decode('utf-8')
        # now parse csv data and create tw5
        csv_read = csv.DictReader(io.StringIO(csvdata))
        # lastGid = 0
        prevIDs = {0: 0}
        notes = []
        prevID = 0
        idd = 0
        # key = endline
        longnoteIDs = {}
        for csv_row in csv_read:
            # TW5에 맞게 계속 씁니다.
            # gid에 대해
            # gid가 0이 아니면
            # 현재 gid에 대해 last id 를 구한다
            # 없으면 0이고 있으면 그게 last이다.
            # 그다음 이 gid에 대해 last id를 자신으로 설정한다.
            
            # 롱노트의 경우 따로 previd를 설정해 줘야 한다.
            # 롱노트 previd는 레인별로이므로 잘 해준다
            # 길이 5짜리 배열을 만든다.
            # 롱노트라면 해당하는 줄의 last가 있는지 찾는다
            # 없으면 자신을 등록하고 자신의 last는 0 하고 종료
            # 있으면 자신의 last에 그것을 이용하고 그걸 제거
            prevID = 0
            #            idd = int(csv_row["id"])
            gid = csv_row["groupId"]
            mode = int(csv_row["type"])
            # avoid metadata
            if mode > 3:
                continue
            idd = idd + 1
            twmode = getTW5Mode(mode)
            endpos = float(csv_row["finishPos"])
            flick = getTW5Flick(int(csv_row["status"]))
            if gid == 0:
                pass
            #    prevID = 0  # prevIDs[gid] = 0
            # 롱노트 중인진 모르겠다.
            else:
                #내가 그룹에 있다.
                if gid in prevIDs:
                    prevID = prevIDs[gid]
                else:
                    pass
                    #prevID = 0
                prevIDs[gid] = idd
            if endpos in longnoteIDs:
                # 롱노트 중이었다면 해제한다. 자신의 prev를 그 롱노트로 설정한다.
                prevID = longnoteIDs[endpos]
                twmode = 1
                longnoteIDs.pop(endpos,None)
            elif mode == 2:
                # 롱노트 중이 아니었고 자신이 롱노트라면 등록한다.
                prevID = 0
                longnoteIDs[endpos] = idd
            # 롱노트 중도 아니었고 자신이 롱노트도 아니다.
            #else:
            if mode ==1 and flick == 0 :
                prevID=0
            # idds must start from 1, not 3 or 0!! Otherwise the game wouldn't end
            notes.append({"ID": idd,
                          "Size": 0,
                          "Color": color,
                          "Mode": twmode,
                          "Flick": flick,
                          "Time": float(csv_row["sec"]),
                          "Speed": 1.0,
                          "StartLine": float(csv_row["startPos"]),
                          "EndLine": endpos,
                          "PrevIDs": [prevID]
                          })
        twData["notes"] = notes
        with open(outfilename, 'w') as outfile:
            json.dump(twData, outfile, indent=4)
        print("DIfficulty:", difficulty)
    # input()
    # print(all_rows)
    conn.close()
mainc.close()
