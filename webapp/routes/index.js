Ember.TEMPLATES['index'] = require('../templates/index.hbs');

var BaseRoute = require('./base.js');

module.exports = BaseRoute.extend({
    model: function() {

        var self = this;
        return new Ember.RSVP.Promise(function (resolve, reject) {

            self.GET("mailboxes").then(function(data) {

                var mailboxes = [];

                data.result.forEach(function(mailbox) {
                    var m = Ember.Object.create({
                        address: mailbox.address,
                        last_activity_str: moment.unix(mailbox.last_activity).fromNow(),
                        will_delete_str: moment.unix(mailbox.will_delete).fromNow()
                    });
                    mailboxes.push(m);
                });

                resolve(Ember.Object.create({
                    mailboxes:mailboxes
                }));

            }, reject);
        });

    }
});
