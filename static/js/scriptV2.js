var chatContainer = document.getElementById('chat-ul');
var userInput = document.getElementById('user-input');
var sendButton = document.getElementById("send-button");
var userID = document.getElementById("user-id").value;
var responseSheetID = document.getElementById("response-sheet-id").value;


function sendMessage() {
    var message = userInput.value.trim();  // 先頭と末尾の余計な空白や改行を削除
    if (message !== '') {
        var status = document.getElementById("status").value;
        // var keywords = document.getElementById("keywords").value;

        // appendMessage(userID, message, 'user-message');
        appendUserInput(message)
		message = document.getElementById("user-input-history").value;
        // 通信中なので送信ボタンを止める
        sendButtonDeactivate();
        let panelEventID = setTimeout(()=>{showLoadingPanel()}, 5000);

        deleteButtons();  // ボタンリストを消す

        // Ajaxリクエスト
        $.ajax({
            url: '/v3/user_response',
            type: 'POST',
            data: {
                userInput: message,
                status: status,
                userID: userID,
                // keywords: keywords,
                responseSheetID: responseSheetID,
            },
            success: function(response) {
                // 送信ボタンを有効化
                sendButtonActivate();
                clearTimeout(panelEventID);
                hideLoadingPanel();

                var newStatus = response["status"];
                document.getElementById("status").value = newStatus;
                var message = response["message"];

                // var newKeywords = response["keywords"];
                // document.getElementById("keywords").value = newKeywords;

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
                    appendBotMessageOnly(message, isFirst=false, isEnd=false, isError=true);
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
        document.getElementById("user-input-history").value += (message + "。");
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

    // チャット画面のオブジェクトを再取得してから表示
    chatContainer = document.getElementById('chat-ul');
    chatContainer.appendChild(messageElement);
    // チャットコンテナを下までスクロール
}

function appendChoices(buttonLabels){
    /* 最新のボットの返答を更新する */
    var messageElement = document.createElement('li');
	messageElement.innerHTML = `
			<div>
			<strong> parrot</strong><br>
            <img class="icon01" src="static/images/f.jpg" alt="qqq" title="たくさん質問してね！！">
                知りたいことを以下のボタンから選んでください。<br>
                この中に無い場合は、もう少し詳しく書いてください。
            </div>
        `;
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
        li.innerHTML = `<button class="button-style" onclick="document.getElementById('user-input').value = '${buttonLabels[i]}';deleteButtons()">${buttonLabels[i]}</button>`;

        ul.appendChild(li);
    }

    // ボタンリストを配置
    messageElement.appendChild(ul);

    // リセットボタンを配置
    createResetButton(messageElement, chatContainer);

    // リセットボタンを作るときに一緒にappendChildするので不要
    // chatContainer.appendChild(messageElement);

    // チャットコンテナを下までスクロール
}

function appendAnswer(message){
    /* 最新のユーザー入力を更新する */
    var messageElement = document.createElement('li');
	console.log("message",message);
    // messageの内容をチェックして適切な処理を行う
    if (message.includes("AIParrotが返答します")) {
        messageElement.innerHTML = `
            <div>
                <strong> AIparrot</strong><br>
                <img class="icon01" src="static/images/robot.png" alt="AIParrotの返答" title="日々精進！！">
                ${message}
            </div>
        `;
    } else {
        messageElement.innerHTML = `
            <div>
                <strong> parrot</strong><br>
                <img class="icon01" src="static/images/f.jpg" alt="一般メッセージ" title="日々精進！！">
                ${message}
            </div>
        `;
    }

    messageElement.classList.add("bot-message"); // メッセージにクラスを追加

    var div = document.createElement("div");
    div.innerHTML += "解決しましたか？<br>\n";
    div.innerHTML += "<button class=button-style onclick='clickYesButton();'>はい</button>\n";
    div.innerHTML += "<button class=button-style onclick='clickNoButton();'>いいえ</button>\n";

    // 古い入力を取得し、「最新」属性を外す
    var old = document.getElementById("newest-bot-message");
    if(old){
        old.removeAttribute("id");
    }

    // 新たな入力に「最新」属性を付ける
    div.setAttribute("id", "newest-bot-message");

    messageElement.appendChild(div);
    chatContainer.appendChild(messageElement);

    // チャットコンテナを下までスクロールz

    // document.getElementById("input-field").style.visibility = "hidden";
    // document.getElementById("user-input").readOnly = true;
    // document.getElementById("user-input").placeholder = "チャット画面に表示されているボタンを押してください";
    // document.getElementById("send-button").disabled = true;
}

function appendBotMessageOnly(message, isFirst=false, isEnd=false, isError=false) {
    /* 最新のユーザー入力を更新する */
    var messageElement = document.createElement('li');
	messageElement.innerHTML = `
			<div>
			<strong>parrot</strong><br>
            <img class="icon01" src="static/images/f.jpg" alt="qqq" title="調べ物ってワクワクするよね！！">
            ${message}
            </div>
        `;

    messageElement.classList.add("bot-message"); // メッセージにクラスを追加

    if(isFirst){
        // 選択肢用のボタンリストを作成
        var ul = document.createElement("ul");
        ul.setAttribute("id", "newest-bot-message");  // 「最新」属性を付与

  		// HTML内のスクリプトタグで定義された配列を取得
    	// コンソールに配列を表示
    	console.log(StartListBase);

		var buttonLabels = StartListBase;

        for(var i = 0; i < buttonLabels.length; i++){
            /* ボタンを一つずつ作成する */
            var li = document.createElement("li");

            // ボタンが押されたらボタンリストを削除する必要があるので、その関数を紐付ける
            li.innerHTML = `<button class="button-style" onclick="document.getElementById('user-input').value = '${buttonLabels[i]}';deleteButtons()">${buttonLabels[i]}</button>`;

            ul.appendChild(li);
        }

        messageElement.appendChild(ul);

        // chatContainer.appendChild(messageElement);
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

    // 最後のメッセージ以外にリセットボタンを配置する
    if(!isEnd){
        if(!isError){  // エラーじゃなければリセットボタンを配置 (変な入力などのときは出さない)
            createResetButton(messageElement, chatContainer);
        }
        else{
            chatContainer.appendChild(messageElement);
        }
    }
    else{
        chatContainer.appendChild(messageElement);
    }
	let target = document.getElementById('chat-container');
	target.scrollIntoView(false);
    // チャットコンテナを下までスクロール

    if(isEnd){
        document.getElementById("input-field").style.visibility = "visible";
        document.getElementById("return-top-link").style.visibility = "visible";
        document.getElementById('user-input').placeholder = '他の質問をしたい場合は、「もう一度質問する」をクリックしてください。';

        userInput.disabled = true; // 入力フォームを無効化
        var sendButton = document.getElementById('send-button');
        sendButton.disabled = true; // 送信ボタンを無効化
                // CSSをリセットしてホバー効果を無効にする
        sendButton.style.background = '#bcbcbc';
        sendButton.style.cursor = 'default';
        sendButton.onmouseover = null;
        sendButton.onmouseout = null;
        console.log("finish");
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

    var message = document.getElementById("user-input-history").value;
    var status = document.getElementById("status").value;
//    var userID = document.getElementById("user-id").value;
    appendUserInput("解決しました", isNewest=false);

    // 通信中の表示を出す
    sendButtonDeactivate();
//    showLoadingPanel();

    // Ajaxリクエスト
    $.ajax({
        url: '/v3/user_response',
        type: 'POST',
        data: {
            userInput: message,
            status: "yes",
            userID:userID,
            responseSheetID: responseSheetID,
        },
        success: function(response) {
            // 通信中の表示を消す
            sendButtonActivate();

            var status = response["status"];
            document.getElementById("status").value = status;
            var message = response["message"];

            removeAllResetButton();

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

    var message = document.getElementById("user-input-history").value;
    var status = document.getElementById("status").value;
    // var userID = document.getElementById("user-id").value;
    // var keywords = document.getElementById("keywords").value;

    appendUserInput("まだ解決しない", isNewest=false);

    // 通信中なので送信ボタンを止める
    sendButtonDeactivate();
    let panelEventID = setTimeout(()=>{showLoadingPanel()}, 3000);

    // Ajaxリクエスト
    $.ajax({
        url: '/v3/user_response',
        type: 'POST',
        data: {
            userInput: message,
            status: status,
            userID: userID,
            // keywords: keywords,
            responseSheetID: responseSheetID,
        },
        success: function(response) {
            // 送信ボタンを有効化
            sendButtonActivate();
            clearTimeout(panelEventID);
            hideLoadingPanel();

            var newStatus = response["status"];
            document.getElementById("status").value = newStatus;
            var message = response["message"];

            // var newKeywords = response["keywords"];
            // document.getElementById("keywords").value = newKeywords;

            console.log("no:", newStatus);

            if(newStatus === "nUsed"){  // N列が帰ってきたら
                appendAnswer(message);
            }
            else if(newStatus === "aiQuestioned"){  // AIの質問が帰ってきたら
                message = marked(message);
                appendAnswer(message);
            }
            else if(newStatus === "closed"){  // これ以上返すものが無い状態なら
                removeAllResetButton();
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

function createResetButton(parent, grandParent){
	console.log("parent:", parent);
	console.log("grandParent:", grandParent);
    /*
    メモ
    bot返信時点でのchat-containerのinnerHTMLを記録する
    記録先はchat-history内に作るinput(hidden)
    inputのidは「chat-history-<n>」とする
    <n>は履歴番号で、今の履歴数+1とする

    リセットが発生するとチャット画面が更新される
    chat-historyとの関連性を保つため、呼び出した履歴番号より後のものを全て削除する
    削除処理は、<n>を順にインクリメントしつつ、nullじゃなければ削除、nullになれば終了
    */

    // リセットボタンを作成
    var buttonDiv = document.createElement("div");
    parent.appendChild(buttonDiv);

    // チャット画面に、最初のメッセージを表示
    grandParent.appendChild(parent);

    var histCount = document.getElementById("chat-history").childElementCount;

    // リセットボタンを作ってから、諸々の設定を行う
    var nowStatus = document.getElementById("status").value;
    var nowInputHistory = document.getElementById("user-input-history").value;
    buttonDiv.setAttribute("class", "reset-button");
    buttonDiv.innerHTML = `<button class="button-style" onclick="resetButtonAction('chat-history-${histCount + 1}', '${nowStatus}', '${nowInputHistory}')">ここからやり直す</button>`;

    // 現時点のチャットのHTMLをダンプする
    var chatHTML = document.getElementById("chat-container").innerHTML;
    var histInput = document.createElement("input");
    histInput.setAttribute("type", "hidden");
    histInput.setAttribute("id", `chat-history-${histCount + 1}`);
    histInput.value = chatHTML;
    var histories = document.getElementById("chat-history");
    histories.appendChild(histInput);
}

function resetButtonAction(chatHistoryID, status, userInputHistory){
    // 古いチャットのHTMLを呼び出して上書き
    var chatHistory = document.getElementById(chatHistoryID).value;
    document.getElementById("chat-container").innerHTML = chatHistory;

    // statusと入力履歴も上書き
    document.getElementById("status").value = status;
    document.getElementById("user-input-history").value = userInputHistory;

    // 履歴IDが今の値より後ろの履歴を削除
    var histID = chatHistoryID.split("-").pop();
    var nextID = parseInt(histID) + 1;
    while(true){
        var obj = document.getElementById(`chat-history-${nextID}`);
        if(obj !== null){
            obj.remove();
        }
        else{
            break;
        }
        nextID += 1;
    }
}

function removeAllResetButton(){
    var resetButtons = document.getElementsByClassName("reset-button");

    // リセットボタンを全て削除
    // 配列の要素ごと消えるので、whileを使って常に0番だけ削除する
    while(resetButtons.length > 0){
        resetButtons[0].remove();
    }
}

function sendButtonDeactivate(){
    document.getElementById("send-button").disabled = true;  // 送信ボタンを殺す
}

function sendButtonActivate(){
    document.getElementById("send-button").disabled = false;  // 送信ボタンを蘇生
}

function showLoadingPanel(){
     document.getElementById("panel").classList.remove("disable");
}

function hideLoadingPanel(){
     document.getElementById("panel").classList.add("disable");
}

// 最初のメッセージを表示
appendBotMessageOnly("困っていることや知りたいことは何ですか？<br>以下のボタンから選ぶか、入力欄に書いてください", isFirst=true);
