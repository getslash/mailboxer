import Ember from 'ember';

export default Ember.Route.extend({
  model: function() {
        return {features: [
            {name: "Font Awesome", ok: true},
            {name: "Ember.js", ok: true},
            {name: "Bootstrap", ok: true}
        ]};
    }
});
