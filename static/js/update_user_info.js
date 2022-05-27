var socket = io.connect('http://' + document.domain + ':' + location.port + "/main_page");
make_modals_work();
socket.on( 'connect', function() {
    console.log("connected to socket");
})
make_modals_work();
function validate_username() {
    var uName = document.getElementById("uName").value + "" || "";
    var helper = document.getElementById("username_help");
    helper.innerText = "";
    var notAllowed = ["<", ">", ":", "\"", "{", "}"];
    for (var char of notAllowed) {
        if (uName && uName.includes(char)) {
            helper.innerText += "Username may not include the character '" + char + "'\n";
        }
    }
    //alert(helper.innerText === "");
    return helper.innerText === "";
}

function request_icon_change(icon) {
    socket.emit("request_icon_change", {"icon": icon})
}

socket.on( 'icon_changed', function(json) {
    document.getElementById('user_icon').src = "/static/Images/" + json.icon + ".png";
    console.log("changed icon")
})

function encrypt_pass() {
    if (validate_username()) {
        var pass = document.getElementById("password");
        pass.value = CryptoJS.MD5(pass.value).toString();
        console.log(pass.value);
        return true;
    } else {
        return false;
    }
}