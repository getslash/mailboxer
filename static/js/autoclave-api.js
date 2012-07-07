if (autoclave === undefined) {
    var autoclave = {};
}

if (autoclave.api === undefined) {
    autoclave.api = {};
}

autoclave.api.call = function(path, data) {
    return $.ajax(path, {
        data : JSON.stringify(data),
        contentType : "application/json",
        processData: false,
        dataType: "json",
        type : "POST",
        error : function (request, msg, error) {
            autoclave.notify_error("Ajax error on <b>" + path + "</b>: " + error);
        }
    });
}
