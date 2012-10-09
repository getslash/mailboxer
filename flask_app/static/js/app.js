if (app === undefined) {
    var app = {};
}

app.delete_all_messages = function() {
    return $.ajax("/mailboxes/*", {
	type : "DELETE",
	error : function (request, msg, error) {
            app.notify_error("Ajax error on <b>" + path + "</b>: " + error);
        },
    })
}
