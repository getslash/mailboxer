module.exports = Ember.Route.extend({

    api: function(method, path, data) {
        var self = this;
        return new Ember.RSVP.Promise(function(resolve, reject) {
            Ember.$.ajax({
                method: method,
                dataType: "json",
                contentType: "application/json",
                url: "/v2/" + path,
                data: (method=="GET")?(null):(JSON.stringify(data))
            }).then(function(result) {
                resolve(result);
            }, reject);
        });
    },

    GET: function(path) {
        return this.api("GET", path);
    },

    POST: function(path, data) {
        return this.api("POST", path, data);
    }

});
