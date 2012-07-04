if (autoclave === undefined) {
    var autoclave = {};
}


autoclave.notify = function(msg, type) {
    $.pnotify.defaults.history = false;
    $.pnotify({
        "title" : type,
        "type" : type,
        "text" : msg
    });
}

autoclave.notify_info = function(msg) {
    autoclave.notify(msg, "info");
}

function __get_notify_div(cls) {
    var returned = $('<div class="alert fade in"></div>');
    returned.addClass(cls);
    return returned;
}
