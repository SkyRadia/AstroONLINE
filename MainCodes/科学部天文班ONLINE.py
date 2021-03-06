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
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?????????????????]))"
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
        return "????????????"
    if three >= one:
        if three >= two:
            return "????????????"
        elif two >= four:
            return [three, four]
        elif four >= two:
            return [three, two]
    elif one >= three:
        if one >= four:
            return "????????????"
        elif four >= two:
            return [one, two]
        elif two >= four:
            return [one, four]
        else:
            return "????????????"
    else:
        return "????????????"


def planet_timespan(one, two, three, four):
    if three >= one:
        if three >= two:
            return "????????????"
        elif two >= four:
            return [three, four]
        elif four >= two:
            return [three, two]
    elif one >= three:
        if one >= four:
            return "????????????"
        elif four >= two:
            return [one, two]
        elif two >= four:
            return [one, four]
        else:
            return "????????????"
    else:
        return "????????????"


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
        season = pointsdata["????????????"]
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
        pointsdata["????????????"] = season
        pointsdata["????????????"] = 0
        upsert("Points", pointsdata)
        activstat = get("ActiveStatistics")
        if activstat["??????????????????????????????????????????"]:
            for i in activstat:
                if i != "??????????????????????????????????????????":
                    activstat[i] = 0
                else:
                    activstat[i] = False
            upsert("ActiveStatistics", activstat)
        else:
            update("ActiveStatistics", "??????????????????????????????????????????", True)
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
        activc = int(pointsdata["????????????"] + 1)
        client = datastore.Client()
        with client.transaction():
            key = client.key("Task", "Points")
            task = client.get(key)
            task["????????????"] = activc
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
    activc = int(pointsdata["????????????"])
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
                TextComponent(text="??????????????????????????????????????????????????????",
                              size='xs', adjustMode='shrink-to-fit', wrap=True),
                TextComponent(text="???" + membersnumber + "?????????\n?????????????????????", weight='bold',
                              size='xl', adjustMode='shrink-to-fit', wrap=True),
                TextComponent(text="\n"),
                TextComponent(
                    text="?????????????????????????????????????????????????????????????????????", weight="bold", color="#979797", wrap=True)
            ],
        )
    )
    flex = FlexSendMessage(
        alt_text="?????????????????????" + membersnumber + "??????????????????????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
            items=[
                QuickReplyButton(
                    action=MessageAction(label="????????????", text="????????????????????????????????????"))
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
            next_act_date = next_act_date.strftime("%-Y???%-m???%-d???")
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
            if observe_or_not == "??????(????????????)":
                end = next_act_data["End_time"]
            elif observe_or_not == "??????(????????????)":
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
                        "   " + str(assign[i]) + "???"
                else:
                    time_list_number = time_list_number + "\n" + \
                        time_list[i] + "   " + str(assign[i]) + "???"
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
                                TextComponent(text=line_name + "?????????????????????????????????????????????",
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
                                            text="?????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=scheduled_time + "(" + str(period_time) + "??????)", flex=3, align="center", wrap=True)
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
                                            text="????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=str(members) + "???", flex=1, align="center", wrap=True)
                                    ]
                                ),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="??????????????????????????????????????????", contents=bubble
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
                        TextComponent(text="???????????????????????????????????????",
                                      size='xs', adjustMode='shrink-to-fit', wrap=True),
                        TextComponent(text="?????????????????????????????????????????????",
                                      size='xs', adjustMode='shrink-to-fit', wrap=True),
                        TextComponent(text=next_act_date, weight='bold',
                                      size='xxl', wrap=True, adjustMode='shrink-to-fit'),
                        TextComponent(text="??????????????????????????????????????????????????????????????????????????????????????????",
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
                alt_text="?????????????????????????????????????????????", contents=bubble
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
                    text="????????????????????????????????????????????????????????????????????????")
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
                                text="????????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="??????????????????????????????\n??????????????????????????????????????????????????????????????????\n??????????????????g-c(nn)name?????????????????????????????????\n1-A(01)????????????\n4-1(01)????????????\n4-???(01)????????????", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????", size="xs", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="?????????", text="?????????"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

        try:
            if userdata["action_type"] == "registering_member":
                if message == "?????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="???????????????????????????????????????")
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
                                        text="?????????????????????", weight="bold", size="xl", wrap=True),
                                    TextComponent("\n"),
                                    TextComponent(
                                        text="???????????????????????????LINE???????????????????????????????????????????????????????????????????????????????????????", wrap=True),
                                    TextComponent(
                                        text="??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????", size="sm", wrap=True
                                    )
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="?????????????????????", contents=bubble)
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
                                        text="??????????????????", weight="bold", size="xl", wrap=True),
                                    TextComponent("\n"),
                                    TextComponent(
                                        text="????????????????????????{}????????????????????????????????????".format(message[7:]), wrap=True)
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="?????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="AOP??????", text="AOP??????"))
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
                                    text="?????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="{}????????????????????????????????????\n?????????????????????????????????????????????????????????????????????".format(message), wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="?????????????????????", contents=bubble)
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
        datetodayFixed = datetoday.strftime("%-Y???%-m???%-d???")
        datetodayFixed = "??????(" + datetodayFixed + ")"
        datecnt2 = datetoday + timedelta(days=1)
        datecnt2Fixed = datecnt2.strftime("%-Y???%-m???%-d???")
        datecnt2Fixed = "??????(" + datecnt2Fixed + ")"
        datecnt3 = datetoday + timedelta(days=2)
        datecnt3Fixed = datecnt3.strftime("%-Y???%-m???%-d???")
        datecnt3Fixed = "????????????(" + datecnt3Fixed + ")"
        datecnt4 = datetoday + timedelta(days=3)
        datecnt4Fixed = datecnt4.strftime("%-Y???%-m???%-d???")
        datecnt4Fixed = "???????????????(" + datecnt4Fixed + ")"
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
                            text="????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()
            except SystemExit:
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="????????????????????????????????????????????????????????????????????????")
                )
                sys.exit()

        if message == "??????????????????????????????":
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
                        text="??????????????????????????????????????????????????????????????????????????????")
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
                            TextComponent(text="?????????????????????????????????",
                                          size='xs', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="??????????????????????????????", weight='bold',
                                          size='xl', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="?????????????????????????????????????????????????????????????????????8??????????????????????????????????????????????????????????????????\n\n????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="???????????????????????????????????????", contents=bubble
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif is_schedule_created and (event.source.user_id in idlist):
                next_act_date = next_act_data["Date"]
                next_act_date = datetime(year=int(next_act_date[:4]), month=int(
                    next_act_date[5:7]), day=int(next_act_date[8:10]))
                next_act_date = next_act_date.strftime("%-Y???%-m???%-d???")
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
                            TextComponent(text="?????????????????????????????????",
                                          size='xs', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="????????????",
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
                    alt_text="????????????????????????????????????", contents=bubble
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
                next_act_date = next_act_date.strftime("%-Y???%-m???%-d???")
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
                            TextComponent(text=name[7:] + "????????????????????????",
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
                                        text="?????????", weight="bold", color="#7D7D7D", flex=1),
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
                                        text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=scheduled_time + "(" + str(period_time) + "??????)", flex=3, align="center", wrap=True)
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
                                        text="????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                        text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(participants) + "???", flex=1, align="center", wrap=True)
                                ]
                            ),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="???????????????????????????????????????", contents=bubble
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
                            TextComponent(text="???????????????????????????????????????", weight='bold',
                                          size='xl', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="??????????????????8??????????????????????????????????????????????????????????????????????????????????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="???????????????????????????????????????", contents=bubble
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif (not is_schedule_created) and ((observe_or_not == "??????(????????????)") or (observe_or_not == "??????(????????????)")):
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
                            TextComponent(text="??????????????????????????????", weight='bold',
                                          size='xl', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="??????????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="????????????", text="????????????")),
                            QuickReplyButton(
                                action=MessageAction(label="???????????????", text="???????????????"))
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
                            TextComponent(text="????????????????????????????????????", weight='bold',
                                          size='xl', adjustMode='shrink-to-fit', wrap=True),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????\n????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="????????????", text="????????????")),
                            QuickReplyButton(
                                action=MessageAction(label="???????????????", text="???????????????"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

        try:
            if userdata["action_type"] == "participate_observation":
                if message == "????????????":
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
                                TextComponent(text="????????????????????????????????????", weight='bold',
                                              size='xl', adjustMode='shrink-to-fit', wrap=True),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="?????????????????????????????????????????????????????????8????????????????????????????????????", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="???????????????????????????????????????", contents=bubble
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    reset_user_data()
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="???????????????????????????????????????")
                    )
                    reset_user_data()
                    sys.exit()

            elif userdata["action_type"] == "participate_observation_late":
                if message == "????????????":
                    reset_user_data()
                    next_act_data = get("NextAct")
                    next_act_date = next_act_data["Date"]
                    next_act_date = datetime(year=int(next_act_date[:4]), month=int(
                        next_act_date[5:7]), day=int(next_act_date[8:10]))
                    next_act_date = next_act_date.strftime("%-Y???%-m???%-d???")
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
                        time_list_number = time_list_number.split("???")
                        time_list_number[index_number] = time_list_number[index_number][:-1] + str(
                            int(time_list_number[index_number][-1]) + 1)
                        time_list_number = "???".join(time_list_number)
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
                                    TextComponent(text="??????????????????????????????",
                                                  size='xs', adjustMode='shrink-to-fit', wrap=True),
                                    TextComponent(text=name[7:] + "????????????????????????",
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
                                                text="?????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=scheduled_time + "(" + str(period_time) + "??????)", flex=3, align="center", wrap=True)
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
                                                text="????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=str(participants) + "???", flex=1, align="center", wrap=True)
                                        ]
                                    ),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="??????????????????????????????", contents=bubble
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
                                    TextComponent(text=name[7:] + "???????????????????????????????????????", weight='bold',
                                                  size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text=name[7:] + "?????????" + scheduled_time + "???????????????????????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=name[7:] + "?????????" + scheduled_time + "???????????????????????????????????????", contents=bubble
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
                                    TextComponent(text='????????????????????????????????????',
                                                  weight='bold', size='xl'),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(text='????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????',
                                                  size='sm', adjustMode='shrink-to-fit'),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="????????????????????????????????????", contents=bubble)
                        line_bot_api.reply_message(
                            event.reply_token,
                            flex
                        )
                        sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="???????????????????????????????????????")
                    )
                    reset_user_data()
                    sys.exit()

        except SystemExit:
            sys.exit()
        except:
            errormessage = str(traceback.format_exc().replace(
                "Traceback (most recent call last)", "????????????????????????"))
            line_bot_api.push_message(
                idmappi, [
                    TextSendMessage(
                        text="????????????????????????????????????????????????\n\n" + errormessage),
                ]
            )

        if message == "???????????????":
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
                            TextComponent(text='???????????????????????????',
                                          weight='bold', size='xl'),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(text='??????????????????????????????????????????????????????',
                                          size='sm', adjustMode='shrink-to-fit'),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="??????????????????????????????????????????????????????", contents=bubble)
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
                activstr = "[???]"
            elif activstr == "Tue":
                activstr = "[???]"
            elif activstr == "Wed":
                activstr = "[???]"
            elif activstr == "Thu":
                activstr = "[???]"
            elif activstr == "Fri":
                activstr = "[???]"
            elif activstr == "Sat":
                activstr = "[???]"
            elif activstr == "Sun":
                activstr = "[???]"
            activsa = datetodaytemp - activdate
            activsa = int(activsa.days)
            activdate = str(int(activdate.strftime("%m"))) + \
                "???" + str(int(activdate.strftime("%d"))) + "???"
            activinfo = next_activity["Info"]
            if activsa == 0:
                activdate = "??????(" + activdate + activstr + ")"
            elif activsa == -1:
                activdate = "??????(" + activdate + activstr + ")"
            elif activsa == -2:
                activdate = "????????????(" + activdate + activstr + ")"
            elif activsa == -3:
                activdate = "???????????????(" + activdate + activstr + ")"
            else:
                activdate = activdate + activstr
            if len(activinfo) == 0:
                activinfo = "??????"

            activity_observe_or_not = next_activity["Observe_or_not"]
            activity_start_time = next_activity["Start_time"]
            activity_end_time = next_activity["End_time"]
            activity_time_span = next_activity["Span"]
            if activity_observe_or_not == "??????(????????????)":
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
                kobun = date.strftime("%-H???%-M???")
                if deltaday.days == 1:
                    plus = "??????,"
                    kobun = plus + kobun
                elif deltaday.days > 1:
                    plus = str(deltaday.days) + "??????,"
                    kobun = plus + kobun
                elif deltaday.days == -1:
                    plus = "??????,"
                    kobun = plus + kobun
                elif deltaday.days < -1:
                    plus = str(abs(deltaday.days)) + "??????,"
                    kobun = plus + kobun
                if kobun[-3:] == "???0???":
                    return kobun[:-2]
                else:
                    return kobun

            if timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage) == "????????????":
                moon_visual = "????????????"
            else:
                moon_visual = timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[
                                      0]) + "??????\n" + timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[1]) + "???????????????\n?????????????????????"

            if cutmoonage == "0":
                moonage = moonage + "????????????"
            elif cutmoonage == "1":
                moonage = moonage + "????????????"
            elif cutmoonage == "2":
                moonage = moonage + "???????????????"
            elif cutmoonage == "7":
                moonage = moonage + "????????????"
            elif cutmoonage == "9":
                moonage = moonage + "??????????????????"
            elif cutmoonage == "12":
                moonage = moonage + "??????????????????"
            elif cutmoonage == "13":
                moonage = moonage + "???????????????"
            elif cutmoonage == "14":
                moonage = moonage + "????????????"
            elif cutmoonage == "15":
                moonage = moonage + "??????????????????"
            elif cutmoonage == "16":
                moonage = moonage + "???????????????"
            elif cutmoonage == "17":
                moonage = moonage + "???????????????"
            elif cutmoonage == "18":
                moonage = moonage + "???????????????"
            elif cutmoonage == "19":
                moonage = moonage + "???????????????"
            elif cutmoonage == "22":
                moonage = moonage + "????????????"
            elif cutmoonage == "25":
                moonage = moonage + "???????????????"

            def normalreply():
                if activity_observe_or_not == "??????(????????????)":
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
                                TextComponent(text="??????????????????", size='sm'),
                                TextComponent(text=activdate, weight='bold',
                                              size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="??????????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=activinfo, wrap=True),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="???????????????", size="lg",
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
                                            text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                TextComponent(text="?????????????????????",
                                              weight="bold", color="#7D7D7D"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="?????????????????????", flex=1),
                                        TextComponent(
                                            text=activity_observation_end_time + "(" + activity_observation_time_span + "??????)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="?????????????????????", flex=1),
                                        TextComponent(
                                            text=activity_end_time + "(" + activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="???????????????", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="17???????????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=moonage, flex=1, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(text=timeFix(
                                            sunset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(text=timeFix(
                                            moonrise), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=timeFix(moonset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=moon_visual, align="center", wrap=True),
                                TextComponent(
                                    text="?????????????????????", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=observable_planets, align="center", wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="?????????????????????" + activdate + "??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="??????????????????????????????", text="??????????????????????????????"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif activity_observe_or_not == "??????":
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
                                TextComponent(text="??????????????????", size='sm'),
                                TextComponent(text=activdate, weight='bold',
                                              size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="??????????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=activinfo, wrap=True),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="???????????????", size="lg",
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
                                            text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=activity_end_time + "(" + activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="?????????????????????" + activdate + "??????????????????????????????", contents=bubble)
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
                                TextComponent(text="??????????????????", size='sm'),
                                TextComponent(text=activdate, weight='bold',
                                              size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="??????????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=activinfo, wrap=True),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="???????????????", size="lg",
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
                                            text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=activity_end_time + "(" + activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="???????????????", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="17???????????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=moonage, flex=1, align="center", wrap=True)
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(text=timeFix(
                                            sunset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(text=timeFix(
                                            moonrise), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=timeFix(moonset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=moon_visual, align="center", wrap=True),
                                TextComponent(
                                    text="?????????????????????", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=observable_planets, align="center", wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="?????????????????????" + activdate + "??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="??????????????????????????????", text="??????????????????????????????"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

            if activsa <= 0:
                try:
                    if datenow > (get("WeatherData")["??????????????????????????????date"] + timedelta(hours=2)):
                        try:
                            line_bot_api.push_message(
                                event.source.user_id, [
                                    TextSendMessage(text="??????????????????????????????????????????????????????"),
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
                            task["??????????????????????????????"] = str(weatherdata)
                            task["??????????????????????????????date"] = datenow
                            client.put(task)

                    weather_datajson = ast.literal_eval(
                        get("WeatherData")["??????????????????????????????"])

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

                    if activity_observe_or_not == "??????(????????????)":
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
                                    TextComponent(text="??????????????????", size='sm'),
                                    TextComponent(text=activdate, weight='bold',
                                                  size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="??????????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=activinfo, wrap=True),
                                    TextComponent(text="\n"),
                                    SeparatorComponent(),
                                    TextComponent(text="\n"),
                                    TextComponent(text="???????????????", size="lg",
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
                                                text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                        text="?????????????????????", weight="bold", color="#7D7D7D"),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="?????????????????????", flex=1),
                                            TextComponent(
                                                text=activity_observation_end_time + "(" + activity_observation_time_span + "??????)", flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="?????????????????????", flex=1),
                                            TextComponent(
                                                text=activity_end_time + "(" + activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    TextComponent(text="\n"),
                                    SeparatorComponent(),
                                    TextComponent(text="\n"),
                                    TextComponent(text="???????????????", size="lg",
                                                  weight="bold", color="#4A4A4A"),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="17???????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=moonage, flex=1, align="center")
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=hoshizora,
                                                          flex=1, align="center"),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=nightphrase, flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=averagetempstr + "???", flex=1, align="center"),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=timeFix(
                                                sunset), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=timeFix(
                                                moonrise), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=timeFix(moonset), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
                                    TextComponent(
                                        text=moon_visual, align="center", wrap=True),
                                    TextComponent(
                                        text="?????????????????????", weight="bold", color="#7D7D7D", wrap=True),
                                    TextComponent(
                                        text=observable_planets, align="center", wrap=True),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="?????????????????????" + activdate + "??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="??????????????????????????????", text="??????????????????????????????"))
                                ]
                            )
                        )
                        line_bot_api.reply_message(event.reply_token, flex)
                        sys.exit()
                    elif activity_observe_or_not == "??????":
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
                                    TextComponent(text="??????????????????", size='sm'),
                                    TextComponent(text=activdate, weight='bold',
                                                  size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="??????????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=activinfo, wrap=True),
                                    TextComponent(text="\n"),
                                    SeparatorComponent(),
                                    TextComponent(text="\n"),
                                    TextComponent(text="???????????????", size="lg",
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
                                                text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=activity_end_time + "(" + activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="?????????????????????" + activdate + "??????????????????????????????", contents=bubble)
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
                                    TextComponent(text="??????????????????", size='sm'),
                                    TextComponent(text=activdate, weight='bold',
                                                  size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="??????????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=activinfo, wrap=True),
                                    TextComponent(text="\n"),
                                    SeparatorComponent(),
                                    TextComponent(text="\n"),
                                    TextComponent(text="???????????????", size="lg",
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
                                                text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=activity_end_time + "(" + activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    TextComponent(text="\n"),
                                    SeparatorComponent(),
                                    TextComponent(text="\n"),
                                    TextComponent(text="???????????????", size="lg",
                                                  weight="bold", color="#4A4A4A"),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="17???????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=moonage, flex=1, align="center")
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=hoshizora,
                                                          flex=1, align="center"),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=nightphrase, flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=averagetempstr + "???", flex=1, align="center"),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=timeFix(
                                                sunset), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(text=timeFix(
                                                moonrise), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    BoxComponent(
                                        layout="horizontal",
                                        contents=[
                                            TextComponent(
                                                text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                            TextComponent(
                                                text=timeFix(moonset), flex=1, align="center", wrap=True),
                                        ]
                                    ),
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
                                    TextComponent(
                                        text=moon_visual, align="center", wrap=True),
                                    TextComponent(
                                        text="?????????????????????", weight="bold", color="#7D7D7D", wrap=True),
                                    TextComponent(
                                        text=observable_planets, align="center", wrap=True),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="?????????????????????" + activdate + "??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="??????????????????????????????", text="??????????????????????????????"))
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
        elif message == "???????????????????????????":
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
                            text="????????????????????????????????????", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="?????????????????????", text="?????????????????????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="?????????????????????", text="?????????????????????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="??????????????????", text="??????????????????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="??????????????????????????????", text="??????????????????????????????"),
                        ),
                    ],
                )
            )
            flex = FlexSendMessage(
                alt_text="????????????????????????????????????", contents=bubble)
            line_bot_api.reply_message(
                event.reply_token, flex)
            sys.exit()

        arraymessage = []
        arrayname = []
        arraydate = []
        if message == "?????????????????????":
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
                                    text="?????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="???????????????????????????????????????????????????????????????????????????", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="???????????????????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="?????????????????????", text="?????????????????????")),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="????????????")),
                                QuickReplyButton(
                                    action=MessageAction(label="?????????", text="?????????"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="????????????????????????????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()
            except SystemExit:
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="????????????????????????????????????????????????????????????????????????????????????????????????")
                )
                sys.exit()
        try:
            if userdata["action_type"] == "broadcast_message":
                if message == "?????????????????????":
                    try:
                        broadcast_message_sender = ast.literal_eval(str(list(authbook.values())).replace(
                            "[", "").replace("]", "").replace(" ", ""))
                        broadcast_message_sender = broadcast_message_sender[broadcast_message_sender.index(
                            event.source.user_id) + 1]
                    except:
                        broadcast_message_sender = "??????"
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
                                    text="?????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="???????????????????????????????????????????????????", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="???????????????????????????????????????????????????", contents=bubble
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

                elif message == "????????????":
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
                                    text="???????????????", weight="bold", size="xxl", wrap=True),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text=read_members, wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="??????????????????????????????????????????", contents=bubble
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

                elif message == "?????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="?????????????????????????????????????????????????????????")
                    )
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="??????????????????????????????????????????????????????????????????????????????????????????")
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
                                text="????????????????????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="????????????????????????????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="????????????????????????????????????????????????????????????", contents=bubble
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
                    broadcast_message_sender = "??????"
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
                                text="?????????????????????", weight="bold", size="xxl", wrap=True),
                            TextComponent(
                                text="????????????" + broadcast_message_sender, size="xxs", color="#979797", flex=2),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
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
                                text="??????????????????", weight="bold", color="#7D7D7D", wrap=True),
                            TextComponent(
                                text=message, wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="??????", text="??????")),
                            QuickReplyButton(
                                action=MessageAction(label="?????????", text="?????????"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "direct_message_check":
                if message == "??????":
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
                                notice = notice.replace(i, "???" + i)
                                urltitle = TextComponent(
                                    text="\n?????????????????????URL:", weight="bold", color="#7D7D7D", wrap=True)
                                sendurl1 = TextComponent(
                                    text="???" + i, color="#0043bf", wrap=True, action=URIAction(uri=i))
                            elif i == urls[1]:
                                notice = notice.replace(i, "???" + i)
                                sepa1 = BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                )
                                sendurl2 = TextComponent(
                                    text="???" + i, color="#0043bf", wrap=True, action=URIAction(uri=i))
                            elif i == urls[2]:
                                notice = notice.replace(i, "???" + i)
                                sepa2 = BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                )
                                sendurl3 = TextComponent(
                                    text="???" + i, color="#0043bf", wrap=True, action=URIAction(uri=i))
                            elif i == urls[3]:
                                notice = notice.replace(i, "???" + i)
                                sepa3 = BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                )
                                sendurl4 = TextComponent(
                                    text="???" + i, color="#0043bf", wrap=True, action=URIAction(uri=i))
                            elif i == urls[4]:
                                notice = notice.replace(i, "???" + i)
                                sepa4 = BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                )
                                sendurl5 = TextComponent(
                                    text="???" + i, color="#0043bf", wrap=True, action=URIAction(uri=i))
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
                                    text="?????????????????????", weight='bold', size='xl', adjustMode='shrink-to-fit'),
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
                                    text="????????????" + broadcast_message_sender, size="xxs", color="#979797", flex=2),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=broadcast_message_title, weight="bold", size="xxl", wrap=True),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="??????????????????", weight="bold", color="#7D7D7D", wrap=True),
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
                        alt_text=broadcast_message_sender + "??????????????????????????????????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label="????????????", data="????????????"))
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
                        TextSendMessage(text="????????????????????????????????????????????????")
                    )
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            errormessage = str(traceback.format_exc().replace(
                "Traceback (most recent call last)", "????????????????????????"))
            line_bot_api.push_message(
                idmappi, [
                    TextSendMessage(
                        text="????????????????????????????????????????????????\n\n" + errormessage),
                ]
            )

        if message == "?????????????????????":
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
                            action=DatetimePickerAction(label='???????????????',
                                                        data='date_postback',
                                                        mode='date')),
                        QuickReplyButton(
                            action=MessageAction(label="?????????", text="?????????")),
                        QuickReplyButton(
                            action=MessageAction(label="???????????????", text=tue)),
                        QuickReplyButton(
                            action=MessageAction(label="???????????????", text=fri)),
                        QuickReplyButton(
                            action=MessageAction(label="??????", text=tod)),
                        QuickReplyButton(
                            action=MessageAction(label="??????", text=tom))
                    ]
                    scheduled_date = get("NextAct")["Date"]
                    try:
                        scheduled_date = datetime(year=int(scheduled_date[:4]), month=int(
                            scheduled_date[5:7]), day=int(scheduled_date[8:10]))
                        datetodaytemp = (datetime.today() +
                                         timedelta(hours=9)) - timedelta(days=1)
                        if scheduled_date >= datetodaytemp:
                            items_list.insert(2, QuickReplyButton(
                                action=MessageAction(label="?????????????????????", text="?????????????????????")))
                    except ValueError:
                        pass
                    bubble = BubbleContainer(
                        direction='ltr',
                        body=BoxComponent(
                            layout='vertical',
                            contents=[
                                TextComponent(
                                    text="?????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="?????????????????????????????????????????????????????????????????????????????????????????????", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="?????????????????????????????????????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=items_list
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="????????????????????????????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()
            except SystemExit:
                sys.exit()
            except:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="????????????????????????????????????????????????????????????????????????????????????????????????")
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
                                text="???????????????????????????????????????????????????????????????????????????", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="??????", text="??????")),
                                        QuickReplyButton(
                                            action=MessageAction(label="?????????", text="?????????"))
                                    ]
                                )
                            )
                        )
                        sys.exit()
                    elif message == "?????????":
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="???????????????????????????????????????")
                        )
                        sys.exit()
                    else:
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
                        )
                        sys.exit()
                if message == "?????????????????????":
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
                                text="???????????????????????????????????????????????????????????????????????????")
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
                                    text="?????????????????????", weight="bold", size="xxl", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="?????????????????????????????????", wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="?????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="??????", text="??????")),
                                QuickReplyButton(
                                    action=MessageAction(label="?????????", text="?????????"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                try:
                    if userdata["flag_cancelling_date"]:
                        if message == "??????":
                            update(event.source.user_id,
                                   "flag_cancelling_date", False)
                            scheduled_date = get("NextAct")["Date"]
                            scheduled_date = datetime(year=int(scheduled_date[:4]), month=int(
                                scheduled_date[5:7]), day=int(scheduled_date[8:10]))
                            scheduled_date = scheduled_date.strftime(
                                "%-Y???%-m???%-d???")
                            client = datastore.Client()
                            with client.transaction():
                                key = client.key("Task", "NextAct")
                                task = client.get(key)
                                task["Date"] = "???????????????????????????"
                                task["Info"] = "???????????????????????????"
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
                                        TextComponent(text='?????????????????????????????????',
                                                      weight='bold', size='xl'),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="10px"
                                        ),
                                        TextComponent(text=scheduled_date + "????????????????????????????????????????????????",
                                                      size='sm', wrap=True, adjustMode='shrink-to-fit'),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="????????????????????????????????????????????????????????????????????????????????????????????????", contents=bubble)
                            broadcast(flex)
                            reset_user_data()
                            sys.exit()
                except KeyError:
                    pass

                if (message[:4].isnumeric() and (message[4:5] == "-") and message[5:7].isnumeric() and (message[7:8] == "-") and message[8:10].isnumeric() and (len(message) == 10)) or message == "??????":
                    try:
                        if userdata["flag_activity_date_already"]:
                            message = userdata["activity_already_date"]
                        elif not userdata["flag_activity_date_already"]:
                            if message == "??????":
                                reset_user_data()
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(
                                        text="??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
                                )
                                sys.exit()
                    except SystemExit:
                        sys.exit()
                    except:
                        if message == "??????":
                            reset_user_data()
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(
                                    text="??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
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
                                text="??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
                        )
                        sys.exit()
                    activstrc = str(activdatec.strftime("%a"))
                    if activstrc == "Mon":
                        activstrc = "[???]"
                    elif activstrc == "Tue":
                        activstrc = "[???]"
                    elif activstrc == "Wed":
                        activstrc = "[???]"
                    elif activstrc == "Thu":
                        activstrc = "[???]"
                    elif activstrc == "Fri":
                        activstrc = "[???]"
                    elif activstrc == "Sat":
                        activstrc = "[???]"
                    elif activstrc == "Sun":
                        activstrc = "[???]"
                    activsac = datetodaytemp - activdatec
                    activsac = int(activsac.days)
                    activdatec = activdatec.strftime("%-Y???%-m???%-d???")
                    if activsac == 0:
                        activdatec = "??????(" + activdatec + activstrc + ")"
                    elif activsac == -1:
                        activdatec = "??????(" + activdatec + activstrc + ")"
                    elif activsac == -2:
                        activdatec = "????????????(" + activdatec + activstrc + ")"
                    elif activsac == -3:
                        activdatec = "???????????????(" + activdatec + activstrc + ")"
                    else:
                        activdatec = activdatec + activstrc
                    if activsac >= 1:
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(text="??????????????????????????????????????????????????????????????????????????????")
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
                                    text="?????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="???????????????????????????\n" + activdatec + "????????????\n??????????????????????????????????????????????????????????????????", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="??????????????????????????????????????????????????????????????????", contents=bubble
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
                                text="????????????????????????????????????????????????")
                        )
                        sys.exit()
                    elif message == "?????????":
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="????????????????????????????????????????????????")
                        )
                        sys.exit()
                    else:
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
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
                                text="???????????????????????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="??????????????????????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="??????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="??????(????????????)", text="??????(????????????)")),
                            QuickReplyButton(
                                action=MessageAction(label="??????(????????????)", text="??????(????????????)")),
                            QuickReplyButton(
                                action=MessageAction(label="??????", text="??????"))
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
                                text="?????????????????????????????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="??????????????????????????????????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="??????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=DatetimePickerAction(label='???????????????????????????',
                                                            data='time_postback',
                                                            mode='time'))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "register_activity_ended":
                if message == "????????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="?????????????????????????????????????????????")
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
                if register_activity_observe_or_not == "??????(????????????)":
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
                                    text="?????????????????????", weight="bold", size="xxl", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="?????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=announce, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="??????????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=register_activity_about, wrap=True),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="???????????????", size="lg",
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
                                            text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                TextComponent(text="?????????????????????",
                                              weight="bold", color="#7D7D7D"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="?????????????????????", flex=1),
                                        TextComponent(text=register_activity_observation_end_time + "(" +
                                                      register_activity_observation_time_span + "??????)", flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="?????????????????????", flex=1),
                                        TextComponent(
                                            text=register_activity_end_time + "(" + register_activity_time_span + "??????)", flex=1, align="center", wrap=True),
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
                                TextComponent(text="??????????????????????????????",
                                              weight="bold", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="??????", text="??????")),
                                QuickReplyButton(
                                    action=MessageAction(label="?????????", text="?????????"))
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
                                    text="?????????????????????", weight="bold", size="xxl", wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="?????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=announce, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="??????????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=register_activity_about, wrap=True),
                                TextComponent(text="\n"),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="???????????????", size="lg",
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
                                            text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                        TextComponent(
                                            text=register_activity_end_time + "(" + register_activity_time_span + "??????)", flex=1, align="center", wrap=True),
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
                                TextComponent(text="??????????????????????????????",
                                              weight="bold", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="??????", text="??????")),
                                QuickReplyButton(
                                    action=MessageAction(label="?????????", text="?????????"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

            elif userdata["action_type"] == "register_activity_check":
                if message == "??????":
                    next_act_data = get("NextAct")
                    register_activity_date = str(
                        userdata["register_activity_date"])
                    register_activity_about = str(
                        userdata["register_activity_about"])
                    register_activity_observe_or_not = userdata["register_activity_observe_or_not"]
                    register_activity_start_time = userdata["register_activity_start_time"]
                    register_activity_end_time = userdata["register_activity_end_time"]
                    register_activity_time_span = userdata["register_activity_time_span"]
                    if register_activity_observe_or_not == "??????(????????????)":
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
                        if register_activity_observe_or_not == "??????(????????????)":
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
                        if (register_activity_observe_or_not != "??????") and flag_activity_date_already and next_act_data["is_schedule_created"]:
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
                        if register_activity_observe_or_not != "??????":
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

                        elif (register_activity_observe_or_not == "??????") and flag_activity_date_already:
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
                            activstrb = "[???]"
                        elif activstrb == "Tue":
                            activstrb = "[???]"
                        elif activstrb == "Wed":
                            activstrb = "[???]"
                        elif activstrb == "Thu":
                            activstrb = "[???]"
                        elif activstrb == "Fri":
                            activstrb = "[???]"
                        elif activstrb == "Sat":
                            activstrb = "[???]"
                        elif activstrb == "Sun":
                            activstrb = "[???]"
                        activsab = datetodaytemp - activdateb
                        activsab = int(activsab.days)
                        activdateb = str(int(activdateb.strftime(
                            "%m"))) + "???" + str(int(activdateb.strftime("%d"))) + "???"
                        activinfob = register_activity_about
                        dataan = False
                        if activsab == 0:
                            activdateb = "??????(" + activdateb + activstrb + ")"
                            dataan = True
                        elif activsab == -1:
                            activdateb = "??????(" + activdateb + activstrb + ")"
                            dataan = True
                        elif activsab == -2:
                            activdateb = "????????????(" + activdateb + activstrb + ")"
                            dataan = True
                        elif activsab == -3:
                            activdateb = "???????????????(" + \
                                activdateb + activstrb + ")"
                            dataan = True
                        elif activsab == -4:
                            activdateb = activdateb + activstrb
                            dataan = True
                        else:
                            activdateb = activdateb + activstrb
                        if len(activinfob) == 0:
                            activinfob = "??????"

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
                        kobun = date.strftime("%-H???%-M???")
                        if deltaday.days == 1:
                            plus = "??????,"
                            kobun = plus + kobun
                        elif deltaday.days > 1:
                            plus = str(deltaday.days) + "??????,"
                            kobun = plus + kobun
                        elif deltaday.days == -1:
                            plus = "??????,"
                            kobun = plus + kobun
                        elif deltaday.days < -1:
                            plus = str(abs(deltaday.days)) + "??????,"
                            kobun = plus + kobun
                        if kobun[-3:] == "???0???":
                            return kobun[:-2]
                        else:
                            return kobun

                    observable_list = ["??????"]
                    if timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage) == "????????????":
                        moon_visual = "????????????"
                    else:
                        observable_list.append("???")
                        moon_visual = timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[
                                              0]) + "??????\n" + timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[1]) + "???????????????\n?????????????????????"

                    if planet_timespan(day_mercuryrise, day_mercuryset, sunset, sunriseafterset) != "????????????":
                        observable_list.append("??????")
                    if planet_timespan(day_venusrise, day_venusset, sunset, sunriseafterset) != "????????????":
                        observable_list.append("??????")
                    if planet_timespan(day_marsrise, day_marsset, sunset, sunriseafterset) != "????????????":
                        observable_list.append("??????")
                    if planet_timespan(day_jupiterrise, day_jupiterset, sunset, sunriseafterset) != "????????????":
                        observable_list.append("??????")
                    if planet_timespan(day_saturnrise, day_saturnset, sunset, sunriseafterset) != "????????????":
                        observable_list.append("??????")
                    if planet_timespan(day_uranusrise, day_uranusset, sunset, sunriseafterset) != "????????????":
                        observable_list.append("?????????")
                    if planet_timespan(day_neptunerise, day_neptuneset, sunset, sunriseafterset) != "????????????":
                        observable_list.append("?????????")
                    if planet_timespan(day_plutorise, day_plutoset, sunset, sunriseafterset) != "????????????":
                        observable_list.append("?????????")

                    observable_planets = str()
                    if len(observable_list) == 1:
                        observable_planets = "????????????"
                    else:
                        for i in observable_list:
                            if i == "??????":
                                observable_planets = "??????"
                            else:
                                observable_planets = observable_planets + "???" + i

                    update("NextAct", "Observable_planets", observable_planets)

                    if cutmoonage == "0":
                        moonage = moonage + "????????????"
                    elif cutmoonage == "1":
                        moonage = moonage + "????????????"
                    elif cutmoonage == "2":
                        moonage = moonage + "???????????????"
                    elif cutmoonage == "7":
                        moonage = moonage + "????????????"
                    elif cutmoonage == "9":
                        moonage = moonage + "??????????????????"
                    elif cutmoonage == "12":
                        moonage = moonage + "??????????????????"
                    elif cutmoonage == "13":
                        moonage = moonage + "???????????????"
                    elif cutmoonage == "14":
                        moonage = moonage + "????????????"
                    elif cutmoonage == "15":
                        moonage = moonage + "??????????????????"
                    elif cutmoonage == "16":
                        moonage = moonage + "???????????????"
                    elif cutmoonage == "17":
                        moonage = moonage + "???????????????"
                    elif cutmoonage == "18":
                        moonage = moonage + "???????????????"
                    elif cutmoonage == "19":
                        moonage = moonage + "???????????????"
                    elif cutmoonage == "22":
                        moonage = moonage + "????????????"
                    elif cutmoonage == "25":
                        moonage = moonage + "???????????????"

                    def normalan():
                        if register_activity_observe_or_not == "??????(????????????)":
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
                                        TextComponent(text="???????????????????????????????????????????????????",
                                                      size='xs', adjustMode='shrink-to-fit'),
                                        TextComponent(text=activdateb, weight='bold',
                                                      size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                        TextComponent(text="\n"),
                                        TextComponent(
                                            text="??????????????????", weight="bold", color="#7D7D7D"),
                                        TextComponent(
                                            text=activinfob, wrap=True),
                                        TextComponent(text="\n"),
                                        SeparatorComponent(),
                                        TextComponent(text="\n"),
                                        TextComponent(text="???????????????", size="lg",
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
                                                    text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                    text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                            text="?????????????????????", weight="bold", color="#7D7D7D"),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="?????????????????????", flex=1),
                                                TextComponent(text=register_activity_observation_end_time + "(" +
                                                              register_activity_observation_time_span + "??????)", flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="?????????????????????", flex=1),
                                                TextComponent(
                                                    text=register_activity_end_time + "(" + register_activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        TextComponent(text="\n"),
                                        SeparatorComponent(),
                                        TextComponent(text="\n"),
                                        TextComponent(text="???????????????", size="lg",
                                                      weight="bold", color="#4A4A4A"),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="17???????????????", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=moonage, flex=1, align="center")
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(text=timeFix(
                                                    sunset), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(text=timeFix(
                                                    moonrise), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=timeFix(moonset), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        TextComponent(
                                            text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
                                        TextComponent(
                                            text=moon_visual, align="center", wrap=True),
                                        TextComponent(
                                            text="?????????????????????", weight="bold", color="#7D7D7D", wrap=True),
                                        TextComponent(
                                            text=observable_planets, align="center", wrap=True),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="?????????????????????" + activdateb + "??????????????????????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="??????????????????????????????", text="??????????????????????????????"))
                                    ]
                                )
                            )
                            broadcast(flex)
                            reset_user_data()
                        elif register_activity_observe_or_not == "??????":
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
                                        TextComponent(text="???????????????????????????????????????????????????",
                                                      size='xs', adjustMode='shrink-to-fit'),
                                        TextComponent(text=activdateb, weight='bold',
                                                      size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                        TextComponent(text="\n"),
                                        TextComponent(
                                            text="??????????????????", weight="bold", color="#7D7D7D"),
                                        TextComponent(
                                            text=activinfob, wrap=True),
                                        TextComponent(text="\n"),
                                        SeparatorComponent(),
                                        TextComponent(text="\n"),
                                        TextComponent(text="???????????????", size="lg",
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
                                                    text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                    text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                    text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=register_activity_end_time + "(" + register_activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="?????????????????????" + activdateb + "??????????????????????????????????????????????????????????????????????????????", contents=bubble)
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
                                        TextComponent(text="???????????????????????????????????????????????????",
                                                      size='xs', adjustMode='shrink-to-fit'),
                                        TextComponent(text=activdateb, weight='bold',
                                                      size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                        TextComponent(text="\n"),
                                        TextComponent(
                                            text="??????????????????", weight="bold", color="#7D7D7D"),
                                        TextComponent(
                                            text=activinfob, wrap=True),
                                        TextComponent(text="\n"),
                                        SeparatorComponent(),
                                        TextComponent(text="\n"),
                                        TextComponent(text="???????????????", size="lg",
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
                                                    text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                    text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                    text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=register_activity_end_time + "(" + register_activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        TextComponent(text="\n"),
                                        SeparatorComponent(),
                                        TextComponent(text="\n"),
                                        TextComponent(text="???????????????", size="lg",
                                                      weight="bold", color="#4A4A4A"),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="17???????????????", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=moonage, flex=1, align="center")
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(text=timeFix(
                                                    sunset), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(text=timeFix(
                                                    moonrise), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        BoxComponent(
                                            layout="horizontal",
                                            contents=[
                                                TextComponent(
                                                    text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                                TextComponent(
                                                    text=timeFix(moonset), flex=1, align="center", wrap=True),
                                            ]
                                        ),
                                        TextComponent(
                                            text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
                                        TextComponent(
                                            text=moon_visual, align="center", wrap=True),
                                        TextComponent(
                                            text="?????????????????????", weight="bold", color="#7D7D7D", wrap=True),
                                        TextComponent(
                                            text=observable_planets, align="center", wrap=True),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="?????????????????????" + activdateb + "??????????????????????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="??????????????????????????????", text="??????????????????????????????"))
                                    ]
                                )
                            )
                            broadcast(flex)
                            reset_user_data()
                    if dataan:
                        try:
                            if datenow > (get("WeatherData")["??????????????????????????????date"] + timedelta(hours=2)):
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
                                    task["??????????????????????????????"] = str(weatherdata)
                                    task["??????????????????????????????date"] = datenow
                                    client.put(task)

                            weather_datajson = ast.literal_eval(
                                get("WeatherData")["??????????????????????????????"])

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

                            if register_activity_observe_or_not == "??????(????????????)":
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
                                            TextComponent(text="???????????????????????????????????????????????????",
                                                          size='xs', adjustMode='shrink-to-fit'),
                                            TextComponent(text=activdateb, weight='bold',
                                                          size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                            TextComponent(text="\n"),
                                            TextComponent(
                                                text="??????????????????", weight="bold", color="#7D7D7D"),
                                            TextComponent(
                                                text=activinfob, wrap=True),
                                            TextComponent(text="\n"),
                                            SeparatorComponent(),
                                            TextComponent(text="\n"),
                                            TextComponent(text="???????????????", size="lg",
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
                                                        text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                        text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                text="?????????????????????", weight="bold", color="#7D7D7D"),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="?????????????????????", flex=1),
                                                    TextComponent(
                                                        text=register_activity_observation_end_time + "(" + register_activity_observation_time_span + "??????)", flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="?????????????????????", flex=1),
                                                    TextComponent(
                                                        text=register_activity_end_time + "(" + register_activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            TextComponent(text="\n"),
                                            SeparatorComponent(),
                                            TextComponent(text="\n"),
                                            TextComponent(text="???????????????", size="lg",
                                                          weight="bold", color="#4A4A4A"),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="17???????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=moonage, flex=1, align="center")
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=hoshizora,
                                                                  flex=1, align="center"),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=nightphrase, flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=averagetempstr + "???", flex=1, align="center"),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=timeFix(
                                                        sunset), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=timeFix(
                                                        moonrise), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=timeFix(moonset), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            TextComponent(
                                                text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
                                            TextComponent(
                                                text=moon_visual, align="center", wrap=True),
                                            TextComponent(
                                                text="?????????????????????", weight="bold", color="#7D7D7D", wrap=True),
                                            TextComponent(
                                                text=observable_planets, align="center", wrap=True),
                                        ],
                                    )
                                )
                                flex = FlexSendMessage(
                                    alt_text="?????????????????????" + activdateb + "??????????????????????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                        items=[
                                            QuickReplyButton(
                                                action=MessageAction(label="??????????????????????????????", text="??????????????????????????????"))
                                        ]
                                    )
                                )
                                broadcast(flex)
                                reset_user_data()
                            elif register_activity_observe_or_not == "??????":
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
                                            TextComponent(text="???????????????????????????????????????????????????",
                                                          size='xs', adjustMode='shrink-to-fit'),
                                            TextComponent(text=activdateb, weight='bold',
                                                          size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                            TextComponent(text="\n"),
                                            TextComponent(
                                                text="??????????????????", weight="bold", color="#7D7D7D"),
                                            TextComponent(
                                                text=activinfob, wrap=True),
                                            TextComponent(text="\n"),
                                            SeparatorComponent(),
                                            TextComponent(text="\n"),
                                            TextComponent(text="???????????????", size="lg",
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
                                                        text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                        text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                        text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=register_activity_end_time + "(" + register_activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                        ],
                                    )
                                )
                                flex = FlexSendMessage(
                                    alt_text="?????????????????????" + activdateb + "??????????????????????????????????????????????????????????????????????????????", contents=bubble)
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
                                            TextComponent(text="???????????????????????????????????????????????????",
                                                          size='xs', adjustMode='shrink-to-fit'),
                                            TextComponent(text=activdateb, weight='bold',
                                                          size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                            TextComponent(text="\n"),
                                            TextComponent(
                                                text="??????????????????", weight="bold", color="#7D7D7D"),
                                            TextComponent(
                                                text=activinfob, wrap=True),
                                            TextComponent(text="\n"),
                                            SeparatorComponent(),
                                            TextComponent(text="\n"),
                                            TextComponent(text="???????????????", size="lg",
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
                                                        text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                        text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
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
                                                        text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=register_activity_end_time + "(" + register_activity_time_span + "??????)", flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            TextComponent(text="\n"),
                                            SeparatorComponent(),
                                            TextComponent(text="\n"),
                                            TextComponent(text="???????????????", size="lg",
                                                          weight="bold", color="#4A4A4A"),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="17???????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=moonage, flex=1, align="center")
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=hoshizora,
                                                                  flex=1, align="center"),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=nightphrase, flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=averagetempstr + "???", flex=1, align="center"),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=timeFix(
                                                        sunset), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(text=timeFix(
                                                        moonrise), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            BoxComponent(
                                                layout="horizontal",
                                                contents=[
                                                    TextComponent(
                                                        text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                                    TextComponent(
                                                        text=timeFix(moonset), flex=1, align="center", wrap=True),
                                                ]
                                            ),
                                            TextComponent(
                                                text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
                                            TextComponent(
                                                text=moon_visual, align="center", wrap=True),
                                            TextComponent(
                                                text="?????????????????????", weight="bold", color="#7D7D7D", wrap=True),
                                            TextComponent(
                                                text=observable_planets, align="center", wrap=True),
                                        ],
                                    )
                                )
                                flex = FlexSendMessage(
                                    alt_text="?????????????????????" + activdateb + "??????????????????????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                        items=[
                                            QuickReplyButton(
                                                action=MessageAction(label="??????????????????????????????", text="??????????????????????????????"))
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
                        TextSendMessage(text="????????????????????????????????????????????????")
                    )
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        if message == "??????????????????":
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
                                    text="??????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="???????????????????????????????????????????????????????????????????????????????????????", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="???????????????????????????????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='???????????????',
                                                                data='date_postback',
                                                                mode='date')),
                                QuickReplyButton(
                                    action=MessageAction(label="?????????", text="?????????"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="????????????????????????????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()
            except SystemExit:
                sys.exit()
            except:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="????????????????????????????????????????????????????????????????????????????????????????????????")
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
                                text="?????????????????????????????????????????????????????????????????????", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="??????", text="??????")),
                                        QuickReplyButton(
                                            action=MessageAction(label="?????????", text="?????????"))
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
                                text="????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
                        )
                        sys.exit()
                elif (message[:4].isnumeric() and (message[4:5] == "-") and message[5:7].isnumeric() and (message[7:8] == "-") and message[8:10].isnumeric() and (len(message) == 10)) or message == "??????":
                    try:
                        if userdata["flag_note_date_already"]:
                            if message == "??????":
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
                                    ksavestr = "[???]"
                                elif ksavestr == "Tue":
                                    ksavestr = "[???]"
                                elif ksavestr == "Wed":
                                    ksavestr = "[???]"
                                elif ksavestr == "Thu":
                                    ksavestr = "[???]"
                                elif ksavestr == "Fri":
                                    ksavestr = "[???]"
                                elif ksavestr == "Sat":
                                    ksavestr = "[???]"
                                elif ksavestr == "Sun":
                                    ksavestr = "[???]"
                                write_note_date_full = write_note_date_full.strftime(
                                    "%-Y???%-m???%-d???") + ksavestr
                            else:
                                reset_user_data()
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(
                                        text="????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
                                )
                                sys.exit()
                        elif not userdata["flag_note_date_already"]:
                            if message == "??????":
                                reset_user_data()
                                line_bot_api.reply_message(
                                    event.reply_token,
                                    TextSendMessage(
                                        text="????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
                                )
                                sys.exit()
                    except SystemExit:
                        sys.exit()
                    except:
                        if message == "??????":
                            reset_user_data()
                            line_bot_api.reply_message(
                                event.reply_token,
                                TextSendMessage(
                                    text="????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
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
                                    text="????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
                            )
                            sys.exit()
                        ksavestr = str(write_note_date_full.strftime("%a"))
                        if ksavestr == "Mon":
                            ksavestr = "[???]"
                        elif ksavestr == "Tue":
                            ksavestr = "[???]"
                        elif ksavestr == "Wed":
                            ksavestr = "[???]"
                        elif ksavestr == "Thu":
                            ksavestr = "[???]"
                        elif ksavestr == "Fri":
                            ksavestr = "[???]"
                        elif ksavestr == "Sat":
                            ksavestr = "[???]"
                        elif ksavestr == "Sun":
                            ksavestr = "[???]"
                        write_note_date_full = write_note_date_full.strftime(
                            "%-Y???%-m???%-d???") + ksavestr
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
                                    text="???????????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text=write_note_date_full + "????????????\n?????????????????????????????????????????????????????????????????????", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='?????????????????????',
                                                                data='time_postback',
                                                                mode='time')),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="????????????"))
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
                                text="????????????????????????????????????????????????")
                        )
                        sys.exit()
                    elif message == "?????????" or message == "?????????":
                        reset_user_data()
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="????????????????????????????????????????????????")
                        )
                        sys.exit()
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()

            elif userdata["action_type"] == "write_note_start_time":
                if message == "????????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????")
                    )
                    sys.exit()

            elif userdata["action_type"] == "write_note_end_time":
                if message == "????????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????")
                    )
                    sys.exit()

            elif userdata["action_type"] == "write_note_weather":
                if message == "????????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????")
                    )
                    sys.exit()

            elif userdata["action_type"] == "write_note_weather_check":
                if message == "????????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????")
                    )
                    sys.exit()
                if not (message == "??????????????????????????????"):
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()
                timeandweather = userdata["write_note_activity_started_time"] + "~" + \
                    userdata["write_note_activity_ended_time"] + \
                    "???" + userdata["write_note_weather"] + "???"
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
                                text="?????????????????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="?????????????????????????????????????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="????????????", text="????????????"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "write_note_about":
                if message == "????????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????")
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
                                text="????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=MessageAction(
                                    label='????????????', text='????????????'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='??????', data='??????', text="??????"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='???', data='???', text="???"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='??????', data='??????', text="??????"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='??????', data='??????', text="??????"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='??????', data='??????', text="??????"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='??????', data='??????', text="??????"),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='???????????????', data='???????????????', text="???????????????")
                            ),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="????????????????????????????????????????????????", contents=bubble)
                line_bot_api.reply_message(
                    event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "write_note_planets":
                if message == "????????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????")
                    )
                    sys.exit()
                if (message == "????????????") or (message == "????????????"):
                    if message == "????????????":
                        client = datastore.Client()
                        with client.transaction():
                            key = client.key("Task", event.source.user_id)
                            task = client.get(key)
                            task["flag_write_note_observed"] = False
                            client.put(task)
                    kpls = userdata["write_note_observed_planets"]
                    kplslist = ast.literal_eval(kpls)
                    lobservedpls = str()
                    if message == "????????????":
                        for i in kplslist:
                            lobservedpls = lobservedpls + i + "???"
                        lobservedpls = lobservedpls[:-1]
                        lobservedpls = lobservedpls + "?????????"
                    else:
                        lobservedpls = "????????????"
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
                                    text="?????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="???????????????????????????????????????????????????????????????????????????????????????", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="????????????"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif (message == "??????") or (message == "???") or (message == "??????") or (message == "??????") or (message == "??????") or (message == "??????") or (message == "???????????????") or (message == "??????"):
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()
            elif userdata["action_type"] == "write_note_message":
                if message == "????????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????")
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
                    knumber = "???{}???".format(str(len(knumber)))
                except:
                    knumber = "????????????"
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
                                text="?????????????????????", weight="bold", size="xxl", wrap=True),
                            TextComponent(text="\n"),
                            TextComponent(
                                text="????????????", weight="bold", color="#7D7D7D", wrap=True),
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
                                text="????????????????????????", weight="bold", color="#7D7D7D", wrap=True),
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
                                text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
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
                                text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
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
                                text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
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
                                text="??????????????????????????????", weight="bold")
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="??????", text="??????")),
                            QuickReplyButton(
                                action=MessageAction(label="?????????", text="?????????"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "write_note_check":
                if message == "????????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????")
                    )
                    sys.exit()
                if message == "??????":
                    write_note_date = userdata["write_note_date"]
                    write_note_date_full = userdata["write_note_date_full"]
                    activity_time = userdata["activity_time"]
                    try:
                        knumber = ast.literal_eval(
                            get("MembersList")[write_note_date])
                        knumber = "???{}???".format(str(len(knumber)))
                    except:
                        knumber = "????????????"
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
                    kactivesta["????????????"] = kactivesta["????????????"] + 1
                    if kobserved:
                        kactivesta["????????????"] = kactivesta["????????????"] + 1
                        kactivesta["???????????????????????????"] = round(
                            (kactivesta["???????????????????????????"] + kactivetime) / kactivesta["????????????"])
                    kactivesta[kweather] = kactivesta[kweather] + 1
                    kactivesta["???????????????????????????"] = round(
                        (kactivesta["???????????????????????????"] + kactivetime) / kactivesta["????????????"])
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
                                        text="????????????????????????????????????????????????", size='sm', wrap=True),
                                    TextComponent(
                                        text=write_note_date_full, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="????????????????????????", weight="bold", color="#7D7D7D"),
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
                                        text="???????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=knumber, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D"),
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
                                        text="???????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(
                                        text=activity_notice, wrap=True)
                                ],
                            )
                        )
                        if knumber == "????????????":
                            flex = FlexSendMessage(
                                alt_text=write_note_date_full + "????????????????????????????????????????????????????????????????????????????????????", contents=bubble)
                        else:
                            flex = FlexSendMessage(
                                alt_text=write_note_date_full + "????????????????????????????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="?????????????????????", text="????????????????????????????????????"))
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
                                        text="???????????????????????????????????????", size='sm', wrap=True),
                                    TextComponent(
                                        text=write_note_date_full, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="????????????????????????", weight="bold", color="#7D7D7D"),
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
                                        text="???????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=knumber, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D"),
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
                                        text="???????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(
                                        text=activity_notice, wrap=True)
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=write_note_date_full + "????????????????????????????????????????????????????????????????????????????????????", contents=bubble)
                        broadcast(flex)
                        reset_user_data()
                        sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????")
                    )
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        if message == "??????????????????????????????":
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
                            text="????????????????????????????????????", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="?????????????????????", text="?????????????????????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="???????????????????????????", text="???????????????????????????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=MessageAction(
                                label="?????????????????????????????????", text="?????????????????????????????????"),
                        )
                    ],
                )
            )
            flex = FlexSendMessage(
                alt_text="????????????????????????????????????", contents=bubble)
            line_bot_api.reply_message(
                event.reply_token, flex)
            sys.exit()

        try:
            if message == "?????????????????????":
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
                                    text="?????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="???????????????????????????????????????????????????????????????????????????????????????\n??????????????????g-c(nn)name?????????????????????????????????\n??????1-A(01)????????????", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="????????????????????????????????????????????????????????????????????????????????????", size="xs", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="?????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="?????????", text="?????????"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="????????????????????????????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()

            elif userdata["action_type"] == "manage_auth":
                if message == "?????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="?????????????????????????????????")
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
                                TextSendMessage(text="?????????????????????????????????????????????????????????")
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
                                            text="?????????????????????", weight="bold", size="xxl", wrap=True),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="10px"
                                        ),
                                        TextComponent(
                                            text="??????????????????????????????????????????????????????????????????????????????????????????", wrap=True),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="??????", text="??????")),
                                        QuickReplyButton(
                                            action=MessageAction(label="?????????", text="?????????"))
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
                                            text="?????????????????????", weight="bold", size="xxl", wrap=True),
                                        BoxComponent(
                                            layout="vertical",
                                            contents=[
                                                FillerComponent()
                                            ],
                                            height="10px"
                                        ),
                                        TextComponent(
                                            text="?????????????????????????????????????????????", wrap=True),
                                    ],
                                )
                            )
                            flex = FlexSendMessage(
                                alt_text="??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="??????", text="??????")),
                                        QuickReplyButton(
                                            action=MessageAction(label="?????????", text="?????????"))
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
                            text="??????????????????????????????????????????\n????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()

            elif userdata["action_type"] == "managing_auth_add":
                if message == "??????":
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
                                TextComponent(text='???????????????????????????',
                                              weight='bold', size='xl'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text=managing_name + '???????????????????????????????????????',
                                              size='sm', adjustMode='shrink-to-fit'),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=managing_name + '???????????????????????????????????????', contents=bubble)
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
                                TextComponent(text='??????????????????????????????',
                                              weight='bold', size='xl'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text="???????????????" + managing_name + '?????????\n????????????????????????????????????????????????',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="???????????????" + managing_name + '?????????\n????????????????????????????????????????????????', contents=bubble)
                    line_bot_api.push_message(
                        managing_id, flex
                    )
                    reset_user_data()
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="?????????????????????????????????")
                    )
                    sys.exit()

            elif userdata["action_type"] == "managing_auth_delete":
                if message == "??????":
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
                                TextComponent(text='???????????????????????????',
                                              weight='bold', size='xl'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text=managing_name + '???????????????????????????????????????',
                                              size='sm', adjustMode='shrink-to-fit'),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=managing_name + '???????????????????????????????????????', contents=bubble)
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
                                TextComponent(text='??????????????????????????????',
                                              weight='bold', size='xl'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text='????????????????????????????????????????????????',
                                              size='sm', adjustMode='shrink-to-fit'),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text='????????????????????????????????????????????????', contents=bubble)
                    line_bot_api.push_message(
                        managing_id, flex
                    )
                    reset_user_data()
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="?????????????????????????????????")
                    )
                    sys.exit()

        except LineBotApiError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="LINEID??????????????????????????????????????????????????????LINEID??????????????????")
            )
            sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        try:
            if message == "???????????????????????????":
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
                                    text="???????????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="??????????????????????????????????????????????????????????????????????????????????????????????????????\n??????????????????g-c(nn)name?????????????????????????????????\n??????1-A(01)????????????", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="????????????????????????????????????????????????????????????????????????????????????", size="xs", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="?????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="?????????", text="?????????"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="????????????????????????????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()
            elif userdata["action_type"] == "managing_auth_bucho":
                if message == "?????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="?????????????????????????????????")
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
                                TextSendMessage(text="????????????????????????????????????????????????")
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
                                        text="????????????????????????????????????", weight="bold", size="xxl", wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="???????????????????????????????????????????????????", wrap=True),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="??????", text="??????")),
                                    QuickReplyButton(
                                        action=MessageAction(label="?????????", text="?????????"))
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
                            text="??????????????????????????????????????????\n????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()
            elif userdata["action_type"] == "managing_auth_bucho_add":
                if message == "??????":
                    managing_id = userdata["managing_id"]
                    points_data = get("PointsID")
                    managing_name = points_data[managing_id][7:] + "????????????"
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
                                TextComponent(text='????????????????????????????????????',
                                              weight='bold', size='xl', wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text=managing_name + '?????????????????????????????????????????????',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=managing_name + '?????????????????????????????????????????????', contents=bubble)
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
                                TextComponent(text='????????????????????????????????????',
                                              weight='bold', size='xl', wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text='??????????????????????????????????????????????????????',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text='???????????????????????????????????????', contents=bubble)
                    line_bot_api.push_message(
                        managing_id, flex
                    )
                    reset_user_data()
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="?????????????????????????????????")
                    )
                    sys.exit()
        except LineBotApiError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="LINEID??????????????????????????????????????????????????????LINEID??????????????????")
            )
            sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        try:
            if message == "?????????????????????????????????":
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
                                text="??????????????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="??????????????????????????????????????????????????????????????????????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="????????????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="?????????", text="?????????"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()

            elif userdata["action_type"] == "requesting_auth_komon":
                if message == "?????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="?????????????????????????????????")
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
                                TextComponent(text='?????????????????????????????????',
                                              weight='bold', size='xl'),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text='?????????????????????????????????????????????????????????????????????',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text='?????????????????????????????????????????????????????????????????????', contents=bubble)
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
                                TextComponent(text='????????????????????????????????????',
                                              weight='bold', size='xl', wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text=message + '?????????????????????????????????????????????\n?????????????????????',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text='???????????????????????????????????????', contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="??????", text="??????")),
                                QuickReplyButton(
                                    action=MessageAction(label="??????", text="??????"))
                            ],
                        )
                    )
                    line_bot_api.push_message(
                        idbucho, flex
                    )
                    reset_user_data()
                    sys.exit()
            elif userdata["action_type"] == "requested_auth_by_komon":
                if message == "??????":
                    managing_id = userdata["managing_id"]
                    managing_name = userdata["komon_name"] + "??????????????????"
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
                                TextComponent(text="?????????????????????????????????",
                                              weight='bold', size='xl', wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text=userdata["komon_name"] + '?????????????????????????????????????????????',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=userdata["komon_name"] + '?????????????????????????????????????????????', contents=bubble)
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
                                TextComponent(text='????????????????????????????????????',
                                              weight='bold', size='xl', wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(text='??????????????????????????????????????????????????????',
                                              size='sm', adjustMode='shrink-to-fit', wrap=True),
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text='???????????????????????????????????????', contents=bubble)
                    line_bot_api.push_message(
                        managing_id, flex
                    )
                    reset_user_data()
                    sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="??????????????????????????????")
                    )
                    sys.exit()

        except LineBotApiError:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="LINEID??????????????????????????????????????????????????????LINEID??????????????????")
            )
            sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        if message == "????????????????????????????????????":
            try:
                reset_user_data()
            except:
                pass
            try:
                latestdatestr = str(get("MembersList")["LatestDate"])
                latestdate = datetime(year=int(latestdatestr[:4]), month=int(
                    latestdatestr[5:7]), day=int(latestdatestr[8:10]))
                latestdate = latestdate.strftime("%-Y???%-m???%-d???")
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
                            TextComponent(text="????????????", size='sm'),
                            TextComponent(
                                text=latestdate + "\n?????????????????????????????????", weight='bold', size='xl', wrap=True, adjustMode='shrink-to-fit'),
                            TextComponent(text="\n"),
                            TextComponent(text=membersstr, wrap=True),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"),
                            TextComponent(
                                text="???" + membersint + "???", weight="bold", color="#7D7D7D"),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text=latestdate + "??????????????????????????????????????????", contents=bubble)
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
            except SystemExit:
                sys.exit()
            except:
                pass

        if message == "??????????????????":
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
                                text="?????????????????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="????????????????????????????????????????????????????????????\n\n????????????????????????????????????????????????????????????", wrap=True),
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
                    alt_text="??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=DatetimePickerAction(label='???????????????',
                                                            data='date_postback',
                                                            mode='date')),
                            QuickReplyButton(
                                action=MessageAction(label="???????????????", text="??????")),
                            QuickReplyButton(
                                action=MessageAction(label="????????????", text="??????"))
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
                        text="LINEID??????????????????????????????????????????????????????LINEID??????????????????")
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
                        kedate = kedate.strftime("%-Y???%-m???%-d???")
                        if kestr == "Mon":
                            kestr = "[???]"
                        elif kestr == "Tue":
                            kestr = "[???]"
                        elif kestr == "Wed":
                            kestr = "[???]"
                        elif kestr == "Thu":
                            kestr = "[???]"
                        elif kestr == "Fri":
                            kestr = "[???]"
                        elif kestr == "Sat":
                            kestr = "[???]"
                        elif kestr == "Sun":
                            kestr = "[???]"
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
                                kenumber = "???{}???\n???????????????????????????????????????".format(
                                    str(len(kenumber)))
                            except:
                                kenumber = "????????????"
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
                                    TextComponent(text="????????????", size='sm'),
                                    TextComponent(
                                        text=kedate + kestr, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="????????????????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=ketime, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=kenumber, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=keactiv, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=kenote, wrap=True)
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=kedate + kestr + "??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="?????????????????????", text="???????????????????????????")),
                                    QuickReplyButton(
                                        action=PostbackAction(label="????????????", data="??????????????????????????????")),
                                    QuickReplyButton(
                                        action=DatetimePickerAction(label='???????????????',
                                                                    data='date_postback',
                                                                    mode='date')),
                                    QuickReplyButton(
                                        action=MessageAction(label="????????????", text="??????")),
                                    QuickReplyButton(
                                        action=MessageAction(label="???????????????", text="??????")),
                                    QuickReplyButton(
                                        action=MessageAction(label="????????????", text="???")),
                                    QuickReplyButton(
                                        action=MessageAction(label="????????????", text="???"))
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
                                        text="??????????????????????????????????????????????????????????????????????????????????????????", quick_reply=QuickReply(
                                            items=[
                                                QuickReplyButton(
                                                    action=MessageAction(label="?????????????????????", text="??????????????????????????????")),
                                                QuickReplyButton(
                                                    action=MessageAction(label="????????????", text="??????"))
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
                                    text="?????????????????????????????????????????????\n??????????????????????????????????????????", quick_reply=QuickReply(
                                        items=[
                                            QuickReplyButton(
                                                action=DatetimePickerAction(label='???????????????',
                                                                            data='date_postback',
                                                                            mode='date')),
                                            QuickReplyButton(
                                                action=MessageAction(label="????????????", text="??????")),
                                            QuickReplyButton(
                                                action=MessageAction(label="???????????????", text="??????"))
                                        ]
                                    )
                                )
                            )
                            sys.exit()
                elif message == "??????????????????????????????":
                    try:
                        view_note_date = userdata["view_note_date"]
                        kedate = datetime(year=int(view_note_date[:4]), month=int(
                            view_note_date[5:7]), day=int(view_note_date[8:10]))
                        kedate = kedate.strftime("%-Y???%-m???%-d???")
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
                                    TextComponent(text="????????????", size='sm'),
                                    TextComponent(
                                        text=kedate + "\n?????????????????????????????????", weight='bold', size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(text=membersstr, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"),
                                    TextComponent(
                                        text="???" + membersint + "???", weight="bold", color="#7D7D7D"),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=kedate + "??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="????????????", text="??????"))
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
                                text="????????????ID??????????????????????????????????????????????????????????????????", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="????????????", text="??????")),
                                    ]
                                )
                            )
                        )
                        sys.exit()
                elif message == "??????":
                    note = ast.literal_eval(get("Notes")["Notes"])
                    notebook = list(note.items())[-1][1]
                    view_note_date = list(note.items())[-1][0]
                    view_note_number = list(
                        note.keys()).index(str(view_note_date))
                    kedate = datetime(year=int(view_note_date[:4]), month=int(
                        view_note_date[5:7]), day=int(view_note_date[8:10]))
                    kestr = str(kedate.strftime("%a"))
                    kedate = kedate.strftime("%-Y???%-m???%-d???")
                    if kestr == "Mon":
                        kestr = "[???]"
                    elif kestr == "Tue":
                        kestr = "[???]"
                    elif kestr == "Wed":
                        kestr = "[???]"
                    elif kestr == "Thu":
                        kestr = "[???]"
                    elif kestr == "Fri":
                        kestr = "[???]"
                    elif kestr == "Sat":
                        kestr = "[???]"
                    elif kestr == "Sun":
                        kestr = "[???]"
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
                            kenumber = "???{}???\n???????????????????????????????????????".format(
                                str(len(kenumber)))
                        except:
                            kenumber = "????????????"
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
                                TextComponent(text="????????????", size='sm'),
                                TextComponent(
                                    text=kedate + kestr, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(text="????????????????????????",
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
                                    text="???????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenumber, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=keactiv, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenote, wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=kedate + kestr + "??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="?????????????????????", text="???????????????????????????")),
                                QuickReplyButton(
                                    action=PostbackAction(label="????????????", data="??????????????????????????????")),
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='???????????????',
                                                                data='date_postback',
                                                                mode='date')),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="??????")),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="???"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif message == "???????????????????????????":
                    try:
                        view_note_date = userdata["view_note_date"]
                        kedate = datetime(year=int(view_note_date[:4]), month=int(
                            view_note_date[5:7]), day=int(view_note_date[8:10]))
                        kedate = kedate.strftime("%-Y???%-m???%-d???")
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
                                    TextComponent(text="????????????", size='sm'),
                                    TextComponent(
                                        text=kedate + "\n?????????????????????????????????", weight='bold', size='xl', wrap=True, adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(text=membersstr, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"),
                                    TextComponent(
                                        text="???" + membersint + "???", weight="bold", color="#7D7D7D"),
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=kedate + "??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="??????????????????", text="??????????????????")),
                                    QuickReplyButton(
                                        action=MessageAction(label="????????????", text="??????"))
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
                                text="????????????ID??????????????????????????????????????????????????????????????????", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=MessageAction(label="??????????????????", text="??????????????????")),
                                        QuickReplyButton(
                                            action=MessageAction(label="????????????", text="??????"))
                                    ]
                                )
                            )
                        )
                        sys.exit()
                elif message == "??????????????????":
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
                    kedate = kedate.strftime("%-Y???%-m???%-d???")
                    if kestr == "Mon":
                        kestr = "[???]"
                    elif kestr == "Tue":
                        kestr = "[???]"
                    elif kestr == "Wed":
                        kestr = "[???]"
                    elif kestr == "Thu":
                        kestr = "[???]"
                    elif kestr == "Fri":
                        kestr = "[???]"
                    elif kestr == "Sat":
                        kestr = "[???]"
                    elif kestr == "Sun":
                        kestr = "[???]"
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
                            kenumber = "???{}???\n???????????????????????????????????????".format(
                                str(len(kenumber)))
                        except:
                            kenumber = "????????????"
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
                                TextComponent(text="????????????", size='sm'),
                                TextComponent(
                                    text=kedate + kestr, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="????????????????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=ketime, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenumber, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=keactiv, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenote, wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=kedate + kestr + "??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="?????????????????????", text="???????????????????????????")),
                                QuickReplyButton(
                                    action=PostbackAction(label="????????????", data="??????????????????????????????")),
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='???????????????',
                                                                data='date_postback',
                                                                mode='date')),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="??????")),
                                QuickReplyButton(
                                    action=MessageAction(label="???????????????", text="??????")),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="???")),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="???"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif message == "??????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="???????????????????????????????????????")
                    )
                    sys.exit()
                elif message == "?????????":
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????????????????????????????????????????", quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='???????????????',
                                        data='date_postback',
                                        mode='date')),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="??????")),
                                QuickReplyButton(
                                    action=MessageAction(label="???????????????", text="??????"))
                            ])
                        )
                    )
                    sys.exit()

                if message == "???":
                    view_note_number = int(
                        userdata["view_note_number"])
                    view_note_number -= 1
                    if view_note_number < 0:
                        line_bot_api.reply_message(
                            event.reply_token,
                            TextSendMessage(
                                text="??????????????????????????????????????????????????????????????????????????????\n?????????????????????????????????????????????", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=DatetimePickerAction(label='???????????????',
                                                                        data='date_postback',
                                                                        mode='date')),
                                        QuickReplyButton(
                                            action=MessageAction(label="????????????", text="??????")),
                                        QuickReplyButton(
                                            action=MessageAction(label="???????????????", text="??????")),
                                        QuickReplyButton(
                                            action=MessageAction(label="????????????", text="???"))
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
                    kedate = kedate.strftime("%-Y???%-m???%-d???")
                    if kestr == "Mon":
                        kestr = "[???]"
                    elif kestr == "Tue":
                        kestr = "[???]"
                    elif kestr == "Wed":
                        kestr = "[???]"
                    elif kestr == "Thu":
                        kestr = "[???]"
                    elif kestr == "Fri":
                        kestr = "[???]"
                    elif kestr == "Sat":
                        kestr = "[???]"
                    elif kestr == "Sun":
                        kestr = "[???]"
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
                            kenumber = "???{}???\n???????????????????????????????????????".format(
                                str(len(kenumber)))
                        except:
                            kenumber = "????????????"
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
                                TextComponent(text="????????????", size='sm'),
                                TextComponent(
                                    text=kedate + kestr, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                TextComponent(
                                    text="????????????????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=ketime, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenumber, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=keactiv, wrap=True),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D"),
                                TextComponent(text=kenote, wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=kedate + kestr + "??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label="?????????????????????", text="???????????????????????????")),
                                QuickReplyButton(
                                    action=PostbackAction(label="????????????", data="??????????????????????????????")),
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='???????????????',
                                                                data='date_postback',
                                                                mode='date')),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="??????")),
                                QuickReplyButton(
                                    action=MessageAction(label="???????????????", text="??????")),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="???")),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="???"))
                            ]
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()
                elif message == "???":
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
                        kedate = kedate.strftime("%-Y???%-m???%-d???")
                        if kestr == "Mon":
                            kestr = "[???]"
                        elif kestr == "Tue":
                            kestr = "[???]"
                        elif kestr == "Wed":
                            kestr = "[???]"
                        elif kestr == "Thu":
                            kestr = "[???]"
                        elif kestr == "Fri":
                            kestr = "[???]"
                        elif kestr == "Sat":
                            kestr = "[???]"
                        elif kestr == "Sun":
                            kestr = "[???]"
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
                                kenumber = "???{}???\n???????????????????????????????????????".format(
                                    str(len(kenumber)))
                            except:
                                kenumber = "????????????"
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
                                    TextComponent(text="????????????", size='sm'),
                                    TextComponent(
                                        text=kedate + kestr, weight='bold', size='xl', adjustMode='shrink-to-fit'),
                                    TextComponent(text="\n"),
                                    TextComponent(
                                        text="????????????????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=ketime, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D"),
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
                                        text="???????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=keactiv, wrap=True),
                                    BoxComponent(
                                        layout="vertical",
                                        contents=[
                                            FillerComponent()
                                        ],
                                        height="10px"
                                    ),
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D"),
                                    TextComponent(text=kenote, wrap=True)
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text=kedate + kestr + "??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="?????????????????????", text="???????????????????????????")),
                                    QuickReplyButton(
                                        action=PostbackAction(label="????????????", data="??????????????????????????????")),
                                    QuickReplyButton(
                                        action=DatetimePickerAction(label='???????????????',
                                                                    data='date_postback',
                                                                    mode='date')),
                                    QuickReplyButton(
                                        action=MessageAction(label="????????????", text="??????")),
                                    QuickReplyButton(
                                        action=MessageAction(label="???????????????", text="??????")),
                                    QuickReplyButton(
                                        action=MessageAction(label="????????????", text="???")),
                                    QuickReplyButton(
                                        action=MessageAction(label="????????????", text="???"))
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
                                text="??????????????????????????????????????????????????????????????????????????????\n?????????????????????????????????????????????", quick_reply=QuickReply(
                                    items=[
                                        QuickReplyButton(
                                            action=DatetimePickerAction(label='???????????????',
                                                                        data='date_postback',
                                                                        mode='date')),
                                        QuickReplyButton(
                                            action=MessageAction(label="????????????", text="??????")),
                                        QuickReplyButton(
                                            action=MessageAction(label="???????????????", text="??????")),
                                        QuickReplyButton(
                                            action=MessageAction(label="????????????", text="???"))
                                    ]
                                )
                            )
                        )
                        sys.exit()
                else:
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        try:
            if (userdata["action_type"] == "calculation_orbit_observable") or (userdata["action_type"] == "calculation_orbit_all_information") or (userdata["action_type"] == "calculation_orbit_sun&moon_information"):
                if message == "????????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="??????????????????????????????????????????????????????")
                    )
                    sys.exit()
        except LineBotApiError:
            pass
        except KeyError:
            pass

        if message == "????????????":
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
                                text="?????????????????????????????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="???????????????????????????????????????????????????????????????????????????????????????\n?????????????????????????????????????????????", wrap=True),
                            TextComponent(text="\n"),
                            SeparatorComponent(),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            TextComponent(text="????????????????????????????????????????????????????????????????????????????????????\n?????????????????????????????????????????????????????????????????????", size='sm', wrap=True
                                          )
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="?????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=DatetimePickerAction(label='???????????????',
                                                            data='datetime_postback',
                                                            mode='datetime')),
                            QuickReplyButton(
                                action=PostbackAction(label='??????', data='ephemnow')),
                            QuickReplyButton(
                                action=MessageAction(label="????????????", text="????????????")),
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
                        text="LINEID??????????????????????????????????????????????????????LINEID??????????????????")
                )
                sys.exit()

        opemanual = re.search("???????????????|?????????|?????????", message)
        opedome = re.search("?????????", message)
        opetelescope = re.search("?????????", message)
        opecamera = re.search("?????????", message)

        queshowmoon = re.search("???", message) and re.search(
            "??????|??????|????????????", message)
        queshowsun = re.search("??????", message) and re.search(
            "??????|??????|????????????", message)
        questarvalue = re.search("????????????|??????", message) and re.search(
            "??????|??????|??????", message)

        opesendai = re.search("??????", message)
        opeizumi = re.search("??????", message)
        opeaoba = re.search("?????????", message)
        opemiyagino = re.search("????????????", message)
        opetaihaku = re.search("?????????", message)
        opewakaba = re.search("?????????", message)
        opetomiya = re.search("??????", message)
        opetagajo = re.search("?????????", message)
        opeshiroishi = re.search("??????", message)
        openatori = re.search("??????", message)

        opecnt3 = re.search("????????????|????????????|???????????????|4???|??????|??????", message)
        opecnt2 = re.search("?????????|????????????|3???|??????|??????", message)
        opecnt1 = re.search("??????|?????????|2???|??????|??????", message)
        opecnt0 = re.search("??????|?????????", message)

        flag_weather_operation_weather = False
        weatherif = re.search("??????|?????????|??????|????????????|??????", message)
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
            setlocation("????????????????????????", "218979")
        elif opeaoba:
            setlocation("???????????????????????????", "218962")
        elif opemiyagino:
            setlocation("??????????????????????????????", "219001")
        elif opetaihaku:
            setlocation("???????????????????????????", "218963")
        elif opewakaba:
            setlocation("???????????????????????????", "219002")
        elif opesendai:
            setlocation("??????????????????", "224683")
        elif opetomiya:
            setlocation("??????????????????", "218974")
        elif opetagajo:
            setlocation("?????????????????????", "218961")
        elif opeshiroishi:
            setlocation("??????????????????", "218990")
        elif openatori:
            setlocation("??????????????????", "218958")

        def settime(datecnt, datenum):
            global weather_month_of_date, weather_date_full_next_day, weather_date_full_previous_day, weather_date_full, weather_days_delta, dayflag, moon, sun
            dayflag = True
            weather_month_of_date = int(datecnt.strftime("%m"))
            weather_date_full_next_day = (datecnt +
                                          timedelta(days=1)).strftime("%d")
            weather_date_full_previous_day = (datecnt -
                                              timedelta(days=1)).strftime("%d")
            weather_date_full = datecnt.strftime("%-Y???%-m???%-d???")
            weather_days_delta = datenum

            global quickday
            if weather_days_delta == 0:
                weather_date_full = "??????(" + weather_date_full + ")"
                quickday = QuickReplyButton(
                    action=MessageAction(label="??????", text="?????????????????????"))
            elif weather_days_delta == 1:
                weather_date_full = "??????(" + weather_date_full + ")"
                quickday = QuickReplyButton(
                    action=MessageAction(label="??????", text="?????????????????????"))
            elif weather_days_delta == 2:
                weather_date_full = "????????????(" + weather_date_full + ")"
                quickday = QuickReplyButton(
                    action=MessageAction(label="??????", text="?????????????????????"))
            elif weather_days_delta == 3:
                weather_date_full = "???????????????(" + weather_date_full + ")"
                quickday = QuickReplyButton(
                    action=MessageAction(label="??????", text="?????????????????????"))

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
                action=MessageAction(label="??????", text="?????????????????????"))
        elif weather_days_delta == 1:
            quickday = QuickReplyButton(
                action=MessageAction(label="??????", text="?????????????????????"))
        elif weather_days_delta == 2:
            quickday = QuickReplyButton(
                action=MessageAction(label="??????", text="?????????????????????"))
        elif weather_days_delta == 3:
            quickday = QuickReplyButton(
                action=MessageAction(label="??????", text="?????????????????????"))

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
                kobun = date.strftime("%-H???%-M???")
                if deltaday.days == 1:
                    plus = "??????,"
                    kobun = plus + kobun
                elif deltaday.days > 1:
                    plus = str(deltaday.days) + "??????,"
                    kobun = plus + kobun
                elif deltaday.days == -1:
                    plus = "??????,"
                    kobun = plus + kobun
                elif deltaday.days < -1:
                    plus = str(abs(deltaday.days)) + "??????,"
                    kobun = plus + kobun
                if kobun[-3:] == "???0???":
                    return kobun[:-2]
                else:
                    return kobun

            if timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage) == "????????????":
                moon_visual = "????????????"
            else:
                moon_visual = timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[
                                      0]) + "??????\n" + timeFix(timespan(moonrise, moonset, sunset, sunriseafterset, cutmoonage)[1]) + "???????????????\n?????????????????????"
            if weather_location_id == None or weather_days_delta == None:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="??????????????????????????????????????????????????????????????????(LINEID????????????????????????????????????????????????????????????)")
                )
                sys.exit()

            dataloc = weather_location_name + "date"
            if datenow > (get("WeatherData")[dataloc] + timedelta(hours=2)):
                try:
                    try:
                        line_bot_api.push_message(
                            event.source.user_id, [
                                TextSendMessage(text="??????????????????????????????????????????????????????"),
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
                                text="API???????????????????????????????????????????????????????????????????????????????????????")
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
                            text="API???????????????????????????????????????????????????????????????????????????????????????")
                    )
                    sys.exit()

            weather_datajson = ast.literal_eval(
                get("WeatherData")[weather_location_name])

            tempunit = "??C"
            try:
                dataFixed = weather_datajson["DailyForecasts"][weather_days_delta]

                if cutmoonage == "0":
                    moonage = moonage + "????????????"
                elif cutmoonage == "1":
                    moonage = moonage + "????????????"
                elif cutmoonage == "2":
                    moonage = moonage + "???????????????"
                elif cutmoonage == "7":
                    moonage = moonage + "????????????"
                elif cutmoonage == "9":
                    moonage = moonage + "??????????????????"
                elif cutmoonage == "12":
                    moonage = moonage + "??????????????????"
                elif cutmoonage == "13":
                    moonage = moonage + "???????????????"
                elif cutmoonage == "14":
                    moonage = moonage + "????????????"
                elif cutmoonage == "15":
                    moonage = moonage + "??????????????????"
                elif cutmoonage == "16":
                    moonage = moonage + "???????????????"
                elif cutmoonage == "17":
                    moonage = moonage + "???????????????"
                elif cutmoonage == "18":
                    moonage = moonage + "???????????????"
                elif cutmoonage == "19":
                    moonage = moonage + "???????????????"
                elif cutmoonage == "22":
                    moonage = moonage + "????????????"
                elif cutmoonage == "25":
                    moonage = moonage + "???????????????"
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
                        text="AccuWeather API???????????????????????????????????????????????????????????????????????????????????????????????????")
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
                    temptext = "???????????????????????????"
                elif (averagetemp >= 8) and (averagetemp < 17):
                    temptext = "???????????????????????????"
                elif averagetemp >= 17:
                    temptext = "???????????????????????????"
            elif (weather_month_of_date >= 6) and (weather_month_of_date <= 8):
                if averagetemp < 20:
                    temptext = "??????????????????????????????"
                elif (averagetemp >= 20) and (averagetemp < 32):
                    temptext = "????????????????????????"
                elif averagetemp >= 32:
                    temptext = "?????????????????????????????????"
            elif (weather_month_of_date >= 9) and (weather_month_of_date <= 11):
                if averagetemp < 9:
                    temptext = "???????????????????????????"
                elif (averagetemp >= 9) and (averagetemp < 15):
                    temptext = "???????????????????????????"
                elif averagetemp >= 15:
                    temptext = "???????????????????????????"
            elif (weather_month_of_date == 12) or (weather_month_of_date <= 2):
                if averagetemp < -3:
                    temptext = "?????????????????????????????????"
                elif (averagetemp >= -3) and (averagetemp < 11):
                    temptext = "????????????????????????"
                elif averagetemp >= 11:
                    temptext = "??????????????????????????????"
            global dayrain, daysnow, nightrain, nightsnow
            if dayrainpro == "0":
                if daysnowpro == "0":
                    daysnow = FillerComponent()
                    dayrain = FillerComponent()
                else:
                    daysnow = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=daysnowpro + "%", flex=1, align="center", wrap=True), ])
                    dayrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=dayrainpro + "%", flex=1, align="center", wrap=True), ])
            else:
                if daysnowpro == "0":
                    daysnow = FillerComponent()
                    dayrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=dayrainpro + "%", flex=1, align="center", wrap=True), ])
                else:
                    daysnow = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=daysnowpro + "%", flex=1, align="center", wrap=True), ])
                    dayrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=dayrainpro + "%", flex=1, align="center", wrap=True), ])

            if nightrainpro == "0":
                if nightsnowpro == "0":
                    nightsnow = FillerComponent()
                    nightrain = FillerComponent()
                else:
                    nightrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=nightrainpro + "%", flex=1, align="center", wrap=True), ])
                    nightsnow = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=nightsnowpro + "%", flex=1, align="center", wrap=True), ])
            else:
                if nightsnowpro == "0":
                    nightsnow = FillerComponent()
                    nightrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=nightrainpro + "%", flex=1, align="center", wrap=True), ])
                else:
                    nightrain = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=nightrainpro + "%", flex=1, align="center", wrap=True), ])
                    nightsnow = BoxComponent(layout="horizontal", contents=[TextComponent(
                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1), TextComponent(text=nightsnowpro + "%", flex=1, align="center", wrap=True), ])

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
                            TextComponent(text="???????????????", size='sm'),
                            TextComponent(text=nightphrase, weight='bold',
                                          size='xxl', wrap=True, adjustMode='shrink-to-fit'),
                            TextComponent(text="\n"),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=averagetempstr + tempunit, flex=1, align="center", wrap=True),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=temptext, flex=1, align="center", wrap=True),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(text=hightemp + tempunit,
                                                  flex=1, align="center"),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=lowtemp + tempunit, flex=1, align="center", wrap=True),
                                ]
                            ),
                            TextComponent(text="\n"),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="??????????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
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
                                        text="??????????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=daycloudcover + "%", flex=1, wrap=True, align="center"),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="??????????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=daywinddir + "???" + daywindsp + "m/s", flex=1, wrap=True, align="center"),
                                ]
                            ),
                            TextComponent(text="\n"),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="??????????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
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
                                        text="??????????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=nightcloudcover + "%", flex=1, wrap=True, align="center"),
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="??????????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                    TextComponent(
                                        text=nightwinddir + "???" + nightwindsp + "m/s", flex=1, wrap=True, align="center"),
                                ]
                            )
                        ]
                    )
                )
                flex = FlexSendMessage(
                    alt_text=weather_date_full + "???" + weather_location_name + "??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=PostbackAction(label='????????????', data='selectdate')),
                            quickday,
                            QuickReplyButton(
                                action=MessageAction(label="?????????", text="???????????????????????????"))
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
                                TextComponent(text="17???????????????", size='sm'),
                                TextComponent(text=moonage, weight='bold',
                                              size='3xl', wrap=True, adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="17???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=moonage, flex=1, wrap=True, align="center"),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(moonrise), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="?????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(moontransit), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(text=str(southmoonalt) + "??",
                                                      flex=1, align="center"),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(moonset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                TextComponent(
                                    text="???????????????", weight="bold", color="#7D7D7D", wrap=True),
                                TextComponent(
                                    text=moon_visual, align="center", wrap=True),
                            ]
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=weather_date_full + "???" + weather_location_name + "??????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label='????????????', data='selectdate')),
                                quickday,
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="?????????????????????")),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="?????????????????????????????????"))
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
                                TextComponent(text="?????????", size='sm'),
                                TextComponent(text=timeFix(sunset), weight='bold',
                                              size='3xl', wrap=True, adjustMode='shrink-to-fit'),
                                TextComponent(text="\n"),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(sunrise), flex=1, wrap=True, align="center"),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="?????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(suntransit), flex=1, align="center", wrap=True),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="???????????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(text=str(southsunalt) + "??",
                                                      flex=1, align="center"),
                                    ]
                                ),
                                BoxComponent(
                                    layout="horizontal",
                                    contents=[
                                        TextComponent(
                                            text="?????????", weight="bold", color="#7D7D7D", wrap=True, flex=1),
                                        TextComponent(
                                            text=timeFix(sunset), flex=1, align="center", wrap=True),
                                    ]
                                ),
                            ]
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=weather_date_full + "???" + weather_location_name + "?????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label='????????????', data='selectdate')),
                                quickday,
                                QuickReplyButton(
                                    action=MessageAction(label="?????????", text="?????????????????????????????????"))
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
                                TextComponent(text="?????????????????????", size='sm'),
                                TextComponent(text=hoshizora, weight='bold',
                                              size='3xl', wrap=True, adjustMode='shrink-to-fit'),
                            ]
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text=weather_date_full + "???" + weather_location_name + "????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label='????????????', data='selectdate')),
                                quickday,
                                QuickReplyButton(
                                    action=MessageAction(label="?????????", text="?????????????????????????????????")),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="??????????????????????????????")),
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
                TextSendMessage(text="???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????\n?????????????????????????????????????????????\n\n\n"
                                "????????????????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkPESuU6Bc7-Bwbpg?e=hwWdAV\n\n"
                                "??????????????????????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkSOgArvp_HKRuGZg?e=3oqveZ\n\n"
                                "???????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJhjElqcc9aqk8jPoA?e=dZc7oo")
            )
            sys.exit()
        elif opemanual and opetelescope:
            try:
                reset_user_data()
            except:
                pass
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="??????????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hMdJM8VjX0a1RgfuRw?e=hGfPX9\n\n"
                                "??????????????????????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkSOgArvp_HKRuGZg?e=3oqveZ\n\n"
                                "???????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJhjElqcc9aqk8jPoA?e=dZc7oo")
            )
            sys.exit()
        elif opemanual and opecamera:
            try:
                reset_user_data()
            except:
                pass
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="???????????????????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hMdJM8VjX0a1RgfuRw?e=iJSrGN\n\n"
                                "??????????????????????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkQ_D6GWgydD0am4g?e=OBn4RC\n\n"
                                "??????????????????????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkSOgArvp_HKRuGZg?e=3oqveZ\n\n"
                                "???????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJhjElqcc9aqk8jPoA?e=dZc7oo")
            )
            sys.exit()
        elif opemanual:
            try:
                reset_user_data()
            except:
                pass
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="??????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hMdG0-dc8XFyY1xoTg?e=qOVAjK\n\n"
                                "?????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJh5BN4l2YXcmxT2Ww?e=kgnQWA\n\n"
                                "??????????????????????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJkSOgArvp_HKRuGZg?e=3oqveZ\n\n"
                                "???????????????????????????????????????\nhttps://1drv.ms/u/s!Aln_7X9LsSg4hJhjElqcc9aqk8jPoA?e=dZc7oo")
            )
            sys.exit()

        if message == "AOP??????":
            try:
                reset_user_data()
            except:
                pass
            try:
                datapoint = get("Points")
                datapointid = get("PointsID")
                pointsdat = ast.literal_eval(
                    datapoint[datapointid[event.source.user_id]])
                season = datapoint["????????????"]
                userpoints = str(pointsdat["Points"])
                userattendance = str(pointsdat["Attendance"])
                userattendance = userattendance + "???"
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
                                text="??????AOP???", wrap=True),
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
                                        text="????????????{}\n????????????".format(season), wrap=True, size="sm", align="center", flex=1),
                                    TextComponent(
                                        text="????????????{}\n?????????".format(season), wrap=True, size="sm", align="center", flex=1),
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
                    alt_text="??????AOP???????????????????????????", contents=bubble
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
                                text="????????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="??????????????????????????????\n??????????????????????????????????????????????????????????????????\n??????????????????g-c(nn)name?????????????????????????????????\n??????1-A(01)????????????\n4-1(01)????????????", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????", size="xs", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="??????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=MessageAction(label="?????????", text="?????????"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
        try:
            if userdata["action_type"] == "registering_member":
                if message == "?????????":
                    reset_user_data()
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="???????????????????????????????????????")
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
                                        text="?????????????????????", weight="bold", size="xl", wrap=True),
                                    TextComponent("\n"),
                                    TextComponent(
                                        text="???????????????????????????LINE???????????????????????????????????????????????????????????????????????????????????????", wrap=True),
                                    TextComponent(
                                        text="??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????", size="sm", wrap=True
                                    )
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="?????????????????????", contents=bubble)
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
                                        text="??????????????????", weight="bold", size="xl", wrap=True),
                                    TextComponent("\n"),
                                    TextComponent(
                                        text="????????????????????????{}????????????????????????????????????".format(message[7:]), wrap=True)
                                ],
                            )
                        )
                        flex = FlexSendMessage(
                            alt_text="?????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label="AOP??????", text="AOP??????"))
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
                                    text="?????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="{}????????????????????????????????????\n?????????????????????????????????????????????????????????????????????".format(message), wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="?????????????????????", contents=bubble)
                    line_bot_api.reply_message(event.reply_token, flex)
                    reset_user_data()
                    sys.exit()
        except SystemExit:
            sys.exit()
        except:
            pass

        if message[:9] == "???????????????????????????":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="????????????????????????????????????????????????")
            )
            line_bot_api.push_message(
                idmappi, [
                    TextSendMessage(text="????????????????????????" + message[8:]),
                ]
            )
            sys.exit()

        try:
            reset_user_data()
        except:
            pass

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="???????????????????????????????????????\n??????????????????????????????????????????")
        )
        sys.exit()

    except SystemExit:
        pass

    except:
        errormessage = str(traceback.format_exc().replace(
            "Traceback (most recent call last)", "????????????????????????"))
        line_bot_api.push_message(
            idmappi, [
                TextSendMessage(text="????????????????????????????????????????????????\n\n" + errormessage),
            ]
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
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
                text="LINEID????????????????????????????????????")
        )

    try:
        if event.postback.data == "????????????":
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
                            text="?????????????????????(AOP+3P)")
                    )
                    sys.exit()
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="???????????????????????????(?????????????????????????????????????)")
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
                            text="????????????????????????AOP????????????????????????????????????")
                    )
                    sys.exit()
                except:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                            text="?????????????????????????????????")
                    )
                    sys.exit()
    except:
        pass

    try:
        if event.postback.data == 'date_postback' and userdata["action_type"] == "view_note":
            viewdatemessage = event.postback.params['date']
            confirm_template = ConfirmTemplate(text='??????????????????????????????????????????????????????', actions=[
                MessageAction(label='??????', text=viewdatemessage),
                MessageAction(label='?????????', text='?????????'),
            ])
            template_message = TemplateSendMessage(
                alt_text='??????????????????????????????????????????????????????', template=confirm_template)
            line_bot_api.reply_message(event.reply_token, template_message)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == 'date_postback') and (userdata["action_type"] == "write_note"):
            viewdatemessage = event.postback.params['date']
            confirm_template = ConfirmTemplate(text='???????????????????????????????????????', actions=[
                MessageAction(label='??????', text=viewdatemessage),
                MessageAction(label='?????????', text='?????????'),
            ])
            template_message = TemplateSendMessage(
                alt_text='???????????????????????????????????????', template=confirm_template)
            line_bot_api.reply_message(event.reply_token, template_message)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "date_postback") and (userdata["action_type"] == "register_activity"):
            viewdatemessage = event.postback.params['date']
            confirm_template = ConfirmTemplate(text='???????????????????????????????????????', actions=[
                MessageAction(label='??????', text=viewdatemessage),
                MessageAction(label='?????????', text='?????????'),
            ])
            template_message = TemplateSendMessage(
                alt_text='???????????????????????????????????????', template=confirm_template)
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
                                text="???????????????????????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="?????????????????????????????????????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=DatetimePickerAction(label='?????????????????????',
                                                            data='time_postback',
                                                            mode='time')),
                            QuickReplyButton(
                                action=MessageAction(label="????????????", text="????????????"))
                        ]
                    )
                )
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEID????????????????????????????????????")
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
                            text="?????????????????????????????????????????????????????????????????????\n??????????????????????????????????????????")
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
                                text="???????????????????????????????????????????????????????????????", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='??????', data='??????'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='??????', data='??????'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='???', data='???'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='???', data='???'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='???????????????', data='???????????????'),
                            ),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="????????????????????????????????????", contents=bubble)
                line_bot_api.reply_message(
                    event.reply_token, flex)
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEID????????????????????????????????????"))
                sys.exit()
    except:
        pass

    try:
        if event.postback.data == "time_postback" and userdata["action_type"] == "register_activity_start_time":
            try:
                register_activity_start_time = event.postback.params['time']
                if userdata["register_activity_observe_or_not"] == "??????(????????????)":
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
                                    text="????????????????????????\n(????????????)?????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="???????????????????????????????????????????????????????????????????????????????????????????????????", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="??????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='???????????????????????????',
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
                                    text="?????????????????????????????????", weight="bold", size="xl", wrap=True),
                                TextComponent("\n"),
                                TextComponent(
                                    text="???????????????????????????????????????????????????????????????????????????", wrap=True)
                            ],
                        )
                    )
                    flex = FlexSendMessage(
                        alt_text="??????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='???????????????????????????',
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
                        text="LINEID????????????????????????????????????")
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
                            text="?????????????????????????????????????????????????????????????????????\n??????????????????????????????????????????")
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
                                text="????????????????????????\n(????????????)?????????", weight="bold", size="xl", wrap=True),
                            TextComponent("\n"),
                            TextComponent(
                                text="????????????????????????????????????????????????????????????????????????????????????????????????????????????", wrap=True)
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="??????????????????????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                        items=[
                            QuickReplyButton(
                                action=DatetimePickerAction(label='???????????????????????????',
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
                        text="LINEID????????????????????????????????????"))
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
                            text="?????????????????????????????????????????????????????????????????????\n??????????????????????????????????????????")
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
                confirm_template = ConfirmTemplate(text='????????????????????????????????????', actions=[
                    MessageAction(label='??????', text="???????????????"),
                    MessageAction(label='?????????', text="????????????"),
                ])
                template_message = TemplateSendMessage(
                    alt_text='????????????????????????????????????', template=confirm_template)
                line_bot_api.reply_message(event.reply_token, template_message)
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEID????????????????????????????????????"))
                sys.exit()
    except:
        pass

    try:
        if (((event.postback.data == "datetime_postback") or (event.postback.data == "ephemnow") or (event.postback.data == "????????????????????????") or (event.postback.data == "???????????????????????????") or (event.postback.data == "??????????????????") or (event.postback.data == "plus_one_minute") or (event.postback.data == "plus_one_hour") or (event.postback.data == "plus_one_day") or (event.postback.data == "back_to_info")) and ((userdata["action_type"] == "calculation_orbit_observable") or (userdata["action_type"] == "calculation_orbit_sun&moon_information") or (userdata["action_type"] == "calculation_orbit_all_information") or (userdata["action_type"] == "view_note"))) or ((event.postback.data == "??????????????????????????????") and userdata["action_type"] == "view_note"):
            ephem_center_date = str()
            if event.postback.data == "ephemnow":
                datetoday = datetime.now() + timedelta(hours=9)
                ephem_center_date = datetoday.strftime("%Y-%m-%dT%H:%M")
            elif event.postback.data == "datetime_postback":
                ephem_center_date = event.postback.params['datetime']
            elif event.postback.data == "back_to_info":
                ephem_center_date = userdata["calculation_orbit_date"]
            elif event.postback.data == "????????????????????????":
                if userdata["action_type"] == "view_note":
                    ephem_center_date = userdata["calculation_orbit_date"]
                else:
                    userdata["action_type"] = "calculation_orbit_observable"
                    update(event.source.user_id, "action_type",
                           "calculation_orbit_observable")
                    ephem_center_date = userdata["calculation_orbit_date"]
            elif event.postback.data == "???????????????????????????":
                if userdata["action_type"] == "view_note":
                    ephem_center_date = userdata["calculation_orbit_date"]
                else:
                    userdata["action_type"] = "calculation_orbit_sun&moon_information"
                    update(event.source.user_id, "action_type",
                           "calculation_orbit_sun&moon_information")
                    ephem_center_date = userdata["calculation_orbit_date"]
            elif event.postback.data == "??????????????????":
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
            elif event.postback.data == "??????????????????????????????":
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
                ephem_center_date, "%Y-%m-%dT%H:%M").strftime("%-Y???%-m???%-d??? %-H???%-M???")
            if date_and_time[-3:] == "???0???":
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
                min_string_sun = "?????????"
            elif min_delta_sun == delta_sunset:
                min_string_sun = "??????"
            moment_moonaz = round(degrees(moon.az), 1)
            moment_moonalt = round(degrees(moon.alt), 1)
            moment_moonage = round(
                tglocation.date - ephem.previous_new_moon(tglocation.date), 1)
            moment_moonage_round = str(round(moment_moonage))
            moment_moonage = str(moment_moonage)
            if moment_moonage_round == "0":
                moment_moonage = moment_moonage + "????????????"
            elif moment_moonage_round == "1":
                moment_moonage = moment_moonage + "????????????"
            elif moment_moonage_round == "2":
                moment_moonage = moment_moonage + "???????????????"
            elif moment_moonage_round == "7":
                moment_moonage = moment_moonage + "????????????"
            elif moment_moonage_round == "9":
                moment_moonage = moment_moonage + "??????????????????"
            elif moment_moonage_round == "12":
                moment_moonage = moment_moonage + "??????????????????"
            elif moment_moonage_round == "13":
                moment_moonage = moment_moonage + "???????????????"
            elif moment_moonage_round == "14":
                moment_moonage = moment_moonage + "????????????"
            elif moment_moonage_round == "15":
                moment_moonage = moment_moonage + "??????????????????"
            elif moment_moonage_round == "16":
                moment_moonage = moment_moonage + "???????????????"
            elif moment_moonage_round == "17":
                moment_moonage = moment_moonage + "???????????????"
            elif moment_moonage_round == "18":
                moment_moonage = moment_moonage + "???????????????"
            elif moment_moonage_round == "19":
                moment_moonage = moment_moonage + "???????????????"
            elif moment_moonage_round == "22":
                moment_moonage = moment_moonage + "????????????"
            elif moment_moonage_round == "25":
                moment_moonage = moment_moonage + "???????????????"
            moment_nextmoonrise = (tglocation.next_rising(
                moon)).datetime() + timedelta(hours=9)
            moment_nextmoonset = (tglocation.next_setting(
                moon)).datetime() + timedelta(hours=9)
            delta_moonrise = moment_nextmoonrise - ephemdatenow
            delta_moonset = moment_nextmoonset - ephemdatenow
            min_delta_moon = min(delta_moonrise, delta_moonset)
            min_string_moon = str()
            if min_delta_moon == delta_moonrise:
                min_string_moon = "?????????"
            elif min_delta_moon == delta_moonset:
                min_string_moon = "????????????"
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
                kobun = "{0}??????{1}???".format(str(hours), str(minutes))
                if kobun[:3] == "0??????":
                    kobun = kobun[3:]
                return kobun

            def timeFix(date):
                deltaday = date - rsdate
                if date.second >= 30:
                    date = date + timedelta(minutes=1)
                kobun = date.strftime("%-H???%-M???")
                if deltaday.days == 1:
                    plus = "??????,"
                    kobun = plus + kobun
                elif deltaday.days > 1:
                    plus = str(deltaday.days) + "??????,"
                    kobun = plus + kobun
                elif deltaday.days == -1:
                    plus = "??????,"
                    kobun = plus + kobun
                elif deltaday.days < -1:
                    plus = str(abs(deltaday.days)) + "??????,"
                    kobun = plus + kobun
                if kobun[-3:] == "???0???":
                    return kobun[:-2]
                else:
                    return kobun

            if ((event.postback.data == "??????????????????") or (userdata["action_type"] == "calculation_orbit_all_information") or (event.postback.data == "????????????????????????") or (userdata["action_type"] == "calculation_orbit_observable") or (event.postback.data == "??????????????????????????????")):
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

                sun_visual = timeFix(day_sunrise) + "??????\n" + \
                    timeFix(day_sunset) + "???????????????"
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
                            text="??????", align="center", weight="bold", color="#7D7D7D"
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
                                text="??????", align="center", weight="bold", color="#7D7D7D",),
                            TextComponent(
                                text=timeFix(day_sunset) + "???????????????\n?????????" + deltaFix((day_sunset - ephemdatenow)) + "???", align="center", wrap=True)
                        ]
                    )
                change_thumbnail = False
                if timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage) == "????????????":
                    moon_visual = "????????????"
                else:
                    moon_visual = timeFix(timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage)[
                        0]) + "??????\n" + timeFix(timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage)[1]) + "???????????????"
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
                                text="???", align="center", weight="bold", color="#7D7D7D"
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
                                    text="???", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage)[1]) + "???????????????\n?????????" + deltaFix((timespan(day_moonrise, day_moonset, day_sunset, day_sunriseafterset, cutmoonage)[1] - ephemdatenow)) + "???\n?????????" + str(moment_moonage), align="center", wrap=True)
                            ]
                        )

                if planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset) == "????????????":
                    mercury_visual = "????????????"
                else:
                    mercury_visual = timeFix(planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset)[
                        0]) + "??????\n" + timeFix(planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset)[1]) + "???????????????"
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
                                text="??????", align="center", weight="bold", color="#7D7D7D"
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
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset)[1]) + "???????????????\n?????????" + deltaFix((planet_timespan(day_mercuryrise, day_mercuryset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "???", align="center", wrap=True)
                            ]
                        )

                if planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset) == "????????????":
                    venus_visual = "????????????"
                else:
                    venus_visual = timeFix(planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset)[
                        0]) + "??????\n" + timeFix(planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset)[1]) + "???????????????"
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
                                text="??????", align="center", weight="bold", color="#7D7D7D"
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
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset)[1]) + "???????????????\n?????????" + deltaFix((planet_timespan(day_venusrise, day_venusset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "???", align="center", wrap=True)
                            ]
                        )

                if planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset) == "????????????":
                    mars_visual = "????????????"
                else:
                    mars_visual = timeFix(planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset)[
                        0]) + "??????\n" + timeFix(planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset)[1]) + "???????????????"
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
                                text="??????", align="center", weight="bold", color="#7D7D7D"
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
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset)[1]) + "???????????????\n?????????" + deltaFix((planet_timespan(day_marsrise, day_marsset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "???", align="center", wrap=True)
                            ]
                        )

                if planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset) == "????????????":
                    jupiter_visual = "????????????"
                else:
                    jupiter_visual = timeFix(planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset)[
                        0]) + "??????\n" + timeFix(planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset)[1]) + "???????????????"
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
                                text="??????", align="center", weight="bold", color="#7D7D7D"
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
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset)[1]) + "???????????????\n?????????" + deltaFix((planet_timespan(day_jupiterrise, day_jupiterset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "???", align="center", wrap=True)
                            ]
                        )

                if planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset) == "????????????":
                    saturn_visual = "????????????"
                else:
                    saturn_visual = timeFix(planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset)[
                        0]) + "??????\n" + timeFix(planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset)[1]) + "???????????????"
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
                                text="??????", align="center", weight="bold", color="#7D7D7D"
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
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset)[1]) + "???????????????\n?????????" + deltaFix((planet_timespan(day_saturnrise, day_saturnset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "???", align="center", wrap=True)
                            ]
                        )
                if planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset) == "????????????":
                    uranus_visual = "????????????"
                else:
                    uranus_visual = timeFix(planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset)[
                        0]) + "??????\n" + timeFix(planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset)[1]) + "???????????????"
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
                                text="?????????", align="center", weight="bold", color="#7D7D7D"
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
                                    text="?????????", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset)[1]) + "???????????????\n?????????" + deltaFix((planet_timespan(day_uranusrise, day_uranusset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "???", align="center", wrap=True)
                            ]
                        )
                if planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset) == "????????????":
                    neptune_visual = "????????????"
                else:
                    neptune_visual = timeFix(planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset)[
                        0]) + "??????\n" + timeFix(planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset)[1]) + "???????????????"
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
                                text="?????????", align="center", weight="bold", color="#7D7D7D"
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
                                    text="?????????", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset)[1]) + "???????????????\n?????????" + deltaFix((planet_timespan(day_neptunerise, day_neptuneset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "???", align="center", wrap=True)
                            ]
                        )
                if planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset) == "????????????":
                    pluto_visual = "????????????"
                else:
                    pluto_visual = timeFix(planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset)[
                        0]) + "??????\n" + timeFix(planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset)[1]) + "???????????????"
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
                                text="?????????", align="center", weight="bold", color="#7D7D7D"
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
                                    text="?????????", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset)[1]) + "???????????????\n?????????" + deltaFix((planet_timespan(day_plutorise, day_plutoset, day_sunset, day_sunriseafterset)[1] - ephemdatenow)) + "???", align="center", wrap=True)
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
                                text="????????????????????????", align="center", wrap=True)
                        ]
                    )

                if change_thumbnail:
                    thumbnail = 'https://raw.githubusercontent.com/SkyRadia/AstroONLINE/main/Images/' + \
                        cutmoonage + '.jpg'
                else:
                    thumbnail = 'https://raw.githubusercontent.com/Washohku/Sources/main/%E8%BB%8C%E9%81%93%E8%A8%88%E7%AE%97.jpg'

                if (event.postback.data == "??????????????????") or (userdata["action_type"] == "calculation_orbit_all_information"):
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
                                    text="??????????????????????????????", wrap=True, size="xxs", color="#7D7D7D", align="center"),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="??????????????????", size="lg",
                                              weight="bold", color="#4A4A4A"),
                                TextComponent(
                                    text="????????????~???????????????", size="sm", color="#7D7D7D", flex=1),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                TextComponent(
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
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
                                    text="???", align="center", weight="bold", color="#7D7D7D"),
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
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
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
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
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
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
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
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
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
                                    text="??????", align="center", weight="bold", color="#7D7D7D"),
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
                                    text="?????????", align="center", weight="bold", color="#7D7D7D"),
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
                                    text="?????????", align="center", weight="bold", color="#7D7D7D"),
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
                                    text="?????????", align="center", weight="bold", color="#7D7D7D"),
                                TextComponent(
                                    text=timeFix(day_plutorise) + "~" + timeFix(day_plutoset), align="center", wrap=True),
                            ]
                        )
                    )
                    if userdata["action_type"] == "view_note":
                        all_data_flex = FlexSendMessage(
                            alt_text="???????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label='??????????????????', text='??????????????????')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='????????????????????????', data='????????????????????????')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='???????????????????????????', data='???????????????????????????'))
                                ]
                            )
                        )

                    else:
                        all_data_flex = FlexSendMessage(
                            alt_text="???????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=PostbackAction(label='????????????????????????', data='????????????????????????')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='???????????????????????????', data='???????????????????????????')),
                                    QuickReplyButton(
                                        action=DatetimePickerAction(label='???????????????',
                                                                    data='datetime_postback',
                                                                    mode='datetime')),
                                    QuickReplyButton(
                                        action=MessageAction(label="????????????", text="????????????")),
                                    QuickReplyButton(
                                        action=PostbackAction(label='+1???', data='plus_one_day'))
                                ]
                            )
                        )
                    flex = all_data_flex
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

                elif (event.postback.data == "????????????????????????") or (userdata["action_type"] == "calculation_orbit_observable") or (event.postback.data == "??????????????????????????????"):
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
                                    text="??????????????????????????????", wrap=True, size="xxs", color="#7D7D7D", align="center"),
                                BoxComponent(
                                    layout="vertical",
                                    contents=[
                                        FillerComponent()
                                    ],
                                    height="10px"
                                ),
                                SeparatorComponent(),
                                TextComponent(text="\n"),
                                TextComponent(text="???????????????????????????", size="lg",
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
                                TextComponent(text="????????????????????????", size="lg",
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
                            alt_text="???????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=MessageAction(label='??????????????????', text='??????????????????')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='???????????????????????????', data='???????????????????????????')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='??????????????????', data='??????????????????'))
                                ]
                            )
                        )
                    else:
                        observable_flex = FlexSendMessage(
                            alt_text="???????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                                items=[
                                    QuickReplyButton(
                                        action=PostbackAction(label='???????????????????????????', data='???????????????????????????')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='??????????????????', data='??????????????????')),
                                    QuickReplyButton(
                                        action=DatetimePickerAction(label='???????????????',
                                                                    data='datetime_postback',
                                                                    mode='datetime')),
                                    QuickReplyButton(
                                        action=MessageAction(label="????????????", text="????????????")),
                                    QuickReplyButton(
                                        action=PostbackAction(label='+1???', data='plus_one_minute')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='+1??????', data='plus_one_hour')),
                                    QuickReplyButton(
                                        action=PostbackAction(label='+1???', data='plus_one_day'))
                                ]
                            )
                        )
                    flex = observable_flex
                    line_bot_api.reply_message(event.reply_token, flex)
                    sys.exit()

            elif (event.postback.data == "???????????????????????????") or (userdata["action_type"] == "calculation_orbit_sun&moon_information"):
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
                                text="??????????????????????????????", wrap=True, size="xxs", color="#7D7D7D", align="center"),
                            BoxComponent(
                                layout="vertical",
                                contents=[
                                    FillerComponent()
                                ],
                                height="10px"
                            ),
                            SeparatorComponent(),
                            TextComponent(text="\n"),
                            TextComponent(text="?????????????????????", size="lg",
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
                                        text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(moment_sunaz) + "??", flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(moment_sunalt) + "??", flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text=min_string_sun + "?????????", weight="bold", color="#7D7D7D", flex=1),
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
                                        text="????????????", weight="bold", color="#7D7D7D", flex=1
                                    ),
                                    TextComponent(
                                        text=str(moment_moonaz) + "??", flex=1, align="center", wrap=True
                                    )
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(moment_moonalt) + "??", flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="?????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=moment_moonage, flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text=min_string_moon + "?????????", weight="bold", color="#7D7D7D", flex=1),
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
                            TextComponent(text="??????????????????", size="lg",
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
                                        text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_sunrise), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_suntransit), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="?????????????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(day_southsunalt) + "??", flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="?????????", weight="bold", color="#7D7D7D", flex=1),
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
                                        text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_moonrise), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_moontransit), flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="??????????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=str(day_southmoonalt) + "??", flex=1, align="center", wrap=True)
                                ]
                            ),
                            BoxComponent(
                                layout="horizontal",
                                contents=[
                                    TextComponent(
                                        text="???????????????", weight="bold", color="#7D7D7D", flex=1),
                                    TextComponent(
                                        text=timeFix(day_moonset), flex=1, align="center", wrap=True)
                                ]
                            ),
                        ]
                    )
                )
                if userdata["action_type"] == "view_note":
                    sun_moon_flex = FlexSendMessage(
                        alt_text="???????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=MessageAction(label='??????????????????', text='??????????????????')),
                                QuickReplyButton(
                                    action=PostbackAction(label='????????????????????????', data='????????????????????????')),
                                QuickReplyButton(
                                    action=PostbackAction(label='??????????????????', data='??????????????????'))
                            ]
                        )
                    )
                else:
                    sun_moon_flex = FlexSendMessage(
                        alt_text="???????????????????????????????????????", contents=bubble, quick_reply=QuickReply(
                            items=[
                                QuickReplyButton(
                                    action=PostbackAction(label='????????????????????????', data='????????????????????????')),
                                QuickReplyButton(
                                    action=PostbackAction(label='??????????????????', data='??????????????????')),
                                QuickReplyButton(
                                    action=DatetimePickerAction(label='???????????????',
                                                                data='datetime_postback',
                                                                mode='datetime')),
                                QuickReplyButton(
                                    action=MessageAction(label="????????????", text="????????????")),
                                QuickReplyButton(
                                    action=PostbackAction(label='+1???', data='plus_one_minute')),
                                QuickReplyButton(
                                    action=PostbackAction(label='+1??????', data='plus_one_hour')),
                                QuickReplyButton(
                                    action=PostbackAction(label='+1???', data='plus_one_day'))
                            ]
                        )
                    )
                flex = sun_moon_flex
                line_bot_api.reply_message(event.reply_token, flex)
                sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "??????" or event.postback.data == "??????" or event.postback.data == "???" or event.postback.data == "???" or event.postback.data == "???????????????") and userdata["action_type"] == "write_note_weather":
            client = datastore.Client()
            with client.transaction():
                key = client.key("Task", event.source.user_id)
                task = client.get(key)
                task["action_type"] = "write_note_weather_check"
                task["write_note_weather"] = event.postback.data
                client.put(task)
            confirm_template = ConfirmTemplate(text='?????????????????????????????????????????????', actions=[
                MessageAction(label='??????', text="??????????????????????????????"),
                MessageAction(label='?????????', text='?????????'),
            ])
            template_message = TemplateSendMessage(
                alt_text='?????????????????????????????????????????????', template=confirm_template)
            line_bot_api.reply_message(event.reply_token, template_message)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "??????" or event.postback.data == "???" or event.postback.data == "??????" or event.postback.data == "??????" or event.postback.data == "??????" or event.postback.data == "??????" or event.postback.data == "???????????????") and userdata["action_type"] == "write_note_planets":
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
                            text="?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='??????', data='??????', text="??????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='??????', data='??????', text="??????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='???', data='???', text="???"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='??????', data='??????', text="??????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='??????', data='??????', text="??????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='??????', data='??????', text="??????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='??????', data='??????', text="??????"),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='???????????????', data='???????????????', text="???????????????")
                        ),
                    ],
                )
            )
            flex = FlexSendMessage(
                alt_text="????????????????????????????????????????????????", contents=bubble)
            line_bot_api.reply_message(
                event.reply_token, flex)
            sys.exit()
    except:
        pass

    try:
        if event.postback.data == "??????" and userdata["action_type"] == "write_note_planets":
            plslist = ast.literal_eval(userdata["write_note_observed_planets"])
            plslist = list(dict.fromkeys(plslist))
            motherlist = ["??????", "???", "??????", "??????", "??????", "??????", "???????????????"]
            plslist = listsort(plslist, motherlist)
            client = datastore.Client()
            with client.transaction():
                key = client.key("Task", event.source.user_id)
                task = client.get(key)
                task["write_note_observed_planets"] = str(plslist)
                client.put(task)
            confirm_template = ConfirmTemplate(text='????????????????????????????????????', actions=[
                MessageAction(label='??????', text="????????????"),
                MessageAction(label='?????????', text="????????????"),
            ])
            template_message = TemplateSendMessage(
                alt_text='????????????????????????????????????', template=confirm_template)
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
                                text="????????????????????????????????????\n????????????????????????????????????????????????", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='??????', data='??????'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(label='??????', data='??????'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='????????????', data='????????????'),
                            ),
                            ButtonComponent(
                                style='link',
                                height='sm',
                                action=PostbackAction(
                                    label='???????????????', data='???????????????'),
                            ),
                        ],
                    )
                )
                flex = FlexSendMessage(
                    alt_text="????????????????????????????????????????????????", contents=bubble)
                line_bot_api.reply_message(
                    event.reply_token, flex)
                sys.exit()
            except LineBotApiError:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                        text="LINEID????????????????????????????????????")
                )
                sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "??????" or event.postback.data == "??????" or event.postback.data == "????????????" or event.postback.data == "???????????????") and (userdata["action_type"] == "weather_auto_input"):
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
                            text="?????????????????????????????????????????????", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(label='???????????????', data='?????????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='???????????????', data='??????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='??????????????????', data='?????????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='?????????????????????', data='????????????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='??????????????????', data='?????????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='??????????????????', data='?????????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='?????????', data='??????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='????????????', data='?????????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='?????????', data='??????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='?????????', data='??????'),
                        ),

                    ],
                )
            )
            flex = FlexSendMessage(alt_text="?????????????????????????????????????????????", contents=bubble)
            line_bot_api.reply_message(
                event.reply_token, flex)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "?????????" or event.postback.data == "??????" or event.postback.data == "?????????" or event.postback.data == "????????????" or event.postback.data == "?????????" or event.postback.data == "?????????" or event.postback.data == "??????" or event.postback.data == "?????????" or event.postback.data == "??????" or event.postback.data == "??????") and (userdata["action_type"] == "weather_auto_input_location"):
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
                            text="????????????????????????????????????????????????????????????", wrap=True, weight='bold', adjustMode='shrink-to-fit'),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(label='??????', data='??????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(
                                label='??????????????????', data='??????????????????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(label='?????????', data='????????????'),
                        ),
                        ButtonComponent(
                            style='link',
                            height='sm',
                            action=PostbackAction(label='????????????', data='???????????????'),
                        )
                    ],
                )
            )
            flex = FlexSendMessage(
                alt_text="????????????????????????????????????????????????????????????", contents=bubble)
            line_bot_api.reply_message(
                event.reply_token, flex)
            sys.exit()
    except:
        pass

    try:
        if (event.postback.data == "??????" or event.postback.data == "??????????????????" or event.postback.data == "????????????" or event.postback.data == "???????????????") and (userdata["action_type"] == "weather_auto_input_information"):
            weather_auto_input_day = userdata["weather_auto_input_day"]
            weather_auto_input_location = userdata["weather_auto_input_location"]
            weather_auto_input_information = event.postback.data
            reset_user_data()
            confirm_template = ConfirmTemplate(text='????????????????????????\n???' + weather_auto_input_day + "???" + weather_auto_input_location + "???" + weather_auto_input_information + "?????????\n\n??????????????????????????????", actions=[
                MessageAction(label='??????', text=weather_auto_input_day + "???" +
                              weather_auto_input_location + "???" + weather_auto_input_information + "??????"),
                PostbackAction(label='?????????', data='?????????'),
            ])
            template_message = TemplateSendMessage(
                alt_text='????????????????????????????????????', template=confirm_template)
            line_bot_api.reply_message(event.reply_token, template_message)
            sys.exit()
    except:
        pass

    try:
        if event.postback.data == "?????????":
            reset_user_data()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text="???????????????????????????????????????")
            )
            sys.exit()
    except:
        pass


if __name__ == "__main__":
    app.run()
