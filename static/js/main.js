var socket = io.connect('http://' + document.domain + ':' + location.port + "/main_page");
makeWork();
socket.on( 'connect', function() {
    console.log("connected to socket");
})

socket.on( 'update_lobbies_list', function(json) {
    var table = document.getElementById('rooms_table');
    var tb = document.querySelectorAll('tbody');
    // delete 'old' list
    /*for (var i = 0; i < tb.length; i++) {
        if (tb[i].children.length === 0) {
            tb[i].parentNode.removeChild(tb[i]);
        }
    }*/
    $('#rooms_table tbody').empty();
    // create new list
    for (var lobby_id of Object.keys(json)) {
        var tr = document.createElement("tr");
        var player_count = json[lobby_id][0];
        var started = json[lobby_id][1];
        var need_pass = json[lobby_id][2];
        var lobby_idTD = document.createElement("td");
        if (need_pass) {  // if requires password
            lobby_idTD.innerHTML = '<div>' +
              '<button type="button" class="js-modal-trigger" data-target="password_modal_' + lobby_id + '">' +
                lobby_id +
              '</button>' +
              '<div id="password_modal_' + lobby_id + '" class="modal">' +
                '<div class="modal-background"></div>' +
                '<div class="modal-content">' +
                 '<div class="box">' +
                    '<div class="field">' +
                      '<label>Room Password</label>' +
                      '<div class="control">' +
                        '<input type="text" id="req_room_password_' + lobby_id + '" name="room_password" placeholder="Enter Password"/>' +
                      '</div>' +
                      '<p style="display: none" id="password_help_' + lobby_id + '" class="help is-danger">Incorrect Password</p>' +
                    '</div>' +
                    '<input type="submit" onclick="updateRoomID(\'' + lobby_id + '\')"/>' +
                  '</div>' +
                '</div>' +
                '<button type="button" class="modal-close is-large" aria-label="close"></button>' +
              '</div>' +
            '</div>'
        } else {
            lobby_idTD.innerHTML = '<div><input type="submit" value="' + lobby_id + '" onclick="updateRoomID(\'' + lobby_id + '\')"/></div>'
        }

        var newTb = document.createElement("tbody");
        var player_countTD = document.createElement("td");
        var startedTD = document.createElement("td");
        var need_passTD = document.createElement("td");
        player_countTD.appendChild(document.createTextNode(player_count));
        startedTD.appendChild(document.createTextNode(started));
        if (need_pass) {
            need_passTD.appendChild(document.createTextNode("Private"));
        } else {
            need_passTD.appendChild(document.createTextNode("Public"));
        }
        tr.appendChild(lobby_idTD);
        tr.appendChild(player_countTD);
        tr.appendChild(startedTD);
        tr.appendChild(need_passTD);
        newTb.appendChild(tr);
        table.appendChild(newTb);
    }
    makeWork();
    //document.getElementById('testTitle').innerText = json.msg;
})

function makeWork() {
  // Functions to open and close a modal
  function openModal($el) {
    $el.classList.add('is-active');
  }

  function closeModal($el) {
    $el.classList.remove('is-active');
  }

  function closeAllModals() {
    (document.querySelectorAll('.modal') || []).forEach(($modal) => {
      closeModal($modal);
    });
  }

  // Add a click event on buttons to open a specific modal
  (document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
    const modal = $trigger.dataset.target;
    const $target = document.getElementById(modal);
    console.log($target);

    $trigger.addEventListener('click', () => {
      openModal($target);
    });
  });

  // Add a click event on various child elements to close the parent modal
  (document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button') || []).forEach(($close) => {
    const $target = $close.closest('.modal');

    $close.addEventListener('click', () => {
      closeModal($target);
    });
  });

  // Add a keyboard event to close all modals
  document.addEventListener('keydown', (event) => {
    const e = event || window.event;

    if (e.keyCode === 27) { // Escape key
      closeAllModals();
    }
  });
}

// modal js:
/*document.addEventListener('DOMContentLoaded', () => {
  // Functions to open and close a modal
  function openModal($el) {
    $el.classList.add('is-active');
  }

  function closeModal($el) {
    $el.classList.remove('is-active');
  }

  function closeAllModals() {
    (document.querySelectorAll('.modal') || []).forEach(($modal) => {
      closeModal($modal);
    });
  }

  // Add a click event on buttons to open a specific modal
  (document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
    const modal = $trigger.dataset.target;
    const $target = document.getElementById(modal);
    console.log($target);

    $trigger.addEventListener('click', () => {
      openModal($target);
    });
  });

  // Add a click event on various child elements to close the parent modal
  (document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button') || []).forEach(($close) => {
    const $target = $close.closest('.modal');

    $close.addEventListener('click', () => {
      closeModal($target);
    });
  });

  // Add a keyboard event to close all modals
  document.addEventListener('keydown', (event) => {
    const e = event || window.event;

    if (e.keyCode === 27) { // Escape key
      closeAllModals();
    }
  });
});*/

// my js
function updateRoomID(id){
    document.getElementById("room_id_1").value = id;
}

function validateForm(){
    document.getElementById("room_id_help2").style.display = "none";
    //alert(document.getElementById("room_id").value)
    //alert(document.getElementById("room_id").value.length)
    if (document.getElementById("room_id").value.length == 0) {
        document.getElementById("room_id_help1").style.display = "block";
        return false;
    }
    document.getElementById("room_id_help1").style.display = "none";
    return true;
}

function request_icon_change(icon) {
    socket.emit("request_icon_change", {"icon": icon})
}

socket.on( 'icon_changed', function(json) {
    document.getElementById('user_icon').src = "/static/Images/" + json.icon + ".png";
    console.log("changed icon")
})