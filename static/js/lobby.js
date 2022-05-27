var socket = io.connect('http://' + document.domain + ':' + location.port + "/lobby");
let pixels_x = [], pixels_y = [];
let curr_stroke = {};
var restore_array = []

socket.on( 'connect', function() {
    console.log("Room: " + room)
    socket.emit( 'player_join')
})

function emitWordChoice(word) {
    socket.emit( 'artist_chose_word', {chosen_word: word} )
}

function writeBoardOverlayList(msg, listElem, ordered) {
    var node;
    var textnode;
    var place = 1;
    for (var key of Object.keys(msg)) {
        if (key !== "type") {
            node = document.createElement("li");
            if (ordered)
                textnode = document.createTextNode(place + ". " + key + ': ' + msg[key]);
            else
                textnode = document.createTextNode(key + ': ' + msg[key]);
            node.appendChild(textnode);
            listElem.appendChild(node);
        }
    }
}

function displayWordChoicesButtons(flag) {
    document.getElementById("WordChoicesButtonDiv").style.display = flag;
}

function isHebrew(num) {
   return (1488 <= num && num <= 1514)
}

function asciiArrayToString(arr) {
    str = "\u202A"
    for (var i = 0; i < arr.length; i++) {
       if (isHebrew(arr[i])) {
           str += String.fromCharCode(arr[i])
        }
        else {
            str += "\u202A" + String.fromCharCode(arr[i]) + "\u202C"
        }
        //console.log(str)
    }
    // str += "\u202C"
    return str
}

socket.on( 'game_overlay', function(msg) {
    //console.log("Game overlay event: " + msg.type)
    displayWordChoicesButtons("None");
    removeCanvasListeners();
    var eType = msg.type;
    console.log(eType);
    var gameScreenStyle = document.getElementById("GameScreen").style
    var gameCanvasStyle = document.getElementById("gameCanvas").style
    var boardOverlayStyle = document.getElementById("boardOverlay").style
    var lobbyScreenStyle = document.getElementById("LobbyScreen").style
    var boardOverlayTitle = document.getElementById("overlay_title")
    var boardOverlaylist = document.getElementById("overlayList")
    var gameHeader = document.getElementById("gameHeader");
    var bDiv = document.getElementById("WordChoicesButtonDiv");
    var toolbarDivStyle = document.getElementById("containerToolbar").style;
    var hintBtnDivStyle = document.getElementById("hintButtonContainer").style;
    boardOverlaylist.innerHTML = "";
    //gameCanvasStyle.zIndex = 1;
    toolbarDivStyle.display = "none";
    hintBtnDivStyle.display = "none";
    gameScreenStyle.display = "flex";
    gameCanvasStyle.opacity = "1";
    lobbyScreenStyle.display = "none";
    red_border(document.getElementById("pen_button"));
    if (eType === "guessing_view") {  // closing overlay
        gameCanvasStyle.display = "block";
        boardOverlayStyle.display = "none";
        context.fillStyle = "white";
        document.getElementById("wordSpace").innerText = "current word:  " + asciiArrayToString(msg["encoded_word"])
        document.getElementById("timeLeft").innerText = msg["time"]
        if (msg["need_hint_box"]) {
            hintBtnDivStyle.display = "Block";
        }
    }
    else if (eType === "artist_view") {  // closing overlay
        addCanvasListeners();
        gameCanvasStyle.display = "block";
        boardOverlayStyle.display = "none";
        context.fillStyle = "white";
        document.getElementById("wordSpace").innerText = "You need to draw: " + asciiArrayToString(msg["word"])
        document.getElementById("timeLeft").innerText = msg["time"]
        toolbarDivStyle.display = "flex";
    }
    else if (eType === "word_to_choose_from") {
        //gameCanvasStyle.zIndex = -1;
        toolbarDivStyle.display = "flex";
        context.fillRect(0, 0, canvas.width, canvas.height);
        gameCanvasStyle.opacity = "0.2";
        boardOverlayStyle.display = "block";
        displayWordChoicesButtons("Block");
        document.getElementById("overlay_title").innerHTML = "Choose a word to draw";
        if (msg['gamemode'] == "Classic") {
            document.getElementById("roundsCounter").innerText = "Round " + msg["current_round"] + " out of " + msg["total_rounds"];
        } else {
            document.getElementById("roundsCounter").innerText = "Round " + msg["current_round"];
        }
        document.getElementById("overlayList").innerHTML = "";
        var currB, currW;
        for (var i = 1; i <= 3; i++) {
            currW = msg["w" + i];
            currB = document.getElementById("choice" + i);
            currB.value = currW;
            currB.innerText = currW;
        }
    }
    else if (eType === "artist_choosing_a_word") {
        context.fillRect(0, 0, canvas.width, canvas.height);
        if (msg['gamemode'] == "Classic") {
            document.getElementById("roundsCounter").innerText = "Round " + msg["current_round"] + " out of " + msg["total_rounds"];
        } else {
            document.getElementById("roundsCounter").innerText = "Round " + msg["current_round"];
        }
        gameCanvasStyle.opacity = "0.2";
        boardOverlayStyle.display = "block";
        boardOverlayTitle.innerText = msg.artist + " is choosing his word.";
    }
    else if (eType === "turn_ended") {
        gameCanvasStyle.opacity = "0.2";
        boardOverlayStyle.display = "block";
        boardOverlayTitle.innerText = "Turn ended";
        writeBoardOverlayList(msg, boardOverlaylist, false);
        restore_array = []; ///!!!
        curr_stroke = {}; ///!!!
        pixels_x = [];
        pixels_y = [];   ///!!!!
    } else if (eType === "new_round") {
        gameCanvasStyle.display = "block";
        gameCanvasStyle.opacity = "0.2";
        boardOverlayStyle.display = "block";
        document.getElementById("roundsCounter").innerText = "Round " + msg.curr_round;
        boardOverlayTitle.innerText = "Round " + msg.curr_round;
    }
    else if (eType === "game_ended") {  // game ended scoreboard
        gameCanvasStyle.display = "block";
        gameCanvasStyle.opacity = "0.2";
        boardOverlayStyle.display = "block";
        boardOverlayTitle.innerText = "Game finished";
        writeBoardOverlayList(msg, boardOverlaylist, true);
        console.log("game ended")
    }
    else if (eType === "lobby") {  // show lobby settings and players
        document.getElementById("messages").innerHTML = "";
        gameScreenStyle.display = "none";
        gameCanvasStyle.display = "none";
        boardOverlayStyle.display = "none";
        lobbyScreenStyle.display = "block";
    }
})

socket.on( 'update_player_list', function(msg) {
    document.getElementById('lobby_player_list').innerHTML = "";
    //console.log("Updating Playerlist: ")
    //console.log(msg)
    var p, div, img;
    for (var key of Object.keys(msg)) {
        p = document.createElement("p");
        p.innerText = key;
        p.style.color = 'black';
        img = document.createElement("img");
        img.src = msg[key];
        img.style.width = "50px";
        div = document.createElement("div");
        div.style.width = "25%"
        div.appendChild(p);
        div.appendChild(img);
        document.getElementById('lobby_player_list').appendChild(div);
    }
})

function create_score_div_html(place, name, points, img) {
    my_str = "<div class=\"player\" id=\"player" + place + "\">"
	my_str += "<div class=\"rank\">#" + place + "</div>"
	my_str += "<div class=\"info\">"
	my_str += "<p class=\"name\">" + name + "</p>"
	my_str += "<p class=\"score\">Points: " + points + "</p></div>"
	my_str += "<div class=\"player_icon\">"
	my_str += "<img class=\"player_icon\" src=\"" + img + "\" alt=\"icon\">";
    my_str += "</div>";
    return my_str;
}


socket.on( 'update_scoreboard', function(msg) {
    var playerCount = 0;
    document.getElementById("scoreboardTblBody").innerHTML = "";
    var scoreboardTblBody = document.getElementById("scoreboardTblBody");
    var width = document.getElementById("containerPlayerList").getBoundingClientRect().width;
    //console.log("Updating Scoreboard: ")
    //console.log(msg)
    for (var key of Object.keys(msg)) {
        playerCount += 1
        //scoreboardTblBody.innerHTML += "<tr><td><div class=\"card\" style=\"width: " + width + "px;color: black;\"><div class=\"card-content\"><div class=\"media\"><div class=\"media-left\"><figure class=\"image is-48x48\"><img src=\"static\\Images\\penguin.png\" alt=\"Placeholder image\"></figure></div><div class=\"media-content\"><p class=\"is-4\">" + key+ "</p><p class=\"is-6\">Points: " + msg[key][0] + "</p></div></div></div></div></td></tr>"
        /*
        document.getElementById("scoreboardTblBody").innerHTML += "<div class=\"columns is-mobile is-centered is-vcentered\">"
        document.getElementById("scoreboardTblBody").innerHTML += "<div class=\"column\"><img src=\"static\\Images\\penguin.png\">"
        document.getElementById("scoreboardTblBody").innerHTML += "</div><div class=\"column\">"
        document.getElementById("scoreboardTblBody").innerHTML += "<span class=\"subtitle\">" + playerCount + ". " + key + ': ' + msg[key][0] + "</span>"
        document.getElementById("scoreboardTblBody").innerHTML += "</div></div></td></tr>"*/
        //document.getElementById("scoreboardTblBody").innerHTML += "<img src=\"static\\Images\\penguin.png\">"
        //document.getElementById("scoreboardTblBody").innerHTML += "<tr><td>" + playerCount + ". " + key + ': ' + msg[key][0]  +"</td></tr>"
        document.getElementById("scoreboardTblBody").innerHTML += "<tr><td>" + create_score_div_html(playerCount, key, msg[key][0], msg[key][1])  + "</td></tr>"
    }
})

socket.on( 'allowed_to_start', function(msg) {  // only admins get this
    //console.log("allowed_to_start event sent:" + msg.flag)
    if (msg.flag === "true")
        document.getElementById('startButton').disabled = false;
    else
        document.getElementById('startButton').disabled = true;
})

socket.on( 'admin_update', function(msg) {  // only admins get this
    if (uName === msg.admin) {
        console.log("You are the admin!")
        document.getElementById('Rounds').disabled = false;
        document.getElementById('DrawTime').disabled = false;
        document.getElementById('Languages').disabled = false;
        document.getElementById('customWords').disabled = false;
        document.getElementById('Gamemode').disabled = false;
        document.getElementById('Difficulty').disabled = false;
        document.getElementById("pointsLimit").disabled = false;
    }
})

socket.on( 'game_started', function() {
    //console.log("Game started!");
    showGame();
})

function requestUpdateSettings() {
    //console.log("Updating settings")
    socket.emit( 'update_lobby_settings', {
        rounds : document.getElementById("Rounds").value,
        draw_time : document.getElementById("DrawTime").value,
        language : document.getElementById("Languages").value,
        custom_words : document.getElementById("customWords").value,
        gamemode : document.getElementById("Gamemode").value,
        points_limit : document.getElementById("pointsLimit").value,
        difficulty : document.getElementById("Difficulty").value
      } )
}

function startGame() {
    //console.log("Requesting game start")
    socket.emit( 'request_game_start')
}

function getIndexOfSelect(elem, value) {
    for (i = 0; i < elem.length; i++) {
        if (elem.options[i].text === "" + value)
            return i;
    }
    return 0;
}

socket.on( 'settings_update', function(msg) {
    //console.log("settings changed");
    //console.log(msg)
    document.getElementById("Rounds").selectedIndex = getIndexOfSelect(document.getElementById("Rounds"), msg["rounds"])
    document.getElementById("DrawTime").selectedIndex = getIndexOfSelect(document.getElementById("DrawTime"), msg["draw_time"])
    document.getElementById("Languages").selectedIndex = getIndexOfSelect(document.getElementById("Languages"), msg["language"])
    document.getElementById("Gamemode").selectedIndex = getIndexOfSelect(document.getElementById("Gamemode"), msg["gamemode"])
    document.getElementById("Difficulty").selectedIndex = getIndexOfSelect(document.getElementById("Difficulty"), msg["difficulty"])
    document.getElementById("pointsLimit").selectedIndex = getIndexOfSelect(document.getElementById("pointsLimit"), msg["points_limit"])
    document.getElementById("customWords").value = msg["custom_words"]
    if (msg['gamemode'] == "Points Rush") {
        document.getElementById("pLimitDiv").style.display = "block";
        document.getElementById("roundsDiv").style.display = "none";
    } else {
        document.getElementById("pLimitDiv").style.display = "none";
        document.getElementById("roundsDiv").style.display = "block";
    }
})

function getRGBFromColor(c) {
    return `rgb(${draw_color.r}, ${draw_color.g}, ${draw_color.b})`;
}

function sendMessage() {
    var msg = document.getElementById("guess_input").value;
    //console.log("New msg: " + msg)
    if (msg.length > 0){
        socket.emit( 'new_chat_message', {
            message : msg
         } )
         document.getElementById("guess_input").innerText = "";
    }
}

function start(msg) {
    if (action != "pen")
        return;
    is_drawing = true;
    context.beginPath();
    context.moveTo(msg.clickX, msg.clickY);
    event.preventDefault();
    draw(msg);
}

function draw(msg) {
    if (is_drawing) {
        wasChanged = true;
        context.lineTo(msg.clickX, msg.clickY);
        //context.strokeStyle = msg.draw_color;
        console.log(draw_color)
        my_color = getRGBFromColor(draw_color);
        context.strokeStyle = my_color;
        context.lineWidth = draw_width;
        context.lineCap = "round";
        context.lineJoin = "round";
        context.stroke();
    }
    event.preventDefault();
}

function stop(msg) {
    if (is_drawing) {
        context.stroke();
        context.closePath();
        is_drawing = false;
    }
}

function clear_canvas() {
    context.fillStyle = "white";
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.strokeStyle = getRGBFromColor(draw_color);
}

function stroke_handler(msg) {
    if (typeof msg.op === 'undefined') {return}
    else if (msg.op === "start") {start(msg)}
    else if (msg.op === "draw") {draw(msg)}
    else if (msg.op === "stop") {stop()}
    else if (msg.op == "clear") {clear_canvas()}
}

socket.on( 'draw_stroke', function( msg ) {
    //console.log(msg)
    stroke_handler(msg)
})

// setup chat
document.getElementById("chatForm").addEventListener("submit", function(event) {
    event.preventDefault();
    var iChat = document.getElementById("inputChat");
    if (iChat.value.length > 0) {
        socket.emit( 'new_chat_message', {message: iChat.value} )
        iChat.value = "";
    }
});

function chat_handler(msg) {
    var mDiv = document.getElementById("messages");
    var myP = document.createElement("p");
    if (typeof msg.type === 'undefined') {
        return}
    else if (msg.type === "prohibited") {
        myP.innerText = 'Message was blocked and not set because it had prohibited text.';
        myP.style.color = 'red';
    }
    else if (msg.type === "regular") {
        myP.innerText = msg.username + ": " + msg.message;
        myP.style.color = 'black';
    }
    else if (msg.type === "correct") {
        myP.innerText = msg.username + ": guessed correctly";
        myP.style.color = '#00FF7F';  //green
    }
    else if (msg.type === "almost_correct") {
        myP.innerText = msg.username + ": " + msg.message;
        myP.style.color = 'black';
        mDiv.appendChild(myP);
        myP = document.createElement("p");
        myP.innerText = "'" + msg.message + "'  is close!";
        myP.style.color = 'yellow';
    }
    else if (msg.type === "guessed_chat") {
        myP.innerText = msg.username + ": " + msg.message;
        myP.style.color = '#8FBC8F';  // darker green
    }
    else if (msg.type === "turn_ended") {
        myP.innerText = "Turn ended, the word was '" + msg.last_word + "'";
        myP.style.fontWeight = 'bold';
        myP.style.color = '#00FF7F';  //green
    }
    else if (msg.type === "turn_started") {
        myP.innerText = msg.artist + " is now drawing!";
        myP.style.color = '#4682B4';  //  steel blue
    }
    else if (msg.type === "join_alert") {
        myP.innerText = msg.username + " joined the game!";
        myP.style.color = '#00FF7F';  //green
    }
    else if (msg.type === "left_alert") {
        myP.innerText = msg.username + " left the game!";
        myP.style.color = '#800000';  // maroon (red)
    }
    else if (msg.type === "hint_alert") {
        if (msg.hint_type === "public") {
            myP.innerText = msg.username + " bought a hint for everyone!";
            myP.style.color = 'blue';
        }
        else if (msg.hint_type === "private") {
            myP.innerText = msg.username + " bought a private hint!";
            myP.style.color = 'blue';
        }
    }
    mDiv.appendChild(myP);
}

socket.on( 'chat_message', function( msg ) {
    console.log(msg)
    chat_handler(msg)
})

// requesting hint handling
function requestHint(mode) {
    console.log("requested hint")
    socket.emit( 'request_hint', {type : mode} )
}


// CANVASES SETUP

//setup color canvas sample
const canvas_sample = document.getElementById("canvas_sample");
canvas_sample.style.display = "none";
canvas_sample.width = 1;
canvas_sample.height = 1;
let canvas_sample_context = canvas_sample.getContext("2d");
canvas_sample_context.fillStyle = "black";
canvas_sample_context.fillRect(0, 0, canvas_sample.width, canvas_sample.height)

//setup draw canvas sample
const draw_sample = document.getElementById("draw_sample");
draw_sample.style.display = "none";
draw_sample.width = 1;
draw_sample.height = 1;
let draw_sample_context = draw_sample.getContext("2d");
draw_sample_context.fillStyle = "black";
draw_sample_context.fillRect(0, 0, draw_sample.width, draw_sample.height)

//setup game canvas
const canvas = document.getElementById("canvas");
const boardContainer = document.getElementById("containerBoard");
const baseWidth = 1000;
const baseHeight = 620;
canvas.width = boardContainer.clientWidth; //
canvas.height = boardContainer.clientHeight; //
let context = canvas.getContext("2d");

context.fillStyle = "white";
context.fillRect(0, 0, canvas.width, canvas.height)

let wasChanged = false;
let start_background_color = "white";
let draw_color = "black";
change_color(document.getElementById("black-field"));
document.getElementById("pen_button").style.border = "2px solid red";
let draw_width = "2";
let is_drawing = false;
let action = "pen";
let isFilling = false;

let index = -1;

let artistWidthFactor = baseWidth / canvas.clientWidth;
let artistHeightFactor = baseHeight / canvas.clientHeight;
let guesserWidthFactor = canvas.clientWidth / baseWidth;
let guesserHeightFactor = canvas.clientHeight / baseHeight;

function scaleXForServer(val) {
    return parseFloat((artistWidthFactor * val).toFixed(2));
}

function scaleYForServer(val) {
    return parseFloat((artistHeightFactor * val).toFixed(2));
}

function handleCanvasResize() {
    if (canvas.width === boardContainer.clientWidth && canvas.height === boardContainer.clientHeight) {
        return false;
    }
    canvas.width = boardContainer.clientWidth;
    canvas.height = boardContainer.clientHeight;
    artistWidthFactor = baseWidth / canvas.clientWidth;
    artistHeightFactor = baseHeight / canvas.clientHeight;
    guesserWidthFactor = canvas.clientWidth / baseWidth;
    guesserHeightFactor = canvas.clientHeight / baseHeight;
    //chat.style.maxHeight = drawingBoard.clientHeight + "px";
    //playerContainer.style.maxHeight = drawingBoard.clientHeight + "px";
    return true;
}

var doit;
function requestEntireDrawing() {
    socket.emit('requestEntireDrawing')
}

handleCanvasResize();

window.addEventListener("resize", () => {
            if (handleCanvasResize()) {
                clearTimeout(doit);
                doit = setTimeout(function() {
                    requestEntireDrawing();
                }, 75);
            }
        }, false);

//canvas events
function addCanvasListeners() {
    canvas.addEventListener("touchstart", sendStart, false);
    canvas.addEventListener("touchmove", sendDraw, false);
    canvas.addEventListener("mousedown", sendStart, false);
    canvas.addEventListener("mousemove", sendDraw, false);
    canvas.addEventListener("touchend", sendStop, false);
    canvas.addEventListener("mouseup", sendStop, false);
    canvas.addEventListener("mouseout", sendStop, false);
}

function removeCanvasListeners() {
canvas.addEventListener("touchstart", sendStart, false);
    canvas.removeEventListener("touchmove", sendDraw, false);
    canvas.removeEventListener("mousedown", sendStart, false);
    canvas.removeEventListener("mousemove", sendDraw, false);
    canvas.removeEventListener("touchend", sendStop, false);
    canvas.removeEventListener("mouseup", sendStop, false);
    canvas.removeEventListener("mouseout", sendStop, false);
}

var canvasPos = canvas.getBoundingClientRect();

function request_color_change(color) {
    socket.emit( 'client_instruction', {inst_type: 'change_color', color: color});
}

function request_width_change(width) {
    socket.emit( 'client_instruction', {inst_type: 'change_width', width: width});
}

function request_action_change(new_action) {
    socket.emit( 'client_instruction', {inst_type: 'change_action', action: new_action});
}

function change_color(element) {
    request_color_change(element.style.background);
    var allEle = document.getElementsByClassName("color-field");
    for (var i = 0; i < allEle.length; i++) {
        allEle[i].style.opacity = 0.6;
        //allEle[i].style.width = "40px";
        //allEle[i].style.height = "40px";
    }
    //element.style.width = "50px";
    //element.style.height = "50px";
    element.style.opacity = 1;
}

function red_border(element) {
    var allEle = document.getElementsByTagName("button")
    for (var i = 0; i < allEle.length; i++) {
        allEle[i].style.border = "2px solid white";
    }
    element.style.border = "2px solid red";
}

function getFixedCordX(eventX) {
    var relative = eventX - canvas.getBoundingClientRect().left
    var resizing = document.getElementById("canvas").width / document.getElementById("containerBoard").clientWidth
    return Math.round(relative * resizing)
}

function getFixedCordY(eventY) {
    var relative = eventY - canvas.getBoundingClientRect().top
    var resizing = document.getElementById("canvas").height / document.getElementById("containerBoard").clientHeight
    return Math.round(relative * resizing)
}

function sendStart(e) {
    console.log("CUrr action is:" + action)
    if (action == "fill") {
        json = {inst_type: 'fill', x: scaleXForServer(getFixedCordX(e.clientX)), y: scaleYForServer(getFixedCordY(e.clientY))}
        socket.emit( 'client_instruction', json);
        return;
    }
    is_drawing = true
    start({clickX : getFixedCordX(e.clientX), clickY : getFixedCordY(e.clientY)})
    pixels_x.push(scaleXForServer(getFixedCordX(e.clientX)));
    pixels_y.push(scaleYForServer(getFixedCordY(e.clientY)));
}

function sendDraw(e) {
    if (is_drawing) {
        console.log(e.clientX, e.clientY)
        draw({clickX : getFixedCordX(e.clientX), clickY : getFixedCordY(e.clientY)} )
        if (pixels_x.length > 50) {
            my_json = {inst_type: 'stroke', pixels_x : pixels_x, pixels_y : pixels_y};
            socket.emit( 'client_instruction', my_json);
            console.log("Sent: \n" + my_json);
            pixels_x = [pixels_x[pixels_x.length - 1]];
            pixels_y = [pixels_y[pixels_y.length - 1]];
        } else {
            pixels_x.push(scaleXForServer(getFixedCordX(e.clientX)));
            pixels_y.push(scaleYForServer(getFixedCordY(e.clientY)));
        }
  }
}

function sendStop(e) {
    if (is_drawing) {
        stop({})
        if (pixels_x.length > 1) {
            my_json = {inst_type: 'stroke', pixels_x : pixels_x, pixels_y : pixels_y}
            socket.emit( 'client_instruction', my_json)
            console.log("Sent: \n" + my_json)
            pixels_x = []
            pixels_y = []
        }
    }
}

function sendClearCanvas(e) {
    socket.emit( 'client_instruction', {inst_type: 'clear'} )
}

function undo_last() {
    socket.emit( 'client_instruction', {inst_type: 'undo'} )
}

socket.on( 'new_instruction', function(inst) {
    console.log("got instruction")
    console.log(inst)
    if (inst.inst_type == "clear") {
        clear_canvas();
        return;
    } else if (inst.inst_type == "fill") {
        //action = "fill"
        red_border(document.getElementById("fill_button"));
        console.log("Filling: " + inst.x + "," + inst.y + "," + "[" + draw_color + ", 1]")
        context.fillFlood(guesserWidthFactor * inst.x, guesserHeightFactor * inst.y, draw_color)
        return;
    } else if (inst.inst_type == "change_action") {
        console.log("action changed")
        action = inst.action;
        console.log(action);
    } else if (inst.inst_type == "change_width") {
        console.log("width changed")
        draw_width = inst.width;
        console.log(draw_width);
    } else if (inst.inst_type == "change_color") {
        console.log("color changed")
        draw_color = inst.color;
        draw_sample_context.fillStyle = draw_color;
        draw_sample_context.fillRect(0, 0, canvas_sample.width, canvas_sample.height);
        console.log(draw_color);
    } else if (inst.inst_type == "stroke") {
        var my_json;
        start({clickX : guesserWidthFactor * inst.pixels_x[0], clickY : guesserHeightFactor * inst.pixels_y[0]});
        console.log("drawing");
        for (var i = 0; i < inst.pixels_x.length; i++) {
            my_x = guesserWidthFactor * inst.pixels_x[i];
            my_y = guesserHeightFactor * inst.pixels_y[i];
            my_json = {clickX : my_x, clickY : my_y}
            draw(my_json);
        }
        my_json['op'] = 'stop';
        stop(my_json);
    }
})

