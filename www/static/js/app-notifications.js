if (app === undefined) {
    var app = {};
}

app.notify = function(msg, type) {
    $.pnotify.defaults.history = false;
    $.pnotify({
        "title" : type,
        "type" : type,
        "text" : msg
    });
}

app.notify_info = function(msg) {
    app.notify(msg, "info");
}

app.notify_warning = function(msg) {
    app.notify(msg, "warning");
}

app.notify_error = function(msg) {
    app.notify(msg, "error");
}

app.notify_success = function(msg) {
    app.notify(msg, "success");
}
