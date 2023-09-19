odoo.define('check_in_location.my_attendances', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var field_utils = require('web.field_utils');

const session = require('web.session');

var BHMyAttendances = AbstractAction.extend({
    contentTemplate: 'BHHrAttendanceMyMainMenu',
    events: {
        "click .o_hr_attendance_sign_in_out_icon": _.debounce(function(e) {
            this.update_attendance(e);
        }, 200, true),
    },

    willStart: function () {
        var self = this;

        var def = this._rpc({
                model: 'hr.employee',
                method: 'search_read',
                args: [[['user_id', '=', this.getSession().uid]], ['attendance_state', 'name', 'hours_today']],
                context: session.user_context,
            })
            .then(function (res) {
                self.employee = res.length && res[0];
                if (res.length) {
                    self.hours_today = field_utils.format.float_time(self.employee.hours_today);
                }
            });

        var def_location = this._rpc({
                model: 'hr.attendance.location',
                method: 'search_read',
                args: [[], ['id', 'code', 'name','loc_class_name'],,,'sequence ASC'],
                context: session.user_context,
            })
            .then(function (res) {
                self.attendance_location = res
            });

        return Promise.all([def, def_location, this._super.apply(this, arguments)]);
    },

    update_attendance: function (e) {
        var self = this;

//        var id_location = this.$el.find('#locationSelected').val();
        var id_location = parseInt(e.currentTarget.getAttribute('location-id'));

        var context = session.user_context;
        context = _.extend({}, context, {
            current_location: id_location,
        });

        this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
                context: context,
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.displayNotification({ title: result.warning, type: 'danger' });
                }
            });
    },
});

core.action_registry.add('bh_hr_attendance_my_attendances', BHMyAttendances);

return BHMyAttendances;

});
