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