function encrypt_pass() {
    var pass = document.getElementById("password");
    pass.value = CryptoJS.MD5(pass.value).toString();
    console.log(pass.value);
    return true;
}