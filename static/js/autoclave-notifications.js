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

autoclave.notify_warning = function(msg) {
    autoclave.notify(msg, "warning");
}

autoclave.notify_error = function(msg) {
    autoclave.notify(msg, "error");
}

autoclave.notify_success = function(msg) {
    autoclave.notify(msg, "success");
}
