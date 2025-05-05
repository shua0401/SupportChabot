var chatContainer = document.getElementById('chat-ul');
var userInput = document.getElementById('user-input');
var sendButton = document.getElementById("send-button");

function sendMessage() {
    var message = userInput.value.trim();  // 先頭と末尾の余計な空白や改行を削除
    if (message !== '') {
        var userID = document.getElementById("user-id").value;
        var status = document.getElementById("status").value;
        var keywords = document.getElementById("keywords").value;

        // appendMessage(userID, message, 'user-message');
        appendUserInput(message)

        // 通信中なので送信ボタンを止める
        sendButtonDeactivate();
        let panelEventID = setTimeout(()=>{showLoadingPanel()}, 5000);

        deleteButtons();  // ボタンリストを消す

        // Ajaxリクエスト
        $.ajax({
            url: '/user_response',
            type: 'POST',
            data: {
                userInput: message,
                status: status,
                userID: userID,
                keywords: keywords
            },
            success: function(response) {
                // 送信ボタンを有効化
                sendButtonActivate();
                clearTimeout(panelEventID);
                hideLoadingPanel();

                var newStatus = response["status"];
                document.getElementById("status").value = newStatus;
                var message = response["message"];

                var newKeywords = response["keywords"];
                document.getElementById("keywords").value = newKeywords;

                console.log("send:", newStatus);

                /* 返答の種類を判定 */
                if(newStatus === "none"){  // 回答が絞り込めていないなら
                    var buttonLabels = [];
                    for(var i = 0; i < message.length; i++){
                        // console.log(message[i]);
                        var title = message[i][1];
                        buttonLabels.push(title);
                    }
                    appendChoices(buttonLabels);
                }
                else if(newStatus === "answered"){  // Answer列を表示する
                    appendAnswer(message);
                }
                else if(newStatus === "nUsed"){  // N列を表示する
                    appendAnswer(message);
                }
                else if(newStatus === "aiQuestioned"){  // AIに質問した結果を表示
                    message = marked(message);
                    appendAnswer(message);
                }
                else if(newStatus === "closed"){  // これ以上返すものが無い状態なら
                    appendBotMessageOnly(message);
                }
                else if(newStatus === "error"){
                    appendBotMessageOnly(message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);

                // 送信ボタンを有効化
                sendButtonActivate();
                clearTimeout(panelEventID);
                hideLoadingPanel();
            }
        });

        userInput.value = '';
    }
}

function appendUserInput(message, isNewest=true){
    /* 最新のユーザー入力を更新する */
    var messageElement = document.createElement('li');

    if(isNewest){
        document.getElementById("newest-user-input").value = message;
    }

    messageElement.innerHTML = `<strong>あなた</strong><br> ${message}`;
    messageElement.classList.add("user-message"); // メッセージにクラスを追加

    // 古い入力を取得し、「最新」属性を外す
    var old = document.getElementById("newest-user-message");
    if(old){
        old.removeAttribute("id");
    }

    // 新たな入力に「最新」属性を付ける
    messageElement.setAttribute("id", "newest-user-message");

    chatContainer.appendChild(messageElement);
    // チャットコンテナを下までスクロール
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendChoices(buttonLabels){
    /* 最新のボットの返答を更新する */
    var messageElement = document.createElement('li');

    messageElement.innerHTML = `<strong>ChatBot</strong><br> もう少し詳しく書くか、以下のボタンから知りたいことを選んでください`;
    messageElement.classList.add("bot-message"); // メッセージにクラスを追加

    // 古い入力を取得し、「最新」属性を外す
    var old = document.getElementById("newest-bot-message");
    if(old){
        old.removeAttribute("id");
    }

    // 選択肢用のボタンリストを作成
    var ul = document.createElement("ul");
    ul.setAttribute("id", "newest-bot-message");  // 「最新」属性を付与

    for(var i = 0; i < buttonLabels.length; i++){
        /* ボタンを一つずつ作成する */
        var li = document.createElement("li");

        // ボタンが押されたらボタンリストを削除する必要があるので、その関数を紐付ける
        li.innerHTML = `<button onclick="document.getElementById('user-input').value = '${buttonLabels[i]}';deleteButtons()">${buttonLabels[i]}</button>`;

        ul.appendChild(li);
    }

    messageElement.appendChild(ul);
    chatContainer.appendChild(messageElement);
    // チャットコンテナを下までスクロール
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendAnswer(message){
    /* 最新のユーザー入力を更新する */
    var messageElement = document.createElement('li');

    messageElement.innerHTML = `<strong>ChatBot</strong><br> ${message}`;
    messageElement.classList.add("bot-message"); // メッセージにクラスを追加

    var div = document.createElement("div");
    div.innerHTML += "解決しましたか？<br>\n";
    div.innerHTML += "<button onclick='clickYesButton();'>はい</button>\n";
    div.innerHTML += "<button onclick='clickNoButton();'>いいえ</button>\n";

    // 古い入力を取得し、「最新」属性を外す
    var old = document.getElementById("newest-bot-message");
    if(old){
        old.removeAttribute("id");
    }

    // 新たな入力に「最新」属性を付ける
    div.setAttribute("id", "newest-bot-message");

    messageElement.appendChild(div);
    chatContainer.appendChild(messageElement);

    // チャットコンテナを下までスクロール
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // document.getElementById("input-field").style.visibility = "hidden";
    // document.getElementById("user-input").readOnly = true;
    // document.getElementById("user-input").placeholder = "チャット画面に表示されているボタンを押してください";
    // document.getElementById("send-button").disabled = true;
}

function appendBotMessageOnly(message, isFirst=false, isEnd=false) {
    /* 最新のユーザー入力を更新する */
    var messageElement = document.createElement('li');

    messageElement.innerHTML = `<strong>ChatBot</strong><br> ${message}`;
    messageElement.classList.add("bot-message"); // メッセージにクラスを追加

    if(isFirst){
        // 選択肢用のボタンリストを作成
        var ul = document.createElement("ul");
        ul.setAttribute("id", "newest-bot-message");  // 「最新」属性を付与

        var buttonLabels = [
            "",
            "",
            ""
        ]

        for(var i = 0; i < buttonLabels.length; i++){
            /* ボタンを一つずつ作成する */
            var li = document.createElement("li");

            // ボタンが押されたらボタンリストを削除する必要があるので、その関数を紐付ける
            li.innerHTML = `<button onclick="document.getElementById('user-input').value = '${buttonLabels[i]}';deleteButtons()">${buttonLabels[i]}</button>`;

            ul.appendChild(li);
        }

        messageElement.appendChild(ul);
        chatContainer.appendChild(messageElement);
    }
    else{
        // 古い入力を取得し、「最新」属性を外す
        var old = document.getElementById("newest-bot-message");
        if(old){
            old.removeAttribute("id");
        }
        // 新たな入力に「最新」属性を付ける
        messageElement.setAttribute("id", "newest-bot-message");

    }

    chatContainer.appendChild(messageElement);
    // チャットコンテナを下までスクロール
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if(isEnd){
        document.getElementById("input-field").style.visibility = "hidden";
        document.getElementById("return-top-link").style.visibility = "visible";
    }
}

/* ボタンの箇条書きを消す */
function deleteButtons(){
    var ul = document.getElementById("newest-bot-message");

    // ボタンの箇条書きがあれば消す
    if(ul){
        ul.remove();
    }

    // 押されたボタンの文章が入力欄に入力されているので、そのまま送信する
    if(document.getElementById("user-input").value !== ""){
        document.getElementById("send-button").click();
    }
}

/* 「解決しましたか？」->「はい」ボタン */
function clickYesButton(){

    // Yes/Noボタンがあれば消す
    var buttons = document.getElementById("newest-bot-message");
    // console.log(buttons);
    if(buttons){
        buttons.remove();
    }

    var message = document.getElementById("newest-user-input").value;
    var status = document.getElementById("status").value;
    var userID = document.getElementById("user-id").value;
    appendUserInput("解決しました", isNewest=false);

    // 通信中の表示を出す
    sendButtonDeactivate();
//    showLoadingPanel();

    // Ajaxリクエスト
    $.ajax({
        url: '/user_response',
        type: 'POST',
        data: {
            userInput: message,
            status: "yes",
            userID:userID
        },
        success: function(response) {
            // 通信中の表示を消す
            sendButtonActivate();

            var status = response["status"];
            document.getElementById("status").value = status;
            var message = response["message"];
            appendBotMessageOnly(message, isFirst=false, isEnd=true);
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);

            // 通信中の表示を消す
            sendButtonActivate();
        }
    });

    userInput.value = '';
}

/* 「解決しましたか？」->「いいえ」ボタン */
function clickNoButton(){
    // Yes/Noボタンがあれば消す
    var buttons = document.getElementById("newest-bot-message");
    // console.log(buttons);
    if(buttons){
        buttons.remove();
    }

    var message = document.getElementById("newest-user-input").value;
    var status = document.getElementById("status").value;
    var userID = document.getElementById("user-id").value;
    var keywords = document.getElementById("keywords").value;

    appendUserInput("まだ解決しない", isNewest=false);

    // 通信中なので送信ボタンを止める
    sendButtonDeactivate();
    let panelEventID = setTimeout(()=>{showLoadingPanel()}, 3000);

    // Ajaxリクエスト
    $.ajax({
        url: '/user_response',
        type: 'POST',
        data: {
            userInput: message,
            status: status,
            userID: userID,
            keywords: keywords
        },
        success: function(response) {
            // 送信ボタンを有効化
            sendButtonActivate();
            clearTimeout(panelEventID);
            hideLoadingPanel();

            var newStatus = response["status"];
            document.getElementById("status").value = newStatus;
            var message = response["message"];

            var newKeywords = response["keywords"];
            document.getElementById("keywords").value = newKeywords;

            console.log("no:", newStatus);

            if(newStatus === "nUsed"){  // N列が帰ってきたら
                appendAnswer(message);
            }
            else if(newStatus === "aiQuestioned"){  // AIの質問が帰ってきたら
                message = marked(message);
                appendAnswer(message);
            }
            else if(newStatus === "closed"){  // これ以上返すものが無い状態なら
                appendBotMessageOnly(message, isFirst=false, isEnd=true);
            }
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);

            // 通信中の表示を消す
            hideLoadingPanel();
        }
    });

    userInput.value = '';
}

function sendButtonDeactivate(){
    document.getElementById("send-button").disabled = true;  // 送信ボタンを殺す
}

function sendButtonActivate(){
    document.getElementById("send-button").disabled = false;  // 送信ボタンを殺す
}

function showLoadingPanel(){
     document.getElementById("panel").classList.remove("disable");
}

function hideLoadingPanel(){
     document.getElementById("panel").classList.add("disable");
}

// 最初のメッセージを表示
appendBotMessageOnly("困っていることや知りたいことは何ですか？<br>以下のボタンから選ぶか、入力欄に書いてください", isFirst=true);
