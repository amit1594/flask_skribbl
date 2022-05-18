var socket = io.connect('http://' + document.domain + ':' + location.port + "/test");

socket.on( 'connect', function() {
    console.log("connected")
})

socket.on( 'disconnect', function() {
    console.log("disconnected")
})

function tryDisc() {
    socket.emit('please_disconnect')
}
