var socket = io.connect('http://' + document.domain + ':' + location.port + "/lobby");
let pixels_x = [], pixels_y = [];
let curr_stroke = {};

socket.on( 'connect', function() {
    console.log("Room: " + room);
    socket.emit( 'player_join');
})

function emitWordChoice(word) {
    // emitting the chosen word
    socket.emit( 'artist_chose_word', {chosen_word: word} );
}

function writeBoardOverlayList(msg, listElem, ordered) {
    // writes the given dict as a list on the overlay
    var node, textnode;
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
    // displays or hides the word choices buttons
    document.getElementById("WordChoicesButtonDiv").style.display = flag;
}

function isHebrew(num) {
   // returns true if the ascii val is within the hebrew range
   return (1488 <= num && num <= 1514);
}

function asciiArrayToString(arr) {
    // turns an ascii array into a string, while fixing ltr and rtl
    str = "\u202A";
    for (var i = 0; i < arr.length; i++) {
       if (isHebrew(arr[i])) {
           str += String.fromCharCode(arr[i]);
        }
        else {
            str += "\u202A" + String.fromCharCode(arr[i]) + "\u202C";
        }
    }
    return str;
}

socket.on( 'game_overlay', function(msg) {
    // displays the appropriate overlay
    displayWordChoicesButtons("None");
    removeCanvasListeners();
    var eType = msg.type;
    var gameScreenStyle = document.getElementById("GameScreen").style;
    var gameCanvasStyle = document.getElementById("gameCanvas").style;
    var boardOverlayStyle = document.getElementById("boardOverlay").style;
    var lobbyScreenStyle = document.getElementById("LobbyScreen").style;
    var boardOverlayTitle = document.getElementById("overlay_title");
    var boardOverlaylist = document.getElementById("overlayList");
    var gameHeader = document.getElementById("gameHeader");
    var bDiv = document.getElementById("WordChoicesButtonDiv");
    var toolbarDivStyle = document.getElementById("containerToolbar").style;
    var hintBtnDivStyle = document.getElementById("hintButtonContainer").style;
    boardOverlaylist.innerHTML = "";
    toolbarDivStyle.display = "none";
    hintBtnDivStyle.display = "none";
    gameScreenStyle.display = "flex";
    gameCanvasStyle.opacity = "1";
    lobbyScreenStyle.display = "none";
    if (eType === "guessing_view") {  // closing overlay
        gameCanvasStyle.display = "block";
        boardOverlayStyle.display = "none";
        context.fillStyle = "white";
        document.getElementById("wordSpace").innerText = "current word:  " + asciiArrayToString(msg["encoded_word"]);
        document.getElementById("timeLeft").innerText = msg["time"];
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
        // resetting the current stroke:
        curr_stroke = {};
        pixels_x = [];
        pixels_y = [];
        red_border(document.getElementById("pen_button"));
    } else if (eType === "new_round") {  // plain new round overlay
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
    // updating the player list on the lobby overlay
    document.getElementById('lobby_player_list').innerHTML = "";
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
    // creates the div for a player in the scoreboard
    my_str = "<div class=\"player\" id=\"player" + place + "\">";
	my_str += "<div class=\"rank\">#" + place + "</div>";
	my_str += "<div class=\"info\">";
	my_str += "<p class=\"name\">" + name + "</p>";
	my_str += "<p class=\"score\">Points: " + points + "</p></div>";
	my_str += "<div class=\"player_icon\">";
	my_str += "<img class=\"player_icon\" src=\"" + img + "\" alt=\"icon\">";
    my_str += "</div>";
    return my_str;
}

socket.on( 'update_scoreboard', function(msg) {
    // updates  the scoreboard
    var playerCount = 0;
    document.getElementById("scoreboardTblBody").innerHTML = "";
    var scoreboardTblBody = document.getElementById("scoreboardTblBody");
    var width = document.getElementById("containerPlayerList").getBoundingClientRect().width;
    for (var key of Object.keys(msg)) {
        playerCount += 1;
        document.getElementById("scoreboardTblBody").innerHTML += "<tr><td>" + create_score_div_html(playerCount, key, msg[key][0], msg[key][1])  + "</td></tr>";
    }
})

socket.on( 'allowed_to_start', function(msg) {
    // if allowed, will enable the startButton. Note: only admins get this event
    if (msg.flag === "true")
        document.getElementById('startButton').disabled = false;
    else
        document.getElementById('startButton').disabled = true;
})

socket.on( 'admin_update', function(msg) {
    // if received, it means this player became admin, enabling to change the settings. Note: only admins get this event
    if (uName === msg.admin) {
        console.log("You are the admin!");
        document.getElementById('Rounds').disabled = false;
        document.getElementById('DrawTime').disabled = false;
        document.getElementById('Languages').disabled = false;
        document.getElementById('customWords').disabled = false;
        document.getElementById('Gamemode').disabled = false;
        document.getElementById('Difficulty').disabled = false;
        document.getElementById("pointsLimit").disabled = false;
    }
})

function requestUpdateSettings() {
    // requesting to change current settings to the new ones
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
    // emitting a request_game_start event
    socket.emit( 'request_game_start')
}

function getIndexOfSelect(elem, value) {
    // returning the index of the searched value inside a list
    for (i = 0; i < elem.length; i++) {
        if (elem.options[i].text === "" + value)
            return i;
    }
    return 0;
}

socket.on( 'settings_update', function(msg) {
    // updates the settings (meaning only updating how a client sees them)
    document.getElementById("Rounds").selectedIndex = getIndexOfSelect(document.getElementById("Rounds"), msg["rounds"]);
    document.getElementById("DrawTime").selectedIndex = getIndexOfSelect(document.getElementById("DrawTime"), msg["draw_time"]);
    document.getElementById("Languages").selectedIndex = getIndexOfSelect(document.getElementById("Languages"), msg["language"]);
    document.getElementById("Gamemode").selectedIndex = getIndexOfSelect(document.getElementById("Gamemode"), msg["gamemode"]);
    document.getElementById("Difficulty").selectedIndex = getIndexOfSelect(document.getElementById("Difficulty"), msg["difficulty"]);
    document.getElementById("pointsLimit").selectedIndex = getIndexOfSelect(document.getElementById("pointsLimit"), msg["points_limit"]);
    document.getElementById("customWords").value = msg["custom_words"];
    if (msg['gamemode'] == "Points Rush") {
        document.getElementById("pLimitDiv").style.display = "block";
        document.getElementById("roundsDiv").style.display = "none";
    } else {
        document.getElementById("pLimitDiv").style.display = "none";
        document.getElementById("roundsDiv").style.display = "block";
    }
})

function getRGBFromColor(c) {
    // returns the rgb string of a color
    return `rgb(${draw_color.r}, ${draw_color.g}, ${draw_color.b})`;
}

function sendMessage() {
    // sending the client's message to the server
    var msg = document.getElementById("guess_input").value;
    if (msg.length > 0){
        socket.emit( 'new_chat_message', {
            message : msg
         } )
         document.getElementById("guess_input").innerText = "";
    }
}

function start(msg) {
    // start a stroke
    if (action != "pen")
        return;
    is_drawing = true;
    context.beginPath();
    context.moveTo(msg.clickX, msg.clickY);
    event.preventDefault();
    draw(msg);
}

function draw(msg) {
    // draw by the given data
    if (is_drawing) {
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
    // stop a stroke
    if (is_drawing) {
        context.stroke();
        context.closePath();
        is_drawing = false;
    }
}

function clear_canvas() {
    // sets the entire canvas white
    context.fillStyle = "white";
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.strokeStyle = getRGBFromColor(draw_color);
}

// CHAT HANDLING:

// instead of sending the form, sending the message to the server
document.getElementById("chatForm").addEventListener("submit", function(event) {
    event.preventDefault();
    var iChat = document.getElementById("inputChat");
    if (iChat.value.length > 0) {
        socket.emit( 'new_chat_message', {message: iChat.value} );
        iChat.value = "";
    }
});

function chat_handler(msg) {
    // updates the chat according to the given data
    var mDiv = document.getElementById("messages");
    var myP = document.createElement("p");
    if (typeof msg.type === 'undefined') {
        return;}
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

socket.on( 'chat_message', function(msg) {
    chat_handler(msg);
})

// HINT HANDLING:
function requestHint(mode) {
    console.log("requested hint")
    socket.emit( 'request_hint', {type : mode} )
}


// CANVASES SETUP:

// setup game canvas
const canvas = document.getElementById("canvas");
const boardContainer = document.getElementById("containerBoard");
const baseWidth = 1000;
const baseHeight = 620;
canvas.width = boardContainer.clientWidth;
canvas.height = boardContainer.clientHeight;
let context = canvas.getContext("2d");

context.fillStyle = "white";
context.fillRect(0, 0, canvas.width, canvas.height)

let start_background_color = "white";
let draw_color = "black";
change_color(document.getElementById("black-field"));
document.getElementById("pen_button").style.border = "2px solid red";
let draw_width = "2";
let is_drawing = false;
let action = "pen";

let artistWidthFactor = baseWidth / canvas.clientWidth;
let artistHeightFactor = baseHeight / canvas.clientHeight;
let guesserWidthFactor = canvas.clientWidth / baseWidth;
let guesserHeightFactor = canvas.clientHeight / baseHeight;

function scaleXForServer(val) {
    // returns the float scaled by artist width factor
    return parseFloat((artistWidthFactor * val).toFixed(2));
}

function scaleYForServer(val) {
    // returns the float scaled by artist height factor
    return parseFloat((artistHeightFactor * val).toFixed(2));
}

// CANVAS RESIZING:

function handleCanvasResize() {
    // handles canvas resizing
    if (canvas.width === boardContainer.clientWidth && canvas.height === boardContainer.clientHeight) {
        return false;
    }
    canvas.width = boardContainer.clientWidth;
    canvas.height = boardContainer.clientHeight;
    artistWidthFactor = baseWidth / canvas.clientWidth;
    artistHeightFactor = baseHeight / canvas.clientHeight;
    guesserWidthFactor = canvas.clientWidth / baseWidth;
    guesserHeightFactor = canvas.clientHeight / baseHeight;
    return true;
}

var doit;
handleCanvasResize();

window.addEventListener("resize", () => {
            if (handleCanvasResize()) {
                clearTimeout(doit);
                doit = setTimeout(function() {
                    socket.emit('requestEntireDrawing');
                }, 75);
            }
        }, false);

// SETUP CANVAS LISTENERS
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
    // request a color change
    request_color_change(element.style.background);
    var allEle = document.getElementsByClassName("color-field");
    for (var i = 0; i < allEle.length; i++) {
        allEle[i].style.opacity = 0.6;
    }
    element.style.opacity = 1;
}

function red_border(element) {
    // red boreders the given element
    var allEle = document.getElementsByTagName("button")
    for (var i = 0; i < allEle.length; i++) {
        allEle[i].style.border = "2px solid white";
    }
    element.style.border = "2px solid red";
}

function getFixedCordX(eventX) {
    // returns the fixed position of the mouse's X according to the canvas
    var relative = eventX - canvas.getBoundingClientRect().left
    var resizing = document.getElementById("canvas").width / document.getElementById("containerBoard").clientWidth;
    return Math.round(relative * resizing)
}

function getFixedCordY(eventY) {
    // returns the fixed position of the mouse's Y according to the canvas
    var relative = eventY - canvas.getBoundingClientRect().top
    var resizing = document.getElementById("canvas").height / document.getElementById("containerBoard").clientHeight;
    return Math.round(relative * resizing)
}

function sendStart(e) {
    // sends instructions
    if (action == "fill") {
        json = {inst_type: 'fill', x: scaleXForServer(getFixedCordX(e.clientX)), y: scaleYForServer(getFixedCordY(e.clientY))}
        socket.emit( 'client_instruction', json);
        return;
    }
    is_drawing = true;
    start({clickX : getFixedCordX(e.clientX), clickY : getFixedCordY(e.clientY)})
    pixels_x.push(scaleXForServer(getFixedCordX(e.clientX)));
    pixels_y.push(scaleYForServer(getFixedCordY(e.clientY)));
}

function sendDraw(e) {
    // sends instructions
    if (is_drawing) {
        draw({clickX : getFixedCordX(e.clientX), clickY : getFixedCordY(e.clientY)} );
        if (pixels_x.length > 50) {
            my_json = {inst_type: 'stroke', pixels_x : pixels_x, pixels_y : pixels_y};
            socket.emit( 'client_instruction', my_json);
            pixels_x = [pixels_x[pixels_x.length - 1]];
            pixels_y = [pixels_y[pixels_y.length - 1]];
        } else {
            pixels_x.push(scaleXForServer(getFixedCordX(e.clientX)));
            pixels_y.push(scaleYForServer(getFixedCordY(e.clientY)));
        }
  }
}

function sendStop(e) {
    // sends instructions
    if (is_drawing) {
        stop({});
        if (pixels_x.length > 1) {
            my_json = {inst_type: 'stroke', pixels_x : pixels_x, pixels_y : pixels_y}
            socket.emit( 'client_instruction', my_json)
            pixels_x = []
            pixels_y = []
        }
    }
}

function sendClearCanvas(e) {
    socket.emit( 'client_instruction', {inst_type: 'clear'} );
}

function undo_last() {
    socket.emit( 'client_instruction', {inst_type: 'undo'} );
}

socket.on( 'new_instruction', function(inst) {
    // processes the given instruction
    if (inst.inst_type == "clear") {
        clear_canvas();
        return;
    } else if (inst.inst_type == "fill") {
        red_border(document.getElementById("fill_button"));
        context.fillFlood(guesserWidthFactor * inst.x, guesserHeightFactor * inst.y, draw_color)
        return;
    } else if (inst.inst_type == "change_action") {
        action = inst.action;
    } else if (inst.inst_type == "change_width") {
        draw_width = inst.width;
    } else if (inst.inst_type == "change_color") {
        draw_color = inst.color;
    } else if (inst.inst_type == "stroke") {
        var my_json;
        start({clickX : guesserWidthFactor * inst.pixels_x[0], clickY : guesserHeightFactor * inst.pixels_y[0]});
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

