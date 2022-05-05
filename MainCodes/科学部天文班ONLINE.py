import ast, os, random, re, sys, traceback, math, ephem

from datetime import datetime, timedelta, timezone
from math import degrees, remainder
from flask import Flask, abort, request, Response
from google.cloud import datastore, scheduler_v1
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (AudioMessage, BeaconEvent, BoxComponent,
                            BubbleContainer, ButtonComponent, ButtonsTemplate,
                            CameraAction, CameraRollAction, CarouselColumn,
                            CarouselTemplate, ConfirmTemplate,
                            DatetimePickerAction, FileMessage, FlexSendMessage,
                            FollowEvent, IconComponent, ImageCarouselColumn,
                            ImageCarouselTemplate, ImageComponent,
                            ImageMessage, ImageSendMessage, JoinEvent,
                            LeaveEvent, LocationAction, LocationMessage,
                            LocationSendMessage, MemberJoinedEvent,
                            MemberLeftEvent, MessageAction, MessageEvent,
                            PostbackAction, PostbackEvent, QuickReply,
                            QuickReplyButton, SeparatorComponent, SourceGroup,
                            SourceRoom, SourceUser, StickerMessage,
                            StickerSendMessage, TemplateSendMessage,
                            TextComponent, TextMessage, TextSendMessage,
                            UnfollowEvent, URIAction, VideoMessage)
from linebot.models.flex_message import FillerComponent, SpanComponent

app = Flask(__name__)
linebot_token = os.environ["linebot_token"]
linebot_secret = os.environ["linebot_secret"]
line_bot_api = LineBotApi(linebot_token)
handler = WebhookHandler(linebot_secret)


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


def Find(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]


def listsort(tolist, fromlist):
    numberdict = dict()
    count = 0
    for i in range(len(fromlist)):
        numberdict[fromlist[i]] = str(count) + fromlist[i]
        count += 1
    makinglist = list()
    for i in range(len(tolist)):
        makinglist.append(numberdict[tolist[i]])
    makinglist.sort()
    sortedlist = list()
    for i in range(len(makinglist)):
        sortedlist.append(makinglist[i][1:])
    return sortedlist


def timespan(one, two, three, four, spanmoonage):
    if spanmoonage == "0":
        return "観測不可"
    if three >= one:
        if three >= two:
            return "観測不可"
        elif two >= four:
            return [three, four]
        elif four >= two:
            return [three, two]
    elif one >= three:
        if one >= four:
            return "観測不可"
        elif four >= two:
            return [one, two]
        elif two >= four:
            return [one, four]
        else:
            return "観測不可"
    else:
        return "観測不可"


def planet_timespan(one, two, three, four):
    if three >= one:
        if three >= two:
            return "観測不可"
        elif two >= four:
            return [three, four]
        elif four >= two:
            return [three, two]
    elif one >= three:
        if one >= four:
            return "観測不可"
        elif four >= two:
            return [one, two]
        elif two >= four:
            return [one, four]
        else:
            return "観測不可"
    else:
        return "観測不可"


def is_now_can_observe(spanlist, nowdate):
    if spanlist[0] <= nowdate:
        if spanlist[1] >= nowdate:
            return True
        else:
            return False
    else:
        return False


tglocation = ephem.Observer()
tglocation.lat = '38.277290'
tglocation.lon = '140.942765'
sun = ephem.Sun()
mercury = ephem.Mercury()
venus = ephem.Venus()
moon = ephem.Moon()
mars = ephem.Mars()
jupiter = ephem.Jupiter()
saturn = ephem.Saturn()
uranus = ephem.Uranus()
neptune = ephem.Neptune()
pluto = ephem.Pluto()

authbook = get("AuthUsers")
idmappi = authbook["mappi"][0]


@app.route("/getdata", methods=["POST"])
def givedata():
    try:
        today = str(request.headers["today"])
        MembersList = str(get("MembersList")[today])
        return MembersList
    except:
        return "Failed"


@app.route("/seasonupdate", methods=["POST"])
def seasonupdate():
    try:
        pointsdata = get("Points")
        for i in pointsdata:
            try:
                pointsast = ast.literal_eval(pointsdata[i])
                pointsdata[i] = "{'Points': 0, 'Attendance': 0, 'Percentage': 0.0, 'Addition': 0, 'Registered': " + str(
                    pointsast["Registered"]) + "}"
            except:
                continue
        season = pointsdata["シーズン"]
        season = season.split("-")
        if season[1] == "I":
            season[1] = "II"
        elif season[1] == "II":
            season[1] = "III"
        elif season[1] == "III":
            season[1] = "IV"
        elif season[1] == "IV":
            season[1] = "I"
            season[0] = str(int(season[0]) + 1)
        season = season[0] + "-" + season[1]
        pointsdata["シーズン"] = season
        pointsdata["活動回数"] = 0
        upsert("Points", pointsdata)
        activstat = get("ActiveStatistics")
        if activstat["次のシーズンにリセットするか"]:
            for i in activstat:
                if i != "次のシーズンにリセットするか":
                    activstat[i] = 0
                else:
                    activstat[i] = False
            upsert("ActiveStatistics", activstat)
        else:
            update("ActiveStatistics", "次のシーズンにリセットするか", True)
        return Response(status=200)
    except:
        return Response(status=500)


@app.route("/updatelog", methods=["POST"])
def updatelog():
    flaskmessage = bytes.fromhex(request.headers["flaskmessage"])
    flaskmessage = str(flaskmessage.decode())
    flaskmessage = ast.literal_eval(flaskmessage)
    today = str(request.headers["today"])
    MembersList = str()
    member_id_list_dict = get("PointsID")
    member_id_list = list()
    for i in member_id_list_dict:
        member_id_list.append(i)
    authbook = get("AuthUsers")
    idlist = list()
    for i in authbook:
        temp = authbook[i][0]
        idlist.append(temp)
    member_id_list = member_id_list + idlist
    member_id_list = list(dict.fromkeys(member_id_list))

    try:
        MembersList = get("MembersList")[today]
    except:
        update("MembersList", today, '[]')
        pointsdata = get("Points")
        activc = int(pointsdata["活動回数"] + 1)
        client = datastore.Client()
        with client.transaction():
            key = client.key("Task", "Points")
            task = client.get(key)
            task["活動回数"] = activc
            client.put(task)
        for i in flaskmessage:
            userdat = ast.literal_eval(pointsdata[i])
            attendance = int(userdat["Attendance"] + 1)
            percentage = round((attendance / activc) * 100, 1)
            additionbonus = round((100 - round(percentage)) / 20)
            addition = 10 + additionbonus
            points = userdat["Points"] + addition
            newdat = {
                "Points": points,
                "Attendance": attendance,
                "Percentage": percentage,
                "Addition": addition,
                "Registered": bool(userdat["Registered"])
            }
            with client.transaction():
                key = client.key("Task", "Points")
                task = client.get(key)
                task[i] = str(newdat)
                client.put(task)

    membersnumber = str(len(flaskmessage))
    client = datastore.Client()
    with client.transaction():
        key = client.key("Task", "MembersList")
        task = client.get(key)
        task[str(today)] = str(flaskmessage)
        task["LatestDate"] = str(today)
        client.put(task)
    pointsdata = get("Points")
    activc = int(pointsdata["活動回数"])
    for i in pointsdata:
        try:
            pointsast = ast.literal_eval(pointsdata[i])
            pointsast["Percentage"] = round(
                (int(pointsast["Attendance"]) / activc) * 100, 1)
            pointsdata[i] = str(pointsast)
        except:
            continue
    upsert("Points", pointsdata)
    bubble = BubbleContainer(
        direction='ltr',
        hero=ImageComponent(
            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
            size='full',
            aspect_ratio='20:13',
            aspect_mode='cover',
        ),
        body=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(text="観測の参加部員情報が更新されました。",
                              size='xs', adjustMode='shrink-to-fit', wrap=True),
                TextComponent(text="計" + membersnumber + "名参加\n（ドームのみ）", weight='bold',
                              size='xl', adjustMode='shrink-to-fit', wrap=True),
                TextComponent(text="\n"),
                TextComponent(
                    text="「表示する」をタップして参加部員の個人名を表示", weight="bold", color="#979797", wrap=True)
            ],
        )
    )
    flex = FlexSendMessage(
        alt_text="本日の観測には" + membersnumber + "名が参加しました。　アプリを開いて確認してください。", contents=bubble, quick_reply=QuickReply(
            items=[
                QuickReplyButton(
                    action=MessageAction(label="表示する", text="最新の参加部員情報を表示"))
            ]
        )
    )
    line_bot_api.multicast(
        member_id_list, flex
    )
    return Response(status=200)


@app.route("/create_schedule", methods=["POST"])
def create():
    try:
        next_act_data = get("NextAct")
        is_created = next_act_data["is_schedule_created"]
        observe_or_not = next_act_data["Observe_or_not"]
        if not is_created:
            next_act_date = next_act_data["Date"]
            next_act_date = datetime(year=int(next_act_date[:4]), month=int(
                next_act_date[5:7]), day=int(next_act_date[8:10]))
            next_act_date = next_act_date.strftime("%-Y年%-m月%-d日")
            members = int(next_act_data["Participants"])
            assign = list()
            division = divmod(members, 7)
            mod = division[1]
            division = division[0]
            stage_minus = (7 * (division + 1)) - members
            if members == 17:
                groups = 1
                assign = [6, 6, 5]
            elif members < 9:
                groups = 1
                assign.append(members)
            elif (members <= 11) and (members >= 9):
                groups = 2
                assign.append(5)
                assign.append(members - 5)
            else:
                if (division + 1) >= stage_minus:
                    groups = division + 1
                    standard_number = 6
                else:
                    groups = division
                    standard_number = 7
                while members >= standard_number:
                    assign.append(standard_number)
                    members -= standard_number
                count = 0
                while members > 0:
                    assign[count] += 1
                    members -= 1
                    count += 1
            start = next_act_data["Start_time"]
            start_time = datetime.strptime(start, "%H:%M")
            start_minutes = int(start[:2]) * 60 + int(start[3:6])
            if observe_or_not == "あり(悪天決行)":
                end = next_act_data["End_time"]
            elif observe_or_not == "あり(悪天中止)":
                end = next_act_data["Observation_end_time"]
            end_minutes = int(end[:2]) * 60 + int(end[3:6])
            time_delta = end_minutes - start_minutes
            period_time = math.ceil(time_delta / groups)
            cis_time = start_time
            calculate_member_text = str()
            time_list = list()
            for i in range(groups):
                if i == 0:
                    cis_time = cis_time
                else:
                    cis_time = cis_time + timedelta(minutes=period_time)
                text = cis_time.strftime(
                    "%H:%M") + " ~ " + (cis_time + timedelta(minutes=period_time)).strftime("%H:%M")
                time_list.append(text)
            participant_info = ast.literal_eval(
                next_act_data["Participants_Info"])

            def grade(s):
                return s[0][0:1]

            def classes(s):
                return s[0][2:3]

            def number(s):
                return s[0][4:6]
            participant_info = sorted(participant_info, key=number)
            participant_info = sorted(participant_info, key=classes)
            participant_info = sorted(participant_info, key=grade)
            schedule = {}
            for j in range(groups):
                schedule[time_list[j]] = []
                for k in range(assign[j]):
                    taple = participant_info[k]
                    schedule[time_list[j]].append(taple)
                participant_info = participant_info[assign[j]:]
            time_list_number = str()
            for i in range(len(time_list)):
                if i == 0:
                    time_list_number = time_list[i] + \
                        "   " + str(assign[i]) + "人"
                else:
                    time_list_number = time_list_number + "\n" + \
                        time_list[i] + "   " + str(assign[i]) + "人"
            client = datastore.Client()
            with client.transaction():
                key = client.key("Task", "NextAct")
                task = client.get(key)
                task["Schedule"] = str(schedule)
                task["is_schedule_created"] = True
                task["Assign"] = str(assign)
                task["time_list_number"] = str(time_list_number)
                task["period_time"] = str(period_time)
                client.put(task)
            for l in list(schedule.values()):
                for m in list(l):
                    line_name = m[0][7:]
                    line_id = m[1]
                    index_number = list(schedule.values()).index(l)
                    scheduled_time = list(schedule.keys())[index_number]
                    update(line_id, "schedule", scheduled_time)
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text=line_name + "さんの活動時間が確定しました。",
                                              size='xs', adjustMode='shrink-to-fit', wrap=True),
                                TextComponent(text=scheduled_time, weight='bold',
                                              size='xxl', wrap=True, adjustMode='shrink-to-fit'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="日時：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=next_act_date, flex=3, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="6px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="時間：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=scheduled_time + "(" + str(period_time) + "分間)", flex=3, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="6px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="時間割：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=time_list_number, flex=3, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="6px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="合計人数：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=str(members) + "人", flex=1, align="center", wrap=True)
                                    ]
                                ),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="観測活動時間が確定しました。", contents=bubble
                    )
                    line_bot_api.push_message(
                        line_id, flex
                    )

            authbook = get("AuthUsers")
            idlist = list()
            for i in authbook:
                temp = authbook[i][0]
                if i != "mappi":
                    idlist.append(temp)
            bubble = BubbleContainer(
                direction='ltr',
                hero=ImageComponent(
                    url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                    size='full',
                    aspect_ratio='20:13',
                    aspect_mode='cover',
                ),
                body=BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(text="顧問・部長・副部長向け連絡",
                                      size='xs', adjustMode='shrink-to-fit', wrap=True),
                        TextComponent(text="活動時間・人数が確定しました。",
                                      size='xs', adjustMode='shrink-to-fit', wrap=True),
                        TextComponent(text=next_act_date, weight='bold',
                                      size='xxl', wrap=True, adjustMode='shrink-to-fit'),
                        TextComponent(text="参加する部員の個人名を、次回活動日確認画面から確認できます。",
                                      size='xs', adjustMode='shrink-to-fit', wrap=True),
                        BoxComponent(
                            layout="vertical",
                            contents=[
                                FillerComponent()
                            ],
                            height="10px"
                        ),
                        TextComponent(
                            text=time_list_number, wrap=True)
                    ],
                )
            )
            flex = FlexSendMessage(
                alt_text="活動時間・人数が確定しました。", contents=bubble
            )
            line_bot_api.multicast(
                idlist, flex
            )
            client = scheduler_v1.CloudSchedulerClient()
            project_name = get("DevMode")["project_name"]
            try:
                job = client.delete_job(
                    name='projects/' + project_name + '/locations/asia-northeast1/jobs/AutoCalculate')
            except:
                pass
        return Response(status=200)
    except:
        return Response(status=500)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text

    def reset_user_data():
        userdata = get(event.source.user_id)
        reset_dict = {
            "action_type": "None",
            "schedule": userdata["schedule"],
            "line_user_name": line_bot_api.get_profile(event.source.user_id).display_name
        }
        upsert(event.source.user_id, reset_dict)

    authbook = get("AuthUsers")
    idmappi = authbook["mappi"][0]
    idbucho = authbook["bucho"][0]
    member_id_list_dict = get("PointsID")
    member_id_list = list()
    for i in member_id_list_dict:
        member_id_list.append(i)
    idlist = list()
    for i in authbook:
        temp = authbook[i][0]
        idlist.append(temp)
    member_id_list = member_id_list + idlist
    member_id_list = list(dict.fromkeys(member_id_list))
    highidlist = list()
    for i in authbook:
        if (i == "bucho") or (i == "komon"):
            temp = authbook[i][0]
            highidlist.append(temp)

    def broadcast(flex):
        DevMode = get("DevMode")["DevMode"]
        if DevMode == False:
            line_bot_api.multicast(
                member_id_list, flex
            )
        else:
            line_bot_api.push_message(
                idmappi, TextSendMessage(
                    text="メンテナンス中のブロードキャストメッセージです。")
            )
            line_bot_api.push_message(
                idmappi, flex
            )
    try:
        DevMode = get("DevMode")["DevMode"]
        try:
            userdata = get(event.source.user_id)
            action_type = userdata["action_type"]
            update(event.source.user_id, "action_type", action_type)
        except:
            userdata = dict()
            userdata["action_type"] = "None"
            userdata["line_user_name"] = line_bot_api.get_profile(
                event.source.user_id).display_name
            userdata["schedule"] = str()
            username_dict = {
                "action_type": userdata["action_type"],
                "line_user_name": userdata["line_user_name"],
                "schedule": userdata["schedule"]
            }
            upsert(event.source.user_id, username_dict)

        try:
            member_real_name = get("PointsID")[event.source.user_id]
        except:
            if (event.source.user_id in member_id_list) or userdata["action_type"] == "registering_member":
                pass
            else:
                update(event.source.user_id,
                       "action_type", "registering_member")
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="部員登録", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="部員登録を行います。\n学年・クラス・番号・名前を入力してください。\n以下の表記（g-c(nn)name）で入力してください。\n1-A(01)学院太郎\n4-1(01)学院太郎\n4-⑩(01)学院太郎", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="部員登録は部員一人につき一アカウントのみとなります。必ず自分を登録するようにしてください。", size="xs", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="部員登録を行います。", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="やめる", text="やめる"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

        try:
            if userdata["action_type"] == "registering_member":
                if message == "やめる":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="部員登録を取り消しました。")
                    )
                    sys.exit()
                try:
                    search = ast.literal_eval(get("Points")[message])
                    if search["Registered"]:
                        reset_user_data()
                        bubble = BubbleContainer(
                            direction='ltr',
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(
                                        text="登録できません", weight="bold", size="xl", wrap=True),
                                    TextComponent("\n"),
                                    TextComponent(
                                        text="この部員は既に別のLINEアカウントで登録されているため、登録することはできません。", wrap=True),
                                    TextComponent(
                                        text="他のアカウントへの心当たりがない場合は、他人があなたで部員登録をしている可能性があります。三宅まで連絡してください。", size="sm", wrap=True
                                    )
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="登録できません", contents=bubble)
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                    else:
                        pointsda = ast.literal_eval(get("Points")[message])
                        pointsda["Registered"] = True
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", "Points")
                            task = client.get(key)
                            task[message] = str(pointsda)
                            client.put(task)
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", "PointsID")
                            task = client.get(key)
                            task[event.source.user_id] = message
                            client.put(task)
                        bubble = BubbleContainer(
                            direction='ltr',
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(
                                        text="登録しました", weight="bold", size="xl", wrap=True),
                                    TextComponent("\n"),
                                    TextComponent(
                                        text="このアカウントを{}さんとして登録しました。".format(message[7:]), wrap=True)
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="登録できません", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="AOP確認", text="AOP確認"))
                                ]
                            )
                        )
                        line_bot_api.reply_message(event.reply_token, flex)
                        reset_user_data()
                        sys.exit()
                except SystemExit:
                    sys.exit()
                except:
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="登録できません", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="{}は部員名簿にありません。\n表記、字を確認し、最初からやり直してください。".format(message), wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="登録できません", contents=bubble)
                    line_bot_api.reply_message(event.reply_token, flex)
                    reset_user_data()
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        global locflag, weather_location_name, weather_location_id, weather_month_of_date, weather_date_full_next_day, weather_date_full_previous_day, weather_date_full, weather_days_delta, dayflag

        dateinaccurate = datetime.today()
        datenow = datetime.now(timezone(timedelta(hours=9)))
        datetoday = dateinaccurate + timedelta(hours=9)
        datetodayFixed = datetoday.strftime("%-Y年%-m月%-d日")
        datetodayFixed = "今日(" + datetodayFixed + ")"
        datecnt2 = datetoday + timedelta(days=1)
        datecnt2Fixed = datecnt2.strftime("%-Y年%-m月%-d日")
        datecnt2Fixed = "明日(" + datecnt2Fixed + ")"
        datecnt3 = datetoday + timedelta(days=2)
        datecnt3Fixed = datecnt3.strftime("%-Y年%-m月%-d日")
        datecnt3Fixed = "あさって(" + datecnt3Fixed + ")"
        datecnt4 = datetoday + timedelta(days=3)
        datecnt4Fixed = datecnt4.strftime("%-Y年%-m月%-d日")
        datecnt4Fixed = "しあさって(" + datecnt4Fixed + ")"
        weather_quesion = None
        weather_date_full = None
        weather_days_delta = None
        weather_location_id = None
        weather_location_name = None
        locflag = False
        dayflag = False
        flag_weather_operation_quesion = False

        weather_month_of_date = None
        weather_date_full_next_day = None
        weather_date_full_previous_day = None

        if DevMode != False:
            try:
                if event.source.user_id != idmappi:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="現在メンテナンス中です。しばらくお待ちください。")
                    )
                    sys.exit()
            except SystemExit:
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="現在メンテナンス中です。しばらくお待ちください。")
                )
                sys.exit()

        if message == "参加希望・時間割確認":
            next_act_data = get("NextAct")
            is_schedule_created = next_act_data["is_schedule_created"]
            observe_or_not = next_act_data["Observe_or_not"]
            participants_info = ast.literal_eval(
                next_act_data["Participants_Info"])
            try:
                name = get("PointsID")[event.source.user_id]
            except:
                reset_user_data()
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="部員登録がなされていないため、参加を希望できません。")
                )
                sys.exit()

            if (not is_schedule_created) and (event.source.user_id in idlist):
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(text="顧問・部長・副部長向け",
                                          size='xs', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="参加希望を受け付け中", weight='bold',
                                          size='xl', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="現在部員の観測参加希望を受け付け中です。当日朝8時に時間割が確定し、この画面で確認できます。\n\n（顧問・部長および副部長は人数制限の対象となっておらず、参加希望ができません。）", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="参加希望を受け付けました。", contents=bubble
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif is_schedule_created and (event.source.user_id in idlist):
                next_act_date = next_act_data["Date"]
                next_act_date = datetime(year=int(next_act_date[:4]), month=int(
                    next_act_date[5:7]), day=int(next_act_date[8:10]))
                next_act_date = next_act_date.strftime("%-Y年%-m月%-d日")
                time_list_number = next_act_data["time_list_number"]
                schedule = ast.literal_eval(next_act_data["Schedule"])
                schedule_times = list(schedule.keys())
                schedule_members = list(schedule.values())
                schedule_times_str = str()
                for i in range(len(schedule_times)):
                    ns = str()
                    nns = str()
                    half = math.floor(len(schedule_members[i]) / 2)
                    for j in range(half):
                        ns = ns + "\n"
                    for j in range(half + 3):
                        nns = nns + "\n"
                    schedule_times_str = schedule_times_str + \
                        ns + schedule_times[i] + nns
                schedule_members_str = str()
                for i in range(len(schedule_members)):
                    for j in range(len(schedule_members[i])):
                        if i == 0:
                            schedule_members_str = schedule_members_str + \
                                schedule_members[i][j][0]
                        else:
                            schedule_members_str = schedule_members_str + \
                                "\n" + schedule_members[i][j][0]

                    schedule_members_str = schedule_members_str + "\n"
                schedule_times_str = schedule_times_str[:-2]
                schedule_members_str = schedule_members_str[:-1]

                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(text="顧問・部長・副部長向け",
                                          size='xs', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="時間割：",
                                          size='xs', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text=next_act_date, weight='bold',
                                          size='xxl', wrap=True, adjustMode='shrink-to-fit'),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text=schedule_times_str, weight="bold", color="#7D7D7D", flex=1, wrap=True, line_spacing="2px"),
                                    TextComponent(
                                        text=schedule_members_str, flex=1, align="center", wrap=True)
                                ]
                            ),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="時間割を表示しています。", contents=bubble
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif is_schedule_created and ((name, event.source.user_id) in participants_info):
                scheduled_time = userdata["schedule"]
                next_act_data = get("NextAct")
                period_time = next_act_data["period_time"]
                next_act_date = next_act_data["Date"]
                next_act_date = datetime(year=int(next_act_date[:4]), month=int(
                    next_act_date[5:7]), day=int(next_act_date[8:10]))
                next_act_date = next_act_date.strftime("%-Y年%-m月%-d日")
                participants = next_act_data["Participants"]
                assign = ast.literal_eval(next_act_data["Assign"])
                schedule = ast.literal_eval(next_act_data["Schedule"])
                time_list_number = next_act_data["time_list_number"]
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(text=name[7:] + "さんの観測時間：",
                                          size='xs', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text=scheduled_time, weight='bold',
                                          size='xxl', wrap=True, adjustMode='shrink-to-fit'),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="日時：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=next_act_date, flex=3, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="6px"
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="時間：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=scheduled_time + "(" + str(period_time) + "分間)", flex=3, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="6px"
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="時間割：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=time_list_number, flex=3, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="6px"
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="合計人数：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(participants) + "人", flex=1, align="center", wrap=True)
                                ]
                            ),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="活動時間を表示しています。", contents=bubble
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif (not is_schedule_created) and ((name, event.source.user_id) in participants_info):
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(text="参加希望を受け付けました。", weight='bold',
                                          size='xl', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="活動日当日朝8時に時間割が確定します。確定後、この画面で時間割が確認できるようになります。", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="参加希望を受け付けました。", contents=bubble
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif (not is_schedule_created) and ((observe_or_not == "あり(悪天決行)") or (observe_or_not == "あり(悪天中止)")):
                update(event.source.user_id, "action_type",
                       "participate_observation")
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(text="参加を希望しますか？", weight='bold',
                                          size='xl', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="この日の観測に参加しますか？", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="この日の観測に参加しますか？", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="参加する", text="参加する")),
                            QuickReplyButton(
                                action=MessageAction(label="参加しない", text="参加しない"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif is_schedule_created and ((name, event.source.user_id) not in participants_info):
                update(event.source.user_id, "action_type",
                       "participate_observation_late")
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(text="当日参加を希望しますか？", weight='bold',
                                          size='xl', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="すでに時間割が確定しているため、人数に空きがあるグループを探し、割り当てます。見つからなかった場合は観測に参加することができません。\n当日参加を希望しますか？", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="当日参加を希望しますか？", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="参加する", text="参加する")),
                            QuickReplyButton(
                                action=MessageAction(label="参加しない", text="参加しない"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

        try:
            if userdata["action_type"] == "participate_observation":
                if message == "参加する":
                    next_act_data = get("NextAct")
                    participants_info = ast.literal_eval(
                        next_act_data["Participants_Info"])
                    participants = next_act_data["Participants"]
                    try:
                        name = get("PointsID")[event.source.user_id]
                    except:
                        name = line_bot_api.get_profile(
                            event.source.user_id).display_name
                    participants_personal_info = (name, event.source.user_id)
                    participants_info.append(participants_personal_info)
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", "NextAct")
                        task = client.get(key)
                        task["Participants_Info"] = str(participants_info)
                        task["Participants"] = participants + 1
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text="参加希望を受け付けました", weight='bold',
                                              size='xl', adjustMode='shrink-to-fit', wrap=True),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="参加希望を受け付けました。活動日当日朝8時に時間割が確定します。", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="参加希望を受け付けました。", contents=bubble
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    reset_user_data()
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="参加希望を取り消しました。")
                    )
                    reset_user_data()
                    sys.exit()

            elif userdata["action_type"] == "participate_observation_late":
                if message == "参加する":
                    reset_user_data()
                    next_act_data = get("NextAct")
                    next_act_date = next_act_data["Date"]
                    next_act_date = datetime(year=int(next_act_date[:4]), month=int(
                        next_act_date[5:7]), day=int(next_act_date[8:10]))
                    next_act_date = next_act_date.strftime("%-Y年%-m月%-d日")
                    assign = ast.literal_eval(next_act_data["Assign"])
                    schedule = ast.literal_eval(next_act_data["Schedule"])
                    participants_info = ast.literal_eval(
                        next_act_data["Participants_Info"])
                    participants = next_act_data["Participants"]
                    period_time = next_act_data["period_time"]
                    found = False
                    time_list_number = next_act_data["time_list_number"]
                    for i in range(len(assign)):
                        if assign[i] <= 7:
                            found = True
                            scheduled_time = list(schedule.keys())[i]
                            index_number = i
                            assign[i] = assign[i] + 1
                            break
                    if found:
                        time_list_number = time_list_number.split("人")
                        time_list_number[index_number] = time_list_number[index_number][:-1] + str(
                            int(time_list_number[index_number][-1]) + 1)
                        time_list_number = "人".join(time_list_number)
                        participants = participants + 1
                        try:
                            name = get("PointsID")[event.source.user_id]
                        except:
                            name = line_bot_api.get_profile(
                                event.source.user_id).display_name
                        participants_info.append((name, event.source.user_id))
                        list(schedule.values())[index_number].append(
                            ((name, event.source.user_id)))
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", "NextAct")
                            task = client.get(key)
                            task["Assign"] = str(assign)
                            task["Participants"] = participants
                            task["Participants_Info"] = str(participants_info)
                            task["time_list_number"] = time_list_number
                            task["Schedule"] = str(schedule)
                            client.put(task)
                        update(event.source.user_id,
                               "schedule", scheduled_time)
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(text="割り当てられました。",
                                                  size='xs', adjustMode='shrink-to-fit', wrap=True),
                                    TextComponent(text=name[7:] + "さんの観測時間：",
                                                  size='xs', adjustMode='shrink-to-fit', wrap=True),
                                    TextComponent(text=scheduled_time, weight='bold',
                                                  size='xxl', wrap=True, adjustMode='shrink-to-fit'),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="日時：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=next_act_date, flex=3, align="center", wrap=True)
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="6px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="時間：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=scheduled_time + "(" + str(period_time) + "分間)", flex=3, align="center", wrap=True)
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="6px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="時間割：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=time_list_number, flex=3, align="center", wrap=True)
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="6px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="合計人数：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=str(participants) + "人", flex=1, align="center", wrap=True)
                                        ]
                                    ),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="割り当てられました。", contents=bubble
                        )
                        line_bot_api.reply_message(event.reply_token, flex)

                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(text=name[7:] + "さんが観測に参加しました。", weight='bold',
                                                  size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text=name[7:] + "さんが" + scheduled_time + "のグループに参加しました。", weight="bold", color="#7D7D7D", flex=1),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=name[7:] + "さんが" + scheduled_time + "のグループに参加しました。", contents=bubble
                        )
                        line_bot_api.multicast(
                            idlist, flex
                        )
                        sys.exit()

                    else:
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(text='割り当てられませんでした',
                                                  weight='bold', size='xl'),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(text='空きのあるグループが見つからなかったため、割り当てられませんでした。本日の観測に参加できません。',
                                                  size='sm', adjustMode='shrink-to-fit'),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="割り当てられませんでした", contents=bubble)
                        line_bot_api.reply_message(
                            event.reply_token,
                            flex
                        )
                        sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="参加希望を取り消しました。")
                    )
                    reset_user_data()
                    sys.exit()

        except SystemExit:
            sys.exit()
        except:
            errormessage = str(traceback.format_exc().replace(
                "Traceback (most recent call last)", "エラーメッセージ"))
            line_bot_api.push_message(
                idmappi, [
                    TextSendMessage(
                        text="ユーザーのエラーが発生しました。\n\n" + errormessage),
                ]
            )

        if message == "次回活動日":
            try:
                reset_user_data()
            except:
                pass

            def noactiv():
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(text='予定されていません',
                                          weight='bold', size='xl'),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(text='次回活動日は現在予定されていません。',
                                          size='sm', adjustMode='shrink-to-fit'),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="次回活動日は現在予定されていません。", contents=bubble)
                line_bot_api.reply_message(
                    event.reply_token,
                    flex
                )
                sys.exit()
            next_activity = get("NextAct")
            activdate = next_activity["Date"]
            if len(activdate) != 10:
                noactiv()
            activdate = datetime(year=int(activdate[:4]), month=int(
                activdate[5:7]), day=int(activdate[8:10]))
            activdatenexta = activdate + timedelta(days=1)
            activdatenexta = activdatenexta.strftime("%d")
            activstr = str(activdate.strftime("%a"))
            datetodaytemp = datetime.today() + timedelta(hours=9)
            if activstr == "Mon":
                activstr = "[月]"
            elif activstr == "Tue":
                activstr = "[火]"
            elif activstr == "Wed":
                activstr = "[水]"
            elif activstr == "Thu":
                activstr = "[木]"
            elif activstr == "Fri":
                activstr = "[金]"
            elif activstr == "Sat":
                activstr = "[土]"
            elif activstr == "Sun":
                activstr = "[日]"
            activsa = datetodaytemp - activdate
            activsa = int(activsa.days)
            activdate = str(int(activdate.strftime("%m"))) + \
                "月" + str(int(activdate.strftime("%d"))) + "日"
            activinfo = next_activity["Info"]
            if activsa == 0:
                activdate = "今日(" + activdate + activstr + ")"
            elif activsa == -1:
                activdate = "明日(" + activdate + activstr + ")"
            elif activsa == -2:
                activdate = "あさって(" + activdate + activstr + ")"
            elif activsa == -3:
                activdate = "しあさって(" + activdate + activstr + ")"
            else:
                activdate = activdate + activstr
            if len(activinfo) == 0:
                activinfo = "なし"

            activity_observe_or_not = next_activity["Observe_or_not"]
            activity_start_time = next_activity["Start_time"]
            activity_end_time = next_activity["End_time"]
            activity_time_span = next_activity["Span"]
            if activity_observe_or_not == "あり(悪天中止)":
                activity_observation_end_time = next_activity["Observation_end_time"]
                activity_observation_time_span = next_activity["Observation_span"]
            observable_planets = next_activity["Observable_planets"]

            global rsdate
            rsdate = datetoday.replace(
                hour=0, minute=0, second=0, microsecond=0)
            rsdate = rsdate + timedelta(days=abs(activsa))
            calculation_orbit_date = rsdate
            calculation_orbit_date = calculation_orbit_date - timedelta(days=1)
            calculation_orbit_date = calculation_orbit_date.replace(
                hour=15, minute=0, second=0, microsecond=0)
            tglocation.date = calculation_orbit_date
            moon.compute(tglocation)
            sun.compute(tglocation)
            moonrise = (tglocation.next_rising(moon)
                        ).datetime() + timedelta(hours=9)
            sunrise = (tglocation.next_rising(sun)
                       ).datetime() + timedelta(hours=9)
            sunset = (tglocation.next_setting(sun)
                      ).datetime() + timedelta(hours=9)
            suntransit = (tglocation.next_transit(
                sun)).datetime() + timedelta(hours=9)
            tglocation.date = calculation_orbit_date + timedelta(hours=17)
            moonage = round(tglocation.date -
                            ephem.previous_new_moon(tglocation.date), 1)
            cutmoonage = str(round(moonage))
            moonage = str(moonage)
            tglocation.date = calculation_orbit_date
            tglocation.date = tglocation.next_transit(sun)
            southsunalt = round(degrees(sun.alt), 1)
            tglocation.date = calculation_orbit_date
            tglocation.date = tglocation.next_rising(moon)
            moontransit = (tglocation.next_transit(
                moon)).datetime() + timedelta(hours=9)
            moonset = (tglocation.next_setting(moon)
                       ).datetime() + timedelta(hours=9)
            tglocation.date = tglocation.next_transit(moon)
            southmoonalt = round(degrees(moon.alt), 1)
            tglocation.date = calculation_orbit_date
            tglocation.date = tglocation.next_setting(sun)
            sunriseafterset = (tglocation.next_rising(
                sun)).datetime() + timedelta(hours=9)

            def timeFix(date):
                global rsdate
                deltaday = date - rsdate
                if date.second >= 30:
                    date = date + timedelta(minutes=1)
                kobun = date.strftime("%-H時%-M分")
                if deltaday.days == 1:
                    plus = "翌日,"
                    kobun = plus + kobun
                elif deltaday.days > 1:
                    plus = str(deltaday.days) + "日後,"
                    kobun = plus + kobun
                elif deltaday.days == -1:
                    plus = "前日,"
                    kobun = plus + kobun
                elif deltaday.days < -1:
                    plus = str(abs(deltaday.days)) + "日前,"
                    kobun = plus + kobun
                if kobun[-3:] == "時0分":
                    return kobun[:-2]
                else:
                    return kobun

            if timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage) == "観測不可":
                moon_visual = "観測不可"
            else:
                moon_visual = timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[
                                      0]) + "から\n" + timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[1]) + "まで観測可\n（天候による）"

            if cutmoonage == "0":
                moonage = moonage + "（新月）"
            elif cutmoonage == "1":
                moonage = moonage + "（繊月）"
            elif cutmoonage == "2":
                moonage = moonage + "（三日月）"
            elif cutmoonage == "7":
                moonage = moonage + "（上限）"
            elif cutmoonage == "9":
                moonage = moonage + "（十日夜月）"
            elif cutmoonage == "12":
                moonage = moonage + "（十三夜月）"
            elif cutmoonage == "13":
                moonage = moonage + "（小望月）"
            elif cutmoonage == "14":
                moonage = moonage + "（満月）"
            elif cutmoonage == "15":
                moonage = moonage + "（十六夜月）"
            elif cutmoonage == "16":
                moonage = moonage + "（立待月）"
            elif cutmoonage == "17":
                moonage = moonage + "（居待月）"
            elif cutmoonage == "18":
                moonage = moonage + "（寝待月）"
            elif cutmoonage == "19":
                moonage = moonage + "（更待月）"
            elif cutmoonage == "22":
                moonage = moonage + "（下弦）"
            elif cutmoonage == "25":
                moonage = moonage + "（有明月）"

            def normalreply():
                if activity_observe_or_not == "あり(悪天中止)":
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text="次回活動日：", size='sm'),
                                TextComponent(text=activdate, weight='bold',
                                              size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=activinfo, wrap=True),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="当日の予定", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=activity_observe_or_not, flex=1, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=activity_start_time, flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(text="活動終了時刻：",
                                              weight="bold", color="#7D7D7D"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="　観測有場合：", flex=1),
                                        TextComponent(
                                            text=activity_observation_end_time + "(" + activity_observation_time_span + "分間)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="　観測無場合：", flex=1),
                                        TextComponent(
                                            text=activity_end_time + "(" + activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="当日の情報", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="17時の月齢：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=moonage, flex=1, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="日没：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(text=timeFix(
                                            sunset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="月の出：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(text=timeFix(
                                            moonrise), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="月の入り：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=timeFix(moonset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                TextComponent(
                                    text="月の観測：", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=moon_visual, align="center", wrap=True),
                                TextComponent(
                                    text="観測可能天体：", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=observable_planets, align="center", wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="次回の活動日は" + activdate + "に予定されています。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="参加希望・時間割確認", text="参加希望・時間割確認"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif activity_observe_or_not == "なし":
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text="次回活動日：", size='sm'),
                                TextComponent(text=activdate, weight='bold',
                                              size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=activinfo, wrap=True),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="当日の予定", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=activity_observe_or_not, flex=1, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=activity_start_time, flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="活動終了時刻：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=activity_end_time + "(" + activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="次回の活動日は" + activdate + "に予定されています。", contents=bubble)
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text="次回活動日：", size='sm'),
                                TextComponent(text=activdate, weight='bold',
                                              size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=activinfo, wrap=True),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="当日の予定", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=activity_observe_or_not, flex=1, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=activity_start_time, flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="活動終了時刻：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=activity_end_time + "(" + activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="当日の情報", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="17時の月齢：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=moonage, flex=1, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="日没：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(text=timeFix(
                                            sunset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="月の出：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(text=timeFix(
                                            moonrise), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="月の入り：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=timeFix(moonset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                TextComponent(
                                    text="月の観測：", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=moon_visual, align="center", wrap=True),
                                TextComponent(
                                    text="観測可能天体：", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=observable_planets, align="center", wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="次回の活動日は" + activdate + "に予定されています。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="参加希望・時間割確認", text="参加希望・時間割確認"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

            if activsa <= 0:
                try:
                    if datenow > (get("WeatherData")["宮城県仙台市宮城野区date"] + timedelta(hours=2)):
                        try:
                            line_bot_api.push_message(
                                event.source.user_id, [
                                    TextSendMessage(text="最新の天気予報を取得しています・・・"),
                                ]
                            )
                        except:
                            pass
                        import requests
                        url = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/219001?apikey=" + str(os.environ["apikey"]) + \
                            "&language=ja-JP&details=true&metric=true"
                        weatherdata = requests.get(url)
                        connectionstatuscode = str(weatherdata.status_code)
                        if connectionstatuscode == "503":
                            normalreply()
                        weatherdata = weatherdata.json()
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", "WeatherData")
                            task = client.get(key)
                            task["宮城県仙台市宮城野区"] = str(weatherdata)
                            task["宮城県仙台市宮城野区date"] = datenow
                            client.put(task)

                    weather_datajson = ast.literal_eval(
                        get("WeatherData")["宮城県仙台市宮城野区"])

                    dataFixed = weather_datajson["DailyForecasts"][abs(
                        activsa)]
                    aboutemp = dataFixed["Temperature"]
                    hightemp = str(aboutemp["Maximum"]["Value"])
                    lowtemp = str(aboutemp["Minimum"]["Value"])
                    hightempfloat = float(hightemp)
                    lowtempfloat = float(lowtemp)
                    averagetemp = (hightempfloat + lowtempfloat) / 2
                    averagetempint = int(round(averagetemp, 1))
                    averagetempstr = str(round(averagetemp, 1))
                    aboutozonePollen = dataFixed["AirAndPollen"][0]
                    ozoneValue = str(aboutozonePollen["Value"])
                    ozoneValueint = int(ozoneValue)
                    aboutnightforecast = dataFixed["Night"]
                    nightphrase = str(aboutnightforecast["LongPhrase"])
                    nightcloudcover = str(aboutnightforecast["CloudCover"])
                    intnightcloud = int(nightcloudcover)
                    averagetempintyes = averagetempint
                    intnightcloudyes = intnightcloud
                    ozoneValueintyes = ozoneValueint
                    hoshizora = (averagetempintyes + 273) * \
                        pow((intnightcloudyes + 273), 2) * \
                        (ozoneValueintyes + 273)
                    hoshizora = (1 / hoshizora) * 60000000000
                    hoshizora = round(hoshizora, 1)
                    hoshizora = str(hoshizora)

                    if activity_observe_or_not == "あり(悪天中止)":
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(text="次回活動日：", size='sm'),
                                    TextComponent(text=activdate, weight='bold',
                                                  size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=activinfo, wrap=True),
                                    TextComponent(text="\n"),
                                    SeparatorComponent(),
                                    TextComponent(text="\n"),
                                    TextComponent(text="当日の予定", size="lg",
                                                  weight="bold", color="#4A4A4A"),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="5px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=activity_observe_or_not, flex=1, align="center", wrap=True)
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="5px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=activity_start_time, flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="5px"
                                    ),
                                    TextComponent(
                                        text="活動終了時刻：", weight="bold", color="#7D7D7D"),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="　観測有場合：", flex=1),
                                            TextComponent(
                                                text=activity_observation_end_time + "(" + activity_observation_time_span + "分間)", flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="　観測無場合：", flex=1),
                                            TextComponent(
                                                text=activity_end_time + "(" + activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    TextComponent(text="\n"),
                                    SeparatorComponent(),
                                    TextComponent(text="\n"),
                                    TextComponent(text="当日の情報", size="lg",
                                                  weight="bold", color="#4A4A4A"),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="17時の月齢：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=moonage, flex=1, align="center")
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="ほしぞら指数：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=hoshizora,
                                                          flex=1, align="center"),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="夜間の天気：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=nightphrase, flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="平均気温：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=averagetempstr + "℃", flex=1, align="center"),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="日没：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=timeFix(
                                                sunset), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="月の出：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=timeFix(
                                                moonrise), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="月の入り：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=timeFix(moonset), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    TextComponent(
                                        text="月の観測：", weight="bold", color="#7D7D7D", wrap=True),
                                    TextComponent(
                                        text=moon_visual, align="center", wrap=True),
                                    TextComponent(
                                        text="観測可能天体：", weight="bold", color="#7D7D7D", wrap=True),
                                    TextComponent(
                                        text=observable_planets, align="center", wrap=True),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="次回の活動日は" + activdate + "に予定されています。", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="参加希望・時間割確認", text="参加希望・時間割確認"))
                                ]
                            )
                        )
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                    elif activity_observe_or_not == "なし":
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(text="次回活動日：", size='sm'),
                                    TextComponent(text=activdate, weight='bold',
                                                  size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=activinfo, wrap=True),
                                    TextComponent(text="\n"),
                                    SeparatorComponent(),
                                    TextComponent(text="\n"),
                                    TextComponent(text="当日の予定", size="lg",
                                                  weight="bold", color="#4A4A4A"),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="5px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=activity_observe_or_not, flex=1, align="center", wrap=True)
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="5px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=activity_start_time, flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="5px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="活動終了時刻：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=activity_end_time + "(" + activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="次回の活動日は" + activdate + "に予定されています。", contents=bubble)
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                    else:
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(text="次回活動日：", size='sm'),
                                    TextComponent(text=activdate, weight='bold',
                                                  size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=activinfo, wrap=True),
                                    TextComponent(text="\n"),
                                    SeparatorComponent(),
                                    TextComponent(text="\n"),
                                    TextComponent(text="当日の予定", size="lg",
                                                  weight="bold", color="#4A4A4A"),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="5px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=activity_observe_or_not, flex=1, align="center", wrap=True)
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="5px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=activity_start_time, flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="5px"
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="活動終了時刻：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=activity_end_time + "(" + activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    TextComponent(text="\n"),
                                    SeparatorComponent(),
                                    TextComponent(text="\n"),
                                    TextComponent(text="当日の情報", size="lg",
                                                  weight="bold", color="#4A4A4A"),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="17時の月齢：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=moonage, flex=1, align="center")
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="ほしぞら指数：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=hoshizora,
                                                          flex=1, align="center"),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="夜間の天気：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=nightphrase, flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="平均気温：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=averagetempstr + "℃", flex=1, align="center"),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="日没：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=timeFix(
                                                sunset), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="月の出：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=timeFix(
                                                moonrise), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="月の入り：", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=timeFix(moonset), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    TextComponent(
                                        text="月の観測：", weight="bold", color="#7D7D7D", wrap=True),
                                    TextComponent(
                                        text=moon_visual, align="center", wrap=True),
                                    TextComponent(
                                        text="観測可能天体：", weight="bold", color="#7D7D7D", wrap=True),
                                    TextComponent(
                                        text=observable_planets, align="center", wrap=True),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="次回の活動日は" + activdate + "に予定されています。", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="参加希望・時間割確認", text="参加希望・時間割確認"))
                                ]
                            )
                        )
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                except SystemExit:
                    sys.exit()
                except:
                    normalreply()
            else:
                noactiv()
        elif message == "アセンブラ専用操作":
            try:
                reset_user_data()
            except:
                pass
            bubble = BubbleContainer(
                direction='ltr',
                body=BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(
                            text="操作を選択してください。", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="次回活動日登録", text="次回活動日登録"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="メッセージ関連", text="メッセージ関連"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="活動記録記入", text="活動記録記入"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="権限付与・解除・申請", text="権限付与・解除・申請"),
                        ),
                    ],
                )
            )
            flex = FlexSendMessage(
                alt_text="操作を選択してください。", contents=bubble)
            line_bot_api.reply_message(
                event.reply_token, flex)
            sys.exit()

        arraymessage = []
        arrayname = []
        arraydate = []
        if message == "メッセージ関連":
            try:
                reset_user_data()
            except:
                pass
            try:
                if event.source.user_id in idlist:
                    update(event.source.user_id,
                           "action_type", "broadcast_message")
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="メッセージ関連", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="配信権限が確認できました。操作を選択してください。", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="配信権限が確認できました。操作を選択してください。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="メッセージ配信", text="メッセージ配信")),
                                QuickReplyButton(
                                    action=MessageAction(label="既読確認", text="既読確認")),
                                QuickReplyButton(
                                    action=MessageAction(label="やめる", text="やめる"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="配信権限が確認できませんでした。これは権限付与者限定の機能です。")
                    )
                    sys.exit()
            except SystemExit:
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="配信権限が確認できませんでした。これは権限付与者限定の機能です。")
                )
                sys.exit()
        try:
            if userdata["action_type"] == "broadcast_message":
                if message == "メッセージ配信":
                    try:
                        broadcast_message_sender = ast.literal_eval(str(list(authbook.values())).replace(
                            "[", "").replace("]", "").replace(" ", ""))
                        broadcast_message_sender = broadcast_message_sender[broadcast_message_sender.index(
                            event.source.user_id) + 1]
                    except:
                        broadcast_message_sender = "匿名"
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["action_type"] = "direct_message_title"
                        task["broadcast_message_type"] = message
                        task["broadcast_message_sender"] = broadcast_message_sender
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="タイトルを入力", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="まず、タイトルを入力してください。", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="まず、タイトルを入力してください。", contents=bubble
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

                elif message == "既読確認":
                    reset_user_data()
                    message_read = ast.literal_eval(get("Notes")["Message_Read"])
                    read_members = str()
                    for i in range(len(message_read)):
                        if i == 0:
                            read_members = message_read[i]
                        else:
                            read_members = read_members + "\n" + message_read[i]
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="既読者一覧", weight="bold", size="xxl", wrap=True),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text=read_members, wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="既読者一覧を表示しています。", contents=bubble
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

                elif message == "やめる":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="メッセージ関連の操作を取り消しました。")
                    )
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="表記が正しくありません。メッセージ関連の操作を終了しました。")
                    )
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        try:
            if userdata["action_type"] == "direct_message_title":
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["action_type"] = "direct_message_message"
                    task["broadcast_message_title"] = message
                    client.put(task)
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="メッセージを入力", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="それでは、メッセージを入力してください。", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="それでは、メッセージを入力してください。", contents=bubble
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "direct_message_message":
                try:
                    broadcast_message_sender = ast.literal_eval(str(list(authbook.values())).replace(
                        "[", "").replace("]", "").replace(" ", ""))
                    broadcast_message_sender = broadcast_message_sender[broadcast_message_sender.index(
                        event.source.user_id) + 1]
                except:
                    broadcast_message_sender = "匿名"
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["action_type"] = "direct_message_check"
                    task["broadcast_message_message"] = message
                    task["broadcast_message_sender"] = broadcast_message_sender
                    client.put(task)
                broadcast_message_title = userdata["broadcast_message_title"]
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="確定しますか？", weight="bold", size="xxl", wrap=True),
                            TextComponent(
                                text="投稿者：" + broadcast_message_sender, size="xxs", color="#979797", flex=2),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="タイトル：", weight="bold", color="#7D7D7D", wrap=True),
                            TextComponent(
                                text=broadcast_message_title, weight="bold", size="xxl", wrap=True),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(
                                text="メッセージ：", weight="bold", color="#7D7D7D", wrap=True),
                            TextComponent(
                                text=message, wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="配信を確定しますか？", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="はい", text="はい")),
                            QuickReplyButton(
                                action=MessageAction(label="やめる", text="やめる"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "direct_message_check":
                if message == "はい":
                    update("Notes", "Message_Read", str("[]"))
                    broadcast_message_sender = userdata["broadcast_message_sender"]
                    broadcast_message_title = userdata["broadcast_message_title"]
                    notice = userdata["broadcast_message_message"]
                    urls = Find(notice)
                    urls = list(dict.fromkeys(urls))
                    urltitle = FillerComponent()
                    sendurl1 = FillerComponent()
                    sepa1 = FillerComponent()
                    sendurl2 = FillerComponent()
                    sepa2 = FillerComponent()
                    sendurl3 = FillerComponent()
                    sepa3 = FillerComponent()
                    sendurl4 = FillerComponent()
                    sepa4 = FillerComponent()
                    sendurl5 = FillerComponent()
                    if len(urls) >= 1:
                        for i in urls:
                            if i == urls[0]:
                                notice = notice.replace(i, "①" + i)
                                urltitle = TextComponent(
                                    text="\nハイパーリンクURL:", weight="bold", color="#7D7D7D", wrap=True)
                                sendurl1 = TextComponent(
                                    text="①" + i, color="#0043bf", wrap=True, action=URIAction(uri=i))
                            elif i == urls[1]:
                                notice = notice.replace(i, "②" + i)
                                sepa1 = BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                )
                                sendurl2 = TextComponent(
                                    text="②" + i, color="#0043bf", wrap=True, action=URIAction(uri=i))
                            elif i == urls[2]:
                                notice = notice.replace(i, "③" + i)
                                sepa2 = BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                )
                                sendurl3 = TextComponent(
                                    text="③" + i, color="#0043bf", wrap=True, action=URIAction(uri=i))
                            elif i == urls[3]:
                                notice = notice.replace(i, "④" + i)
                                sepa3 = BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                )
                                sendurl4 = TextComponent(
                                    text="④" + i, color="#0043bf", wrap=True, action=URIAction(uri=i))
                            elif i == urls[4]:
                                notice = notice.replace(i, "⑤" + i)
                                sepa4 = BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                )
                                sendurl5 = TextComponent(
                                    text="⑤" + i, color="#0043bf", wrap=True, action=URIAction(uri=i))
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E3%83%A1%E3%83%83%E3%82%BB%E3%83%BC%E3%82%B8%E9%85%8D%E4%BF%A1.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="メッセージ配信", weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                SeparatorComponent(),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="投稿者：" + broadcast_message_sender, size="xxs", color="#979797", flex=2),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="タイトル：", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=broadcast_message_title, weight="bold", size="xxl", wrap=True),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="メッセージ：", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=notice, wrap=True),
                                urltitle,
                                sendurl1,
                                sepa1,
                                sendurl2,
                                sepa2,
                                sendurl3,
                                sepa3,
                                sendurl4,
                                sepa4,
                                sendurl5
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=broadcast_message_sender + "がメッセージを配信しました。アプリを開いて確認してください。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label="既読する", data="既読する"))
                            ]
                        )
                    )
                    broadcast(flex)
                    reset_user_data()
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="メッセージ配信を取り消しました。")
                    )
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            errormessage = str(traceback.format_exc().replace(
                "Traceback (most recent call last)", "エラーメッセージ"))
            line_bot_api.push_message(
                idmappi, [
                    TextSendMessage(
                        text="ユーザーのエラーが発生しました。\n\n" + errormessage),
                ]
            )

        if message == "次回活動日登録":
            try:
                reset_user_data()
            except:
                pass
            try:
                if event.source.user_id in idlist:
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["action_type"] = "register_activity"
                        task["flag_activity_date_already"] = False
                        client.put(task)
                    Prex = 0
                    Prez = 0
                    Pretoday = datetime.today() + timedelta(hours=9)
                    Pretomo = Pretoday + timedelta(days=1)
                    tod = str(Pretoday)[:10]
                    tom = str(Pretomo)[:10]
                    tue = str()
                    fri = str()
                    while True:
                        Prex += 1
                        tue = Pretoday + timedelta(days=Prex)
                        if str(tue.strftime("%a")) == "Tue":
                            break
                    while True:
                        Prez += 1
                        fri = Pretoday + timedelta(days=Prez)
                        if str(fri.strftime("%a")) == "Fri":
                            break
                    tue = str(tue)[:10]
                    fri = str(fri)[:10]
                    items_list = [
                        QuickReplyButton(
                            action=DatetimePickerAction(label='日付を選択',
                                                        data='date_postback',
                                                        mode='date')),
                        QuickReplyButton(
                            action=MessageAction(label="やめる", text="やめる")),
                        QuickReplyButton(
                            action=MessageAction(label="次の火曜日", text=tue)),
                        QuickReplyButton(
                            action=MessageAction(label="次の金曜日", text=fri)),
                        QuickReplyButton(
                            action=MessageAction(label="今日", text=tod)),
                        QuickReplyButton(
                            action=MessageAction(label="明日", text=tom))
                    ]
                    scheduled_date = get("NextAct")["Date"]
                    try:
                        scheduled_date = datetime(year=int(scheduled_date[:4]), month=int(
                            scheduled_date[5:7]), day=int(scheduled_date[8:10]))
                        datetodaytemp = (datetime.today() +
                                         timedelta(hours=9)) - timedelta(days=1)
                        if scheduled_date >= datetodaytemp:
                            items_list.insert(2, QuickReplyButton(
                                action=MessageAction(label="予定を取り消す", text="予定を取り消す")))
                    except ValueError:
                        pass
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="次回活動日登録", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="登録権限が確認できました。次回活動日の日付を選択してください。", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="登録権限が確認できました。次回活動日の日付を選択してください。", contents=bubble, quick_reply=QuickReply(
                            items=items_list
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="登録権限が確認できませんでした。これは権限付与者限定の機能です。")
                    )
                    sys.exit()
            except SystemExit:
                sys.exit()
            except:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="登録権限が確認できませんでした。これは権限付与者限定の機能です。")
                )
                sys.exit()

        try:
            if userdata["action_type"] == "register_activity":
                if message == get("NextAct")["Date"]:
                    if message[:4].isnumeric() and (message[4:5] == "-") and message[5:7].isnumeric() and (message[7:8] == "-") and message[8:10].isnumeric() and (len(message) == 10):
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", event.source.user_id)
                            task = client.get(key)
                            task["flag_activity_date_already"] = True
                            task["activity_already_date"] = message
                            client.put(task)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="既にこの日として登録されていますが、続行しますか？", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="はい", text="はい")),
                                        QuickReplyButton(
                                            action=MessageAction(label="やめる", text="やめる"))
                                    ]
                                )
                            )
                        )
                        sys.exit()
                    elif message == "いいえ":
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="活動日登録を終了しました。")
                        )
                        sys.exit()
                    else:
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="表記が正しくありません。もう一度最初からやり直してください。活動日登録を終了します。")
                        )
                        sys.exit()
                if message == "予定を取り消す":
                    scheduled_date = get("NextAct")["Date"]
                    scheduled_date = datetime(year=int(scheduled_date[:4]), month=int(
                        scheduled_date[5:7]), day=int(scheduled_date[8:10]))
                    datetodaytemp = (datetime.today() +
                                     timedelta(hours=9)) - timedelta(days=1)
                    if scheduled_date < datetodaytemp:
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="予定が存在しませんので、取り消すことができません。")
                        )
                        sys.exit()
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["flag_cancelling_date"] = True
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="確定しますか？", weight="bold", size="xxl", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="予定を取り消しますか？", wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="予定を取り消しますか？", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="はい", text="はい")),
                                QuickReplyButton(
                                    action=MessageAction(label="やめる", text="やめる"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                try:
                    if userdata["flag_cancelling_date"]:
                        if message == "はい":
                            update(event.source.user_id,
                                   "flag_cancelling_date", False)
                            scheduled_date = get("NextAct")["Date"]
                            scheduled_date = datetime(year=int(scheduled_date[:4]), month=int(
                                scheduled_date[5:7]), day=int(scheduled_date[8:10]))
                            scheduled_date = scheduled_date.strftime(
                                "%-Y年%-m月%-d日")
                            client = datastore.Client()
                            with client.transaction():
                                key = client.key("Task", "NextAct")
                                task = client.get(key)
                                task["Date"] = "取り消されました。"
                                task["Info"] = "取り消されました。"
                                task["is_schedule_created"] = False
                                task["Participants_Info"] = "[]"
                                task["Schedule"] = str()
                                task["Participants"] = 0
                                task["Assign"] = "[]"
                                task["time_list_number"] = str()
                                task["period_time"] = str()
                                client.put(task)
                            try:
                                client = scheduler_v1.CloudSchedulerClient()
                                project_name = get("DevMode")["project_name"]
                                job = client.delete_job(
                                    name='projects/' + project_name + '/locations/asia-northeast1/jobs/AutoCalculate')
                            except:
                                pass
                            bubble = BubbleContainer(
                                direction='ltr',
                                hero=ImageComponent(
                                    url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                                    size='full',
                                    aspect_ratio='20:13',
                                    aspect_mode='cover',
                                ),
                                body=BoxComponent(
                                    layout='vertical',
                                    contents=[
                                        TextComponent(text='予定が取り消されました',
                                                      weight='bold', size='xl'),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="10px"
                                        ),
                                        TextComponent(text=scheduled_date + "の活動の予定が取り消されました。",
                                                      size='sm', wrap=True, adjustMode='shrink-to-fit'),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="活動の予定が取り消されました。　アプリを開いて確認してください。", contents=bubble)
                            broadcast(flex)
                            reset_user_data()
                            sys.exit()
                except KeyError:
                    pass

                if (message[:4].isnumeric() and (message[4:5] == "-") and message[5:7].isnumeric() and (message[7:8] == "-") and message[8:10].isnumeric() and (len(message) == 10)) or message == "はい":
                    try:
                        if userdata["flag_activity_date_already"]:
                            message = userdata["activity_already_date"]
                        elif not userdata["flag_activity_date_already"]:
                            if message == "はい":
                                reset_user_data()
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(
                                        text="表記が正しくありません。もう一度最初からやり直してください。活動日登録を終了します。")
                                )
                                sys.exit()
                    except SystemExit:
                        sys.exit()
                    except:
                        if message == "はい":
                            reset_user_data()
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(
                                    text="表記が正しくありません。もう一度最初からやり直してください。活動日登録を終了します。")
                            )
                            sys.exit()
                        else:
                            pass
                    datetodaytemp = datetime.today() + timedelta(hours=9)
                    try:
                        activdatec = datetime(year=int(message[:4]), month=int(
                            message[5:7]), day=int(message[8:10]))
                    except:
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="日付が正しくありません。もう一度最初からやり直してください。活動日登録を終了します。")
                        )
                        sys.exit()
                    activstrc = str(activdatec.strftime("%a"))
                    if activstrc == "Mon":
                        activstrc = "[月]"
                    elif activstrc == "Tue":
                        activstrc = "[火]"
                    elif activstrc == "Wed":
                        activstrc = "[水]"
                    elif activstrc == "Thu":
                        activstrc = "[木]"
                    elif activstrc == "Fri":
                        activstrc = "[金]"
                    elif activstrc == "Sat":
                        activstrc = "[土]"
                    elif activstrc == "Sun":
                        activstrc = "[日]"
                    activsac = datetodaytemp - activdatec
                    activsac = int(activsac.days)
                    activdatec = activdatec.strftime("%-Y年%-m月%-d日")
                    if activsac == 0:
                        activdatec = "今日(" + activdatec + activstrc + ")"
                    elif activsac == -1:
                        activdatec = "明日(" + activdatec + activstrc + ")"
                    elif activsac == -2:
                        activdatec = "あさって(" + activdatec + activstrc + ")"
                    elif activsac == -3:
                        activdatec = "しあさって(" + activdatec + activstrc + ")"
                    else:
                        activdatec = activdatec + activstrc
                    if activsac >= 1:
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="過去の日付は登録できません。活動日登録を終了します。")
                        )
                        sys.exit()
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["register_activity_date_full"] = str(activdatec)
                        task["register_activity_date"] = str(message)
                        task["action_type"] = "register_activity_about"
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="活動内容を入力", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="かしこまりました。\n" + activdatec + "ですね。\n次に、この日の活動の詳細を入力してください。", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="次に、この日の活動の詳細を入力してください。", contents=bubble
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    if userdata["flag_activity_date_already"]:
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", event.source.user_id)
                            task = client.get(key)
                            task["action_type"] = "None"
                            task["flag_activity_date_already"] = False
                            client.put(task)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="次回活動日登録を取り消しました。")
                        )
                        sys.exit()
                    elif message == "やめる":
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="次回活動日登録を取り消しました。")
                        )
                        sys.exit()
                    else:
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="表記が正しくありません。もう一度最初からやり直してください。活動日登録を終了します。")
                        )
                        sys.exit()

            elif userdata["action_type"] == "register_activity_about":
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["register_activity_about"] = str(message)
                    task["action_type"] = "register_activity_observe_or_not"
                    client.put(task)
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="観測を行いますか？", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="この日に観測を行う予定はありますか？", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="この日に観測を行う予定はありますか？", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="あり(悪天決行)", text="あり(悪天決行)")),
                            QuickReplyButton(
                                action=MessageAction(label="あり(悪天中止)", text="あり(悪天中止)")),
                            QuickReplyButton(
                                action=MessageAction(label="なし", text="なし"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "register_activity_observe_or_not":
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["register_activity_observe_or_not"] = str(message)
                    task["action_type"] = "register_activity_start_time"
                    client.put(task)
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="活動開始予定時刻を選択", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="この日の活動開始予定時刻を選択してください。", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="活動開始予定時刻を選択してください。", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=DatetimePickerAction(label='開始予定時刻を選択',
                                                            data='time_postback',
                                                            mode='time'))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "register_activity_ended":
                if message == "取り消し":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="次回活動日登録を終了しました。")
                    )
                    sys.exit()
                update(event.source.user_id, "action_type",
                       "register_activity_check")
                register_activity_date = str(
                    userdata["register_activity_date"])
                announce = str(userdata["register_activity_date_full"])
                register_activity_about = userdata["register_activity_about"]
                register_activity_observe_or_not = userdata["register_activity_observe_or_not"]
                register_activity_start_time = userdata["register_activity_start_time"]
                register_activity_end_time = userdata["register_activity_end_time"]
                register_activity_time_span = userdata["register_activity_time_span"]
                if register_activity_observe_or_not == "あり(悪天中止)":
                    register_activity_observation_end_time = userdata[
                        "register_activity_observation_end_time"]
                    register_activity_observation_time_span = userdata[
                        "register_activity_observation_time_span"]
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="確定しますか？", weight="bold", size="xxl", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="日付：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=announce, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=register_activity_about, wrap=True),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="当日の予定", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=register_activity_observe_or_not, flex=1, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=register_activity_start_time, flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(text="活動終了時刻：",
                                              weight="bold", color="#7D7D7D"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="　観測有場合：", flex=1),
                                        TextComponent(text=register_activity_observation_end_time + "(" +
                                                      register_activity_observation_time_span + "分間)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="　観測無場合：", flex=1),
                                        TextComponent(
                                            text=register_activity_end_time + "(" + register_activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                SeparatorComponent(),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(text="登録を確定しますか？",
                                              weight="bold", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="登録を確定しますか？", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="はい", text="はい")),
                                QuickReplyButton(
                                    action=MessageAction(label="やめる", text="やめる"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="確定しますか？", weight="bold", size="xxl", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="日付：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=announce, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=register_activity_about, wrap=True),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="当日の予定", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=register_activity_observe_or_not, flex=1, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=register_activity_start_time, flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="活動終了時刻：", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=register_activity_end_time + "(" + register_activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                SeparatorComponent(),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(text="登録を確定しますか？",
                                              weight="bold", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="登録を確定しますか？", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="はい", text="はい")),
                                QuickReplyButton(
                                    action=MessageAction(label="やめる", text="やめる"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

            elif userdata["action_type"] == "register_activity_check":
                if message == "はい":
                    next_act_data = get("NextAct")
                    register_activity_date = str(
                        userdata["register_activity_date"])
                    register_activity_about = str(
                        userdata["register_activity_about"])
                    register_activity_observe_or_not = userdata["register_activity_observe_or_not"]
                    register_activity_start_time = userdata["register_activity_start_time"]
                    register_activity_end_time = userdata["register_activity_end_time"]
                    register_activity_time_span = userdata["register_activity_time_span"]
                    if register_activity_observe_or_not == "あり(悪天中止)":
                        register_activity_observation_end_time = userdata[
                            "register_activity_observation_end_time"]
                        register_activity_observation_time_span = userdata[
                            "register_activity_observation_time_span"]
                    flag_activity_date_already = userdata["flag_activity_date_already"]
                    reset_user_data()
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", "NextAct")
                        task = client.get(key)
                        task["Date"] = register_activity_date
                        task["Info"] = register_activity_about
                        task["Observe_or_not"] = register_activity_observe_or_not
                        task["Start_time"] = register_activity_start_time
                        task["End_time"] = register_activity_end_time
                        task["Span"] = register_activity_time_span
                        if flag_activity_date_already:
                            task["is_schedule_created"] = False
                            task["Participants_Info"] = next_act_data["Participants_Info"]
                            task["Schedule"] = next_act_data["Schedule"]
                            task["Participants"] = next_act_data["Participants"]
                            task["Assign"] = next_act_data["Assign"]
                            task["time_list_number"] = next_act_data["time_list_number"]
                            task["period_time"] = next_act_data["period_time"]
                        else:
                            task["is_schedule_created"] = False
                            task["Participants_Info"] = "[]"
                            task["Schedule"] = str()
                            task["Participants"] = 0
                            task["Assign"] = "[]"
                            task["time_list_number"] = str()
                            task["period_time"] = str()
                        if register_activity_observe_or_not == "あり(悪天中止)":
                            task["Observation_end_time"] = register_activity_observation_end_time
                            task["Observation_span"] = register_activity_observation_time_span
                        client.put(task)
                    activdateb = register_activity_date
                    activstrb = str()
                    activsab = str()
                    activinfob = str()
                    datetodaytemp = datetime.today() + timedelta(hours=9)
                    if len(activdateb) == 10:
                        activdateb = datetime(year=int(activdateb[:4]), month=int(
                            activdateb[5:7]), day=int(activdateb[8:10]))
                        datenext = datetime.now() + timedelta(hours=9) + timedelta(minutes=1)
                        if (register_activity_observe_or_not != "なし") and flag_activity_date_already and next_act_data["is_schedule_created"]:
                            try:
                                try:
                                    client = scheduler_v1.CloudSchedulerClient()
                                    project_name = get("DevMode")[
                                        "project_name"]
                                    job = client.delete_job(
                                        name='projects/' + project_name + '/locations/asia-northeast1/jobs/AutoCalculate')
                                except:
                                    pass
                                crons = datenext.strftime("%-M %-H %-d %-m *")
                                project_name = get("DevMode")["project_name"]
                                client = scheduler_v1.CloudSchedulerClient()
                                job = scheduler_v1.Job()
                                job.name = 'projects/' + project_name + \
                                    '/locations/asia-northeast1/jobs/AutoCalculate'
                                job.schedule = crons
                                job.time_zone = 'Asia/Tokyo'
                                http_target = scheduler_v1.HttpTarget()
                                http_target.uri = "https://" + project_name + ".an.r.appspot.com/create_schedule"
                                http_target.http_method = "POST"
                                job.http_target = http_target
                                job = client.create_job(
                                    parent='projects/' + project_name + '/locations/asia-northeast1', job=job)
                            except:
                                pass
                        if register_activity_observe_or_not != "なし":
                            try:
                                crons = "0 8 {0} {1} *".format(activdateb.strftime(
                                    "%-d"), activdateb.strftime("%-m"))
                                project_name = get("DevMode")["project_name"]
                                client = scheduler_v1.CloudSchedulerClient()
                                job = scheduler_v1.Job()
                                job.name = 'projects/' + project_name + \
                                    '/locations/asia-northeast1/jobs/AutoCalculate'
                                job.schedule = crons
                                job.time_zone = 'Asia/Tokyo'
                                http_target = scheduler_v1.HttpTarget()
                                http_target.uri = "https://" + project_name + ".an.r.appspot.com/create_schedule"
                                http_target.http_method = "POST"
                                job.http_target = http_target
                                job = client.create_job(
                                    parent='projects/' + project_name + '/locations/asia-northeast1', job=job)
                            except:
                                pass

                        elif (register_activity_observe_or_not == "なし") and flag_activity_date_already:
                            try:
                                client = scheduler_v1.CloudSchedulerClient()
                                project_name = get("DevMode")["project_name"]
                                job = client.delete_job(
                                    name='projects/' + project_name + '/locations/asia-northeast1/jobs/AutoCalculate')
                            except:
                                pass
                        activdatenext = activdateb + timedelta(days=1)
                        activdatenext = activdatenext.strftime("%d")
                        activstrb = str(activdateb.strftime("%a"))
                        if activstrb == "Mon":
                            activstrb = "[月]"
                        elif activstrb == "Tue":
                            activstrb = "[火]"
                        elif activstrb == "Wed":
                            activstrb = "[水]"
                        elif activstrb == "Thu":
                            activstrb = "[木]"
                        elif activstrb == "Fri":
                            activstrb = "[金]"
                        elif activstrb == "Sat":
                            activstrb = "[土]"
                        elif activstrb == "Sun":
                            activstrb = "[日]"
                        activsab = datetodaytemp - activdateb
                        activsab = int(activsab.days)
                        activdateb = str(int(activdateb.strftime(
                            "%m"))) + "月" + str(int(activdateb.strftime("%d"))) + "日"
                        activinfob = register_activity_about
                        dataan = False
                        if activsab == 0:
                            activdateb = "今日(" + activdateb + activstrb + ")"
                            dataan = True
                        elif activsab == -1:
                            activdateb = "明日(" + activdateb + activstrb + ")"
                            dataan = True
                        elif activsab == -2:
                            activdateb = "あさって(" + activdateb + activstrb + ")"
                            dataan = True
                        elif activsab == -3:
                            activdateb = "しあさって(" + \
                                activdateb + activstrb + ")"
                            dataan = True
                        elif activsab == -4:
                            activdateb = activdateb + activstrb
                            dataan = True
                        else:
                            activdateb = activdateb + activstrb
                        if len(activinfob) == 0:
                            activinfob = "なし"

                    rsdate = datetoday.replace(
                        hour=0, minute=0, second=0, microsecond=0)
                    rsdate = rsdate + timedelta(days=abs(activsab))
                    calculation_orbit_date = rsdate
                    calculation_orbit_date = calculation_orbit_date - \
                        timedelta(days=1)
                    calculation_orbit_date = calculation_orbit_date.replace(
                        hour=15, minute=0, second=0, microsecond=0)
                    tglocation.date = calculation_orbit_date
                    moon.compute(tglocation)
                    sun.compute(tglocation)
                    mercury.compute(tglocation)
                    venus.compute(tglocation)
                    mars.compute(tglocation)
                    jupiter.compute(tglocation)
                    saturn.compute(tglocation)
                    uranus.compute(tglocation)
                    neptune.compute(tglocation)
                    pluto.compute(tglocation)
                    day_mercuryrise = (tglocation.next_rising(
                        mercury)).datetime() + timedelta(hours=9)
                    tglocation.date = tglocation.next_rising(mercury)
                    day_mercuryset = (tglocation.next_setting(
                        mercury)).datetime() + timedelta(hours=9)
                    tglocation.date = calculation_orbit_date
                    day_venusrise = (tglocation.next_rising(
                        venus)).datetime() + timedelta(hours=9)
                    tglocation.date = tglocation.next_rising(venus)
                    day_venusset = (tglocation.next_setting(
                        venus)).datetime() + timedelta(hours=9)
                    tglocation.date = calculation_orbit_date
                    day_marsrise = (tglocation.next_rising(
                        mars)).datetime() + timedelta(hours=9)
                    tglocation.date = tglocation.next_rising(mars)
                    day_marsset = (tglocation.next_setting(
                        mars)).datetime() + timedelta(hours=9)
                    tglocation.date = calculation_orbit_date
                    day_jupiterrise = (tglocation.next_rising(
                        jupiter)).datetime() + timedelta(hours=9)
                    tglocation.date = tglocation.next_rising(jupiter)
                    day_jupiterset = (tglocation.next_setting(
                        jupiter)).datetime() + timedelta(hours=9)
                    tglocation.date = calculation_orbit_date
                    day_saturnrise = (tglocation.next_rising(
                        saturn)).datetime() + timedelta(hours=9)
                    tglocation.date = tglocation.next_rising(saturn)
                    day_saturnset = (tglocation.next_setting(
                        saturn)).datetime() + timedelta(hours=9)
                    day_uranusrise = (tglocation.next_rising(
                        uranus)).datetime() + timedelta(hours=9)
                    tglocation.date = tglocation.next_rising(uranus)
                    day_uranusset = (tglocation.next_setting(
                        uranus)).datetime() + timedelta(hours=9)
                    tglocation.date = calculation_orbit_date
                    day_neptunerise = (tglocation.next_rising(
                        neptune)).datetime() + timedelta(hours=9)
                    tglocation.date = tglocation.next_rising(neptune)
                    day_neptuneset = (tglocation.next_setting(
                        neptune)).datetime() + timedelta(hours=9)
                    tglocation.date = calculation_orbit_date
                    day_plutorise = (tglocation.next_rising(
                        pluto)).datetime() + timedelta(hours=9)
                    tglocation.date = tglocation.next_rising(pluto)
                    day_plutoset = (tglocation.next_setting(
                        pluto)).datetime() + timedelta(hours=9)
                    tglocation.date = calculation_orbit_date
                    moonrise = (tglocation.next_rising(moon)
                                ).datetime() + timedelta(hours=9)
                    sunrise = (tglocation.next_rising(sun)
                               ).datetime() + timedelta(hours=9)
                    sunset = (tglocation.next_setting(sun)
                              ).datetime() + timedelta(hours=9)
                    tglocation.date = tglocation.next_setting(sun)
                    sunriseafterset = (tglocation.next_rising(
                        sun)).datetime() + timedelta(hours=9)
                    tglocation.date = calculation_orbit_date
                    suntransit = (tglocation.next_transit(
                        sun)).datetime() + timedelta(hours=9)
                    tglocation.date = calculation_orbit_date + \
                        timedelta(hours=17)
                    moonage = round(tglocation.date -
                                    ephem.previous_new_moon(tglocation.date), 1)
                    cutmoonage = str(round(moonage))
                    moonage = str(moonage)
                    tglocation.date = calculation_orbit_date
                    tglocation.date = tglocation.next_transit(sun)
                    southsunalt = round(degrees(sun.alt), 1)
                    tglocation.date = calculation_orbit_date
                    tglocation.date = tglocation.next_rising(moon)
                    moontransit = (tglocation.next_transit(
                        moon)).datetime() + timedelta(hours=9)
                    moonset = (tglocation.next_setting(moon)
                               ).datetime() + timedelta(hours=9)
                    tglocation.date = tglocation.next_transit(moon)
                    southmoonalt = round(degrees(moon.alt), 1)
                    tglocation.date = calculation_orbit_date
                    tglocation.date = tglocation.next_setting(sun)
                    sunriseafterset = (tglocation.next_rising(
                        sun)).datetime() + timedelta(hours=9)

                    def timeFix(date):
                        global rsdate
                        deltaday = date - rsdate
                        if date.second >= 30:
                            date = date + timedelta(minutes=1)
                        kobun = date.strftime("%-H時%-M分")
                        if deltaday.days == 1:
                            plus = "翌日,"
                            kobun = plus + kobun
                        elif deltaday.days > 1:
                            plus = str(deltaday.days) + "日後,"
                            kobun = plus + kobun
                        elif deltaday.days == -1:
                            plus = "前日,"
                            kobun = plus + kobun
                        elif deltaday.days < -1:
                            plus = str(abs(deltaday.days)) + "日前,"
                            kobun = plus + kobun
                        if kobun[-3:] == "時0分":
                            return kobun[:-2]
                        else:
                            return kobun

                    observable_list = ["太陽"]
                    if timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage) == "観測不可":
                        moon_visual = "観測不可"
                    else:
                        observable_list.append("月")
                        moon_visual = timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[
                                              0]) + "から\n" + timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[1]) + "まで観測可\n（天候による）"

                    if planet_timespan(day_mercuryrise, day_mercuryset, sunset, sunriseafterset) != "観測不可":
                        observable_list.append("水星")
                    if planet_timespan(day_venusrise, day_venusset, sunset, sunriseafterset) != "観測不可":
                        observable_list.append("金星")
                    if planet_timespan(day_marsrise, day_marsset, sunset, sunriseafterset) != "観測不可":
                        observable_list.append("火星")
                    if planet_timespan(day_jupiterrise, day_jupiterset, sunset, sunriseafterset) != "観測不可":
                        observable_list.append("木星")
                    if planet_timespan(day_saturnrise, day_saturnset, sunset, sunriseafterset) != "観測不可":
                        observable_list.append("土星")
                    if planet_timespan(day_uranusrise, day_uranusset, sunset, sunriseafterset) != "観測不可":
                        observable_list.append("天王星")
                    if planet_timespan(day_neptunerise, day_neptuneset, sunset, sunriseafterset) != "観測不可":
                        observable_list.append("海王星")
                    if planet_timespan(day_plutorise, day_plutoset, sunset, sunriseafterset) != "観測不可":
                        observable_list.append("冥王星")

                    observable_planets = str()
                    if len(observable_list) == 1:
                        observable_planets = "太陽のみ"
                    else:
                        for i in observable_list:
                            if i == "太陽":
                                observable_planets = "太陽"
                            else:
                                observable_planets = observable_planets + "・" + i

                    update("NextAct", "Observable_planets", observable_planets)

                    if cutmoonage == "0":
                        moonage = moonage + "（新月）"
                    elif cutmoonage == "1":
                        moonage = moonage + "（繊月）"
                    elif cutmoonage == "2":
                        moonage = moonage + "（三日月）"
                    elif cutmoonage == "7":
                        moonage = moonage + "（上限）"
                    elif cutmoonage == "9":
                        moonage = moonage + "（十日夜月）"
                    elif cutmoonage == "12":
                        moonage = moonage + "（十三夜月）"
                    elif cutmoonage == "13":
                        moonage = moonage + "（小望月）"
                    elif cutmoonage == "14":
                        moonage = moonage + "（満月）"
                    elif cutmoonage == "15":
                        moonage = moonage + "（十六夜月）"
                    elif cutmoonage == "16":
                        moonage = moonage + "（立待月）"
                    elif cutmoonage == "17":
                        moonage = moonage + "（居待月）"
                    elif cutmoonage == "18":
                        moonage = moonage + "（寝待月）"
                    elif cutmoonage == "19":
                        moonage = moonage + "（更待月）"
                    elif cutmoonage == "22":
                        moonage = moonage + "（下弦）"
                    elif cutmoonage == "25":
                        moonage = moonage + "（有明月）"

                    def normalan():
                        if register_activity_observe_or_not == "あり(悪天中止)":
                            dataan = False
                            bubble = BubbleContainer(
                                direction='ltr',
                                hero=ImageComponent(
                                    url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                                    size='full',
                                    aspect_ratio='20:13',
                                    aspect_mode='cover',
                                ),
                                body=BoxComponent(
                                    layout='vertical',
                                    contents=[
                                        TextComponent(text="次回活動日の予定が更新されました。",
                                                      size='xs', adjustMode='shrink-to-fit'),
                                        TextComponent(text=activdateb, weight='bold',
                                                      size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                        TextComponent(text="\n"),
                                        TextComponent(
                                            text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                        TextComponent(
                                            text=activinfob, wrap=True),
                                        TextComponent(text="\n"),
                                        SeparatorComponent(),
                                        TextComponent(text="\n"),
                                        TextComponent(text="当日の予定", size="lg",
                                                      weight="bold", color="#4A4A4A"),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="5px"
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=register_activity_observe_or_not, flex=1, align="center", wrap=True)
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="5px"
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=register_activity_start_time, flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="5px"
                                        ),
                                        TextComponent(
                                            text="活動終了時刻：", weight="bold", color="#7D7D7D"),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="　観測有場合：", flex=1),
                                                TextComponent(text=register_activity_observation_end_time + "(" +
                                                              register_activity_observation_time_span + "分間)", flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="　観測無場合：", flex=1),
                                                TextComponent(
                                                    text=register_activity_end_time + "(" + register_activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        TextComponent(text="\n"),
                                        SeparatorComponent(),
                                        TextComponent(text="\n"),
                                        TextComponent(text="当日の情報", size="lg",
                                                      weight="bold", color="#4A4A4A"),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="17時の月齢：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=moonage, flex=1, align="center")
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="日没：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(text=timeFix(
                                                    sunset), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="月の出：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(text=timeFix(
                                                    moonrise), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="月の入り：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=timeFix(moonset), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        TextComponent(
                                            text="月の観測：", weight="bold", color="#7D7D7D", wrap=True),
                                        TextComponent(
                                            text=moon_visual, align="center", wrap=True),
                                        TextComponent(
                                            text="観測可能天体：", weight="bold", color="#7D7D7D", wrap=True),
                                        TextComponent(
                                            text=observable_planets, align="center", wrap=True),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="次回の活動日が" + activdateb + "に予定されました。　アプリを開いて確認してください。", contents=bubble, quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="参加希望・時間割確認", text="参加希望・時間割確認"))
                                    ]
                                )
                            )
                            broadcast(flex)
                            reset_user_data()
                        elif register_activity_observe_or_not == "なし":
                            dataan = False
                            bubble = BubbleContainer(
                                direction='ltr',
                                hero=ImageComponent(
                                    url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                                    size='full',
                                    aspect_ratio='20:13',
                                    aspect_mode='cover',
                                ),
                                body=BoxComponent(
                                    layout='vertical',
                                    contents=[
                                        TextComponent(text="次回活動日の予定が更新されました。",
                                                      size='xs', adjustMode='shrink-to-fit'),
                                        TextComponent(text=activdateb, weight='bold',
                                                      size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                        TextComponent(text="\n"),
                                        TextComponent(
                                            text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                        TextComponent(
                                            text=activinfob, wrap=True),
                                        TextComponent(text="\n"),
                                        SeparatorComponent(),
                                        TextComponent(text="\n"),
                                        TextComponent(text="当日の予定", size="lg",
                                                      weight="bold", color="#4A4A4A"),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="5px"
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=register_activity_observe_or_not, flex=1, align="center", wrap=True)
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="5px"
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=register_activity_start_time, flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="5px"
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="活動終了時刻：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=register_activity_end_time + "(" + register_activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="次回の活動日が" + activdateb + "に予定されました。　アプリを開いて確認してください。", contents=bubble)
                            broadcast(flex)
                            reset_user_data()
                        else:
                            dataan = False
                            bubble = BubbleContainer(
                                direction='ltr',
                                hero=ImageComponent(
                                    url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                                    size='full',
                                    aspect_ratio='20:13',
                                    aspect_mode='cover',
                                ),
                                body=BoxComponent(
                                    layout='vertical',
                                    contents=[
                                        TextComponent(text="次回活動日の予定が更新されました。",
                                                      size='xs', adjustMode='shrink-to-fit'),
                                        TextComponent(text=activdateb, weight='bold',
                                                      size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                        TextComponent(text="\n"),
                                        TextComponent(
                                            text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                        TextComponent(
                                            text=activinfob, wrap=True),
                                        TextComponent(text="\n"),
                                        SeparatorComponent(),
                                        TextComponent(text="\n"),
                                        TextComponent(text="当日の予定", size="lg",
                                                      weight="bold", color="#4A4A4A"),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="5px"
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=register_activity_observe_or_not, flex=1, align="center", wrap=True)
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="5px"
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=register_activity_start_time, flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="5px"
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="活動終了時刻：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=register_activity_end_time + "(" + register_activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        TextComponent(text="\n"),
                                        SeparatorComponent(),
                                        TextComponent(text="\n"),
                                        TextComponent(text="当日の情報", size="lg",
                                                      weight="bold", color="#4A4A4A"),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="17時の月齢：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=moonage, flex=1, align="center")
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="日没：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(text=timeFix(
                                                    sunset), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="月の出：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(text=timeFix(
                                                    moonrise), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="月の入り：", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=timeFix(moonset), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        TextComponent(
                                            text="月の観測：", weight="bold", color="#7D7D7D", wrap=True),
                                        TextComponent(
                                            text=moon_visual, align="center", wrap=True),
                                        TextComponent(
                                            text="観測可能天体：", weight="bold", color="#7D7D7D", wrap=True),
                                        TextComponent(
                                            text=observable_planets, align="center", wrap=True),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="次回の活動日が" + activdateb + "に予定されました。　アプリを開いて確認してください。", contents=bubble, quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="参加希望・時間割確認", text="参加希望・時間割確認"))
                                    ]
                                )
                            )
                            broadcast(flex)
                            reset_user_data()
                    if dataan:
                        try:
                            if datenow > (get("WeatherData")["宮城県仙台市宮城野区date"] + timedelta(hours=2)):
                                import requests
                                url = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/219001?apikey=" + str(os.environ["apikey"]) + \
                                    "&language=ja-JP&details=true&metric=true"
                                weatherdata = requests.get(url)
                                connectionstatuscode = str(
                                    weatherdata.status_code)
                                if connectionstatuscode == "503":
                                    normalan()
                                weatherdata = weatherdata.json()
                                client = datastore.Client()
                                with client.transaction():
                                    key = client.key("Task", "WeatherData")
                                    task = client.get(key)
                                    task["宮城県仙台市宮城野区"] = str(weatherdata)
                                    task["宮城県仙台市宮城野区date"] = datenow
                                    client.put(task)

                            weather_datajson = ast.literal_eval(
                                get("WeatherData")["宮城県仙台市宮城野区"])

                            dataFixed = weather_datajson["DailyForecasts"][abs(
                                activsab)]
                            aboutemp = dataFixed["Temperature"]
                            hightemp = str(aboutemp["Maximum"]["Value"])
                            lowtemp = str(aboutemp["Minimum"]["Value"])
                            hightempfloat = float(hightemp)
                            lowtempfloat = float(lowtemp)
                            averagetemp = (hightempfloat + lowtempfloat) / 2
                            averagetempint = int(round(averagetemp, 1))
                            averagetempstr = str(round(averagetemp, 1))
                            aboutozonePollen = dataFixed["AirAndPollen"][0]
                            ozoneValue = str(aboutozonePollen["Value"])
                            ozoneValueint = int(ozoneValue)
                            aboutnightforecast = dataFixed["Night"]
                            nightphrase = str(aboutnightforecast["LongPhrase"])
                            nightcloudcover = str(
                                aboutnightforecast["CloudCover"])
                            intnightcloud = int(nightcloudcover)
                            averagetempintyes = averagetempint
                            intnightcloudyes = intnightcloud
                            ozoneValueintyes = ozoneValueint
                            hoshizora = (averagetempintyes + 273) * \
                                pow((intnightcloudyes + 273), 2) * \
                                (ozoneValueintyes + 273)
                            hoshizora = (1 / hoshizora) * 60000000000
                            hoshizora = round(hoshizora, 1)
                            hoshizora = str(hoshizora)

                            if register_activity_observe_or_not == "あり(悪天中止)":
                                bubble = BubbleContainer(
                                    direction='ltr',
                                    hero=ImageComponent(
                                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                                        size='full',
                                        aspect_ratio='20:13',
                                        aspect_mode='cover',
                                    ),
                                    body=BoxComponent(
                                        layout='vertical',
                                        contents=[
                                            TextComponent(text="次回活動日の予定が更新されました。",
                                                          size='xs', adjustMode='shrink-to-fit'),
                                            TextComponent(text=activdateb, weight='bold',
                                                          size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                            TextComponent(text="\n"),
                                            TextComponent(
                                                text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                            TextComponent(
                                                text=activinfob, wrap=True),
                                            TextComponent(text="\n"),
                                            SeparatorComponent(),
                                            TextComponent(text="\n"),
                                            TextComponent(text="当日の予定", size="lg",
                                                          weight="bold", color="#4A4A4A"),
                                            BoxComponent(
                                                layout="vertical",
                                                contents=[
                                                    FillerComponent()
                                                ],
                                                height="5px"
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=register_activity_observe_or_not, flex=1, align="center", wrap=True)
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="vertical",
                                                contents=[
                                                    FillerComponent()
                                                ],
                                                height="5px"
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=register_activity_start_time, flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="vertical",
                                                contents=[
                                                    FillerComponent()
                                                ],
                                                height="5px"
                                            ),
                                            TextComponent(
                                                text="活動終了時刻：", weight="bold", color="#7D7D7D"),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="　観測有場合：", flex=1),
                                                    TextComponent(
                                                        text=register_activity_observation_end_time + "(" + register_activity_observation_time_span + "分間)", flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="　観測無場合：", flex=1),
                                                    TextComponent(
                                                        text=register_activity_end_time + "(" + register_activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            TextComponent(text="\n"),
                                            SeparatorComponent(),
                                            TextComponent(text="\n"),
                                            TextComponent(text="当日の情報", size="lg",
                                                          weight="bold", color="#4A4A4A"),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="17時の月齢：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=moonage, flex=1, align="center")
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="ほしぞら指数：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=hoshizora,
                                                                  flex=1, align="center"),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="夜間の天気：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=nightphrase, flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="平均気温：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=averagetempstr + "℃", flex=1, align="center"),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="日没：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=timeFix(
                                                        sunset), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="月の出：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=timeFix(
                                                        moonrise), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="月の入り：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=timeFix(moonset), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            TextComponent(
                                                text="月の観測：", weight="bold", color="#7D7D7D", wrap=True),
                                            TextComponent(
                                                text=moon_visual, align="center", wrap=True),
                                            TextComponent(
                                                text="観測可能天体：", weight="bold", color="#7D7D7D", wrap=True),
                                            TextComponent(
                                                text=observable_planets, align="center", wrap=True),
                                        ],
                                    )
                                )
                                flex = FlexSendMessage(
                                    alt_text="次回の活動日が" + activdateb + "に予定されました。　アプリを開いて確認してください。", contents=bubble, quick_reply=QuickReply(
                                        items=[
                                            QuickReplyButton(
                                                action=MessageAction(label="参加希望・時間割確認", text="参加希望・時間割確認"))
                                        ]
                                    )
                                )
                                broadcast(flex)
                                reset_user_data()
                            elif register_activity_observe_or_not == "なし":
                                dataan = False
                                bubble = BubbleContainer(
                                    direction='ltr',
                                    hero=ImageComponent(
                                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                                        size='full',
                                        aspect_ratio='20:13',
                                        aspect_mode='cover',
                                    ),
                                    body=BoxComponent(
                                        layout='vertical',
                                        contents=[
                                            TextComponent(text="次回活動日の予定が更新されました。",
                                                          size='xs', adjustMode='shrink-to-fit'),
                                            TextComponent(text=activdateb, weight='bold',
                                                          size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                            TextComponent(text="\n"),
                                            TextComponent(
                                                text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                            TextComponent(
                                                text=activinfob, wrap=True),
                                            TextComponent(text="\n"),
                                            SeparatorComponent(),
                                            TextComponent(text="\n"),
                                            TextComponent(text="当日の予定", size="lg",
                                                          weight="bold", color="#4A4A4A"),
                                            BoxComponent(
                                                layout="vertical",
                                                contents=[
                                                    FillerComponent()
                                                ],
                                                height="5px"
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=register_activity_observe_or_not, flex=1, align="center", wrap=True)
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="vertical",
                                                contents=[
                                                    FillerComponent()
                                                ],
                                                height="5px"
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=register_activity_start_time, flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="vertical",
                                                contents=[
                                                    FillerComponent()
                                                ],
                                                height="5px"
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="活動終了時刻：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=register_activity_end_time + "(" + register_activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                        ],
                                    )
                                )
                                flex = FlexSendMessage(
                                    alt_text="次回の活動日が" + activdateb + "に予定されました。　アプリを開いて確認してください。", contents=bubble)
                                broadcast(flex)
                                reset_user_data()
                            else:
                                bubble = BubbleContainer(
                                    direction='ltr',
                                    hero=ImageComponent(
                                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%AC%A1%E5%9B%9E%E6%B4%BB%E5%8B%95%E6%97%A5.jpg',
                                        size='full',
                                        aspect_ratio='20:13',
                                        aspect_mode='cover',
                                    ),
                                    body=BoxComponent(
                                        layout='vertical',
                                        contents=[
                                            TextComponent(text="次回活動日の予定が更新されました。",
                                                          size='xs', adjustMode='shrink-to-fit'),
                                            TextComponent(text=activdateb, weight='bold',
                                                          size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                            TextComponent(text="\n"),
                                            TextComponent(
                                                text="活動の詳細：", weight="bold", color="#7D7D7D"),
                                            TextComponent(
                                                text=activinfob, wrap=True),
                                            TextComponent(text="\n"),
                                            SeparatorComponent(),
                                            TextComponent(text="\n"),
                                            TextComponent(text="当日の予定", size="lg",
                                                          weight="bold", color="#4A4A4A"),
                                            BoxComponent(
                                                layout="vertical",
                                                contents=[
                                                    FillerComponent()
                                                ],
                                                height="5px"
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="観測の有無：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=register_activity_observe_or_not, flex=1, align="center", wrap=True)
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="vertical",
                                                contents=[
                                                    FillerComponent()
                                                ],
                                                height="5px"
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="活動開始時刻：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=register_activity_start_time, flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="vertical",
                                                contents=[
                                                    FillerComponent()
                                                ],
                                                height="5px"
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="活動終了時刻：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=register_activity_end_time + "(" + register_activity_time_span + "分間)", flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            TextComponent(text="\n"),
                                            SeparatorComponent(),
                                            TextComponent(text="\n"),
                                            TextComponent(text="当日の情報", size="lg",
                                                          weight="bold", color="#4A4A4A"),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="17時の月齢：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=moonage, flex=1, align="center")
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="ほしぞら指数：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=hoshizora,
                                                                  flex=1, align="center"),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="夜間の天気：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=nightphrase, flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="平均気温：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=averagetempstr + "℃", flex=1, align="center"),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="日没：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=timeFix(
                                                        sunset), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="月の出：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=timeFix(
                                                        moonrise), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="月の入り：", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=timeFix(moonset), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            TextComponent(
                                                text="月の観測：", weight="bold", color="#7D7D7D", wrap=True),
                                            TextComponent(
                                                text=moon_visual, align="center", wrap=True),
                                            TextComponent(
                                                text="観測可能天体：", weight="bold", color="#7D7D7D", wrap=True),
                                            TextComponent(
                                                text=observable_planets, align="center", wrap=True),
                                        ],
                                    )
                                )
                                flex = FlexSendMessage(
                                    alt_text="次回の活動日が" + activdateb + "に予定されました。　アプリを開いて確認してください。", contents=bubble, quick_reply=QuickReply(
                                        items=[
                                            QuickReplyButton(
                                                action=MessageAction(label="参加希望・時間割確認", text="参加希望・時間割確認"))
                                        ]
                                    )
                                )
                                broadcast(flex)
                                reset_user_data()

                        except:
                            normalan()
                    elif not dataan:
                        normalan()
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="次回活動日登録を取り消しました。")
                    )
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        if message == "活動記録記入":
            try:
                reset_user_data()
            except:
                pass
            try:
                if event.source.user_id in idlist:
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["action_type"] = "write_note"
                        task["flag_note_date_already"] = False
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="活動記録記入", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="編集権限が確認できました。記録する日付を選択してください。", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="編集権限が確認できました。記録する日付を選択してください。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='日付を選択',
                                                                data='date_postback',
                                                                mode='date')),
                                QuickReplyButton(
                                    action=MessageAction(label="やめる", text="やめる"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="編集権限が確認できませんでした。これは権限付与者限定の機能です。")
                    )
                    sys.exit()
            except SystemExit:
                sys.exit()
            except:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="編集権限が確認できませんでした。これは権限付与者限定の機能です。")
                )
                sys.exit()
        try:
            if userdata["action_type"] == "write_note":
                acnote = ast.literal_eval(get("Notes")["Notes"])
                if message in acnote:
                    if message[:4].isnumeric() and (message[4:5] == "-") and message[5:7].isnumeric() and (message[7:8] == "-") and message[8:10].isnumeric() and (len(message) == 10):
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", event.source.user_id)
                            task = client.get(key)
                            task["flag_note_date_already"] = True
                            task["write_note_date_already"] = str(message)
                            client.put(task)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="この日は既に記録されていますが、続行しますか？", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="はい", text="はい")),
                                        QuickReplyButton(
                                            action=MessageAction(label="やめる", text="やめる"))
                                    ]
                                )
                            )
                        )
                        sys.exit()
                    else:
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="表記が正しくありません。もう一度最初からやり直してください。活動記録の記入を終了します。")
                        )
                        sys.exit()
                elif (message[:4].isnumeric() and (message[4:5] == "-") and message[5:7].isnumeric() and (message[7:8] == "-") and message[8:10].isnumeric() and (len(message) == 10)) or message == "はい":
                    try:
                        if userdata["flag_note_date_already"]:
                            if message == "はい":
                                write_note_date_already = userdata["write_note_date_already"]
                                client = datastore.Client()
                                with client.transaction():
                                    key = client.key(
                                        "Task", event.source.user_id)
                                    task = client.get(key)
                                    task["write_note_date"] = write_note_date_already
                                    task["flag_note_date_already"] = False
                                    task["write_note_is_announced"] = "No(Update)"
                                    client.put(task)
                                write_note_date_full = datetime(year=int(write_note_date_already[:4]), month=int(
                                    write_note_date_already[5:7]), day=int(write_note_date_already[8:10]))
                                ksavestr = str(
                                    write_note_date_full.strftime("%a"))
                                if ksavestr == "Mon":
                                    ksavestr = "[月]"
                                elif ksavestr == "Tue":
                                    ksavestr = "[火]"
                                elif ksavestr == "Wed":
                                    ksavestr = "[水]"
                                elif ksavestr == "Thu":
                                    ksavestr = "[木]"
                                elif ksavestr == "Fri":
                                    ksavestr = "[金]"
                                elif ksavestr == "Sat":
                                    ksavestr = "[土]"
                                elif ksavestr == "Sun":
                                    ksavestr = "[日]"
                                write_note_date_full = write_note_date_full.strftime(
                                    "%-Y年%-m月%-d日") + ksavestr
                            else:
                                reset_user_data()
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(
                                        text="表記が正しくありません。もう一度最初からやり直してください。活動記録の記入を終了します。")
                                )
                                sys.exit()
                        elif not userdata["flag_note_date_already"]:
                            if message == "はい":
                                reset_user_data()
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(
                                        text="表記が正しくありません。もう一度最初からやり直してください。活動記録の記入を終了します。")
                                )
                                sys.exit()
                    except SystemExit:
                        sys.exit()
                    except:
                        if message == "はい":
                            reset_user_data()
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(
                                    text="表記が正しくありません。もう一度最初からやり直してください。活動記録の記入を終了します。")
                            )
                            sys.exit()
                        else:
                            pass
                    if message[:4].isnumeric() and (message[4:5] == "-") and message[5:7].isnumeric() and (message[7:8] == "-") and message[8:10].isnumeric() and (len(message) == 10):
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", event.source.user_id)
                            task = client.get(key)
                            task["write_note_date"] = str(message)
                            task["write_note_is_announced"] = "No"
                            client.put(task)
                        try:
                            write_note_date_full = datetime(year=int(message[:4]), month=int(
                                message[5:7]), day=int(message[8:10]))
                        except:
                            reset_user_data()
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(
                                    text="日付が正しくありません。もう一度最初からやり直してください。活動記録の記入を終了します。")
                            )
                            sys.exit()
                        ksavestr = str(write_note_date_full.strftime("%a"))
                        if ksavestr == "Mon":
                            ksavestr = "[月]"
                        elif ksavestr == "Tue":
                            ksavestr = "[火]"
                        elif ksavestr == "Wed":
                            ksavestr = "[水]"
                        elif ksavestr == "Thu":
                            ksavestr = "[木]"
                        elif ksavestr == "Fri":
                            ksavestr = "[金]"
                        elif ksavestr == "Sat":
                            ksavestr = "[土]"
                        elif ksavestr == "Sun":
                            ksavestr = "[日]"
                        write_note_date_full = write_note_date_full.strftime(
                            "%-Y年%-m月%-d日") + ksavestr
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["action_type"] = "write_note_start_time"
                        task["write_note_date_full"] = write_note_date_full
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="活動開始時刻を選択", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text=write_note_date_full + "ですね。\n次に、この日の活動開始時刻を選択してください。", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="活動開始時刻を選択してください。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='開始時刻を選択',
                                                                data='time_postback',
                                                                mode='time')),
                                QuickReplyButton(
                                    action=MessageAction(label="取り消し", text="取り消し"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    if userdata["flag_note_date_already"]:
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", event.source.user_id)
                            task = client.get(key)
                            task["action_type"] = "None"
                            task["flag_note_date_already"] = False
                            client.put(task)
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="活動記録の記入を取り消しました。")
                        )
                        sys.exit()
                    elif message == "やめる" or message == "いいえ":
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="活動記録の記入を取り消しました。")
                        )
                        sys.exit()
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="表記が正しくありません。もう一度最初からやり直してください。活動記録の記入を終了します。")
                    )
                    sys.exit()

            elif userdata["action_type"] == "write_note_start_time":
                if message == "取り消し":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="活動記録の記入を取り消しました。")
                    )
                    sys.exit()

            elif userdata["action_type"] == "write_note_end_time":
                if message == "取り消し":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="活動記録の記入を取り消しました。")
                    )
                    sys.exit()

            elif userdata["action_type"] == "write_note_weather":
                if message == "取り消し":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="活動記録の記入を取り消しました。")
                    )
                    sys.exit()

            elif userdata["action_type"] == "write_note_weather_check":
                if message == "取り消し":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="活動記録の記入を取り消しました。")
                    )
                    sys.exit()
                if not (message == "活動時間・天気の確定"):
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="表記が正しくありません。もう一度最初からやり直してください。活動記録の記入を終了します。")
                    )
                    sys.exit()
                timeandweather = userdata["write_note_activity_started_time"] + "~" + \
                    userdata["write_note_activity_ended_time"] + \
                    "（" + userdata["write_note_weather"] + "）"
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["action_type"] = "write_note_about"
                    task["activity_time"] = timeandweather
                    client.put(task)
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="活動内容を入力", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="それでは、この日の活動内容を入力してください。", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="活動内容を入力してください。", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="取り消し", text="取り消し"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "write_note_about":
                if message == "取り消し":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="活動記録の記入を取り消しました。")
                    )
                    sys.exit()
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["activity_detail"] = str(message)
                    task["write_note_observed_planets"] = str("[]")
                    task["action_type"] = "write_note_planets"
                    client.put(task)
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="観測した天体をひとつずつ選択してください。観測がなかった場合は、「観測なし」を選択してください。", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=MessageAction(
                                    label='観測なし', text='観測なし'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='太陽', data='太陽', text="太陽"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='月', data='月', text="月"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='金星', data='金星', text="金星"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='火星', data='火星', text="火星"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='木星', data='木星', text="木星"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='土星', data='土星', text="土星"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='その他天体', data='その他天体', text="その他天体")
                            ),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="観測した天体を選択してください。", contents=bubble)
                line_bot_api.reply_message(
                    event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "write_note_planets":
                if message == "取り消し":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="活動記録の記入を取り消しました。")
                    )
                    sys.exit()
                if (message == "観測あり") or (message == "観測なし"):
                    if message == "観測なし":
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", event.source.user_id)
                            task = client.get(key)
                            task["flag_write_note_observed"] = False
                            client.put(task)
                    kpls = userdata["write_note_observed_planets"]
                    kplslist = ast.literal_eval(kpls)
                    lobservedpls = str()
                    if message == "観測あり":
                        for i in kplslist:
                            lobservedpls = lobservedpls + i + "・"
                        lobservedpls = lobservedpls[:-1]
                        lobservedpls = lobservedpls + "の観測"
                    else:
                        lobservedpls = "観測なし"
                    activity_detail = userdata["activity_detail"]
                    activity_detail = lobservedpls + "\n" + activity_detail
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["activity_detail"] = activity_detail
                        task["action_type"] = "write_note_message"
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="連絡事項を入力", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="それでは、この日について連絡事項があれば入力してください。", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="連絡事項を入力してください。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="取り消し", text="取り消し"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif (message == "太陽") or (message == "月") or (message == "金星") or (message == "火星") or (message == "木星") or (message == "土星") or (message == "その他天体") or (message == "完了"):
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="表記が正しくありません。もう一度最初からやり直してください。活動記録の記入を終了します。")
                    )
                    sys.exit()
            elif userdata["action_type"] == "write_note_message":
                if message == "取り消し":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="活動記録の記入を取り消しました。")
                    )
                    sys.exit()
                write_note_date = userdata["write_note_date"]
                write_note_date_full = userdata["write_note_date_full"]
                activity_time = userdata["activity_time"]
                activity_detail = userdata["activity_detail"]
                activity_notice = str(message)
                knumber = str()
                try:
                    knumber = ast.literal_eval(
                        get("MembersList")[write_note_date])
                    knumber = "計{}名".format(str(len(knumber)))
                except:
                    knumber = "情報なし"
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["action_type"] = "write_note_check"
                    task["activity_notice"] = activity_notice
                    client.put(task)
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="確定しますか？", weight="bold", size="xxl", wrap=True),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="記録日：", weight="bold", color="#7D7D7D", wrap=True),
                            TextComponent(
                                text=write_note_date_full, weight="bold", size="lg", wrap=True),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(
                                text="活動時間・天気：", weight="bold", color="#7D7D7D", wrap=True),
                            TextComponent(
                                text=activity_time, wrap=True),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(
                                text="参加部員：", weight="bold", color="#7D7D7D", wrap=True),
                            TextComponent(
                                text=knumber, wrap=True),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(
                                text="活動内容：", weight="bold", color="#7D7D7D", wrap=True),
                            TextComponent(
                                text=activity_detail, wrap=True),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(
                                text="連絡事項：", weight="bold", color="#7D7D7D", wrap=True),
                            TextComponent(
                                text=activity_notice, wrap=True),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            SeparatorComponent(),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(
                                text="記録を確定しますか？", weight="bold")
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="配信を確定しますか？", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="はい", text="はい")),
                            QuickReplyButton(
                                action=MessageAction(label="やめる", text="やめる"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "write_note_check":
                if message == "取り消し":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="活動記録の記入を取り消しました。")
                    )
                    sys.exit()
                if message == "はい":
                    write_note_date = userdata["write_note_date"]
                    write_note_date_full = userdata["write_note_date_full"]
                    activity_time = userdata["activity_time"]
                    try:
                        knumber = ast.literal_eval(
                            get("MembersList")[write_note_date])
                        knumber = "計{}名".format(str(len(knumber)))
                    except:
                        knumber = "情報なし"
                    activity_detail = userdata["activity_detail"]
                    activity_notice = userdata["activity_notice"]
                    write_note_is_announced = userdata["write_note_is_announced"]
                    activdics = ast.literal_eval(get("Notes")["Notes"])
                    activdics[write_note_date] = {}
                    activdics[write_note_date]["activity_time"] = activity_time
                    activdics[write_note_date]["activity_detail"] = activity_detail
                    activdics[write_note_date]["activity_notice"] = activity_notice
                    activdics = str(activdics)
                    update("Notes", "Notes", activdics)
                    kobserved = userdata["flag_write_note_observed"]
                    kpls = ast.literal_eval(
                        userdata["write_note_observed_planets"])
                    kweather = userdata["write_note_weather"]
                    kactivetime = int(userdata["write_note_activity_span"])
                    kactivesta = get("ActiveStatistics")
                    kactivesta["活動回数"] = kactivesta["活動回数"] + 1
                    if kobserved:
                        kactivesta["観測回数"] = kactivesta["観測回数"] + 1
                        kactivesta["平均観測時間（分）"] = round(
                            (kactivesta["平均観測時間（分）"] + kactivetime) / kactivesta["観測回数"])
                    kactivesta[kweather] = kactivesta[kweather] + 1
                    kactivesta["平均活動時間（分）"] = round(
                        (kactivesta["平均活動時間（分）"] + kactivetime) / kactivesta["活動回数"])
                    for i in kpls:
                        kactivesta[i] = kactivesta[i] + 1
                    upsert("ActiveStatistics", kactivesta)
                    if write_note_is_announced == "No":
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(
                                        text="新しい活動記録が記入されました。", size='sm', wrap=True),
                                    TextComponent(
                                        text=write_note_date_full, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="活動時間・天気：", weight="bold", color="#7D7D7D"),
                                    TextComponent(
                                        text=activity_time, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="参加部員：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=knumber, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="活動内容：", weight="bold", color="#7D7D7D"),
                                    TextComponent(
                                        text=activity_detail, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="連絡事項：", weight="bold", color="#7D7D7D"),
                                    TextComponent(
                                        text=activity_notice, wrap=True)
                                ],
                            )
                        )
                        if knumber == "情報なし":
                            flex = FlexSendMessage(
                                alt_text=write_note_date_full + "の活動が記録されました。アプリを開いて確認してください。", contents=bubble)
                        else:
                            flex = FlexSendMessage(
                                alt_text=write_note_date_full + "の活動が記録されました。アプリを開いて確認してください。", contents=bubble, quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="参加部員を表示", text="最新の参加部員情報を表示"))
                                    ]
                                )
                            )
                        broadcast(flex)
                        reset_user_data()
                        sys.exit()
                    elif write_note_is_announced == "No(Update)":
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(
                                        text="活動記録が更新されました。", size='sm', wrap=True),
                                    TextComponent(
                                        text=write_note_date_full, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="活動時間・天気：", weight="bold", color="#7D7D7D"),
                                    TextComponent(
                                        text=activity_time, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="参加部員：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=knumber, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="活動内容：", weight="bold", color="#7D7D7D"),
                                    TextComponent(
                                        text=activity_detail, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="連絡事項：", weight="bold", color="#7D7D7D"),
                                    TextComponent(
                                        text=activity_notice, wrap=True)
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=write_note_date_full + "の活動が記録されました。アプリを開いて確認してください。", contents=bubble)
                        broadcast(flex)
                        reset_user_data()
                        sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="活動記録の記入を取り消しました。")
                    )
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        if message == "権限付与・解除・申請":
            try:
                reset_user_data()
            except:
                pass
            bubble = BubbleContainer(
                direction='ltr',
                body=BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(
                            text="操作を選択してください。", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="部員権限の操作", text="部員権限の操作"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="部長権限の切り替え", text="部長権限の切り替え"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="顧問権限の切り替え申請", text="顧問権限の切り替え申請"),
                        )
                    ],
                )
            )
            flex = FlexSendMessage(
                alt_text="操作を選択してください。", contents=bubble)
            line_bot_api.reply_message(
                event.reply_token, flex)
            sys.exit()

        try:
            if message == "部員権限の操作":
                if event.source.user_id in highidlist:
                    update(event.source.user_id, "action_type", "manage_auth")
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="権限付与・削除", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="操作する部員の学年・クラス・番号・名前を入力してください。\n以下の表記（g-c(nn)name）で入力してください。\n例：1-A(01)学院太郎", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="操作する部員には、部員登録がなされている必要があります。", size="xs", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="操作する部員の情報を入力してください。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="やめる", text="やめる"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="権限が確認できませんでした。この操作は部長と顧問のみが可能です。")
                    )
                    sys.exit()

            elif userdata["action_type"] == "manage_auth":
                if message == "やめる":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="操作を取り消しました。")
                    )
                    sys.exit()
                points_data = get("PointsID")
                hit = False
                for i in points_data:
                    if points_data[i] == message:
                        hit = True
                        managing_id = i
                        if managing_id in highidlist:
                            reset_user_data()
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="部長の権限を解除することはできません。")
                            )
                            sys.exit()
                        if managing_id in idlist:
                            client = datastore.Client()
                            with client.transaction():
                                key = client.key("Task", event.source.user_id)
                                task = client.get(key)
                                task["action_type"] = "managing_auth_delete"
                                task["managing_id"] = managing_id
                                client.put(task)
                            bubble = BubbleContainer(
                                direction='ltr',
                                body=BoxComponent(
                                    layout='vertical',
                                    contents=[
                                        TextComponent(
                                            text="解除しますか？", weight="bold", size="xxl", wrap=True),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="10px"
                                        ),
                                        TextComponent(
                                            text="この部員には既に権限が付与されています。権限を解除しますか？", wrap=True),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="権限を解除しますか？", contents=bubble, quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="はい", text="はい")),
                                        QuickReplyButton(
                                            action=MessageAction(label="やめる", text="やめる"))
                                    ]
                                )
                            )
                            line_bot_api.reply_message(event.reply_token, flex)
                            sys.exit()
                        else:
                            client = datastore.Client()
                            with client.transaction():
                                key = client.key("Task", event.source.user_id)
                                task = client.get(key)
                                task["action_type"] = "managing_auth_add"
                                task["managing_id"] = managing_id
                                client.put(task)
                            bubble = BubbleContainer(
                                direction='ltr',
                                body=BoxComponent(
                                    layout='vertical',
                                    contents=[
                                        TextComponent(
                                            text="付与しますか？", weight="bold", size="xxl", wrap=True),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="10px"
                                        ),
                                        TextComponent(
                                            text="この部員に権限を付与しますか？", wrap=True),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="権限を付与しますか？", contents=bubble, quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="はい", text="はい")),
                                        QuickReplyButton(
                                            action=MessageAction(label="やめる", text="やめる"))
                                    ]
                                )
                            )
                            line_bot_api.reply_message(event.reply_token, flex)
                            sys.exit()
                if not hit:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="部員が見つかりませんでした。\n部員登録がなされていないか、表記が誤っています。")
                    )
                    sys.exit()

            elif userdata["action_type"] == "managing_auth_add":
                if message == "はい":
                    managing_id = userdata["managing_id"]
                    points_data = get("PointsID")
                    managing_name = points_data[managing_id][7:]
                    managing_list = [managing_id, managing_name]
                    update("AuthUsers", managing_name, managing_list)
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text='権限を付与しました',
                                              weight='bold', size='xl'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text=managing_name + 'さんに権限を付与しました。',
                                              size='sm', adjustMode='shrink-to-fit'),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=managing_name + 'さんに権限を付与しました。', contents=bubble)
                    line_bot_api.reply_message(
                        event.reply_token, flex
                    )

                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text='権限が付与されました',
                                              weight='bold', size='xl'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text="ようこそ、" + managing_name + 'さん。\nアセンブラ権限が付与されました。',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="ようこそ、" + managing_name + 'さん。\nアセンブラ権限が付与されました。', contents=bubble)
                    line_bot_api.push_message(
                        managing_id, flex
                    )
                    reset_user_data()
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="操作を取り消しました。")
                    )
                    sys.exit()

            elif userdata["action_type"] == "managing_auth_delete":
                if message == "はい":
                    managing_id = userdata["managing_id"]
                    points_data = get("PointsID")
                    managing_name = points_data[managing_id][7:]
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", "AuthUsers")
                        task = client.get(key)
                        task.pop(managing_name)
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text='権限を解除しました',
                                              weight='bold', size='xl'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text=managing_name + 'さんの権限を解除しました。',
                                              size='sm', adjustMode='shrink-to-fit'),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=managing_name + 'さんの権限を解除しました。', contents=bubble)
                    line_bot_api.reply_message(
                        event.reply_token, flex
                    )

                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text='権限が解除されました',
                                              weight='bold', size='xl'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text='アセンブラ権限が解除されました。',
                                              size='sm', adjustMode='shrink-to-fit'),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text='アセンブラ権限が解除されました。', contents=bubble)
                    line_bot_api.push_message(
                        managing_id, flex
                    )
                    reset_user_data()
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="操作を取り消しました。")
                    )
                    sys.exit()

        except LineBotApiError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="LINEIDが確認できませんでした。この機能にはLINEIDが必要です。")
            )
            sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        try:
            if message == "部長権限の切り替え":
                if event.source.user_id in highidlist:
                    update(event.source.user_id, "action_type",
                           "managing_auth_bucho")
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="部長権限の切り替え", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="部長権限を付与する部員の学年・クラス・番号・名前を入力してください。\n以下の表記（g-c(nn)name）で入力してください。\n例：1-A(01)学院太郎", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="操作する部員には、部員登録がなされている必要があります。", size="xs", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="操作する部員の情報を入力してください。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="やめる", text="やめる"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="権限が確認できませんでした。この操作は部長と顧問のみが可能です。")
                    )
                    sys.exit()
            elif userdata["action_type"] == "managing_auth_bucho":
                if message == "やめる":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="操作を取り消しました。")
                    )
                    sys.exit()
                points_data = get("PointsID")
                hit = False
                for i in points_data:
                    if points_data[i] == message:
                        hit = True
                        managing_id = i
                        if managing_id in highidlist:
                            reset_user_data()
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(text="既に部長権限が付与されています。")
                            )
                            sys.exit()
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", event.source.user_id)
                            task = client.get(key)
                            task["action_type"] = "managing_auth_bucho_add"
                            task["managing_id"] = managing_id
                            client.put(task)
                        bubble = BubbleContainer(
                            direction='ltr',
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(
                                        text="部長権限を付与しますか？", weight="bold", size="xxl", wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="この部員に部長権限を付与しますか？", wrap=True),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="部長権限を付与しますか？", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="はい", text="はい")),
                                    QuickReplyButton(
                                        action=MessageAction(label="やめる", text="やめる"))
                                ]
                            )
                        )
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                if not hit:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="部員が見つかりませんでした。\n部員登録がなされていないか、表記が誤っています。")
                    )
                    sys.exit()
            elif userdata["action_type"] == "managing_auth_bucho_add":
                if message == "はい":
                    managing_id = userdata["managing_id"]
                    points_data = get("PointsID")
                    managing_name = points_data[managing_id][7:] + "（部長）"
                    managing_list = [managing_id, managing_name]
                    update("AuthUsers", "bucho", managing_list)
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text='部長権限を切り替えました',
                                              weight='bold', size='xl', wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text=managing_name + 'さんに部長権限を付与しました。',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=managing_name + 'さんに部長権限を付与しました。', contents=bubble)
                    line_bot_api.reply_message(
                        event.reply_token, flex
                    )

                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text='部長権限が付与されました',
                                              weight='bold', size='xl', wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text='ようこそ。部長権限が付与されました。',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text='部長権限が付与されました。', contents=bubble)
                    line_bot_api.push_message(
                        managing_id, flex
                    )
                    reset_user_data()
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="操作を取り消しました。")
                    )
                    sys.exit()
        except LineBotApiError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="LINEIDが確認できませんでした。この機能にはLINEIDが必要です。")
            )
            sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        try:
            if message == "顧問権限の切り替え申請":
                update(event.source.user_id, "action_type",
                       "requesting_auth_komon")
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="顧問権限申請", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="部長に顧問権限を申請します。氏名（スペース不要）を入力してください。", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="氏名（スペース不要）を入力してください。", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="やめる", text="やめる"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "requesting_auth_komon":
                if message == "やめる":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="申請を取り消しました。")
                    )
                    sys.exit()
                else:
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", idbucho)
                        task = client.get(key)
                        task["action_type"] = "requested_auth_by_komon"
                        task["komon_name"] = message
                        task["managing_id"] = event.source.user_id
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text='顧問権限を申請しました',
                                              weight='bold', size='xl'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text='部長に顧問権限を申請しました。お待ちください。',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text='部長に顧問権限を申請しました。お待ちください。', contents=bubble)
                    line_bot_api.reply_message(
                        event.reply_token, flex
                    )

                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text='顧問権限が申請されました',
                                              weight='bold', size='xl', wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text=message + '先生が顧問権限を申請しました。\n承認しますか？',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text='部長権限が付与されました。', contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="承認", text="承認")),
                                QuickReplyButton(
                                    action=MessageAction(label="拒否", text="拒否"))
                            ],
                        )
                    )
                    line_bot_api.push_message(
                        idbucho, flex
                    )
                    reset_user_data()
                    sys.exit()
            elif userdata["action_type"] == "requested_auth_by_komon":
                if message == "承認":
                    managing_id = userdata["managing_id"]
                    managing_name = userdata["komon_name"] + "先生（顧問）"
                    managing_list = [managing_id, managing_name]
                    update("AuthUsers", "komon", managing_list)
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text="顧問権限を付与しました",
                                              weight='bold', size='xl', wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text=userdata["komon_name"] + '先生に顧問権限を付与しました。',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=userdata["komon_name"] + '先生に顧問権限を付与しました。', contents=bubble)
                    line_bot_api.reply_message(
                        event.reply_token, flex
                    )

                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text='顧問権限が付与されました',
                                              weight='bold', size='xl', wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text='ようこそ。顧問権限が付与されました。',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text='顧問権限が付与されました。', contents=bubble)
                    line_bot_api.push_message(
                        managing_id, flex
                    )
                    reset_user_data()
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="申請を拒否しました。")
                    )
                    sys.exit()

        except LineBotApiError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="LINEIDが確認できませんでした。この機能にはLINEIDが必要です。")
            )
            sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        if message == "最新の参加部員情報を表示":
            try:
                reset_user_data()
            except:
                pass
            try:
                latestdatestr = str(get("MembersList")["LatestDate"])
                latestdate = datetime(year=int(latestdatestr[:4]), month=int(
                    latestdatestr[5:7]), day=int(latestdatestr[8:10]))
                latestdate = latestdate.strftime("%-Y年%-m月%-d日")
                MembersList = ast.literal_eval(
                    str(get("MembersList")[latestdatestr]))
                membersint = str(len(MembersList))
                membersstr = str()
                for i in MembersList:
                    membersstr = membersstr + i + "\n"
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(text="活動記録", size='sm'),
                            TextComponent(
                                text=latestdate + "\n参加部員（ドームのみ）", weight='bold', size='xl', wrap=True, adjustMode='shrink-to-fit'),
                            TextComponent(text="\n"),
                            TextComponent(text=membersstr, wrap=True),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"),
                            TextComponent(
                                text="計" + membersint + "名", weight="bold", color="#7D7D7D"),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text=latestdate + "の参加部員を表示しています。", contents=bubble)
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
            except SystemExit:
                sys.exit()
            except:
                pass

        if message == "活動記録閲覧":
            try:
                reset_user_data()
            except:
                pass
            try:
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["action_type"] = "view_note"
                    client.put(task)
                global tempdate
                tempdate = datetime.today()
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="記録閲覧モード", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="閲覧したい記録の日付を選択してください。\n\nこちらより記録済みの日付が確認できます。", wrap=True),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    TextComponent(
                                        "https://bit.ly/3z9ObNA", color="#0043bf", action=URIAction(uri="https://bit.ly/3z9ObNA"))
                                ]
                            )
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="記録閲覧モードに入りました。", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=DatetimePickerAction(label='日付を選択',
                                                            data='date_postback',
                                                            mode='date')),
                            QuickReplyButton(
                                action=MessageAction(label="最新の記録", text="最新")),
                            QuickReplyButton(
                                action=MessageAction(label="終了する", text="終了"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
            except SystemExit:
                sys.exit()
            except:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEIDが確認できませんでした。この機能にはLINEIDが必要です。")
                )
                sys.exit()
        try:
            if userdata["action_type"] == "view_note":
                if message[:4].isnumeric() and (message[4:5] == "-") and message[5:7].isnumeric() and (message[7:8] == "-") and message[8:10].isnumeric() and (len(message) == 10):
                    try:
                        acnote = ast.literal_eval(get("Notes")["Notes"])
                        notebook = acnote[str(message)]
                        view_note_date = str(message)
                        kedate = datetime(year=int(view_note_date[:4]), month=int(
                            view_note_date[5:7]), day=int(view_note_date[8:10]))
                        kestr = str(kedate.strftime("%a"))
                        kedate = kedate.strftime("%-Y年%-m月%-d日")
                        if kestr == "Mon":
                            kestr = "[月]"
                        elif kestr == "Tue":
                            kestr = "[火]"
                        elif kestr == "Wed":
                            kestr = "[水]"
                        elif kestr == "Thu":
                            kestr = "[木]"
                        elif kestr == "Fri":
                            kestr = "[金]"
                        elif kestr == "Sat":
                            kestr = "[土]"
                        elif kestr == "Sun":
                            kestr = "[日]"
                        note = acnote = ast.literal_eval(get("Notes")["Notes"])
                        view_note_number = list(note.keys()).index(
                            str(message))
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", event.source.user_id)
                            task = client.get(key)
                            task["view_note_date"] = view_note_date
                            task["view_note_number"] = view_note_number
                            client.put(task)
                        ketime = notebook["activity_time"]
                        try:
                            kenumber = notebook["knumber"]
                        except:
                            try:
                                kenumber = ast.literal_eval(
                                    get("MembersList")[str(message)])
                                kenumber = "計{}名\n「参加部員を表示」をタップ".format(
                                    str(len(kenumber)))
                            except:
                                kenumber = "情報なし"
                        keactiv = notebook["activity_detail"]
                        kenote = notebook["activity_notice"]
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(text="活動記録", size='sm'),
                                    TextComponent(
                                        text=kedate + kestr, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="活動時間・天気：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=ketime, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="参加部員：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=kenumber, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="活動内容：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=keactiv, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="連絡事項：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=kenote, wrap=True)
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=kedate + kestr + "の活動記録を表示しています。", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="参加部員を表示", text="参加した部員を表示")),
                                    QuickReplyButton(
                                        action=PostbackAction(label="軌道計算", data="活動記録から軌道計算")),
                                    QuickReplyButton(
                                        action=DatetimePickerAction(label='日付を選択',
                                                                    data='date_postback',
                                                                    mode='date')),
                                    QuickReplyButton(
                                        action=MessageAction(label="終了する", text="終了")),
                                    QuickReplyButton(
                                        action=MessageAction(label="最新の記録", text="最新")),
                                    QuickReplyButton(
                                        action=MessageAction(label="前の記録", text="前")),
                                    QuickReplyButton(
                                        action=MessageAction(label="後の記録", text="後"))
                                ]
                            )
                        )
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                    except SystemExit:
                        sys.exit()
                    except:
                        try:
                            t = get("MembersList")[str(message)]
                            if len(ast.literal_eval(t)) != 0:
                                update(event.source.user_id,
                                       "view_note_date", str(message))
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(
                                        text="その日には記録されていませんが、参加部員の情報が存在します。", quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=MessageAction(label="参加部員を表示", text="参加した部員のみ表示")),
                                                QuickReplyButton(
                                                    action=MessageAction(label="終了する", text="終了"))
                                            ]
                                        )
                                    )
                                )
                                sys.exit()
                            else:
                                raise Exception
                        except SystemExit:
                            sys.exit()
                        except:
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(
                                    text="その日には記録されていません。\n閲覧モードはまだ実行中です。", quick_reply=QuickReply(
                                        items=[
                                            QuickReplyButton(
                                                action=DatetimePickerAction(label='日付を選択',
                                                                            data='date_postback',
                                                                            mode='date')),
                                            QuickReplyButton(
                                                action=MessageAction(label="終了する", text="終了")),
                                            QuickReplyButton(
                                                action=MessageAction(label="最新の記録", text="最新"))
                                        ]
                                    )
                                )
                            )
                            sys.exit()
                elif message == "参加した部員のみ表示":
                    try:
                        view_note_date = userdata["view_note_date"]
                        kedate = datetime(year=int(view_note_date[:4]), month=int(
                            view_note_date[5:7]), day=int(view_note_date[8:10]))
                        kedate = kedate.strftime("%-Y年%-m月%-d日")
                        MembersList = ast.literal_eval(
                            str(get("MembersList")[view_note_date]))
                        membersint = str(len(MembersList))
                        membersstr = str()
                        for i in MembersList:
                            membersstr = membersstr + i + "\n"
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(text="活動記録", size='sm'),
                                    TextComponent(
                                        text=kedate + "\n参加部員（ドームのみ）", weight='bold', size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(text=membersstr, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"),
                                    TextComponent(
                                        text="計" + membersint + "名", weight="bold", color="#7D7D7D"),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=kedate + "の参加部員を表示しています。", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="終了する", text="終了"))
                                ]
                            )
                        )
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                    except SystemExit:
                        sys.exit()
                    except:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="この日のID記録システムによる参加部員情報はありません。", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="終了する", text="終了")),
                                    ]
                                )
                            )
                        )
                        sys.exit()
                elif message == "最新":
                    note = ast.literal_eval(get("Notes")["Notes"])
                    notebook = list(note.items())[-1][1]
                    view_note_date = list(note.items())[-1][0]
                    view_note_number = list(
                        note.keys()).index(str(view_note_date))
                    kedate = datetime(year=int(view_note_date[:4]), month=int(
                        view_note_date[5:7]), day=int(view_note_date[8:10]))
                    kestr = str(kedate.strftime("%a"))
                    kedate = kedate.strftime("%-Y年%-m月%-d日")
                    if kestr == "Mon":
                        kestr = "[月]"
                    elif kestr == "Tue":
                        kestr = "[火]"
                    elif kestr == "Wed":
                        kestr = "[水]"
                    elif kestr == "Thu":
                        kestr = "[木]"
                    elif kestr == "Fri":
                        kestr = "[金]"
                    elif kestr == "Sat":
                        kestr = "[土]"
                    elif kestr == "Sun":
                        kestr = "[日]"
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["view_note_date"] = view_note_date
                        task["view_note_number"] = view_note_number
                        client.put(task)
                    ketime = notebook["activity_time"]
                    try:
                        kenumber = notebook["knumber"]
                    except:
                        try:
                            kenumber = ast.literal_eval(
                                get("MembersList")[str(view_note_date)])
                            kenumber = "計{}名\n「参加部員を表示」をタップ".format(
                                str(len(kenumber)))
                        except:
                            kenumber = "情報なし"
                    keactiv = notebook["activity_detail"]
                    kenote = notebook["activity_notice"]
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text="活動記録", size='sm'),
                                TextComponent(
                                    text=kedate + kestr, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(text="活動時間・天気：",
                                              weight="bold", color="#7D7D7D"),
                                TextComponent(text=ketime, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="参加部員：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenumber, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="活動内容：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=keactiv, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="連絡事項：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenote, wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=kedate + kestr + "の活動記録を表示しています。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="参加部員を表示", text="参加した部員を表示")),
                                QuickReplyButton(
                                    action=PostbackAction(label="軌道計算", data="活動記録から軌道計算")),
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='日付を選択',
                                                                data='date_postback',
                                                                mode='date')),
                                QuickReplyButton(
                                    action=MessageAction(label="終了する", text="終了")),
                                QuickReplyButton(
                                    action=MessageAction(label="前の記録", text="前"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif message == "参加した部員を表示":
                    try:
                        view_note_date = userdata["view_note_date"]
                        kedate = datetime(year=int(view_note_date[:4]), month=int(
                            view_note_date[5:7]), day=int(view_note_date[8:10]))
                        kedate = kedate.strftime("%-Y年%-m月%-d日")
                        MembersList = ast.literal_eval(
                            str(get("MembersList")[view_note_date]))
                        membersint = str(len(MembersList))
                        membersstr = str()
                        for i in MembersList:
                            membersstr = membersstr + i + "\n"
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(text="活動記録", size='sm'),
                                    TextComponent(
                                        text=kedate + "\n参加部員（ドームのみ）", weight='bold', size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(text=membersstr, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"),
                                    TextComponent(
                                        text="計" + membersint + "名", weight="bold", color="#7D7D7D"),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=kedate + "の参加部員を表示しています。", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="記録にもどる", text="記録にもどる")),
                                    QuickReplyButton(
                                        action=MessageAction(label="終了する", text="終了"))
                                ]
                            )
                        )
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                    except SystemExit:
                        sys.exit()
                    except:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="この日のID記録システムによる参加部員情報はありません。", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="記録にもどる", text="記録にもどる")),
                                        QuickReplyButton(
                                            action=MessageAction(label="終了する", text="終了"))
                                    ]
                                )
                            )
                        )
                        sys.exit()
                elif message == "記録にもどる":
                    view_note_number = int(
                        userdata["view_note_number"])
                    note = ast.literal_eval(get("Notes")["Notes"])
                    notebook = list(note.items())[
                        view_note_number][1]
                    view_note_date = list(note.items())[
                        view_note_number][0]
                    kedate = datetime(year=int(view_note_date[:4]), month=int(
                        view_note_date[5:7]), day=int(view_note_date[8:10]))
                    kestr = str(kedate.strftime("%a"))
                    kedate = kedate.strftime("%-Y年%-m月%-d日")
                    if kestr == "Mon":
                        kestr = "[月]"
                    elif kestr == "Tue":
                        kestr = "[火]"
                    elif kestr == "Wed":
                        kestr = "[水]"
                    elif kestr == "Thu":
                        kestr = "[木]"
                    elif kestr == "Fri":
                        kestr = "[金]"
                    elif kestr == "Sat":
                        kestr = "[土]"
                    elif kestr == "Sun":
                        kestr = "[日]"
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["view_note_date"] = view_note_date
                        task["view_note_number"] = view_note_number
                        client.put(task)
                    ketime = notebook["activity_time"]
                    try:
                        kenumber = notebook["knumber"]
                    except:
                        try:
                            kenumber = ast.literal_eval(
                                get("MembersList")[str(view_note_date)])
                            kenumber = "計{}名\n「参加部員を表示」をタップ".format(
                                str(len(kenumber)))
                        except:
                            kenumber = "情報なし"
                    keactiv = notebook["activity_detail"]
                    kenote = notebook["activity_notice"]
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text="活動記録", size='sm'),
                                TextComponent(
                                    text=kedate + kestr, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="活動時間・天気：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=ketime, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="参加部員：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenumber, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="活動内容：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=keactiv, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="連絡事項：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenote, wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=kedate + kestr + "の活動記録を表示しています。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="参加部員を表示", text="参加した部員を表示")),
                                QuickReplyButton(
                                    action=PostbackAction(label="軌道計算", data="活動記録から軌道計算")),
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='日付を選択',
                                                                data='date_postback',
                                                                mode='date')),
                                QuickReplyButton(
                                    action=MessageAction(label="終了する", text="終了")),
                                QuickReplyButton(
                                    action=MessageAction(label="最新の記録", text="最新")),
                                QuickReplyButton(
                                    action=MessageAction(label="前の記録", text="前")),
                                QuickReplyButton(
                                    action=MessageAction(label="後の記録", text="後"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif message == "終了":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="閲覧モードを終了しました。")
                    )
                    sys.exit()
                elif message == "いいえ":
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="問い合わせを取り消しました。閲覧モードはまだ続行中です。", quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='日付を選択',
                                        data='date_postback',
                                        mode='date')),
                                QuickReplyButton(
                                    action=MessageAction(label="終了する", text="終了")),
                                QuickReplyButton(
                                    action=MessageAction(label="最新の記録", text="最新"))
                            ])
                        )
                    )
                    sys.exit()

                if message == "前":
                    view_note_number = int(
                        userdata["view_note_number"])
                    view_note_number -= 1
                    if view_note_number < 0:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="今のが最初の記録です。これより前の記録はありません。\n（閲覧モードはまだ続行中です）", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=DatetimePickerAction(label='日付を選択',
                                                                        data='date_postback',
                                                                        mode='date')),
                                        QuickReplyButton(
                                            action=MessageAction(label="終了する", text="終了")),
                                        QuickReplyButton(
                                            action=MessageAction(label="最新の記録", text="最新")),
                                        QuickReplyButton(
                                            action=MessageAction(label="後の記録", text="後"))
                                    ]
                                )
                            )
                        )
                        sys.exit()
                    note = ast.literal_eval(get("Notes")["Notes"])
                    notebook = list(note.items())[
                        view_note_number][1]
                    view_note_date = list(note.items())[
                        view_note_number][0]
                    kedate = datetime(year=int(view_note_date[:4]), month=int(
                        view_note_date[5:7]), day=int(view_note_date[8:10]))
                    kestr = str(kedate.strftime("%a"))
                    kedate = kedate.strftime("%-Y年%-m月%-d日")
                    if kestr == "Mon":
                        kestr = "[月]"
                    elif kestr == "Tue":
                        kestr = "[火]"
                    elif kestr == "Wed":
                        kestr = "[水]"
                    elif kestr == "Thu":
                        kestr = "[木]"
                    elif kestr == "Fri":
                        kestr = "[金]"
                    elif kestr == "Sat":
                        kestr = "[土]"
                    elif kestr == "Sun":
                        kestr = "[日]"
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["view_note_date"] = view_note_date
                        task["view_note_number"] = view_note_number
                        client.put(task)
                    ketime = notebook["activity_time"]
                    try:
                        kenumber = notebook["knumber"]
                    except:
                        try:
                            kenumber = ast.literal_eval(
                                get("MembersList")[str(view_note_date)])
                            kenumber = "計{}名\n「参加部員を表示」をタップ".format(
                                str(len(kenumber)))
                        except:
                            kenumber = "情報なし"
                    keactiv = notebook["activity_detail"]
                    kenote = notebook["activity_notice"]
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(text="活動記録", size='sm'),
                                TextComponent(
                                    text=kedate + kestr, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="活動時間・天気：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=ketime, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="参加部員：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenumber, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="活動内容：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=keactiv, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="連絡事項：", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenote, wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=kedate + kestr + "の活動記録を表示しています。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="参加部員を表示", text="参加した部員を表示")),
                                QuickReplyButton(
                                    action=PostbackAction(label="軌道計算", data="活動記録から軌道計算")),
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='日付を選択',
                                                                data='date_postback',
                                                                mode='date')),
                                QuickReplyButton(
                                    action=MessageAction(label="終了する", text="終了")),
                                QuickReplyButton(
                                    action=MessageAction(label="最新の記録", text="最新")),
                                QuickReplyButton(
                                    action=MessageAction(label="前の記録", text="前")),
                                QuickReplyButton(
                                    action=MessageAction(label="後の記録", text="後"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif message == "後":
                    try:
                        view_note_number = int(userdata["view_note_number"])
                        view_note_number += 1
                        note = ast.literal_eval(get("Notes")["Notes"])
                        notebook = list(note.items())[
                            view_note_number][1]
                        view_note_date = list(note.items())[
                            view_note_number][0]
                        kedate = datetime(year=int(view_note_date[:4]), month=int(
                            view_note_date[5:7]), day=int(view_note_date[8:10]))
                        kestr = str(kedate.strftime("%a"))
                        kedate = kedate.strftime("%-Y年%-m月%-d日")
                        if kestr == "Mon":
                            kestr = "[月]"
                        elif kestr == "Tue":
                            kestr = "[火]"
                        elif kestr == "Wed":
                            kestr = "[水]"
                        elif kestr == "Thu":
                            kestr = "[木]"
                        elif kestr == "Fri":
                            kestr = "[金]"
                        elif kestr == "Sat":
                            kestr = "[土]"
                        elif kestr == "Sun":
                            kestr = "[日]"
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", event.source.user_id)
                            task = client.get(key)
                            task["view_note_date"] = view_note_date
                            task["view_note_number"] = view_note_number
                            client.put(task)
                        ketime = notebook["activity_time"]
                        try:
                            kenumber = notebook["knumber"]
                        except:
                            try:
                                kenumber = ast.literal_eval(
                                    get("MembersList")[str(view_note_date)])
                                kenumber = "計{}名\n「参加部員を表示」をタップ".format(
                                    str(len(kenumber)))
                            except:
                                kenumber = "情報なし"
                        keactiv = notebook["activity_detail"]
                        kenote = notebook["activity_notice"]
                        bubble = BubbleContainer(
                            direction='ltr',
                            hero=ImageComponent(
                                url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E6%B4%BB%E5%8B%95%E8%A8%98%E9%8C%B2.jpg',
                                size='full',
                                aspect_ratio='20:13',
                                aspect_mode='cover',
                            ),
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(text="活動記録", size='sm'),
                                    TextComponent(
                                        text=kedate + kestr, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="活動時間・天気：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=ketime, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="参加部員：", weight="bold", color="#7D7D7D"),
                                    TextComponent(
                                        text=kenumber, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="活動内容：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=keactiv, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="連絡事項：", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=kenote, wrap=True)
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=kedate + kestr + "の活動記録を表示しています。", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="参加部員を表示", text="参加した部員を表示")),
                                    QuickReplyButton(
                                        action=PostbackAction(label="軌道計算", data="活動記録から軌道計算")),
                                    QuickReplyButton(
                                        action=DatetimePickerAction(label='日付を選択',
                                                                    data='date_postback',
                                                                    mode='date')),
                                    QuickReplyButton(
                                        action=MessageAction(label="終了する", text="終了")),
                                    QuickReplyButton(
                                        action=MessageAction(label="最新の記録", text="最新")),
                                    QuickReplyButton(
                                        action=MessageAction(label="前の記録", text="前")),
                                    QuickReplyButton(
                                        action=MessageAction(label="後の記録", text="後"))
                                ]
                            )
                        )
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                    except SystemExit:
                        sys.exit()
                    except:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="これが最新の記録です。これより後の記録はありません。\n（閲覧モードはまだ続行中です）", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=DatetimePickerAction(label='日付を選択',
                                                                        data='date_postback',
                                                                        mode='date')),
                                        QuickReplyButton(
                                            action=MessageAction(label="終了する", text="終了")),
                                        QuickReplyButton(
                                            action=MessageAction(label="最新の記録", text="最新")),
                                        QuickReplyButton(
                                            action=MessageAction(label="前の記録", text="前"))
                                    ]
                                )
                            )
                        )
                        sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="表記が正しくありません。閲覧モードを終了します。")
                    )
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        try:
            if (userdata["action_type"] == "calculation_orbit_observable") or (userdata["action_type"] == "calculation_orbit_all_information") or (userdata["action_type"] == "calculation_orbit_sun&moon_information"):
                if message == "終了する":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="太陽・月軌計算モードを終了しました。")
                    )
                    sys.exit()
        except LineBotApiError:
            pass
        except KeyError:
            pass

        if message == "軌道計算":
            try:
                reset_user_data()
            except:
                pass
            try:
                update(event.source.user_id, "action_type",
                       "calculation_orbit_observable")
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/%E8%BB%8C%E9%81%93%E8%A8%88%E7%AE%97.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="太陽・月軌道計算モード", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="指定時間と指定日に観測できる天体を計算することができます。\nまず、日時を選択してください。", wrap=True),
                            TextComponent(text="\n"),
                            SeparatorComponent(),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(text="月の出時間に出た月の南中、入り時間を計算していますので、\nこれらは翌日の時間が表示されることがあります。", size='sm', wrap=True
                                          )
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="まず、日時を選択してください。", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=DatetimePickerAction(label='日時を選択',
                                                            data='datetime_postback',
                                                            mode='datetime')),
                            QuickReplyButton(
                                action=PostbackAction(label='現在', data='ephemnow')),
                            QuickReplyButton(
                                action=MessageAction(label="終了する", text="終了する")),
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
            except SystemExit:
                sys.exit()
            except:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEIDが確認できませんでした。この機能にはLINEIDが必要です。")
                )
                sys.exit()

        opemanual = re.search("マニュアル|不具合|エラー", message)
        opedome = re.search("ドーム", message)
        opetelescope = re.search("望遠鏡", message)
        opecamera = re.search("カメラ", message)

        queshowmoon = re.search("月", message) and re.search(
            "情報|状態|インフォ", message)
        queshowsun = re.search("太陽", message) and re.search(
            "情報|状態|インフォ", message)
        questarvalue = re.search("ほしぞら|星空", message) and re.search(
            "指数|数値|具合", message)

        opesendai = re.search("仙台", message)
        opeizumi = re.search("泉区", message)
        opeaoba = re.search("青葉区", message)
        opemiyagino = re.search("宮城野区", message)
        opetaihaku = re.search("太白区", message)
        opewakaba = re.search("若林区", message)
        opetomiya = re.search("富谷", message)
        opetagajo = re.search("多賀城", message)
        opeshiroishi = re.search("白石", message)
        openatori = re.search("名取", message)

        opecnt3 = re.search("明明後日|明々後日|しあさって|4日|４日|四日", message)
        opecnt2 = re.search("明後日|あさって|3日|３日|三日", message)
        opecnt1 = re.search("明日|あした|2日|２日|二日", message)
        opecnt0 = re.search("今日|きょう", message)

        flag_weather_operation_weather = False
        weatherif = re.search("天気|てんき|天候|てんこう|気象", message)
        if weatherif:
            flag_weather_operation_weather = True
        else:
            flag_weather_operation_weather = False

        def setlocation(String, Id):
            global locflag, weather_location_name, weather_location_id
            locflag = True
            weather_location_name = String
            weather_location_id = Id

        if opeizumi:
            setlocation("宮城県仙台市泉区", "218979")
        elif opeaoba:
            setlocation("宮城県仙台市青葉区", "218962")
        elif opemiyagino:
            setlocation("宮城県仙台市宮城野区", "219001")
        elif opetaihaku:
            setlocation("宮城県仙台市太白区", "218963")
        elif opewakaba:
            setlocation("宮城県仙台市若林区", "219002")
        elif opesendai:
            setlocation("宮城県仙台市", "224683")
        elif opetomiya:
            setlocation("宮城県富谷市", "218974")
        elif opetagajo:
            setlocation("宮城県多賀城市", "218961")
        elif opeshiroishi:
            setlocation("宮城県白石市", "218990")
        elif openatori:
            setlocation("宮城県名取市", "218958")

        def settime(datecnt, datenum):
            global weather_month_of_date, weather_date_full_next_day, weather_date_full_previous_day, weather_date_full, weather_days_delta, dayflag, moon, sun
            dayflag = True
            weather_month_of_date = int(datecnt.strftime("%m"))
            weather_date_full_next_day = (datecnt +
                                          timedelta(days=1)).strftime("%d")
            weather_date_full_previous_day = (datecnt -
                                              timedelta(days=1)).strftime("%d")
            weather_date_full = datecnt.strftime("%-Y年%-m月%-d日")
            weather_days_delta = datenum

            global quickday
            if weather_days_delta == 0:
                weather_date_full = "今日(" + weather_date_full + ")"
                quickday = QuickReplyButton(
                    action=MessageAction(label="明日", text="じゃあ明日は？"))
            elif weather_days_delta == 1:
                weather_date_full = "明日(" + weather_date_full + ")"
                quickday = QuickReplyButton(
                    action=MessageAction(label="今日", text="じゃあ今日は？"))
            elif weather_days_delta == 2:
                weather_date_full = "あさって(" + weather_date_full + ")"
                quickday = QuickReplyButton(
                    action=MessageAction(label="今日", text="じゃあ今日は？"))
            elif weather_days_delta == 3:
                weather_date_full = "しあさって(" + weather_date_full + ")"
                quickday = QuickReplyButton(
                    action=MessageAction(label="今日", text="じゃあ今日は？"))

        if opecnt3:
            settime(datecnt4, 3)
        elif opecnt2:
            settime(datecnt3, 2)
        elif opecnt1:
            settime(datecnt2, 1)
        elif opecnt0:
            settime(datetoday, 0)

        if queshowmoon:
            flag_weather_operation_quesion = True
            weather_quesion = "weather_quesion_about_moon"
        elif queshowsun:
            flag_weather_operation_quesion = True
            weather_quesion = "weather_quesion_about_sun"
        elif questarvalue:
            flag_weather_operation_quesion = True
            weather_quesion = "weather_quesion_about_hoshizora"

        try:
            if (locflag) or (dayflag) or (flag_weather_operation_quesion) or flag_weather_operation_weather:
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    if locflag:
                        task["weather_location_name"] = weather_location_name
                        task["weather_location_id"] = weather_location_id
                    if dayflag:
                        task["weather_days_delta"] = weather_days_delta
                        task["weather_date_full"] = weather_date_full
                        task["weather_month_of_date"] = weather_month_of_date
                        task["weather_date_full_next_day"] = weather_date_full_next_day
                        task["weather_date_full_previous_day"] = weather_date_full_previous_day
                    if flag_weather_operation_quesion:
                        task["weather_quesion"] = weather_quesion
                        task["flag_weather_operation_quesion"] = flag_weather_operation_quesion
                        task["flag_weather_operation_weather"] = False
                    if flag_weather_operation_weather:
                        task["flag_weather_operation_quesion"] = False
                        task["flag_weather_operation_weather"] = True
                    client.put(task)
        except LineBotApiError:
            pass

        oriweaflag = False
        oriqueflag = False
        if flag_weather_operation_weather:
            oriweaflag = True
            oriqueflag = False
        elif flag_weather_operation_quesion:
            oriqueflag = True
            oriweaflag = False

        try:
            if locflag or dayflag or flag_weather_operation_quesion or flag_weather_operation_weather:
                if not flag_weather_operation_weather:
                    flag_weather_operation_weather = bool(
                        userdata["flag_weather_operation_weather"])
                if not locflag:
                    weather_location_name = str(
                        userdata["weather_location_name"])
                    weather_location_id = str(
                        userdata["weather_location_id"])
                    locflag = True
                if not dayflag:
                    weather_days_delta = int(userdata["weather_days_delta"])
                    weather_date_full = str(userdata["weather_date_full"])
                    weather_month_of_date = int(
                        userdata["weather_month_of_date"])
                    weather_date_full_next_day = str(
                        userdata["weather_date_full_next_day"])
                    weather_date_full_previous_day = str(
                        userdata["weather_date_full_previous_day"])
                    dayflag = True
                if not flag_weather_operation_quesion:
                    weather_quesion = str(userdata["weather_quesion"])
                    flag_weather_operation_quesion = bool(
                        userdata["flag_weather_operation_quesion"])
        except KeyError:
            pass
        except LineBotApiError:
            pass
        except TypeError:
            pass

        if flag_weather_operation_weather and flag_weather_operation_quesion:
            if oriweaflag:
                flag_weather_operation_weather = True
                flag_weather_operation_quesion = False
            elif oriqueflag:
                flag_weather_operation_quesion = True
                flag_weather_operation_weather = False

        if (not locflag) or (not dayflag) or (not flag_weather_operation_quesion):
            if not flag_weather_operation_weather:
                try:
                    reset_user_data()
                except LineBotApiError:
                    pass

        global quickday
        if weather_days_delta == 0:
            quickday = QuickReplyButton(
                action=MessageAction(label="明日", text="じゃあ明日は？"))
        elif weather_days_delta == 1:
            quickday = QuickReplyButton(
                action=MessageAction(label="今日", text="じゃあ今日は？"))
        elif weather_days_delta == 2:
            quickday = QuickReplyButton(
                action=MessageAction(label="今日", text="じゃあ今日は？"))
        elif weather_days_delta == 3:
            quickday = QuickReplyButton(
                action=MessageAction(label="今日", text="じゃあ今日は？"))

        if flag_weather_operation_weather or flag_weather_operation_quesion:
            try:
                update(event.source.user_id, "action_type", "None")
            except:
                pass
            rsdate = datetoday.replace(
                hour=0, minute=0, second=0, microsecond=0)
            rsdate = rsdate + timedelta(days=weather_days_delta)
            calculation_orbit_date = rsdate
            calculation_orbit_date = calculation_orbit_date - timedelta(days=1)
            calculation_orbit_date = calculation_orbit_date.replace(
                hour=15, minute=0, second=0, microsecond=0)
            tglocation.date = calculation_orbit_date
            moon.compute(tglocation)
            sun.compute(tglocation)
            moonrise = (tglocation.next_rising(moon)
                        ).datetime() + timedelta(hours=9)
            sunrise = (tglocation.next_rising(sun)
                       ).datetime() + timedelta(hours=9)
            sunset = (tglocation.next_setting(sun)
                      ).datetime() + timedelta(hours=9)
            suntransit = (tglocation.next_transit(
                sun)).datetime() + timedelta(hours=9)
            tglocation.date = calculation_orbit_date + timedelta(hours=17)
            moonage = round(tglocation.date -
                            ephem.previous_new_moon(tglocation.date), 1)
            cutmoonage = str(round(moonage))
            moonage = str(moonage)
            tglocation.date = calculation_orbit_date
            tglocation.date = tglocation.next_transit(sun)
            southsunalt = round(degrees(sun.alt), 1)
            tglocation.date = calculation_orbit_date
            tglocation.date = tglocation.next_rising(moon)
            moontransit = (tglocation.next_transit(
                moon)).datetime() + timedelta(hours=9)
            moonset = (tglocation.next_setting(moon)
                       ).datetime() + timedelta(hours=9)
            tglocation.date = tglocation.next_transit(moon)
            southmoonalt = round(degrees(moon.alt), 1)
            tglocation.date = calculation_orbit_date
            tglocation.date = tglocation.next_setting(sun)
            sunriseafterset = (tglocation.next_rising(
                sun)).datetime() + timedelta(hours=9)

            def timeFix(date):
                global rsdate
                deltaday = date - rsdate
                if date.second >= 30:
                    date = date + timedelta(minutes=1)
                kobun = date.strftime("%-H時%-M分")
                if deltaday.days == 1:
                    plus = "翌日,"
                    kobun = plus + kobun
                elif deltaday.days > 1:
                    plus = str(deltaday.days) + "日後,"
                    kobun = plus + kobun
                elif deltaday.days == -1:
                    plus = "前日,"
                    kobun = plus + kobun
                elif deltaday.days < -1:
                    plus = str(abs(deltaday.days)) + "日前,"
                    kobun = plus + kobun
                if kobun[-3:] == "時0分":
                    return kobun[:-2]
                else:
                    return kobun

            if timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage) == "観測不可":
                moon_visual = "観測不可"
            else:
                moon_visual = timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[
                                      0]) + "から\n" + timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[1]) + "まで観測可\n（天候による）"
            if weather_location_id == None or weather_days_delta == None:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="必要なデータが入力または保存されていません。(LINEID未設定者は「じゃあ～」構文が使えません。)")
                )
                sys.exit()

            dataloc = weather_location_name + "date"
            if datenow > (get("WeatherData")[dataloc] + timedelta(hours=2)):
                try:
                    try:
                        line_bot_api.push_message(
                            event.source.user_id, [
                                TextSendMessage(text="最新の天気予報を取得しています・・・"),
                            ]
                        )
                    except:
                        pass
                    import requests
                    url = "http://dataservice.accuweather.com/forecasts/v1/daily/5day/" + weather_location_id + \
                        "?apikey=" + str(os.environ["apikey"]) + \
                        "&language=ja-JP&details=true&metric=true"
                    weatherdata = requests.get(url)
                    connectionstatuscode = str(weatherdata.status_code)
                    if connectionstatuscode == "503":
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="API側で何らかのエラーが発生し、データが取得できませんでした。")
                        )
                        sys.exit()
                    weatherdata = weatherdata.json()
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", "WeatherData")
                        task = client.get(key)
                        task[weather_location_name] = str(weatherdata)
                        task[dataloc] = datenow
                        client.put(task)
                except:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="API側で何らかのエラーが発生し、データが取得できませんでした。")
                    )
                    sys.exit()

            weather_datajson = ast.literal_eval(
                get("WeatherData")[weather_location_name])

            tempunit = "°C"
            try:
                dataFixed = weather_datajson["DailyForecasts"][weather_days_delta]

                if cutmoonage == "0":
                    moonage = moonage + "（新月）"
                elif cutmoonage == "1":
                    moonage = moonage + "（繊月）"
                elif cutmoonage == "2":
                    moonage = moonage + "（三日月）"
                elif cutmoonage == "7":
                    moonage = moonage + "（上限）"
                elif cutmoonage == "9":
                    moonage = moonage + "（十日夜月）"
                elif cutmoonage == "12":
                    moonage = moonage + "（十三夜月）"
                elif cutmoonage == "13":
                    moonage = moonage + "（小望月）"
                elif cutmoonage == "14":
                    moonage = moonage + "（満月）"
                elif cutmoonage == "15":
                    moonage = moonage + "（十六夜月）"
                elif cutmoonage == "16":
                    moonage = moonage + "（立待月）"
                elif cutmoonage == "17":
                    moonage = moonage + "（居待月）"
                elif cutmoonage == "18":
                    moonage = moonage + "（寝待月）"
                elif cutmoonage == "19":
                    moonage = moonage + "（更待月）"
                elif cutmoonage == "22":
                    moonage = moonage + "（下弦）"
                elif cutmoonage == "25":
                    moonage = moonage + "（有明月）"
                aboutemp = dataFixed["Temperature"]
                hightemp = str(aboutemp["Maximum"]["Value"])
                lowtemp = str(aboutemp["Minimum"]["Value"])
                hightempfloat = float(hightemp)
                lowtempfloat = float(lowtemp)
                averagetemp = (hightempfloat + lowtempfloat) / 2
                averagetempint = int(round(averagetemp, 1))
                averagetempstr = str(round(averagetemp, 1))
                aboutozonePollen = dataFixed["AirAndPollen"][0]
                ozoneValue = str(aboutozonePollen["Value"])
                ozoneValueint = int(ozoneValue)
                aboutdayforecast = dataFixed["Day"]
                dayphrase = str(aboutdayforecast["LongPhrase"])
                dayrainpro = str(aboutdayforecast["RainProbability"])
                daysnowpro = str(aboutdayforecast["SnowProbability"])
                aboutdaywind = aboutdayforecast["Wind"]
                daywindsp = str(aboutdaywind["Speed"]["Value"])
                daywinddir = str(aboutdaywind["Direction"]["Localized"])
                daycloudcover = str(aboutdayforecast["CloudCover"])
                aboutnightforecast = dataFixed["Night"]
                nightphrase = str(aboutnightforecast["LongPhrase"])
                nightrainpro = str(aboutnightforecast["RainProbability"])
                nightsnowpro = str(aboutnightforecast["SnowProbability"])
                aboutnightwind = aboutnightforecast["Wind"]
                nightwindsp = str(aboutnightwind["Speed"]["Value"])
                nightwinddir = str(aboutnightwind["Direction"]["Localized"])
                nightcloudcover = str(aboutnightforecast["CloudCover"])
                intnightcloud = int(nightcloudcover)
            except:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="AccuWeather APIに一部のデータが存在しませんでした。この日の情報を表示できません。")
                )
                sys.exit()

            averagetempintyes = averagetempint
            intnightcloudyes = intnightcloud
            ozoneValueintyes = ozoneValueint
            hoshizora = (averagetempintyes + 273) * \
                pow((intnightcloudyes + 273), 2) * (ozoneValueintyes + 273)
            hoshizora = (1 / hoshizora) * 60000000000
            hoshizora = round(hoshizora, 1)
            hoshizora = str(hoshizora)

            if (weather_month_of_date >= 3) and (weather_month_of_date <= 5):
                if averagetemp < 8:
                    temptext = "春の中でも寒い気温"
                elif (averagetemp >= 8) and (averagetemp < 17):
                    temptext = "春ならではの暖かさ"
                elif averagetemp >= 17:
                    temptext = "春の中でも暑い気温"
            elif (weather_month_of_date >= 6) and (weather_month_of_date <= 8):
                if averagetemp < 20:
                    temptext = "夏の中でも涼しい気温"
                elif (averagetemp >= 20) and (averagetemp < 32):
                    temptext = "夏ならではの暑さ"
                elif averagetemp >= 32:
                    temptext = "夏の中でも特に暑い気温"
            elif (weather_month_of_date >= 9) and (weather_month_of_date <= 11):
                if averagetemp < 9:
                    temptext = "秋の中でも寒い気温"
                elif (averagetemp >= 9) and (averagetemp < 15):
                    temptext = "秋ならではの涼しさ"
                elif averagetemp >= 15:
                    temptext = "秋の中でも暑い気温"
            elif (weather_month_of_date == 12) or (weather_month_of_date <= 2):
                if averagetemp < -3:
                    temptext = "冬の中でも特に寒い気温"
                elif (averagetemp >= -3) and (averagetemp < 11):
                    temptext = "冬ならではの寒さ"
                elif averagetemp >= 11:
                    temptext = "冬の中でも暖かい気温"
            global dayrain, daysnow, nightrain, nightsnow
            if dayrainpro == "0":
                if daysnowpro == "0":
                    daysnow = FillerComponent()
                    dayrain = FillerComponent()
                else:
                    daysnow = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="降雪確率：", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=daysnowpro + "%", flex=1, align="center", wrap=True), ])
                    dayrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="降水確率：", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=dayrainpro + "%", flex=1, align="center", wrap=True), ])
            else:
                if daysnowpro == "0":
                    daysnow = FillerComponent()
                    dayrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="降水確率：", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=dayrainpro + "%", flex=1, align="center", wrap=True), ])
                else:
                    daysnow = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="降雪確率：", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=daysnowpro + "%", flex=1, align="center", wrap=True), ])
                    dayrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="降水確率：", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=dayrainpro + "%", flex=1, align="center", wrap=True), ])

            if nightrainpro == "0":
                if nightsnowpro == "0":
                    nightsnow = FillerComponent()
                    nightrain = FillerComponent()
                else:
                    nightrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="降水確率：", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=nightrainpro + "%", flex=1, align="center", wrap=True), ])
                    nightsnow = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="降雪確率：", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=nightsnowpro + "%", flex=1, align="center", wrap=True), ])
            else:
                if nightsnowpro == "0":
                    nightsnow = FillerComponent()
                    nightrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="降水確率：", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=nightrainpro + "%", flex=1, align="center", wrap=True), ])
                else:
                    nightrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="降水確率：", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=nightrainpro + "%", flex=1, align="center", wrap=True), ])
                    nightsnow = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="降雪確率：", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=nightsnowpro + "%", flex=1, align="center", wrap=True), ])

            if flag_weather_operation_weather:
                thumbnail = ["t1", "t2", "t3", "t4", "t5", "t6", "t7"]
                thumbnail = random.choice(thumbnail)
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/' +
                            thumbnail + '.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text=weather_date_full, wrap=True, size="xxs", color="#7D7D7D", align="center", flex=1),
                                    TextComponent(
                                        text=weather_location_name, wrap=True, size="xxs", color="#7D7D7D", align="center", flex=1),
                                ]
                            ),
                            TextComponent(text="\n"),
                            SeparatorComponent(),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(text="夜間の天気", size='sm'),
                            TextComponent(text=nightphrase, weight='bold',
                                          size='xxl', wrap=True, adjustMode='shrink-to-fit'),
                            TextComponent(text="\n"),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="平均気温：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=averagetempstr + tempunit, flex=1, align="center", wrap=True),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="気温評価：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=temptext, flex=1, align="center", wrap=True),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="最高気温：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(text=hightemp + tempunit,
                                                  flex=1, align="center"),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="最低気温：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=lowtemp + tempunit, flex=1, align="center", wrap=True),
                                ]
                            ),
                            TextComponent(text="\n"),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="日中の天気：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=dayphrase, flex=1, wrap=True, align="center"),
                                ]
                            ),
                            dayrain,
                            daysnow,
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="雲の占有率：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=daycloudcover + "%", flex=1, wrap=True, align="center"),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="風向・風速：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=daywinddir + "・" + daywindsp + "m/s", flex=1, wrap=True, align="center"),
                                ]
                            ),
                            TextComponent(text="\n"),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="夜間の天気：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=nightphrase, flex=1, wrap=True, align="center"),
                                ]
                            ),
                            nightrain,
                            nightsnow,
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="雲の占有率：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=nightcloudcover + "%", flex=1, wrap=True, align="center"),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="風向・風速：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=nightwinddir + "・" + nightwindsp + "m/s", flex=1, wrap=True, align="center"),
                                ]
                            )
                        ]
                    )
                )
                flex = FlexSendMessage(
                    alt_text=weather_date_full + "の" + weather_location_name + "の天気予報を表示しています。", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=PostbackAction(label='自動入力', data='selectdate')),
                            quickday,
                            QuickReplyButton(
                                action=MessageAction(label="月情報", text="じゃあ月の情報は？"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif flag_weather_operation_quesion:
                if weather_quesion == "weather_quesion_about_moon":
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/' +
                                cutmoonage + '.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text=weather_date_full, wrap=True, size="xxs", color="#7D7D7D", align="center", flex=1),
                                        TextComponent(
                                            text=weather_location_name, wrap=True, size="xxs", color="#7D7D7D", align="center", flex=1),
                                    ]
                                ),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text="17時の月齢：", size='sm'),
                                TextComponent(text=moonage, weight='bold',
                                              size='3xl', wrap=True, adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="17時の月齢：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=moonage, flex=1, wrap=True, align="center"),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="月の出：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(moonrise), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="南中：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(moontransit), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="南中高度：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(text=str(southmoonalt) + "°",
                                                      flex=1, align="center"),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="月の入り：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(moonset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                TextComponent(
                                    text="月の観測：", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=moon_visual, align="center", wrap=True),
                            ]
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=weather_date_full + "の" + weather_location_name + "の月の情報を表示しています。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label='自動入力', data='selectdate')),
                                quickday,
                                QuickReplyButton(
                                    action=MessageAction(label="天気予報", text="じゃあ天気は？")),
                                QuickReplyButton(
                                    action=MessageAction(label="太陽情報", text="次は太陽の情報を教えて"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                if weather_quesion == "weather_quesion_about_sun":
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/Washohku/Sources/main/%E5%A4%AA%E9%99%BD%E6%83%85%E5%A0%B1.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text=weather_date_full, wrap=True, size="xxs", color="#7D7D7D", align="center", flex=1),
                                        TextComponent(
                                            text=weather_location_name, wrap=True, size="xxs", color="#7D7D7D", align="center", flex=1),
                                    ]
                                ),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text="日没：", size='sm'),
                                TextComponent(text=timeFix(sunset), weight='bold',
                                              size='3xl', wrap=True, adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="日の出：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(sunrise), flex=1, wrap=True, align="center"),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="南中：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(suntransit), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="南中高度：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(text=str(southsunalt) + "°",
                                                      flex=1, align="center"),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="日没：", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(sunset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                            ]
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=weather_date_full + "の" + weather_location_name + "の太陽の情報を表示しています。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label='自動入力', data='selectdate')),
                                quickday,
                                QuickReplyButton(
                                    action=MessageAction(label="月情報", text="じゃあ月の情報を教えて"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif weather_quesion == "weather_quesion_about_hoshizora":
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/Washohku/Sources/main/%E3%81%BB%E3%81%97%E3%81%9E%E3%82%89%E6%8C%87%E6%95%B0.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text=weather_date_full, wrap=True, size="xxs", color="#7D7D7D", align="center", flex=1),
                                        TextComponent(
                                            text=weather_location_name, wrap=True, size="xxs", color="#7D7D7D", align="center", flex=1),
                                    ]
                                ),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text="ほしぞら指数：", size='sm'),
                                TextComponent(text=hoshizora, weight='bold',
                                              size='3xl', wrap=True, adjustMode='shrink-to-fit'),
                            ]
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=weather_date_full + "の" + weather_location_name + "のほしぞら指数を表示しています。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label='自動入力', data='selectdate')),
                                quickday,
                                QuickReplyButton(
                                    action=MessageAction(label="月情報", text="じゃあ月の情報を教えて")),
                                QuickReplyButton(
                                    action=MessageAction(label="太陽情報", text="じゃあ太陽の情報は？")),
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

        if opemanual and opedome:
            try:
                reset_user_data()
            except:
                pass
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="配線の問題は、すべての電源を切り、コントローラの接続を外し、もう一度起動してみてください。\nドーム内の公式マニュアルです。\n\n\n"
                                "ドーム内の手段編マニュアルです。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkPESuU6Bc7-Bwbpg?e=hwWdAV\n\n"
                                "不具合が発生した際のマニュアルです。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkSOgArvp_HKRuGZg?e=3oqveZ\n\n"
                                "ドーム環境の説明写真です。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJhjElqcc9aqk8jPoA?e=dZc7oo")
            )
            sys.exit()
        elif opemanual and opetelescope:
            try:
                reset_user_data()
            except:
                pass
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="望遠鏡の公式マニュアルです。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hMdJM8VjX0a1RgfuRw?e=hGfPX9\n\n"
                                "不具合が発生した際のマニュアルです。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkSOgArvp_HKRuGZg?e=3oqveZ\n\n"
                                "ドーム環境の説明写真です。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJhjElqcc9aqk8jPoA?e=dZc7oo")
            )
            sys.exit()
        elif opemanual and opecamera:
            try:
                reset_user_data()
            except:
                pass
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="観測用カメラの公式マニュアルです。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hMdJM8VjX0a1RgfuRw?e=iJSrGN\n\n"
                                "観測用カメラの手段編マニュアルです。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkQ_D6GWgydD0am4g?e=OBn4RC\n\n"
                                "不具合が発生した際のマニュアルです。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkSOgArvp_HKRuGZg?e=3oqveZ\n\n"
                                "ドーム環境の説明写真です。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJhjElqcc9aqk8jPoA?e=dZc7oo")
            )
            sys.exit()
        elif opemanual:
            try:
                reset_user_data()
            except:
                pass
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="公式マニュアルです。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hMdG0-dc8XFyY1xoTg?e=qOVAjK\n\n"
                                "手段編マニュアルです。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJh5BN4l2YXcmxT2Ww?e=kgnQWA\n\n"
                                "不具合が発生した際のマニュアルです。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkSOgArvp_HKRuGZg?e=3oqveZ\n\n"
                                "ドーム環境の説明写真です。\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJhjElqcc9aqk8jPoA?e=dZc7oo")
            )
            sys.exit()

        if message == "AOP確認":
            try:
                reset_user_data()
            except:
                pass
            try:
                datapoint = get("Points")
                datapointid = get("PointsID")
                pointsdat = ast.literal_eval(
                    datapoint[datapointid[event.source.user_id]])
                season = datapoint["シーズン"]
                userpoints = str(pointsdat["Points"])
                userattendance = str(pointsdat["Attendance"])
                userattendance = userattendance + "回"
                userpercentage = str(pointsdat["Percentage"])
                userpercentage = userpercentage.replace(".0", "")
                userpercentage = userpercentage + "%"
                useraddition = str(pointsdat["Addition"])
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text=datapointid[event.source.user_id][7:], wrap=True, size="xxs", color="#7D7D7D", align="center", flex=1),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            SeparatorComponent(),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(
                                text="保有AOP：", wrap=True),
                            TextComponent(
                                contents=[
                                    SpanComponent(
                                        text="{}P".format(userpoints), size="3xl", weight="bold",
                                    ),
                                    SpanComponent(
                                        text="(+{})".format(useraddition), weight="bold", size="md", color="#7D7D7D")
                                ]
                            ),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="シーズン{}\n参加回数".format(season), wrap=True, size="sm", align="center", flex=1),
                                    TextComponent(
                                        text="シーズン{}\n参加率".format(season), wrap=True, size="sm", align="center", flex=1),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text=userattendance, wrap=True, size="xxl", color="#7D7D7D", weight="bold", align="center", flex=1),
                                    TextComponent(
                                        text=userpercentage, wrap=True, size="xxl", color="#7D7D7D", weight="bold", align="center", flex=1),
                                ]
                            ),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="保有AOPを表示しています。", contents=bubble
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
            except SystemExit:
                sys.exit()
            except:
                update(event.source.user_id,
                       "action_type", "registering_member")
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/SkyRadiaCloud.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="部員登録", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="部員登録を行います。\n学年・クラス・番号・名前を入力してください。\n以下の表記（g-c(nn)name）で入力してください。\n例：1-A(01)学院太郎\n4-1(01)学院太郎", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="部員登録は部員一人につき一アカウントのみとなります。必ず自分を登録するようにしてください。", size="xs", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="部員登録を行います。", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="やめる", text="やめる"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
        try:
            if userdata["action_type"] == "registering_member":
                if message == "やめる":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="部員登録を取り消しました。")
                    )
                    sys.exit()
                try:
                    search = ast.literal_eval(get("Points")[message])
                    if search["Registered"]:
                        reset_user_data()
                        bubble = BubbleContainer(
                            direction='ltr',
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(
                                        text="登録できません", weight="bold", size="xl", wrap=True),
                                    TextComponent("\n"),
                                    TextComponent(
                                        text="この部員は既に別のLINEアカウントで登録されているため、登録することはできません。", wrap=True),
                                    TextComponent(
                                        text="他のアカウントへの心当たりがない場合は、他人があなたで部員登録をしている可能性があります。三宅まで連絡してください。", size="sm", wrap=True
                                    )
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="登録できません", contents=bubble)
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                    else:
                        pointsda = ast.literal_eval(get("Points")[message])
                        pointsda["Registered"] = True
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", "Points")
                            task = client.get(key)
                            task[message] = str(pointsda)
                            client.put(task)
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", "PointsID")
                            task = client.get(key)
                            task[event.source.user_id] = message
                            client.put(task)
                        bubble = BubbleContainer(
                            direction='ltr',
                            body=BoxComponent(
                                layout='vertical',
                                contents=[
                                    TextComponent(
                                        text="登録しました", weight="bold", size="xl", wrap=True),
                                    TextComponent("\n"),
                                    TextComponent(
                                        text="このアカウントを{}さんとして登録しました。".format(message[7:]), wrap=True)
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="登録できません", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="AOP確認", text="AOP確認"))
                                ]
                            )
                        )
                        line_bot_api.reply_message(event.reply_token, flex)
                        reset_user_data()
                        sys.exit()
                except SystemExit:
                    sys.exit()
                except:
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="登録できません", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="{}は部員名簿にありません。\n表記、字を確認し、最初からやり直してください。".format(message), wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="登録できません", contents=bubble)
                    line_bot_api.reply_message(event.reply_token, flex)
                    reset_user_data()
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        if message[:9] == "簡易メッセージ送信":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="部長にメッセージを送信しました。")
            )
            line_bot_api.push_message(
                idmappi, [
                    TextSendMessage(text="新着メッセージ：" + message[8:]),
                ]
            )
            sys.exit()

        try:
            reset_user_data()
        except:
            pass

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="語句エラーが発生しました。\n入力文字をお確かめください。")
        )
        sys.exit()

    except SystemExit:
        pass

    except:
        errormessage = str(traceback.format_exc().replace(
            "Traceback (most recent call last)", "エラーメッセージ"))
        line_bot_api.push_message(
            idmappi, [
                TextSendMessage(text="ユーザーのエラーが発生しました。\n\n" + errormessage),
            ]
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="致命的システムエラー（レッドクラス）が発生しました。データベースにエラーメッセージを送信しました。")
        )


@handler.add(PostbackEvent)
def handle_postback(event):
    def reset_user_data():
        userdata = get(event.source.user_id)
        reset_dict = {
            "action_type": "None",
            "schedule": userdata["schedule"],
            "line_user_name": line_bot_api.get_profile(event.source.user_id).display_name
        }
        upsert(event.source.user_id, reset_dict)
    try:
        userdata = get(event.source.user_id)
    except LineBotApiError:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="LINEIDが確認できませんでした。")
        )

    try:
        if event.postback.data == "既読する":
            try:
                member_real_name = get("PointsID")[event.source.user_id]
                message_read = ast.literal_eval(get("Notes")["Message_Read"])
                if not (member_real_name in message_read):
                    message_read.append(member_real_name)

                    def grade(s):
                        return s[0:1]

                    def classes(s):
                        return s[2:3]

                    def number(s):
                        return s[4:6]
                    message_read = sorted(message_read, key=number)
                    message_read = sorted(message_read, key=classes)
                    message_read = sorted(message_read, key=grade)
                    update("Notes", "Message_Read", str(message_read))
                    member_points_data = ast.literal_eval(
                        get("Points")[member_real_name])
                    member_points_data["Points"] = member_points_data["Points"] + 3
                    member_points_data["Addition"] = 3
                    update("Points", member_real_name, str(member_points_data))
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="既読しました。(AOP+3P)")
                    )
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="既に既読しています(既に既に読んでいますだと?)")
                    )
                    sys.exit()
            except SystemExit:
                sys.exit()
            except:
                try:
                    message_read = ast.literal_eval(
                        get("Notes")["Message_Read"])
                    message_read.append(line_bot_api.get_profile(
                        event.source.user_id).display_name)
                    def grade(s):
                        return s[0:1]

                    def classes(s):
                        return s[2:3]

                    def number(s):
                        return s[4:6]
                    message_read = sorted(message_read, key=number)
                    message_read = sorted(message_read, key=classes)
                    message_read = sorted(message_read, key=grade)
                    update("Notes", "Message_Read", str(message_read))
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="既読しましたが、AOP加算はありませんでした。")
                    )
                    sys.exit()
                except:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="既読できませんでした。")
                    )
                    sys.exit()
    except:
        pass

    try:
        if event.postback.data == 'date_postback' and userdata["action_type"] == "view_note":
            viewdatemessage = event.postback.params['date']
            confirm_template = ConfirmTemplate(text='この日の活動記録を問い合わせますか？', actions=[
                MessageAction(label='はい', text=viewdatemessage),
                MessageAction(label='いいえ', text='いいえ'),
            ])
            template_message = TemplateSendMessage(
                alt_text='この日の活動記録を問い合わせますか？', template=confirm_template)
            line_bot_api.reply_message(event.reply_token, template_message)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == 'date_postback') and (userdata["action_type"] == "write_note"):
            viewdatemessage = event.postback.params['date']
            confirm_template = ConfirmTemplate(text='この日として送信しますか？', actions=[
                MessageAction(label='はい', text=viewdatemessage),
                MessageAction(label='いいえ', text='いいえ'),
            ])
            template_message = TemplateSendMessage(
                alt_text='この日として送信しますか？', template=confirm_template)
            line_bot_api.reply_message(event.reply_token, template_message)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "date_postback") and (userdata["action_type"] == "register_activity"):
            viewdatemessage = event.postback.params['date']
            confirm_template = ConfirmTemplate(text='この日として送信しますか？', actions=[
                MessageAction(label='はい', text=viewdatemessage),
                MessageAction(label='いいえ', text='いいえ'),
            ])
            template_message = TemplateSendMessage(
                alt_text='この日として送信しますか？', template=confirm_template)
            line_bot_api.reply_message(event.reply_token, template_message)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "time_postback") and (userdata["action_type"] == "write_note_start_time"):
            try:
                viewtimemessage = event.postback.params['time']
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["action_type"] = "write_note_end_time"
                    task["write_note_activity_started_time"] = viewtimemessage
                    client.put(task)
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="活動終了時刻を選択", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="次に、この日の活動終了時刻を選択してください。", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="活動終了時刻を選択してください。", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=DatetimePickerAction(label='終了時刻を選択',
                                                            data='time_postback',
                                                            mode='time')),
                            QuickReplyButton(
                                action=MessageAction(label="取り消し", text="取り消し"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEIDが確認できませんでした。")
                )
                sys.exit()
    except:
        pass

    try:
        if event.postback.data == "time_postback" and userdata["action_type"] == "write_note_end_time":
            try:
                viewtimemessage = event.postback.params['time']
                minxstart = int(userdata["write_note_activity_started_time"][:2]) * \
                    60 + int(userdata["write_note_activity_started_time"][3:6])
                minxend = int(viewtimemessage[:2]) * \
                    60 + int(viewtimemessage[3:6])
                if minxend < minxstart:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="開始時刻より早い時刻を記録しようとしています。\n最初からやり直してください。")
                    )
                    sys.exit()
                write_note_activity_span = minxend - minxstart
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["action_type"] = "write_note_weather"
                    task["write_note_activity_ended_time"] = viewtimemessage
                    task["write_note_activity_span"] = str(
                        write_note_activity_span)
                    client.put(task)
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="それでは、この日の天気を選択してください。", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='晴れ', data='晴れ'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='曇り', data='曇り'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='雨', data='雨'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='雪', data='雪'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='その他天気', data='その他天気'),
                            ),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="天気を選択してください。", contents=bubble)
                line_bot_api.reply_message(
                    event.reply_token, flex)
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEIDが確認できませんでした。"))
                sys.exit()
    except:
        pass

    try:
        if event.postback.data == "time_postback" and userdata["action_type"] == "register_activity_start_time":
            try:
                register_activity_start_time = event.postback.params['time']
                if userdata["register_activity_observe_or_not"] == "あり(悪天中止)":
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["action_type"] = "register_activity_observation_end_time"
                        task["register_activity_start_time"] = register_activity_start_time
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="活動終了予定時刻\n(観測あり)を選択", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="次に、この日に観測がある場合の活動終了予定時刻を選択してください。", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="活動終了予定時刻を選択してください。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='終了予定時刻を選択',
                                                                data='time_postback',
                                                                mode='time'))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    client = datastore.Client()
                    with client.transaction():
                        key = client.key("Task", event.source.user_id)
                        task = client.get(key)
                        task["action_type"] = "register_activity_end_time"
                        task["register_activity_start_time"] = register_activity_start_time
                        client.put(task)
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="活動終了予定時刻を選択", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="次に、この日の活動終了予定時刻を選択してください。", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="活動終了予定時刻を選択してください。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='終了予定時刻を選択',
                                                                data='time_postback',
                                                                mode='time'))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEIDが確認できませんでした。")
                )
                sys.exit()
    except:
        pass

    try:
        if event.postback.data == "time_postback" and userdata["action_type"] == "register_activity_observation_end_time":
            try:
                register_activity_observation_end_time = event.postback.params['time']
                minxstart = int(userdata["register_activity_start_time"][:2]) * \
                    60 + int(userdata["register_activity_start_time"][3:6])
                minxend = int(register_activity_observation_end_time[:2]) * \
                    60 + int(register_activity_observation_end_time[3:6])
                if minxend < minxstart:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="開始時刻より早い時刻を記録しようとしています。\n最初からやり直してください。")
                    )
                    sys.exit()
                register_activity_observation_time_span = minxend - minxstart
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["action_type"] = "register_activity_end_time"
                    task["register_activity_observation_end_time"] = register_activity_observation_end_time
                    task["register_activity_observation_time_span"] = str(
                        register_activity_observation_time_span)
                    client.put(task)
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="活動終了予定時刻\n(観測なし)を選択", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="次に、この日に観測がなくなった場合の活動終了予定時刻を選択してください。", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="活動終了予定時刻を選択してください。", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=DatetimePickerAction(label='終了予定時刻を選択',
                                                            data='time_postback',
                                                            mode='time'))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEIDが確認できませんでした。"))
                sys.exit()
    except:
        pass

    try:
        if event.postback.data == "time_postback" and userdata["action_type"] == "register_activity_end_time":
            try:
                register_activity_end_time = event.postback.params['time']
                minxstart = int(userdata["register_activity_start_time"][:2]) * \
                    60 + int(userdata["register_activity_start_time"][3:6])
                minxend = int(register_activity_end_time[:2]) * \
                    60 + int(register_activity_end_time[3:6])
                if minxend < minxstart:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="開始時刻より早い時刻を記録しようとしています。\n最初からやり直してください。")
                    )
                    sys.exit()
                register_activity_time_span = minxend - minxstart
                client = datastore.Client()
                with client.transaction():
                    key = client.key("Task", event.source.user_id)
                    task = client.get(key)
                    task["action_type"] = "register_activity_ended"
                    task["register_activity_end_time"] = register_activity_end_time
                    task["register_activity_time_span"] = str(
                        register_activity_time_span)
                    client.put(task)
                confirm_template = ConfirmTemplate(text='情報を確定してください。', actions=[
                    MessageAction(label='確定', text="情報を確定"),
                    MessageAction(label='やめる', text="取り消し"),
                ])
                template_message = TemplateSendMessage(
                    alt_text='情報を確定してください。', template=confirm_template)
                line_bot_api.reply_message(event.reply_token, template_message)
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEIDが確認できませんでした。"))
                sys.exit()
    except:
        pass

    try:
        if (((event.postback.data == "datetime_postback") or (event.postback.data == "ephemnow") or (event.postback.data == "観測可能天体情報") or (event.postback.data == "太陽・月の詳細情報") or (event.postback.data == "出・入り情報") or (event.postback.data == "plus_one_minute") or (event.postback.data == "plus_one_hour") or (event.postback.data == "plus_one_day") or (event.postback.data == "back_to_info")) and ((userdata["action_type"] == "calculation_orbit_observable") or (userdata["action_type"] == "calculation_orbit_sun&moon_information") or (userdata["action_type"] == "calculation_orbit_all_information") or (userdata["action_type"] == "view_note"))) or ((event.postback.data == "活動記録から軌道計算") and userdata["action_type"] == "view_note"):
            ephem_center_date = str()
            if event.postback.data == "ephemnow":
                datetoday = datetime.now() + timedelta(hours=9)
                ephem_center_date = datetoday.strftime("%Y-%m-%dT%H:%M")
            elif event.postback.data == "datetime_postback":
                ephem_center_date = event.postback.params['datetime']
            elif event.postback.data == "back_to_info":
                ephem_center_date = userdata["calculation_orbit_date"]
            elif event.postback.data == "観測可能天体情報":
                if userdata["action_type"] == "view_note":
                    ephem_center_date = userdata["calculation_orbit_date"]
                else:
                    userdata["action_type"] = "calculation_orbit_observable"
                    update(event.source.user_id, "action_type",
                           "calculation_orbit_observable")
                    ephem_center_date = userdata["calculation_orbit_date"]
            elif event.postback.data == "太陽・月の詳細情報":
                if userdata["action_type"] == "view_note":
                    ephem_center_date = userdata["calculation_orbit_date"]
                else:
                    userdata["action_type"] = "calculation_orbit_sun&moon_information"
                    update(event.source.user_id, "action_type",
                           "calculation_orbit_sun&moon_information")
                    ephem_center_date = userdata["calculation_orbit_date"]
            elif event.postback.data == "出・入り情報":
                if userdata["action_type"] == "view_note":
                    ephem_center_date = userdata["calculation_orbit_date"]
                else:
                    userdata["action_type"] = "calculation_orbit_all_information"
                    update(event.source.user_id, "action_type",
                           "calculation_orbit_all_information")
                    ephem_center_date = userdata["calculation_orbit_date"]
            elif event.postback.data == "plus_one_minute":
                ephem_center_date = (datetime.strptime(
                    userdata["calculation_orbit_date"], "%Y-%m-%dT%H:%M") + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M")
            elif event.postback.data == "plus_one_hour":
                ephem_center_date = (datetime.strptime(
                    userdata["calculation_orbit_date"], "%Y-%m-%dT%H:%M") + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
            elif event.postback.data == "plus_one_day":
                ephem_center_date = (datetime.strptime(
                    userdata["calculation_orbit_date"], "%Y-%m-%dT%H:%M") + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
            elif event.postback.data == "活動記録から軌道計算":
                calculate_note_date = userdata["view_note_date"]
                notebook = get("Notes")
                notebook = ast.literal_eval(notebook["Notes"])
                calculate_note_time = notebook[calculate_note_date]["activity_time"]
                calculate_note_time = calculate_note_time[:5]
                ephem_center_date = calculate_note_date + "T" + calculate_note_time
            client = datastore.Client()
            with client.transaction():
                key = client.key("Task", event.source.user_id)
                task = client.get(key)
                task["calculation_orbit_date"] = ephem_center_date
                client.put(task)
            date_and_time = datetime.strptime(
                ephem_center_date, "%Y-%m-%dT%H:%M").strftime("%-Y年%-m月%-d日 %-H時%-M分")
            if date_and_time[-3:] == "時0分":
                date_and_time = date_and_time[:-2]
            tglocation.date = ephemdatenow = datetime.strptime(
                ephem_center_date, "%Y-%m-%dT%H:%M")
            tglocation.date = tglocation.date.datetime() - timedelta(hours=9)
            moon.compute(tglocation)
            sun.compute(tglocation)
            moment_sunaz = round(degrees(sun.az), 1)
            moment_sunalt = round(degrees(sun.alt), 1)
            moment_nextsunrise = (tglocation.next_rising(
                sun)).datetime() + timedelta(hours=9)
            moment_nextsunset = (tglocation.next_setting(
                sun)).datetime() + timedelta(hours=9)
            delta_sunrise = moment_nextsunrise - ephemdatenow
            delta_sunset = moment_nextsunset - ephemdatenow
            min_delta_sun = min(delta_sunrise, delta_sunset)
            min_string_sun = str()
            if min_delta_sun == delta_sunrise:
                min_string_sun = "日の出"
            elif min_delta_sun == delta_sunset:
                min_string_sun = "日没"
            moment_moonaz = round(degrees(moon.az), 1)
            moment_moonalt = round(degrees(moon.alt), 1)
            moment_moonage = round(
                tglocation.date - ephem.previous_new_moon(tglocation.date), 1)
            moment_moonage_round = str(round(moment_moonage))
            moment_moonage = str(moment_moonage)
            if moment_moonage_round == "0":
                moment_moonage = moment_moonage + "（新月）"
            elif moment_moonage_round == "1":
                moment_moonage = moment_moonage + "（繊月）"
            elif moment_moonage_round == "2":
                moment_moonage = moment_moonage + "（三日月）"
            elif moment_moonage_round == "7":
                moment_moonage = moment_moonage + "（上限）"
            elif moment_moonage_round == "9":
                moment_moonage = moment_moonage + "（十日夜月）"
            elif moment_moonage_round == "12":
                moment_moonage = moment_moonage + "（十三夜月）"
            elif moment_moonage_round == "13":
                moment_moonage = moment_moonage + "（小望月）"
            elif moment_moonage_round == "14":
                moment_moonage = moment_moonage + "（満月）"
            elif moment_moonage_round == "15":
                moment_moonage = moment_moonage + "（十六夜月）"
            elif moment_moonage_round == "16":
                moment_moonage = moment_moonage + "（立待月）"
            elif moment_moonage_round == "17":
                moment_moonage = moment_moonage + "（居待月）"
            elif moment_moonage_round == "18":
                moment_moonage = moment_moonage + "（寝待月）"
            elif moment_moonage_round == "19":
                moment_moonage = moment_moonage + "（更待月）"
            elif moment_moonage_round == "22":
                moment_moonage = moment_moonage + "（下弦）"
            elif moment_moonage_round == "25":
                moment_moonage = moment_moonage + "（有明月）"
            moment_nextmoonrise = (tglocation.next_rising(
                moon)).datetime() + timedelta(hours=9)
            moment_nextmoonset = (tglocation.next_setting(
                moon)).datetime() + timedelta(hours=9)
            delta_moonrise = moment_nextmoonrise - ephemdatenow
            delta_moonset = moment_nextmoonset - ephemdatenow
            min_delta_moon = min(delta_moonrise, delta_moonset)
            min_string_moon = str()
            if min_delta_moon == delta_moonrise:
                min_string_moon = "月の出"
            elif min_delta_moon == delta_moonset:
                min_string_moon = "月の入り"
            rsdate = datetime.strptime(
                ephem_center_date, "%Y-%m-%dT%H:%M").replace(hour=0, minute=0, second=0, microsecond=0)
            calculation_orbit_date = rsdate
            calculation_orbit_date = calculation_orbit_date - timedelta(days=1)
            calculation_orbit_date = calculation_orbit_date.replace(
                hour=15, minute=0, second=0, microsecond=0)
            tglocation.date = calculation_orbit_date
            day_moonrise = (tglocation.next_rising(moon)
                            ).datetime() + timedelta(hours=9)
            day_sunrise = (tglocation.next_rising(
                sun)).datetime() + timedelta(hours=9)
            day_sunset = (tglocation.next_setting(
                sun)).datetime() + timedelta(hours=9)
            day_suntransit = (tglocation.next_transit(
                sun)).datetime() + timedelta(hours=9)
            tglocation.date = calculation_orbit_date
            tglocation.date = tglocation.next_transit(sun)
            day_southsunalt = round(degrees(sun.alt), 1)
            tglocation.date = calculation_orbit_date
            tglocation.date = tglocation.next_rising(moon)
            day_moontransit = (tglocation.next_transit(
                moon)).datetime() + timedelta(hours=9)
            day_moonset = (tglocation.next_setting(moon)
                           ).datetime() + timedelta(hours=9)
            tglocation.date = tglocation.next_transit(moon)
            day_southmoonalt = round(degrees(moon.alt), 1)
            tglocation.date = calculation_orbit_date
            tglocation.date = tglocation.next_setting(sun)
            day_sunriseafterset = (tglocation.next_rising(
                sun)).datetime() + timedelta(hours=9)
            tglocation.date = calculation_orbit_date + timedelta(hours=17)
            moonage = round(tglocation.date -
                            ephem.previous_new_moon(tglocation.date), 1)
            cutmoonage = str(round(moonage))

            def deltaFix(deltatime):
                seconds = deltatime.days * 86400 + deltatime.seconds
                hours, remainder = divmod(seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                if seconds >= 30:
                    minutes += 1
                kobun = "{0}時間{1}分".format(str(hours), str(minutes))
                if kobun[:3] == "0時間":
                    kobun = kobun[3:]
                return kobun

            def timeFix(date):
                deltaday = date - rsdate
                if date.second >= 30:
                    date = date + timedelta(minutes=1)
                kobun = date.strftime("%-H時%-M分")
                if deltaday.days == 1:
                    plus = "翌日,"
                    kobun = plus + kobun
                elif deltaday.days > 1:
                    plus = str(deltaday.days) + "日後,"
                    kobun = plus + kobun
                elif deltaday.days == -1:
                    plus = "前日,"
                    kobun = plus + kobun
                elif deltaday.days < -1:
                    plus = str(abs(deltaday.days)) + "日前,"
                    kobun = plus + kobun
                if kobun[-3:] == "時0分":
                    return kobun[:-2]
                else:
                    return kobun

            if ((event.postback.data == "出・入り情報") or (userdata["action_type"] == "calculation_orbit_all_information") or (event.postback.data == "観測可能天体情報") or (userdata["action_type"] == "calculation_orbit_observable") or (event.postback.data == "活動記録から軌道計算")):
                rsdate = datetime.strptime(
                    ephem_center_date, "%Y-%m-%dT%H:%M").replace(hour=0, minute=0, second=0, microsecond=0)
                calculation_orbit_date = rsdate
                calculation_orbit_date = calculation_orbit_date - \
                    timedelta(days=1)
                calculation_orbit_date = calculation_orbit_date.replace(
                    hour=15, minute=0, second=0, microsecond=0)
                tglocation.date = calculation_orbit_date
                mercury.compute(tglocation)
                venus.compute(tglocation)
                mars.compute(tglocation)
                jupiter.compute(tglocation)
                saturn.compute(tglocation)
                uranus.compute(tglocation)
                neptune.compute(tglocation)
                pluto.compute(tglocation)
                day_mercuryrise = (tglocation.next_rising(
                    mercury)).datetime() + timedelta(hours=9)
                tglocation.date = tglocation.next_rising(mercury)
                day_mercuryset = (tglocation.next_setting(
                    mercury)).datetime() + timedelta(hours=9)
                tglocation.date = calculation_orbit_date
                day_venusrise = (tglocation.next_rising(
                    venus)).datetime() + timedelta(hours=9)
                tglocation.date = tglocation.next_rising(venus)
                day_venusset = (tglocation.next_setting(
                    venus)).datetime() + timedelta(hours=9)
                tglocation.date = calculation_orbit_date
                day_marsrise = (tglocation.next_rising(
                    mars)).datetime() + timedelta(hours=9)
                tglocation.date = tglocation.next_rising(mars)
                day_marsset = (tglocation.next_setting(
                    mars)).datetime() + timedelta(hours=9)
                tglocation.date = calculation_orbit_date
                day_jupiterrise = (tglocation.next_rising(
                    jupiter)).datetime() + timedelta(hours=9)
                tglocation.date = tglocation.next_rising(jupiter)
                day_jupiterset = (tglocation.next_setting(
                    jupiter)).datetime() + timedelta(hours=9)
                tglocation.date = calculation_orbit_date
                day_saturnrise = (tglocation.next_rising(
                    saturn)).datetime() + timedelta(hours=9)
                tglocation.date = tglocation.next_rising(saturn)
                day_saturnset = (tglocation.next_setting(
                    saturn)).datetime() + timedelta(hours=9)
                day_uranusrise = (tglocation.next_rising(
                    uranus)).datetime() + timedelta(hours=9)
                tglocation.date = tglocation.next_rising(uranus)
                day_uranusset = (tglocation.next_setting(
                    uranus)).datetime() + timedelta(hours=9)
                tglocation.date = calculation_orbit_date
                day_neptunerise = (tglocation.next_rising(
                    neptune)).datetime() + timedelta(hours=9)
                tglocation.date = tglocation.next_rising(neptune)
                day_neptuneset = (tglocation.next_setting(
                    neptune)).datetime() + timedelta(hours=9)
                tglocation.date = calculation_orbit_date
                day_plutorise = (tglocation.next_rising(
                    pluto)).datetime() + timedelta(hours=9)
                tglocation.date = tglocation.next_rising(pluto)
                day_plutoset = (tglocation.next_setting(
                    pluto)).datetime() + timedelta(hours=9)
                tglocation.date = calculation_orbit_date

                now_sun_observe = FillerComponent()
                now_mercury_observe = FillerComponent()
                now_venus_observe = FillerComponent()
                now_moon_observe = FillerComponent()
                now_mars_observe = FillerComponent()
                now_jupiter_observe = FillerComponent()
                now_saturn_observe = FillerComponent()
                now_uranus_observe = FillerComponent()
                now_neptune_observe = FillerComponent()
                now_pluto_observe = FillerComponent()

                day_sun_observe = FillerComponent()
                day_mercury_observe = FillerComponent()
                day_venus_observe = FillerComponent()
                day_moon_observe = FillerComponent()
                day_mars_observe = FillerComponent()
                day_jupiter_observe = FillerComponent()
                day_saturn_observe = FillerComponent()
                day_uranus_observe = FillerComponent()
                day_neptune_observe = FillerComponent()
                day_pluto_observe = FillerComponent()

                sun_visual = timeFix(day_sunrise) + "から\n" + \
                    timeFix(day_sunset) + "まで観測可"
                day_sun_observe = BoxComponent(
                    layout="vertical",
                    contents=[
                        BoxComponent(
                            layout="vertical",
                            contents=[
                                FillerComponent()
                            ],
                            height="5px"
                        ),
                        TextComponent(
                            text="太陽", align="center", weight="bold", color="#7D7D7D"
                        ),
                        TextComponent(
                            text=sun_visual, align="center", wrap=True
                        )
                    ]
                )
                if is_now_can_observe(([day_sunrise, day_sunset]), ephemdatenow):
                    now_moon_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="太陽", align="center", weight="bold", color="#7D7D7D",),
                            TextComponent(
                                text=timeFix(day_sunset) + "まで観測可\n（あと" + deltaFix((day_sunset - ephemdatenow)) + "）", align="center", wrap=True)
                        ]
                    )
                change_thumbnail = False
                if timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage) == "観測不可":
                    moon_visual = "観測不可"
                else:
                    moon_visual = timeFix(timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage)[
                        0]) + "から\n" + timeFix(timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage)[1]) + "まで観測可"
                    day_moon_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="月", align="center", weight="bold", color="#7D7D7D"
                            ),
                            TextComponent(
                                text=moon_visual, align="center", wrap=True
                            )
                        ]
                    )
                    if is_now_can_observe(timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage), ephemdatenow):
                        change_thumbnail = True
                        now_moon_observe = BoxComponent(
                            layout="vertical",
                            contents=[
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(
                                    text="月", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage)[1]) + "まで観測可\n（あと" + deltaFix((timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage)[1] - ephemdatenow)) + "）\n月齢：" + str(moment_moonage), align="center", wrap=True)
                            ]
                        )

                if planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset) == "観測不可":
                    mercury_visual = "観測不可"
                else:
                    mercury_visual = timeFix(planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset)[
                        0]) + "から\n" + timeFix(planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset)[1]) + "まで観測可"
                    day_mercury_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="水星", align="center", weight="bold", color="#7D7D7D"
                            ),
                            TextComponent(
                                text=mercury_visual, align="center", wrap=True
                            )
                        ]
                    )
                    if is_now_can_observe(planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset), ephemdatenow):
                        now_mercury_observe = BoxComponent(
                            layout="vertical",
                            contents=[
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(
                                    text="水星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset)[1]) + "まで観測可\n（あと" + deltaFix((planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "）", align="center", wrap=True)
                            ]
                        )

                if planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset) == "観測不可":
                    venus_visual = "観測不可"
                else:
                    venus_visual = timeFix(planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset)[
                        0]) + "から\n" + timeFix(planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset)[1]) + "まで観測可"
                    day_venus_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="金星", align="center", weight="bold", color="#7D7D7D"
                            ),
                            TextComponent(
                                text=venus_visual, align="center", wrap=True
                            )
                        ]
                    )
                    if is_now_can_observe(planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset), ephemdatenow):
                        now_venus_observe = BoxComponent(
                            layout="vertical",
                            contents=[
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(
                                    text="金星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset)[1]) + "まで観測可\n（あと" + deltaFix((planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "）", align="center", wrap=True)
                            ]
                        )

                if planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset) == "観測不可":
                    mars_visual = "観測不可"
                else:
                    mars_visual = timeFix(planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset)[
                        0]) + "から\n" + timeFix(planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset)[1]) + "まで観測可"
                    day_mars_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="火星", align="center", weight="bold", color="#7D7D7D"
                            ),
                            TextComponent(
                                text=mars_visual, align="center", wrap=True
                            )
                        ]
                    )
                    if is_now_can_observe(planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset), ephemdatenow):
                        now_mars_observe = BoxComponent(
                            layout="vertical",
                            contents=[
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(
                                    text="火星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset)[1]) + "まで観測可\n（あと" + deltaFix((planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "）", align="center", wrap=True)
                            ]
                        )

                if planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset) == "観測不可":
                    jupiter_visual = "観測不可"
                else:
                    jupiter_visual = timeFix(planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset)[
                        0]) + "から\n" + timeFix(planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset)[1]) + "まで観測可"
                    day_jupiter_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="木星", align="center", weight="bold", color="#7D7D7D"
                            ),
                            TextComponent(
                                text=jupiter_visual, align="center", wrap=True
                            )
                        ]
                    )
                    if is_now_can_observe(planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset), ephemdatenow):
                        now_jupiter_observe = BoxComponent(
                            layout="vertical",
                            contents=[
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(
                                    text="木星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset)[1]) + "まで観測可\n（あと" + deltaFix((planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "）", align="center", wrap=True)
                            ]
                        )

                if planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset) == "観測不可":
                    saturn_visual = "観測不可"
                else:
                    saturn_visual = timeFix(planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset)[
                        0]) + "から\n" + timeFix(planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset)[1]) + "まで観測可"
                    day_saturn_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="土星", align="center", weight="bold", color="#7D7D7D"
                            ),
                            TextComponent(
                                text=saturn_visual, align="center", wrap=True
                            )
                        ]
                    )
                    if is_now_can_observe(planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset), ephemdatenow):
                        now_saturn_observe = BoxComponent(
                            layout="vertical",
                            contents=[
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(
                                    text="土星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset)[1]) + "まで観測可\n（あと" + deltaFix((planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "）", align="center", wrap=True)
                            ]
                        )
                if planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset) == "観測不可":
                    uranus_visual = "観測不可"
                else:
                    uranus_visual = timeFix(planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset)[
                        0]) + "から\n" + timeFix(planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset)[1]) + "まで観測可"
                    day_uranus_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="天王星", align="center", weight="bold", color="#7D7D7D"
                            ),
                            TextComponent(
                                text=uranus_visual, align="center", wrap=True
                            )
                        ]
                    )
                    if is_now_can_observe(planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset), ephemdatenow):
                        now_uranus_observe = BoxComponent(
                            layout="vertical",
                            contents=[
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(
                                    text="天王星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset)[1]) + "まで観測可\n（あと" + deltaFix((planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "）", align="center", wrap=True)
                            ]
                        )
                if planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset) == "観測不可":
                    neptune_visual = "観測不可"
                else:
                    neptune_visual = timeFix(planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset)[
                        0]) + "から\n" + timeFix(planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset)[1]) + "まで観測可"
                    day_neptune_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="海王星", align="center", weight="bold", color="#7D7D7D"
                            ),
                            TextComponent(
                                text=neptune_visual, align="center", wrap=True
                            )
                        ]
                    )
                    if is_now_can_observe(planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset), ephemdatenow):
                        now_neptune_observe = BoxComponent(
                            layout="vertical",
                            contents=[
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(
                                    text="海王星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset)[1]) + "まで観測可\n（あと" + deltaFix((planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "）", align="center", wrap=True)
                            ]
                        )
                if planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset) == "観測不可":
                    pluto_visual = "観測不可"
                else:
                    pluto_visual = timeFix(planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset)[
                        0]) + "から\n" + timeFix(planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset)[1]) + "まで観測可"
                    day_pluto_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="冥王星", align="center", weight="bold", color="#7D7D7D"
                            ),
                            TextComponent(
                                text=pluto_visual, align="center", wrap=True
                            )
                        ]
                    )
                    if is_now_can_observe(planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset), ephemdatenow):
                        now_pluto_observe = BoxComponent(
                            layout="vertical",
                            contents=[
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="5px"
                                ),
                                TextComponent(
                                    text="冥王星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset)[1]) + "まで観測可\n（あと" + deltaFix((planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "）", align="center", wrap=True)
                            ]
                        )

                if now_sun_observe == now_moon_observe == now_mercury_observe == now_venus_observe == now_mars_observe == now_jupiter_observe == now_saturn_observe == now_uranus_observe == now_neptune_observe == now_pluto_observe == FillerComponent():
                    now_sun_observe = BoxComponent(
                        layout="vertical",
                        contents=[
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="5px"
                            ),
                            TextComponent(
                                text="観測可能天体なし", align="center", wrap=True)
                        ]
                    )

                if change_thumbnail:
                    thumbnail = 'https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/' + \
                        cutmoonage + '.jpg'
                else:
                    thumbnail = 'https://raw.githubusercontent.com/Washohku/Sources/main/%E8%BB%8C%E9%81%93%E8%A8%88%E7%AE%97.jpg'

                if (event.postback.data == "出・入り情報") or (userdata["action_type"] == "calculation_orbit_all_information"):
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url='https://raw.githubusercontent.com/Washohku/Sources/main/%E8%BB%8C%E9%81%93%E8%A8%88%E7%AE%97.jpg',
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text=date_and_time, wrap=True, size="xxs", color="#7D7D7D", align="center"),
                                TextComponent(
                                    text="座標：学院天文ドーム", wrap=True, size="xxs", color="#7D7D7D", align="center"),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="出・入り時間", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                TextComponent(
                                    text="（出時間~入り時間）", size="sm", color="#7D7D7D", flex=1),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="太陽", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_sunrise) + "~" + timeFix(day_sunset), align="center", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="月", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_sunrise) + "~" + timeFix(day_moonset), align="center", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="水星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_mercuryrise) + "~" + timeFix(day_mercuryset), align="center", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="金星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_venusrise) + "~" + timeFix(day_venusset), align="center", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="火星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_marsrise) + "~" + timeFix(day_marsset), align="center", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="木星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_jupiterrise) + "~" + timeFix(day_jupiterset), align="center", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="土星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_saturnrise) + "~" + timeFix(day_saturnset), align="center", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="天王星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_uranusrise) + "~" + timeFix(day_uranusset), align="center", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="海王星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_neptunerise) + "~" + timeFix(day_neptuneset), align="center", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="冥王星", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_plutorise) + "~" + timeFix(day_plutoset), align="center", wrap=True),
                            ]
                        )
                    )
                    if userdata["action_type"] == "view_note":
                        all_data_flex = FlexSendMessage(
                            alt_text="計算結果を表示しています。", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label='記録にもどる', text='記録にもどる')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='観測可能天体情報', data='観測可能天体情報')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='太陽・月の詳細情報', data='太陽・月の詳細情報'))
                                ]
                            )
                        )

                    else:
                        all_data_flex = FlexSendMessage(
                            alt_text="計算結果を表示しています。", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=PostbackAction(label='観測可能天体情報', data='観測可能天体情報')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='太陽・月の詳細情報', data='太陽・月の詳細情報')),
                                    QuickReplyButton(
                                        action=DatetimePickerAction(label='日時を選択',
                                                                    data='datetime_postback',
                                                                    mode='datetime')),
                                    QuickReplyButton(
                                        action=MessageAction(label="終了する", text="終了する")),
                                    QuickReplyButton(
                                        action=PostbackAction(label='+1日', data='plus_one_day'))
                                ]
                            )
                        )
                    flex = all_data_flex
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

                elif (event.postback.data == "観測可能天体情報") or (userdata["action_type"] == "calculation_orbit_observable") or (event.postback.data == "活動記録から軌道計算"):
                    bubble = BubbleContainer(
                        direction='ltr',
                        hero=ImageComponent(
                            url=thumbnail,
                            size='full',
                            aspect_ratio='20:13',
                            aspect_mode='cover',
                        ),
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text=date_and_time, wrap=True, size="xxs", color="#7D7D7D", align="center"),
                                TextComponent(
                                    text="座標：学院天文ドーム", wrap=True, size="xxs", color="#7D7D7D", align="center"),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="この時間に観測可能", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                now_sun_observe,
                                now_moon_observe,
                                now_mercury_observe,
                                now_venus_observe,
                                now_mars_observe,
                                now_jupiter_observe,
                                now_saturn_observe,
                                now_uranus_observe,
                                now_neptune_observe,
                                now_pluto_observe,
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text="\n"),
                                TextComponent(text="この日に観測可能", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                day_sun_observe,
                                day_moon_observe,
                                day_mercury_observe,
                                day_venus_observe,
                                day_mars_observe,
                                day_jupiter_observe,
                                day_saturn_observe,
                                day_uranus_observe,
                                day_neptune_observe,
                                day_pluto_observe,
                            ]
                        )
                    )
                    if userdata["action_type"] == "view_note":
                        observable_flex = FlexSendMessage(
                            alt_text="計算結果を表示しています。", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label='記録にもどる', text='記録にもどる')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='太陽・月の詳細情報', data='太陽・月の詳細情報')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='出・入り情報', data='出・入り情報'))
                                ]
                            )
                        )
                    else:
                        observable_flex = FlexSendMessage(
                            alt_text="計算結果を表示しています。", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=PostbackAction(label='太陽・月の詳細情報', data='太陽・月の詳細情報')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='出・入り情報', data='出・入り情報')),
                                    QuickReplyButton(
                                        action=DatetimePickerAction(label='日時を選択',
                                                                    data='datetime_postback',
                                                                    mode='datetime')),
                                    QuickReplyButton(
                                        action=MessageAction(label="終了する", text="終了する")),
                                    QuickReplyButton(
                                        action=PostbackAction(label='+1分', data='plus_one_minute')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='+1時間', data='plus_one_hour')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='+1日', data='plus_one_day'))
                                ]
                            )
                        )
                    flex = observable_flex
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

            elif (event.postback.data == "太陽・月の詳細情報") or (userdata["action_type"] == "calculation_orbit_sun&moon_information"):
                bubble = BubbleContainer(
                    direction='ltr',
                    hero=ImageComponent(
                        url='https://raw.githubusercontent.com/Washohku/Sources/main/%E8%BB%8C%E9%81%93%E8%A8%88%E7%AE%97.jpg',
                        size='full',
                        aspect_ratio='20:13',
                        aspect_mode='cover',
                    ),
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text=date_and_time, wrap=True, size="xxs", color="#7D7D7D", align="center"),
                            TextComponent(
                                text="座標：学院天文ドーム", wrap=True, size="xxs", color="#7D7D7D", align="center"),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            SeparatorComponent(),
                            TextComponent(text="\n"),
                            TextComponent(text="この時間の情報", size="lg",
                                          weight="bold", color="#4A4A4A"),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="3px"
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="太陽方位：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(moment_sunaz) + "°", flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="太陽高度：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(moment_sunalt) + "°", flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text=min_string_sun + "まで：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=deltaFix(min_delta_sun), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="6px"
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="月方位：", weight="bold", color="#7D7D7D", flex=1
                                    ),
                                    TextComponent(
                                        text=str(moment_moonaz) + "°", flex=1, align="center", wrap=True
                                    )
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="月高度：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(moment_moonalt) + "°", flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="月齢：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=moment_moonage, flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text=min_string_moon + "まで：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=deltaFix(min_delta_moon), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(text="この日の情報", size="lg",
                                          weight="bold", color="#4A4A4A"),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="3px"
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="日の出：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_sunrise), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="太陽南中：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_suntransit), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="太陽南中高度：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(day_southsunalt) + "°", flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="日没：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_sunset), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="6px"
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="月の出：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_moonrise), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="月南中：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_moontransit), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="月南中高度：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(day_southmoonalt) + "°", flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="月の入り：", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_moonset), flex=1, align="center", wrap=True)
                                ]
                            ),
                        ]
                    )
                )
                if userdata["action_type"] == "view_note":
                    sun_moon_flex = FlexSendMessage(
                        alt_text="計算結果を表示しています。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label='記録にもどる', text='記録にもどる')),
                                QuickReplyButton(
                                    action=PostbackAction(label='観測可能天体情報', data='観測可能天体情報')),
                                QuickReplyButton(
                                    action=PostbackAction(label='出・入り情報', data='出・入り情報'))
                            ]
                        )
                    )
                else:
                    sun_moon_flex = FlexSendMessage(
                        alt_text="計算結果を表示しています。", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label='観測可能天体情報', data='観測可能天体情報')),
                                QuickReplyButton(
                                    action=PostbackAction(label='出・入り情報', data='出・入り情報')),
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='日時を選択',
                                                                data='datetime_postback',
                                                                mode='datetime')),
                                QuickReplyButton(
                                    action=MessageAction(label="終了する", text="終了する")),
                                QuickReplyButton(
                                    action=PostbackAction(label='+1分', data='plus_one_minute')),
                                QuickReplyButton(
                                    action=PostbackAction(label='+1時間', data='plus_one_hour')),
                                QuickReplyButton(
                                    action=PostbackAction(label='+1日', data='plus_one_day'))
                            ]
                        )
                    )
                flex = sun_moon_flex
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "晴れ" or event.postback.data == "曇り" or event.postback.data == "雨" or event.postback.data == "雪" or event.postback.data == "その他天気") and userdata["action_type"] == "write_note_weather":
            client = datastore.Client()
            with client.transaction():
                key = client.key("Task", event.source.user_id)
                task = client.get(key)
                task["action_type"] = "write_note_weather_check"
                task["write_note_weather"] = event.postback.data
                client.put(task)
            confirm_template = ConfirmTemplate(text='活動時間と天気を確定しますか？', actions=[
                MessageAction(label='はい', text="活動時間・天気の確定"),
                MessageAction(label='いいえ', text='いいえ'),
            ])
            template_message = TemplateSendMessage(
                alt_text='活動時間と天気を入力しますか？', template=confirm_template)
            line_bot_api.reply_message(event.reply_token, template_message)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "太陽" or event.postback.data == "月" or event.postback.data == "金星" or event.postback.data == "火星" or event.postback.data == "木星" or event.postback.data == "土星" or event.postback.data == "その他天体") and userdata["action_type"] == "write_note_planets":
            plslist = ast.literal_eval(userdata["write_note_observed_planets"])
            plslist.append(event.postback.data)
            client = datastore.Client()
            with client.transaction():
                key = client.key("Task", event.source.user_id)
                task = client.get(key)
                task["write_note_observed_planets"] = str(plslist)
                task["flag_write_note_observed"] = True
                client.put(task)
            bubble = BubbleContainer(
                direction='ltr',
                body=BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(
                            text="続けてひとつずつ選択してください。選択が完了したら「完了」を選択してください。", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='完了', data='完了', text="完了"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='太陽', data='太陽', text="太陽"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='月', data='月', text="月"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='金星', data='金星', text="金星"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='火星', data='火星', text="火星"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='木星', data='木星', text="木星"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='土星', data='土星', text="土星"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='その他天体', data='その他天体', text="その他天体")
                        ),
                    ],
                )
            )
            flex = FlexSendMessage(
                alt_text="観測した天体を選択してください。", contents=bubble)
            line_bot_api.reply_message(
                event.reply_token, flex)
            sys.exit()
    except:
        pass

    try:
        if event.postback.data == "完了" and userdata["action_type"] == "write_note_planets":
            plslist = ast.literal_eval(userdata["write_note_observed_planets"])
            plslist = list(dict.fromkeys(plslist))
            motherlist = ["太陽", "月", "金星", "火星", "木星", "土星", "その他天体"]
            plslist = listsort(plslist, motherlist)
            client = datastore.Client()
            with client.transaction():
                key = client.key("Task", event.source.user_id)
                task = client.get(key)
                task["write_note_observed_planets"] = str(plslist)
                client.put(task)
            confirm_template = ConfirmTemplate(text='情報を確定してください。', actions=[
                MessageAction(label='確定', text="観測あり"),
                MessageAction(label='やめる', text="取り消し"),
            ])
            template_message = TemplateSendMessage(
                alt_text='情報を確定してください。', template=confirm_template)
            line_bot_api.reply_message(event.reply_token, template_message)
            sys.exit()
    except:
        pass

    try:
        if event.postback.data == "selectdate":
            try:
                update(event.source.user_id,
                       "action_type", "weather_auto_input")
                bubble = BubbleContainer(
                    direction='ltr',
                    body=BoxComponent(
                        layout='vertical',
                        contents=[
                            TextComponent(
                                text="指定の情報を表示します。\nまず、日にちを選択してください。", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='今日', data='今日'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='明日', data='明日'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='あさって', data='あさって'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='しあさって', data='しあさって'),
                            ),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="まず、日にちを選択してください。", contents=bubble)
                line_bot_api.reply_message(
                    event.reply_token, flex)
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEIDが確認できませんでした。")
                )
                sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "今日" or event.postback.data == "明日" or event.postback.data == "あさって" or event.postback.data == "しあさって") and (userdata["action_type"] == "weather_auto_input"):
            client = datastore.Client()
            with client.transaction():
                key = client.key("Task", event.source.user_id)
                task = client.get(key)
                task["weather_auto_input_day"] = event.postback.data
                task["action_type"] = "weather_auto_input_location"
                client.put(task)
            bubble = BubbleContainer(
                direction='ltr',
                body=BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(
                            text="次に、地域を選択してください。", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(label='仙台市全域', data='仙台市'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='仙台市泉区', data='泉区'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='仙台市青葉区', data='青葉区'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='仙台市宮城野区', data='宮城野区'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='仙台市太白区', data='太白区'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='仙台市若林区', data='若林区'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='富谷市', data='富谷'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='多賀城市', data='多賀城'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='名取市', data='名取'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='白石市', data='白石'),
                        ),

                    ],
                )
            )
            flex = FlexSendMessage(alt_text="次に、地域を選択してください。", contents=bubble)
            line_bot_api.reply_message(
                event.reply_token, flex)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "仙台市" or event.postback.data == "泉区" or event.postback.data == "青葉区" or event.postback.data == "宮城野区" or event.postback.data == "太白区" or event.postback.data == "若林区" or event.postback.data == "富谷" or event.postback.data == "多賀城" or event.postback.data == "名取" or event.postback.data == "白石") and (userdata["action_type"] == "weather_auto_input_location"):
            client = datastore.Client()
            with client.transaction():
                key = client.key("Task", event.source.user_id)
                task = client.get(key)
                task["weather_auto_input_location"] = event.postback.data
                task["action_type"] = "weather_auto_input_information"
                client.put(task)
            bubble = BubbleContainer(
                direction='ltr',
                body=BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(
                            text="最後に、知りたい情報を選択してください。", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(label='天気', data='天気'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='ほしぞら指数', data='ほしぞら指数'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(label='月情報', data='月の情報'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(label='太陽情報', data='太陽の情報'),
                        )
                    ],
                )
            )
            flex = FlexSendMessage(
                alt_text="最後に、知りたい情報を選択してください。", contents=bubble)
            line_bot_api.reply_message(
                event.reply_token, flex)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "天気" or event.postback.data == "ほしぞら指数" or event.postback.data == "月の情報" or event.postback.data == "太陽の情報") and (userdata["action_type"] == "weather_auto_input_information"):
            weather_auto_input_day = userdata["weather_auto_input_day"]
            weather_auto_input_location = userdata["weather_auto_input_location"]
            weather_auto_input_information = event.postback.data
            reset_user_data()
            confirm_template = ConfirmTemplate(text='自動入力の内容：\n「' + weather_auto_input_day + "の" + weather_auto_input_location + "の" + weather_auto_input_information + "は？」\n\nこれを送信しますか？", actions=[
                MessageAction(label='はい', text=weather_auto_input_day + "の" +
                              weather_auto_input_location + "の" + weather_auto_input_information + "は？"),
                PostbackAction(label='いいえ', data='いいえ'),
            ])
            template_message = TemplateSendMessage(
                alt_text='自動入力を送信しますか？', template=confirm_template)
            line_bot_api.reply_message(event.reply_token, template_message)
            sys.exit()
    except:
        pass

    try:
        if event.postback.data == "いいえ":
            reset_user_data()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="自動入力を取り消しました。")
            )
            sys.exit()
    except:
        pass


if __name__ == "__main__":
    app.run()
