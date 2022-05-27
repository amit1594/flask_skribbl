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