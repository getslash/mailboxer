var api = require('../utils/api.js');

App.MailboxesModel = Ember.Object.extend({
    mailboxes: [],

    refreshIntervalSeconds: 5,

    refresh: function() {
        var self = this;

        return api.GET("mailboxes").then(function(data) {

            self.set("mailboxes", []);

            data.result.forEach(function(mailbox) {
                var m = Ember.Object.create({
                    address: mailbox.address,
                    last_activity_str: moment.unix(mailbox.last_activity).fromNow(),
                    will_delete_str: moment.unix(mailbox.will_delete).fromNow(),
                    lastUpdated: moment().format()
                });
                self.mailboxes.push(m);
            });
        });
    },

    startRefreshing: function() {
        var self = this;
        self.set("timerId", Ember.run.later(function() {

            self.refresh();

            self.startRefreshing();
        }, self.get("refreshIntervalSeconds") * 1000));
    },

    stopRefreshing: function() {
        var self = this;

        Ember.run.cancel(self.get("timerId"));
    }
    
});

module.exports = Ember.Route.extend({

    deactivate: function() {
        var self = this;

        self.get("model").stopRefreshing();
    },

    model: function() {

        var self = this;
        var returned = App.MailboxesModel.create();
        self.set("model", returned);

        return new Ember.RSVP.Promise(function (resolve, reject) {

            returned.refresh().then(function() {
                resolve(returned);
                returned.startRefreshing();
            }, reject);
        });

    }
});
