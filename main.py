import os
from flask import Flask, render_template, request, jsonify, send_file
import utils
import utils2
from datetime import datetime as dt

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def topPage():
    userID = request.args.get("userID")
    if userID == None:
        return "MoodleのURLからアクセスしてください"

    return render_template("cl-chat.html",
                           userID=userID, status="none")


@app.route("/v3", methods=["GET", "POST"])
def topPageV2():
    userID = request.args.get("userID")
    if userID == None:
        return "MoodleのURLからアクセスしてください"

    responseSheetID = request.args.get("responseSheetID")
    if responseSheetID == None:
        return "応答シートのIDを指定してください"

    StartListName = "スタート画面"
    StartListContent = utils2.connectSheet(responseSheetID, StartListName)
    StartListBase = []
    for sublist in StartListContent:
        for item in sublist:
            StartListBase.append(item)


    return render_template("v2/cl-chat.html",
                           userID=userID, status="none",
                           responseSheetID=responseSheetID,
                           StartListBase=StartListBase
                          )

@app.route("/user_response", methods=["GET", "POST"])
def chat():
    userInput = request.form["userInput"]
    status = request.form["status"]
    userID = request.form["userID"]

    #print(status)

    try:
        sheet = utils.connectSheet()
        choices = utils.filteringChoices(sheet, userInput)

        # 即レスは味気ないので、シート読み込みをディレイ代わりに使ってから表示
        if status == "yes":
            message = "お役に立てて良かったです。また困ったらお声がけください。"
            utils.writeLog(userID, "解決した", "解決できて良かった")
            return jsonify({"message": message, "status": "closed",
                            "keywords": ""})

        keywords = request.form["keywords"]
        #print(keywords)
        #print(choices[0][2])
        # 途中で質問が変わったらリセット（変わったあとも一つに絞り込まれたら）
        if len(choices) == 1 and keywords != choices[0][2]:
            status = "none"

        #print(status)
        #print("1")

        # 途中で質問が変わったらリセット（変わったあとひとつに絞り込まれない）
        if status in ["answered", "nUsed", "aiQuestioned"] and len(choices) > 1:
            status = "none"

        #print("2")

        if len(choices) == 0:  # 想定してない質問の場合
            return jsonify(
                {"message": "すみません、よく分かりません。誤字脱字や表記ゆれを確認してください。",
                 "status": "error",
                 "keywords": ""})
        elif status == "answered":  # 既にAnswer列を返していれば
            if choices[0][4] == "":  # N列が無ければ
                if choices[0][5] == "T":  # AIに質問する
                    res, message = utils.useGemini(userInput)  # .replace("\n", "<br>\n")
                    utils.writeLog(userID, "AIに聞きたい", message)
                    if res:
                        return jsonify({"message": message, "status": "aiQuestioned",
                                        "keywords": choices[0][2]})
                    else:
                        return jsonify({"message": message, "status": "closed",
                                        "keywords": choices[0][2]})
                else:  # 教員やTAに質問するよう促す
                    message = "申し訳ありませんが、これ以上は教員やTAに質問してください。"
                    utils.writeLog(userID, "最後まで解決しない", "これ以上は知らん")
                    return jsonify({"message": message, "status": "closed",
                                    "keywords": choices[0][2]})
            else:  # N列があれば、それを表示する
                utils.writeLog(userID, "N列見せて", choices[0][4])
                return jsonify({"message": choices[0][4], "status": "nUsed",
                                "keywords": choices[0][2]})
        elif status == "nUsed":  # AIに聞く
            if choices[0][5] == "T":  # AIに聞くべき質問なら(AI列がTなら)
                res, message = utils.useGemini(userInput)  # .replace("\n", "<br>\n")
                utils.writeLog(userID, "AIに聞きたい", message)
                if res:
                    return jsonify({"message": message, "status": "aiQuestioned",
                                    "keywords": choices[0][2]})
                else:
                    return jsonify({"message": message, "status": "closed",
                                    "keywords": choices[0][2]})
            else:  # AIに聞かない質問なら(AI列がFなら)
                return jsonify({"message": "申し訳ありませんが、これ以上は教員やTAに質問してください。",
                                "status": "closed",
                                "keywords": ""})
        elif status == "aiQuestioned":  # AIに質問済み（これ以上は無理）
            message = "申し訳ありませんが、これ以上は教員やTAに質問してください。"
            utils.writeLog(userID, "最後まで解決しない", "これ以上は知らん")
            return jsonify({"message": message, "status": "closed",
                            "keywords": ""})
        # elif status == "yes":
        #     message = "お役に立てて良かったです。また困ったらお声がけください。"
        #     utils.writeLog(userID, "解決した", "解決できて良かった")
        #     return jsonify({"message": message, "status": "closed",
        #                     "keywords": ""})
        elif len(choices) == 1:  # 初めて質問が確定したとき
            try:
                # AND検索で1つに絞り込まれた
                utils.writeLog(userID, userInput, choices[0][3])
                return jsonify({"message": choices[0][3], "status": "answered",
                                "keywords": choices[0][2]})
            except:
                # OR検索で1つに絞り込まれた
                utils.writeLog(userID, userInput, choices[0][3])
                return jsonify({"message": choices[0][3], "status": "answered",
                                "keywords": choices[0][2]})
        else:
            utils.writeLog(userID, userInput, "もっと詳しく書け")
            return jsonify({"message": choices, "status": "none",
                            "keywords": ""})
    except Exception as e:
        utils.writeLog("Error", userInput, str(e))
        return jsonify(
            {"message": "すみません、よく分かりません。誤字脱字や表記ゆれを確認してください。", "status": "error"})


@app.route("/v3/user_response", methods=["GET", "POST"])
def chatV2():
    userInput = request.form["userInput"]
    status = request.form["status"]
    userID = request.form["userID"]
    responseSheetID = request.form["responseSheetID"]
    responseSheetName = "質問回答辞書"
    synonymDictSheetName ="同義語辞書"
    Related_words = "関連語辞書"

    # print(userID, status, userInput)

    try:
        responseSheet = utils2.connectSheet(responseSheetID, responseSheetName)
        synonymDictSheet = utils2.connectSheet(responseSheetID, synonymDictSheetName)
        Related_word = utils2.connectSheet(responseSheetID, Related_words)

        add = []
        add.extend(synonymDictSheet)
        add.extend(Related_word)

        choices = utils2.filtering(userInput, responseSheet, add)
        # pprint(choices)
        # print(len(choices))

        # 即レスは味気ないので、シート読み込みをディレイ代わりに使ってから表示
        if status == "yes":
            message = "お役に立てて良かったです。また困ったらお声がけください。"
            utils2.writeLog(userID, "解決した", "解決できて良かった", responseSheetID)
            return jsonify({"message": message, "status": "closed",
                            "keywords": ""})

        # keywords = request.form["keywords"]

        # 途中で質問が変わったらリセット（変わったあとも一つに絞り込まれたら）
        # if len(choices) == 1 and keywords != choices[0][2]:
        #     status = "none"

        # 途中で質問が変わったらリセット（変わったあとひとつに絞り込まれない）
        if status in ["answered", "nUsed", "aiQuestioned"] and len(choices) > 1:
            status = "none"

        if len(choices) == 0:  # 想定してない質問の場合
            return jsonify(
                {"message": "すみません、よく分かりません。誤字脱字や表記ゆれを確認してください。",
                 "status": "error",
                 "keywords": ""})
        elif status == "answered":  # 既にAnswer列を返していれば
            if choices[0][4] == "":  # N列が無ければ
                if choices[0][5] == "T":  # AIに質問する
                    res, message = utils2.useGemini(userInput)  # .replace("\n", "<br>\n")
                    utils2.writeLog(userID, "AIに聞きたい", message, responseSheetID)
                    if res:
                        return jsonify({"message": message, "status": "aiQuestioned",
                                        "keywords": choices[0][2]})
                    else:
                        return jsonify({"message": message, "status": "closed",
                                        "keywords": choices[0][2]})
                else:  # 教員やTAに質問するよう促す
                    message = "申し訳ありませんが、これ以上は教員やTAに質問してください。"
                    utils.writeLog(userID, "最後まで解決しない", "これ以上は知らん")
                    return jsonify({"message": message, "status": "closed",
                                    "keywords": choices[0][2]})
            else:  # N列があれば、それを表示する
                utils2.writeLog(userID, "N列見せて", choices[0][4], responseSheetID)
                return jsonify({"message": choices[0][4], "status": "nUsed",
                                "keywords": choices[0][2]})
        elif status == "nUsed":  # AIに聞く
            if choices[0][5] == "T":  # AIに聞くべき質問なら(AI列がTなら)
                res, message = utils2.useGemini(userInput)  # .replace("\n", "<br>\n")
                utils2.writeLog(userID, "AIに聞きたい", message, responseSheetID)
                if res:
                    return jsonify({"message": message, "status": "aiQuestioned",
                                    "keywords": choices[0][2]})
                else:
                    return jsonify({"message": message, "status": "closed",
                                    "keywords": choices[0][2]})
            else:  # AIに聞かない質問なら(AI列がFなら)
                return jsonify({"message": "申し訳ありませんが、これ以上は教員やTAに質問してください。",
                                "status": "closed",
                                "keywords": ""})
        elif status == "aiQuestioned":  # AIに質問済み（これ以上は無理）
            message = "申し訳ありませんが、これ以上は教員やTAに質問してください。"
            utils2.writeLog(userID, "最後まで解決しない", "これ以上は知らん", responseSheetID)
            return jsonify({"message": message, "status": "closed",
                            "keywords": ""})
        # elif status == "yes":
        #     message = "お役に立てて良かったです。また困ったらお声がけください。"
        #     utils.writeLog(userID, "解決した", "解決できて良かった")
        #     return jsonify({"message": message, "status": "closed",
        #                     "keywords": ""})
        elif len(choices) == 1:  # 初めて質問が確定したとき
            try:
                # AND検索で1つに絞り込まれた
                utils2.writeLog(userID, userInput, choices[0][3], responseSheetID)
                return jsonify({"message": choices[0][3], "status": "answered",
                                "keywords": choices[0][2]})
            except:
                # OR検索で1つに絞り込まれた
                utils2.writeLog(userID, userInput, choices[0][3], responseSheetID)
                return jsonify({"message": choices[0][3], "status": "answered",
                                "keywords": choices[0][2]})
        else:
            utils2.writeLog(userID, userInput, "もっと詳しく書け", responseSheetID)
            return jsonify({"message": choices, "status": "none",
                            "keywords": ""})
    except Exception as e:
        utils.writeLog("Error", userInput, str(e))
        return jsonify(
            {"message": "すみません、よく分かりません。誤字脱字や表記ゆれを確認してください。", "status": "error"})


@app.route("/log", methods=["GET", "POST"])
def log():
    if not os.path.exists(utils.logPath):
        with open(utils.logPath, "w", encoding="utf-8") as f:
            pass
        lineCount = 0
    else:
        with open(utils.logPath, "r", encoding="utf-8") as f:
            rows = f.readlines()
        lineCount = len(rows)

    try:
        if request.method == "POST":
            startDate = request.form["startDate"]
            endDate = request.form["endDate"]
            selectWeekDay = int(request.form["selectWeekDay"])
            selectClass = request.form["selectClass"]

            # 日付が空欄なら絞り込みをしない
            if startDate == "" and endDate == "":
                return render_template("log.html", logLineCount=lineCount, filterResult="")

            # 片方が空欄なら、両方同じ日にする
            if startDate == "":
                startDate = endDate
            elif endDate == "":
                endDate = startDate

            if selectClass == "1":
                startDate += " 09:00"
                endDate += " 10:45"
            elif selectClass == "2":
                startDate += " 10:55"
                endDate += " 12:40"
            elif selectClass == "3":
                startDate += " 13:25"
                endDate += " 15:10"
            elif selectClass == "4":
                startDate += " 15:20"
                endDate += " 17:05"
            elif selectClass == "5":
                startDate += " 17:15"
                endDate += " 19:00"
            else:
                startDate += " 00:00"
                endDate += " 23:59"

            startDate = dt.strptime(startDate, '%Y-%m-%d %H:%M')
            endDate = dt.strptime(endDate, '%Y-%m-%d %H:%M')

            result = "絞り込み：" + startDate.strftime("%Y-%m-%d %H:%M") + " - " + endDate.strftime(
                "%Y-%m-%d %H:%M") + "<br>\n"

            with open(utils.logPath, "r", encoding="utf-8", newline="") as f:
                rows = f.readlines()

            count = 0
            for row in rows:
                date, userID, userInput, botMessage = row[:-1].split("\t")  # 改行消してから分割
                date = dt.strptime(date, "%Y/%m/%d %H:%M:%S")
                day = date.strftime("%Y/%m/%d")
                time = date.strftime("%H:%M")

                weekday = date.weekday()
                if selectWeekDay == weekday or selectWeekDay == -1:
                    if startDate.strftime("%Y/%m/%d") <= day <= endDate.strftime("%Y/%m/%d"):
                        if startDate.strftime("%H:%M") <= time <= endDate.strftime("%H:%M"):
                            count += 1

            result += f"期間中のログ数: {count}"

            return jsonify({"res": result})
        else:
            return render_template("log.html", logLineCount=lineCount, filterResult="")
    except Exception as e:
        print("error")
        return jsonify({"res": e})

@app.route("/log2", methods=["GET", "POST"])
def log2():
    if not os.path.exists(utils2.logPath):
        with open(utils2.logPath, "w", encoding="utf-8") as f:
            pass
        lineCount = 0
    else:
        with open(utils2.logPath, "r", encoding="utf-8") as f:
            rows = f.readlines()
        lineCount = len(rows)
        #print("Request method:", request.method)
    try:
        if request.method == "POST":

            #print("POST request received")
            #print("Form data:", request.form)

            startDate = request.form["startDate"]
            endDate = request.form["endDate"]
            selectWeekDay = int(request.form["selectWeekDay"])
            selectClass = request.form["selectClass"]

            # 日付が空欄なら絞り込みをしない
            if startDate == "" and endDate == "":
                return render_template("log2.html", logLineCount=lineCount, filterResult="")

            # 片方が空欄なら、両方同じ日にする
            if startDate == "":
                startDate = endDate
            elif endDate == "":
                endDate = startDate

            if selectClass == "1":
                startDate += " 09:00"
                endDate += " 10:45"
            elif selectClass == "2":
                startDate += " 10:55"
                endDate += " 12:40"
            elif selectClass == "3":
                startDate += " 13:25"
                endDate += " 15:10"
            elif selectClass == "4":
                startDate += " 15:20"
                endDate += " 17:05"
            elif selectClass == "5":
                startDate += " 17:15"
                endDate += " 19:00"
            else:
                startDate += " 00:00"
                endDate += " 23:59"

            startDate = dt.strptime(startDate, '%Y-%m-%d %H:%M')
            endDate = dt.strptime(endDate, '%Y-%m-%d %H:%M')

            result = "絞り込み：" + startDate.strftime("%Y-%m-%d %H:%M") + " - " + endDate.strftime(
                "%Y-%m-%d %H:%M") + "<br>\n"

            with open(utils2.logPath, "r", encoding="utf-8", newline="") as f:
                rows = f.readlines()

            count = 0
            for row in rows:
                date, userID, userInput, botMessage = row[:-1].split("\t")  # 改行消してから分割
                date = dt.strptime(date, "%Y/%m/%d %H:%M:%S")
                day = date.strftime("%Y/%m/%d")
                time = date.strftime("%H:%M")

                weekday = date.weekday()
                if selectWeekDay == weekday or selectWeekDay == -1:
                    if startDate.strftime("%Y/%m/%d") <= day <= endDate.strftime("%Y/%m/%d"):
                        if startDate.strftime("%H:%M") <= time <= endDate.strftime("%H:%M"):
                            count += 1

            result += f"期間中のログ数: {count}"

            return jsonify({"res": result})
        else:
            return render_template("log2.html", logLineCount=lineCount, filterResult="")
    except Exception as e:
        print("error")
        return jsonify({"res": e})


@app.route("/log-download", methods=["GET", "POST"])
def logDownLoad():
    return send_file(utils.logPath, mimetype="text/plain", as_attachment=True,
                     download_name="log.tsv")

@app.route("/log-download2", methods=["GET", "POST"])
def logDownLoad2():
    responseSheetID = request.form["responseSheetID"]
    #print(responseSheetID)

    log_file_path = utils2.logPath.format(responseSheetID)
    if not os.path.exists(log_file_path):
        return "ファイルが見つかりません", 404
    return send_file(utils2.logPath.format(responseSheetID), mimetype="text/plain", as_attachment=True,
                     download_name="log.tsv")


if __name__ == "__main__":
    app.run(debug=True)
