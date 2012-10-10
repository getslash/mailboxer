if (app === undefined) {
    var app = {};
}

if (app.api === undefined) {
    app.api = {};
}

app.api.call = function(path, data) {
    return $.ajax(path, {
        data : JSON.stringify(data),
        contentType : "application/json",
        processData: false,
        dataType: "json",
        type : "POST",
        error : function (request, msg, error) {
            app.notify_error("Ajax error on <b>" + path + "</b>: " + error);
        }
    });
}
