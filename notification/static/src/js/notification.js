var executed = false;

odoo.define("notification.Notify", function (require) {
  "use strict";

  var ListController = require("web.ListController");
  var FormController = require("web.FormController");
  var KanbanController = require("web.KanbanController");

  KanbanController.include({
    init: function () {
      this._super.apply(this, arguments);
      var self = this;

      var inicioPromise = this._rpc({
        model: "ir.config_parameter",
        method: "search_read",
        fields: ["key", "value"],
        domain: [["key", "=", "horario_noti_inicio"]],
      });

      var finPromise = this._rpc({
        model: "ir.config_parameter",
        method: "search_read",
        fields: ["key", "value"],
        domain: [["key", "=", "horario_noti_fin"]],
      });

      Promise.all([inicioPromise, finPromise]).then(function (results) {
        if (results[0].length > 0 && results[1].length > 0) {
          var inicio = parseInt(results[0][0].value, 10);
          var fin = parseInt(results[1][0].value, 10);
        }
        var now = new Date();

        if (now.getHours() >= inicio && now.getHours() < fin && !executed) {
          self.displayNotification({
            type: "danger",
            title: "Registrar marcación de salida",
            message: "Recordá registrar tu marcación de salida",
            sticky: true,
          });

          executed = true;
        }
      });
    },
  });

  FormController.include({
    init: function () {
      this._super.apply(this, arguments);
      var self = this;

      var inicioPromise = this._rpc({
        model: "ir.config_parameter",
        method: "search_read",
        fields: ["key", "value"],
        domain: [["key", "=", "horario_noti_inicio"]],
      });

      var finPromise = this._rpc({
        model: "ir.config_parameter",
        method: "search_read",
        fields: ["key", "value"],
        domain: [["key", "=", "horario_noti_fin"]],
      });

      Promise.all([inicioPromise, finPromise]).then(function (results) {
        if (results[0].length > 0 && results[1].length > 0) {
          var inicio = parseInt(results[0][0].value, 10);
          var fin = parseInt(results[1][0].value, 10);
        }
        var now = new Date();

        if (now.getHours() >= inicio && now.getHours() < fin && !executed) {
          self.displayNotification({
            type: "danger",
            title: "Registrar marcación de salida",
            message: "Recordá registrar tu marcación de salida",
            sticky: false,
          });

          executed = true;
        }
      });
    },
  });

  ListController.include({
    init: function () {
      this._super.apply(this, arguments);
      var self = this;

      var inicioPromise = this._rpc({
        model: "ir.config_parameter",
        method: "search_read",
        fields: ["key", "value"],
        domain: [["key", "=", "horario_noti_inicio"]],
      });

      var finPromise = this._rpc({
        model: "ir.config_parameter",
        method: "search_read",
        fields: ["key", "value"],
        domain: [["key", "=", "horario_noti_fin"]],
      });

      Promise.all([inicioPromise, finPromise]).then(function (results) {
        if (results[0].length > 0 && results[1].length > 0) {
          var inicio = parseInt(results[0][0].value, 10);
          var fin = parseInt(results[1][0].value, 10);
        }
        var now = new Date();

        if (now.getHours() >= inicio && now.getHours() < fin && !executed) {
          self.displayNotification({
            type: "danger",
            title: "Registrar marcación de salida",
            message: "Recordá registrar tu marcación de salida",
            sticky: false,
          });

          executed = true;
        }
      });
    },
  });
});
