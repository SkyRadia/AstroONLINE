import os
import tkinter as tk
from PIL import Image, ImageTk
from threading import Thread
import nfc
import requests
import json
import binascii
import ast
import time
import pygame
from datetime import datetime, timedelta
from google.cloud import datastore
cwd = os.getcwd()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Keys/tgtenmon-account-1bba0d987b0b.json"


def upsert(name, dic):
    client = datastore.Client()
    complete_key = client.key("Task", name)
    task = datastore.Entity(key=complete_key)
    task.update(dic)
    client.put(task)


def insert(name, dic):
    client = datastore.Client()
    with client.transaction():
        incomplete_key = client.key("Task", name)
        task = datastore.Entity(key=incomplete_key)
        task.update(dic)
        client.put(task)


def update(name, book, value):
    client = datastore.Client()
    with client.transaction():
        key = client.key("Task", name)
        task = client.get(key)
        task[book] = value
        client.put(task)


def get(name):
    client = datastore.Client()
    key = client.key("Task", name)
    return client.get(key)

pygame.mixer.init()
pygame.mixer.music.set_volume(0.5)

today = datetime.now().strftime("%Y-%m-%d")

global memberjson, datajson, authjson
memberopen = open(
    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Members.json", "r", encoding="utf_8")
memberjson = json.load(memberopen)
memberopen.close()
dataopen = open(
    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Data.json", "r", encoding="utf_8")
datajson = json.load(dataopen)
dataopen.close()
authopen = open(
    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/AuthList.json", "r", encoding="utf_8")
authjson = json.load(authopen)
authopen.close()

auth = False
boolexit = False
bgcolor = "#e2e7fb"
status = int()


def flaskmessage(message):
    global status
    try:
        status = int()
        message = str(message).encode()
        strhex = binascii.hexlify(message).decode()
        url = 'https://tgtenmon-account.an.r.appspot.com/updatelog'
        headers = {
            'today': str(today),
            'flaskmessage': str(strhex)
        }
        access = requests.post(url, headers=headers)
        status = access.status_code
    except requests.exceptions.ConnectionError:
        status = "ConnectionError"
    except:
        status = 400


def on_startup(targets):
    return targets


def cutgrade(str):
    return str[:1]


def cutclass(str):
    return str[2:3]


def cutnumber(str):
    if str[4:6].isnumeric:
        return str[4:6]
    else:
        return str[9:11]


def on_connect(tag):
    try:
        tag = str(tag).replace("Type2Tag 'NXP NTAG215' ID=", "")
    except:
        tag = "Error"
    global info1, info2, info3, info4, auth, guide1, guide2, guide3, guide4, guide5, guide6, guide7, wantreg, wantauthreg, wantcopy, ready, check
    ready = True
    today = datetime.now().strftime("%Y-%m-%d")
    if datajson["today"] != today:
        ready = False
        def renew():
            var.set(1)
            global ready
            datajson["today"] = today
            datajson["logged members"] = []
            with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Data.json", "w", encoding="utf-8") as dataopen:
                json.dump(datajson, dataopen)
            ready = True
            check.place_forget()
        pygame.mixer.music.load(
            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemused.wav")
        pygame.mixer.music.play()
        var = tk.IntVar()
        label.config(text="新しい日の記録を作成します。\n確定してください。", font=("源ノ角ゴシック", font, "bold"))
        check = tk.Button(root, command=renew, text="作成", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=10, height=1)
        check.place(relx=0.5, rely=0.64, relheight=0.08,
                        relwidth=0.2, anchor="c")
        check.wait_variable(var)

    if str(tag) in memberjson:

        def okchange():
            global ident
            info1.place_forget()
            info2.place_forget()
            info3.place_forget()
            info4.place_forget()
            ident = tk.Entry(width=50, justify="center",
                             background=bgcolor, relief="flat", foreground="#616161", font=("源ノ角ゴシック", font, "bold"))
            ident.focus()
            ident.pack(pady=8)
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/205 OK 'Ssuka.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                continue
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/07 Your Name, Please (Noiseless).mp3")
            pygame.mixer.music.play(-1)
            label.config(text="学籍情報を変更します。\n学年-クラス(番号)を\n入力してください。",
                         font=("源ノ角ゴシック", font, "bold"))

            def okident(event):
                root.unbind("<Return>")
                ident.pack_forget()
                root.focus()
                identstr = str(ident.get())
                if len(identstr) == 7:
                    def change():
                        try:
                            url = "https://tgtenmon-account.an.r.appspot.com/getdata"
                            requests.post(url)
                            url = "https://tgtenmon-account.an.r.appspot.com/getdata"
                            requests.post(url)
                            pointsdata = get("Points")
                            pointsdata[identstr +
                                       memberjson[str(tag)][7:]] = pointsdata[memberjson[str(tag)]]
                            pointsdata.pop(memberjson[str(tag)])
                            upsert("Points", pointsdata)
                            pointsid = get("PointsID")
                            for i in pointsid:
                                if pointsid[i] == memberjson[str(tag)]:
                                    pointsid[i] = identstr + \
                                        memberjson[str(tag)][7:]
                                    upsert("PointsID", pointsid)
                                    break
                            memberjson[str(tag)] = identstr + \
                                memberjson[str(tag)][7:]
                            with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Members.json", "w", encoding="utf-8") as memberopen:
                                json.dump(memberjson, memberopen)
                            pygame.mixer.music.load(
                                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemused.wav")
                            pygame.mixer.music.play()
                            label.config(text="学籍情報を変更しました。\nカードを離してください。",
                                         font=("源ノ角ゴシック", font, "bold"))
                        except:
                            pygame.mixer.music.load(
                                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                            pygame.mixer.music.play()
                            label.config(text="インターネットに接続されていないため、\n変更ができませんでした。\nカードを離してください。",
                                         font=("源ノ角ゴシック", font, "bold"))
                    label.config(text="通信しています・・・", font=(
                        "源ノ角ゴシック", font, "bold"))
                    root.after(1, change)
                else:
                    pygame.mixer.music.load(
                        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                    pygame.mixer.music.play()
                    label.config(text="7桁で入力してください。\nカードを離してください。",
                                 font=("源ノ角ゴシック", font, "bold"))
            root.bind('<Return>', okident)

        def okunreg():
            global check
            info1.place_forget()
            info2.place_forget()
            info3.place_forget()
            info4.place_forget()
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemequip.wav")
            pygame.mixer.music.play()
            label.config(text="{}さんの\n登録を解除します。\n確定してください。".format(
                memberjson[str(tag)][7:]), font=("源ノ角ゴシック", font, "bold"))

            def okdelete():
                global label
                check.place_forget()

                def bgm():
                    pygame.mixer.music.load(
                        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/54 A Bad Dream.mp3")
                    pygame.mixer.music.play(-1)
                    try:
                        url = "https://tgtenmon-account.an.r.appspot.com/getdata"
                        requests.post(url)
                        pointsdata = get("Points")
                        pointsdata.pop(memberjson[str(tag)])
                        upsert("Points", pointsdata)
                        pointsid = get("PointsID")
                        for i in pointsid:
                            if pointsid[i] == memberjson[str(tag)]:
                                pointsid.pop(i)
                                upsert("PointsID", pointsid)
                                break
                        datajson["logged members"].remove(memberjson[str(tag)])
                        with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Data.json", "w", encoding="utf-8") as dataopen:
                            json.dump(datajson, dataopen)
                        memberjson.pop(str(tag), None)
                        with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Members.json", "w", encoding="utf-8") as memberopen:
                            json.dump(memberjson, memberopen)
                        time.sleep(5)
                        label.config(text="登録を解除し、\n今日の記録から削除しました。\nカードを離してください。\n⊙﹏⊙∥bye...", font=(
                            "源ノ角ゴシック", font, "bold"))
                    except:
                        pygame.mixer.music.load(
                            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                        pygame.mixer.music.play()
                        label.config(text="インターネットに接続されていないため、\n処理ができませんでした。\nカードを離してください。", font=(
                            "源ノ角ゴシック", font, "bold"))

                label.config(text="削除しています・・・", font=("源ノ角ゴシック", font, "bold"))
                root.after(1, bgm)
            check = tk.Button(root, command=okdelete, text="確定", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=10, height=1)
            check.place(relx=0.5, rely=0.73, relheight=0.08,
                        relwidth=0.2, anchor="c")

        def okunwrite():
            global check
            info1.place_forget()
            info2.place_forget()
            info3.place_forget()
            info4.place_forget()
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemequip.wav")
            pygame.mixer.music.play()
            label.config(text="{}さんを\n今日の記録から削除します。\n確定してください。".format(
                memberjson[str(tag)][7:]), font=("源ノ角ゴシック", font, "bold"))

            def okpop():
                check.place_forget()
                datajson["logged members"].remove(memberjson[str(tag)])
                with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Data.json", "w", encoding="utf-8") as dataopen:
                    json.dump(datajson, dataopen)
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/die.wav")
                pygame.mixer.music.play()
                label.config(text="{}さんを\n今日の記録から削除しました。\nカードを離してください。".format(
                    memberjson[str(tag)][7:]), font=("源ノ角ゴシック", font, "bold"))
            check = tk.Button(root, command=okpop, text="確定", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=10, height=1)
            check.place(relx=0.5, rely=0.73, relheight=0.08,
                        relwidth=0.2, anchor="c")

        def okcopy_member():
            info1.place_forget()
            info2.place_forget()
            info3.place_forget()
            info4.place_forget()
            root.clipboard_append(str(tag))
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemused.wav")
            pygame.mixer.music.play()
            label.config(text="このカードのIDをコピーしました。\nカードを離してください。",
                         font=("源ノ角ゴシック", font, "bold"), bg=bgcolor)

        while True:
            if ready == False:
                continue
            else:
                break

        if memberjson[str(tag)] in datajson["logged members"]:
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/reflect2.wav")
            pygame.mixer.music.play()
            label.config(text="{}さんは\nすでに記録されています。".format(
                memberjson[str(tag)][7:]), font=("源ノ角ゴシック", font, "bold"))
        else:
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/reflect1.wav")
            pygame.mixer.music.play()
            datajson["logged members"].append(memberjson[str(tag)])
            datajson["logged members"] = sorted(
                datajson["logged members"], key=cutnumber)
            datajson["logged members"] = sorted(
                datajson["logged members"], key=cutclass)
            datajson["logged members"] = sorted(
                datajson["logged members"], key=cutgrade, reverse=True)
            with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Data.json", "w", encoding="utf-8") as dataopen:
                json.dump(datajson, dataopen)
            label.config(
                text="ようこそ、{}さん。\n参加を記録しました。".format(memberjson[str(tag)][7:]), font=("源ノ角ゴシック", font, "bold"))
        if auth == True:
            info1 = tk.Button(root, command=okunwrite, text="記録から削除", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
            info2 = tk.Button(root, command=okunreg, text="登録解除", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
            info3 = tk.Button(root, command=okchange, text="学籍情報変更", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
            info4 = tk.Button(root, command=okcopy_member, text="IDをコピー", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
            if boolexit == False:
                info1.place(relx=0.5, rely=0.6, relheight=0.08,
                            relwidth=0.2, anchor="c")
                info2.place(relx=0.5, rely=0.7, relheight=0.08,
                            relwidth=0.2, anchor="c")
                info3.place(relx=0.5, rely=0.8, relheight=0.08,
                            relwidth=0.2, anchor="c")
                info4.place(relx=0.5, rely=0.9, relheight=0.08,
                            relwidth=0.2, anchor="c")
    elif str(tag) in authjson["authlist"]:
        pygame.mixer.music.load(
            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemopen.wav")
        pygame.mixer.music.play()
        label.config(text="管理者用キーを認証しました。\nオペレーションをタップしてください。",
                     font=("源ノ角ゴシック", font, "bold"))
        guide1 = tk.Button(root)
        guide2 = tk.Button(root)
        guide3 = tk.Button(root)
        guide4 = tk.Button(root)
        guide5 = tk.Button(root)
        guide6 = tk.Button(root)
        guide7 = tk.Button(root)

        def oksend():
            global check
            guide1.place_forget()
            guide2.place_forget()
            guide3.place_forget()
            guide4.place_forget()
            guide5.place_forget()
            guide6.place_forget()
            if len(authjson["authlist"]) >= 2:
                guide7.place_forget()
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemequip.wav")
            pygame.mixer.music.play()
            label.config(text="今日の記録をクラウドに上書きします。\n確定してください。",
                         font=("源ノ角ゴシック", font, "bold"))

            def okcloud():
                def connectc():
                    flaskmessage(str(datajson["logged members"]))
                    if status == 200:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(
                            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/Windows Proximity Notification.wav")
                        pygame.mixer.music.play()
                        label.config(text="上書きが完了しました。\nカードを離してください。",
                                     font=("源ノ角ゴシック", font, "bold"))
                        label.pack()
                    elif status == "ConnectionError":
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(
                            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                        pygame.mixer.music.play()
                        label.config(text="インターネットに\n接続されていません。\nカードを離してください。",
                                     font=("源ノ角ゴシック", font, "bold"))
                        label.pack()
                    else:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(
                            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                        pygame.mixer.music.play()
                        label.config(text="通信に失敗しました。\nカードを離してください。",
                                     font=("源ノ角ゴシック", font, "bold"))
                        label.pack()
                check.place_forget()
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/Windows Proximity Connection.wav")
                pygame.mixer.music.play(-1)
                label.config(text="通信しています・・・", font=("源ノ角ゴシック", font, "bold"))
                root.after(500, connectc)
            check = tk.Button(root, command=okcloud, text="確定", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=10, height=1)
            check.place(relx=0.5, rely=0.64, relheight=0.08,
                        relwidth=0.2, anchor="c")

        def okdelete():
            global check
            guide1.place_forget()
            guide2.place_forget()
            guide3.place_forget()
            guide4.place_forget()
            guide5.place_forget()
            guide6.place_forget()
            if len(authjson["authlist"]) >= 2:
                guide7.place_forget()
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemequip.wav")
            pygame.mixer.music.play()
            label.config(text="今日の記録を削除します。\n確定してください。",
                         font=("源ノ角ゴシック", font, "bold"))

            def okdel():
                check.place_forget()
                datajson["logged members"] = []
                with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Data.json", "w", encoding="utf-8") as dataopen:
                    json.dump(datajson, dataopen)
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/die.wav")
                pygame.mixer.music.play()
                label.config(text="今日の記録を削除しました。\nカードを離してください。",
                             font=("源ノ角ゴシック", font, "bold"))
            check = tk.Button(root, command=okdel, text="確定", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=10, height=1)
            check.place(relx=0.5, rely=0.64, relheight=0.08,
                        relwidth=0.2, anchor="c")

        def okauth():
            global bgcolor, auth
            guide1.place_forget()
            guide2.place_forget()
            guide3.place_forget()
            guide4.place_forget()
            guide5.place_forget()
            guide6.place_forget()
            if len(authjson["authlist"]) >= 2:
                guide7.place_forget()
            if auth == True:
                auth = False
                bgcolor = "#e2e7fb"
                root.configure(bg=bgcolor)
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemequip.wav")
                pygame.mixer.music.play()
                label.config(text="管理者モードがオフになりました。\nカードを離してください。",
                             font=("源ノ角ゴシック", font, "bold"), bg=bgcolor)
            else:
                auth = True
                bgcolor = "#efe3fb"
                root.configure(bg=bgcolor)
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemequip.wav")
                pygame.mixer.music.play()
                label.config(text="管理者モードがオンになりました。\nカードを離してください。",
                             font=("源ノ角ゴシック", font, "bold"), bg=bgcolor)

        def okauthpop():
            global check
            guide1.place_forget()
            guide2.place_forget()
            guide3.place_forget()
            guide4.place_forget()
            guide5.place_forget()
            guide6.place_forget()
            guide7.place_forget()
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemequip.wav")
            pygame.mixer.music.play()
            label.config(text="このカードの管理者権限を解除します。\n確定してください。",
                         font=("源ノ角ゴシック", font, "bold"))

            def okokauthpop():
                check.place_forget()
                authjson["authlist"].remove(str(tag))
                with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/AuthList.json", "w", encoding="utf-8") as authopen:
                    json.dump(authjson, authopen)
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/die.wav")
                pygame.mixer.music.play()
                label.config(text="このカードの権限を解除しました。\nカードを離してください。",
                             font=("源ノ角ゴシック", font, "bold"), bg=bgcolor)
            check = tk.Button(root, command=okokauthpop, text="確定", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=10, height=1)
            check.place(relx=0.5, rely=0.64, relheight=0.08,
                        relwidth=0.2, anchor="c")

        def okconcheck():
            guide1.place_forget()
            guide2.place_forget()
            guide3.place_forget()
            guide4.place_forget()
            guide5.place_forget()
            guide6.place_forget()
            guide7.place_forget()

            def checkconnect():
                try:
                    datajson["today"] = today
                    url = "https://tgtenmon-account.an.r.appspot.com/getdata"
                    requests.post(url)
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(
                        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/Windows Proximity Notification.wav")
                    pygame.mixer.music.play()
                    label.config(text="通信に成功しました。\nインターネット環境は正常です。\nカードを離してください。", font=(
                        "源ノ角ゴシック", font, "bold"))
                except requests.exceptions.ConnectionError:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(
                        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                    pygame.mixer.music.play()
                    label.config(text="インターネットに\n接続されていません。\nカードを離してください。",
                                 font=("源ノ角ゴシック", font, "bold"))
                except:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(
                        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                    pygame.mixer.music.play()
                    label.config(text="通信に失敗しました。\nカードを離してください。",
                                 font=("源ノ角ゴシック", font, "bold"))
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/Windows Proximity Connection.wav")
            pygame.mixer.music.play(-1)
            label.config(text="通信しています・・・", font=("源ノ角ゴシック", font, "bold"))
            root.after(500, checkconnect)

        def oksync():
            global check
            guide1.place_forget()
            guide2.place_forget()
            guide3.place_forget()
            guide4.place_forget()
            guide5.place_forget()
            guide6.place_forget()
            guide7.place_forget()
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemequip.wav")
            pygame.mixer.music.play()
            label.config(text="クラウドの記録を読み込み、\nシステムの記録に上書きします。\n確定してください。",
                         font=("源ノ角ゴシック", font, "bold"))

            def okoksync():
                def connect():
                    try:
                        datajson["today"] = today
                        url = "https://tgtenmon-account.an.r.appspot.com/getdata"
                        headers = {
                            "today": today
                        }
                        data = requests.post(url, headers=headers)
                        if data.text != "Failed":
                            pygame.mixer.music.stop()
                            pygame.mixer.music.load(
                                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/Windows Proximity Notification.wav")
                            pygame.mixer.music.play()
                            data = ast.literal_eval(data.text)
                            datajson["logged members"] = data
                            with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Data.json", "w", encoding="utf-8") as dataopen:
                                json.dump(datajson, dataopen)
                            label.config(text="記録を上書きしました。\nカードを離してください。",
                                     font=("源ノ角ゴシック", font, "bold"))
                        else:
                            pygame.mixer.music.stop()
                            pygame.mixer.music.load(
                                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                            pygame.mixer.music.play()
                            label.config(text="データがありません。\nカードを離してください。",
                                     font=("源ノ角ゴシック", font, "bold"))
                        check.place_forget()
                    except requests.exceptions.ConnectionError:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(
                            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                        pygame.mixer.music.play()
                        label.config(text="インターネットに\n接続されていません。\nカードを離してください。",
                                     font=("源ノ角ゴシック", font, "bold"))
                        label.pack()
                    except:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(
                            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                        pygame.mixer.music.play()
                        label.config(text="通信に失敗しました。\nカードを離してください。",
                                     font=("源ノ角ゴシック", font, "bold"))
                check.place_forget()
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/Windows Proximity Connection.wav")
                pygame.mixer.music.play(-1)
                label.config(text="通信しています・・・", font=("源ノ角ゴシック", font, "bold"))
                root.after(500, connect)

            check = tk.Button(root, command=okoksync, text="確定", font=(
                "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=10, height=1)
            check.place(relx=0.5, rely=0.73, relheight=0.08,
                        relwidth=0.2, anchor="c")

        def okguide6():
            global txt
            guide1.place_forget()
            guide2.place_forget()
            guide3.place_forget()
            guide4.place_forget()
            guide5.place_forget()
            guide6.place_forget()
            guide7.place_forget()
            pygame.mixer.music.load(
                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemequip.wav")
            pygame.mixer.music.play()
            label.config(text="操作する部員のIDを入力してください。",
                         font=("源ノ角ゴシック", font, "bold"))
            txt = tk.Entry(width=50, justify="center",
                           background=bgcolor, relief="flat", foreground="#616161", font=("源ノ角ゴシック", font, "bold"))
            txt.focus()
            txt.pack(pady=8)

            def okguide6_connect(event):
                root.unbind("<Return>")
                txt.pack_forget()
                root.focus()
                IDs = str(txt.get()).replace("Type2Tag 'NXP NTAG215' ID=", "")
                on_connect(IDs)
            root.bind('<Return>', okguide6_connect)

        guide1 = tk.Button(root, command=oksync, text="クラウド読込み", font=(
            "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
        guide2 = tk.Button(root, command=oksend, text="クラウド上書き", font=(
            "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
        guide3 = tk.Button(root, command=okdelete, text="記録削除", font=(
            "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
        guide4 = tk.Button(root, command=okconcheck, text="接続確認", font=(
            "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
        guide5 = tk.Button(root, command=okauth, text="モード切り替え", font=(
            "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
        guide7 = tk.Button(root, command=okauthpop, text="管理者権限解除", font=(
            "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
        guide6 = tk.Button(root, command=okguide6, text="手動設定", font=(
            "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
        if boolexit == False:
            if len(authjson["authlist"]) >= 2:
                guide7.place(relx=0.5, rely=0.91, relheight=0.08,
                             relwidth=0.2, anchor="c")
            guide1.place(relx=0.25, rely=0.65, relheight=0.08,
                         relwidth=0.2, anchor="c")
            guide2.place(relx=0.5, rely=0.65, relheight=0.08,
                         relwidth=0.2, anchor="c")
            guide3.place(relx=0.75, rely=0.65, relheight=0.08,
                         relwidth=0.2, anchor="c")
            guide4.place(relx=0.25, rely=0.78, relheight=0.08,
                         relwidth=0.2, anchor="c")
            guide5.place(relx=0.5, rely=0.78, relheight=0.08,
                         relwidth=0.2, anchor="c")
            guide6.place(relx=0.75, rely=0.78, relheight=0.08,
                         relwidth=0.2, anchor="c")

    elif str(tag) == "0418937A136F80":
        label.config(text="ようこそ、高アンナ先生。\n参加の記録はされません。",
                     font=("源ノ角ゴシック", font, "bold"))

    else:
        if tag == "Error":
            label.config(text="カードが正確に読み取れませんでした。\nもう一度かざしてください。",
                     font=("源ノ角ゴシック", font, "bold"))
        else:
            label.config(text="未登録のカードです。",
                    font=("源ノ角ゴシック", font, "bold"))

            def okreg():
                global txt
                wantreg.place_forget()
                wantauthreg.place_forget()
                wantcopy.place_forget()
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/205 OK 'Ssuka.mp3")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    continue
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/06 Your Name, Please.mp3")
                pygame.mixer.music.play(-1)
                label.config(text="学年-クラス(番号)名前を\n入力してください。\n（例：1-A(01)学院太郎）",
                            font=("源ノ角ゴシック", font, "bold"))
                txt = tk.Entry(width=50, justify="center",
                            background=bgcolor, relief="flat", foreground="#616161", font=("源ノ角ゴシック", font, "bold"))
                txt.focus()
                txt.pack(pady=8)

                def okinfo(event):
                    root.unbind("<Return>")
                    txt.pack_forget()
                    root.focus()
                    name = str(txt.get())
                    if name[:1].isnumeric() and (name[1:2] == "-") and (name[3:4] == "(") and name[4:6].isnumeric() and (name[6:7] == ")") and (len(name) > 7):
                        def bgm():
                            pygame.mixer.music.load(
                                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/55 You Defeated the Boss!.mp3")
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                continue
                            pygame.mixer.music.load(
                                r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/46 You Gained a Level!.mp3")
                            pygame.mixer.music.play(1)
                            try:
                                url = "https://tgtenmon-account.an.r.appspot.com/getdata"
                                requests.post(url)
                                pointsdata = get("Points")
                                pointsdata[name] = "{'Points': 0, 'Attendance': 0, 'Percentage': 0.0, 'Addition': 0, 'Registered': False}"
                                insert("Points", pointsdata)
                                memberjson[str(tag)] = name
                                with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Members.json", "w", encoding="utf-8") as memberopen:
                                    json.dump(memberjson, memberopen)
                                label.config(text="IDを登録しました。\nカードを離してください。",
                                            font=("源ノ角ゴシック", font, "bold"))
                            except:
                                pygame.mixer.music.load(
                                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                                pygame.mixer.music.play()
                                label.config(text="インターネットに接続されていないため、\n処理ができませんでした。\nカードを離してください。",
                                            font=("源ノ角ゴシック", font, "bold"))

                            def secret():
                                while pygame.mixer.music.get_busy():
                                    continue
                                pygame.mixer.music.load(
                                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/Earthbound - Eight Melodies Orchestra Remix (Plasma3Music).mp3")
                                pygame.mixer.music.play(1)
                            root.after(300, secret)
                        label.config(text="登録しています・・・\nWELCOME!!!",
                                    font=("源ノ角ゴシック", font, "bold"))
                        root.after(1, bgm)
                    else:
                        pygame.mixer.music.load(
                            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/error.wav")
                        pygame.mixer.music.play()
                        label.config(text="表記が正しくありません。\nカードを離してください。",
                                    font=("源ノ角ゴシック", font, "bold"))
                root.bind('<Return>', okinfo)

            def okauthreg():
                global check
                wantreg.place_forget()
                wantauthreg.place_forget()
                wantcopy.place_forget()
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemequip.wav")
                pygame.mixer.music.play()
                label.config(text="このカードを管理者用カードとして\n登録します。確定してください。",
                            font=("源ノ角ゴシック", font, "bold"))

                def okokauthreg():
                    check.place_forget()
                    authjson["authlist"].append(str(tag))
                    with open(r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/AuthList.json", "w", encoding="utf-8") as authopen:
                        json.dump(authjson, authopen)
                    pygame.mixer.music.load(
                        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/187 Spell Learned.mp3")
                    pygame.mixer.music.play()
                    label.config(text="このカードを登録しました。\nカードを離してください。",
                                font=("源ノ角ゴシック", font, "bold"), bg=bgcolor)
                check = tk.Button(root, command=okokauthreg, text="確定", font=(
                    "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=10, height=1)
                check.place(relx=0.5, rely=0.64, relheight=0.08,
                            relwidth=0.2, anchor="c")

            def okcopy():
                wantreg.place_forget()
                wantauthreg.place_forget()
                wantcopy.place_forget()
                root.clipboard_append(str(tag))
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/itemused.wav")
                pygame.mixer.music.play()
                label.config(text="このカードのIDをコピーしました。\nカードを離してください。",
                            font=("源ノ角ゴシック", font, "bold"), bg=bgcolor)

            if auth == True:
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/reflectun.wav")
                pygame.mixer.music.play()
                wantreg = tk.Button(root, command=okreg, text="部員登録", font=(
                    "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
                wantauthreg = tk.Button(root, command=okauthreg, text="管理者登録", font=(
                    "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
                wantcopy = tk.Button(root, command=okcopy, text="IDをコピー", font=(
                    "源ノ角ゴシック", buttonfont, "bold"), bg=bgcolor, bd=5, relief="solid", justify="center", width=13, height=1)
                wantreg.place(relx=0.5, rely=0.55, relheight=0.08,
                            relwidth=0.2, anchor="c")
                wantauthreg.place(relx=0.5, rely=0.65,
                                relheight=0.08, relwidth=0.2, anchor="c")
                wantcopy.place(relx=0.5, rely=0.75, relheight=0.08,
                            relwidth=0.2, anchor="c")
            else:
                pygame.mixer.music.load(
                    r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/unknown.wav")
                pygame.mixer.music.play()
    return True


def hideall():
    try:
        txt.pack_forget()
    except:
        pass
    try:
        guide1.place_forget()
        guide2.place_forget()
        guide3.place_forget()
        guide4.place_forget()
        guide5.place_forget()
        guide6.place_forget()
        guide7.place_forget()
    except:
        pass
    try:
        check.place_forget()
    except:
        pass
    try:
        ident.pack_forget()
    except:
        pass
    try:
        info1.place_forget()
    except:
        pass
    try:
        info2.place_forget()
    except:
        pass
    try:
        info3.place_forget()
    except:
        pass
    try:
        info4.place_forget()
    except:
        pass
    try:
        wantreg.place_forget()
    except:
        pass
    try:
        wantauthreg.place_forget()
    except:
        pass
    try:
        wantcopy.place_forget()
    except:
        pass


def on_release(tag):
    global memberjson, datajson, authjson
    memberopen = open(
        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Members.json", "r", encoding="utf_8")
    memberjson = json.load(memberopen)
    memberopen.close()
    dataopen = open(
        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Data.json", "r", encoding="utf_8")
    datajson = json.load(dataopen)
    dataopen.close()
    authopen = open(
        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/AuthList.json", "r", encoding="utf_8")
    authjson = json.load(authopen)
    authopen.close()
    time.sleep(0.5)
    pygame.mixer.music.load(
        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/curshoriz.wav")
    pygame.mixer.music.play()
    root.unbind("<Key>")
    root.unbind("<Return>")
    hideall()
    root.focus()
    label.config(text="IDカードをカードリーダーに\nかざしてください。",
                 font=("源ノ角ゴシック", font, "bold"))
    return tag


def refresh():
    while True:
        global memberjson, datajson, authjson
        memberopen = open(
            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Members.json", "r", encoding="utf_8")
        memberjson = json.load(memberopen)
        memberopen.close()
        dataopen = open(
            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/Data.json", "r", encoding="utf_8")
        datajson = json.load(dataopen)
        dataopen.close()
        authopen = open(
            r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Database/AuthList.json", "r", encoding="utf_8")
        authjson = json.load(authopen)
        authopen.close()
        def fullscreen(event):
            global fullscreen_bool
            fullscreen_bool = (not fullscreen_bool)
            if fullscreen_bool:
                root.attributes('-fullscreen', True)
            else:
                root.attributes('-fullscreen', False)
        root.bind("<F10>", fullscreen)
        try:
            nfc.ContactlessFrontend('usb')
            label.config(text="IDカードをカードリーダーに\nかざしてください。",
                         font=("源ノ角ゴシック", font, "bold"), bg=bgcolor)
            rdwr_options = {
                'on-startup': on_startup,
                'on-connect': on_connect,
                'on-release': on_release,
                'beep-on-connect': False,
            }
            with nfc.ContactlessFrontend('usb') as clf:
                tag = clf.connect(rdwr=rdwr_options)
        except:
            hideall()
            label.config(text="カードリーダーが\n接続されていません。",
                         font=("源ノ角ゴシック", font, "bold"))
            pass


def okquit():
    pygame.mixer.music.load(
        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/SoundEffects/codecover.wav")
    pygame.mixer.music.play()
    root.destroy()
    while pygame.mixer.music.get_busy():
        continue
    os._exit(status=0)


def main():
    global label, root, exitl, fullscreen_bool
    root = tk.Tk()
    root.title('SkyRadia参加記録システム')
    root.geometry("1920x1080")
    root.attributes('-fullscreen', True)
    fullscreen_bool = True
    root.config(cursor="none")
    root.protocol("WM_DELETE_WINDOW", okquit)
    root.configure(bg=bgcolor)
    global font, buttonfont
    font = int(root.winfo_screenwidth() / 35)
    buttonfont = int(root.winfo_screenwidth() / 70)
    label = tk.Label(root, text="IDカードをカードリーダーに\nかざしてください。",
                     font=("源ノ角ゴシック", font, "bold"), bg=bgcolor)
    background = Image.open(
        r"/home/pi/Documents/作譜作品/SkyRadia記録システム/Resources/Images/logo.png")
    width = int(root.winfo_screenwidth())
    height = int(root.winfo_screenwidth() / 4.987405)
    background = background.resize((width, height))
    background = ImageTk.PhotoImage(background)
    global bg
    bg = tk.Label(root, image=background)
    bg.pack(fill="x")
    label.pack()
    exitl = tk.Button(root, command=okquit, text="終了", font=("源ノ角ゴシック", buttonfont, "bold"),
                      bg="#e2e7fb", bd=5, relief="solid", justify="center", width=5, height=1)
    exitl.place(relx=0.99, rely=0.06, relheight=0.08,
                relwidth=0.09, anchor="e")
    Thread(target=refresh).start()
    root.mainloop()


if __name__ == "__main__":
    main()
