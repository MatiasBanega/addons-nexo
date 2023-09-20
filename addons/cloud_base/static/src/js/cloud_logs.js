/** @odoo-module **/

import AbstractAction from "web.AbstractAction";
import { action_registry, qweb, _lt } from "web.core";
import framework from "web.framework";
import session from "web.session";

const CloudLogsWidget = AbstractAction.extend({
    template: 'cloud.base.log',
    hasControlPanel: true,
    loadControlPanel: true,
    withSearchBar: true,
    searchMenuTypes: ['filter', 'favorite'],
    /*
     * override to initialize our own action
     * add export button to control pannel
    */
    init(parent, action, options={}) {
        this._super(...arguments);
        this.action = action;
        this.actionManager = parent;
        this.searchModelConfig.modelName = 'clouds.log';
        this.options = options;
        this.lastLog = false;
        this.firstLog = false;
        this.searchDomain = [];
    },    
    /**
     * @override to render logs at the first initiation
     */
    async start() {
        await this._super(...arguments);
        var logEl = this.$el.find("#cloud_logs_html");
        this.logEl = logEl[0];
        this.clientList = this.$el.find("#cloud_logs_clients_state")[0];
        this.queueList = this.$el.find("#cloud_logs_queue")[0];
        this.moreBtn = this.$el.find("#clouds_logs_more_div");
        this.selectedClients = [];
        this.$el.on('click', '#clouds_logs_more_div', ev => this._updatePreviousLogs(ev));
        this.$el.on('click', '.cloud_logs_client_select', ev => this._onClickClient(ev));
        this.$el.on('click', '#cloud_logs_open_client', ev => this._onOpenClient(ev));
        this.$el.on('click', '#cloud_logs_active_tasks', ev => this._onOpenActiveQueue(ev, false));
        this.$el.on('click', '#cloud_logs_failed_tasks', ev => this._onOpenActiveQueue(ev, true));
        this.$el.on('click', '#cloud_logs_export', ev => this._onExportLogs(ev, true));
        this._loadRefreshClients();
        this._loadRefreshQueue();
        await this._loadLogs();
        this._setRefreshInterval();

    },
    /**
     * The method to set refreshing logs 
    */
    _setRefreshInterval() {
        if (this.intervalId) {clearInterval(this.intervalId)};
        this.intervalId = setInterval(() => {
            this._loadRefreshClients();
            this._loadRefreshQueue();
            this._refreshLogs();
        }, 6000); // once in 6 seconds        
    },
    /**
     * The method to load/refresh list of clients and their states
     */
    async _loadRefreshClients() {
        var cloud_clients = await this._rpc({
            model: "clouds.log",
            method: "get_cloud_clients",
            args: [this.selectedClients],
        }); 
        this.clientList.innerHTML = qweb.render('cloud.base.clients.state', {"cloud_clients": cloud_clients});
    },
    /**
     * The method to load/refresh list of tasks related to chosen clients
     */
    async _loadRefreshQueue() {
        var client_queue = await this._rpc({
            model: "clouds.log",
            method: "get_cloud_queue",
            args: [this.selectedClients],
        }); 
        this.queueList.innerHTML = qweb.render('cloud.base.clients.queue', {"client_queue": client_queue});
    },
    /**
    * The method fully replace logs since initial load or because filters are changed
    */
    async _loadLogs() {
        this.logEl.innerHTML = "";
        var logsHTMLRes = await this._getLogs({});       
        if (logsHTMLRes.log_html) {
            this.logEl.innerHTML = logsHTMLRes.log_html;
            this.lastLog = logsHTMLRes.last_log;
            this.firstLog = logsHTMLRes.first_log;
            this._updateMoreBtn(logsHTMLRes.load_more_btn);
        }
        else {
            this.logEl.innerHTML = "";
            this.lastLog = false;
            this.firstLog = false;
            if (this.moreBtn) {this.moreBtn.addClass("cloud_base_hidden")};
            this.moreBtn = false;
        };
    },
    /**
     * The method to refresh logs (after) since time has passed and new logs might appear
     */
    async _refreshLogs() {
        var logsHTMLRes = await this._getLogs({"last_log": this.lastLog});
        if (logsHTMLRes.log_html) {
            this.logEl.innerHTML = this.logEl.innerHTML + logsHTMLRes.log_html;
            this.lastLog = logsHTMLRes.last_log;
        };
    },
    /**
     * The method to load previous logs (before) because of the triggered 'load more method'
     */
    async _updatePreviousLogs(ev) {
        event.preventDefault();
        event.stopPropagation(); 
        var logsHTMLRes = await this._getLogs({"first_log": this.firstLog});
        if (logsHTMLRes.log_html) {
            this.logEl.innerHTML = logsHTMLRes.log_html + this.logEl.innerHTML;
            this.firstLog = logsHTMLRes.first_log;
            this._updateMoreBtn(logsHTMLRes.load_more_btn);
        };
    },
    /**
     * The method to prepare HTML of existing logs + update current state
     * @param required logArgs - dict of filters/settings. 
     */
    async _getLogs(logArgs) {
        var logsHTMLRes = await this._rpc({
            model: "clouds.log",
            method: "action_prepare_logs_html",
            args: [logArgs, this.searchDomain, this.selectedClients],
        });
        return logsHTMLRes;
    },
    /**
     * @private
     * @param {Object} searchQuery
     * The method to apply search criteria (the top search box)
    */
    _onSearch: function(searchQuery) {
        if (this.intervalId) {clearInterval(this.intervalId)};
        this.searchDomain = searchQuery.domain;
        this._reloadLogsOnSearch();
    },
    /**
     * The method to select/unselect a client
     */
    async _onClickClient(ev) {
        if (this.intervalId) {clearInterval(this.intervalId)};
        ev.preventDefault();
        ev.stopPropagation(); 
        var resID = parseInt(ev.currentTarget.id);
        if ($(ev.currentTarget).hasClass("cloud_logs_client_checked")) {
            $(ev.currentTarget).removeClass("cloud_logs_client_checked");
        }
        else {
            this.selectedClients.push(resID);
            $(ev.currentTarget).addClass("cloud_logs_client_checked");
        };
        var all_selected = this.$el.find(".cloud_logs_client_checked");
        var finalArray = [];
        await _.each(all_selected, function (choice) {finalArray.push(choice.id)});      
        this.selectedClients = finalArray;
        this._loadRefreshQueue();
        this._reloadLogsOnSearch();
    },
    /**
     * The method to open client in a new window
     */
    async _onOpenClient(ev){
        ev.preventDefault();
        ev.stopPropagation();
        var resID = parseInt($(event.target).data("id"));
        var actionDict = await this._rpc({
            route: "/web/action/load",
            params: {action_id: "cloud_base.clouds_client_action_form_only"}
        })
        actionDict.res_id = resID;
        return this.do_action(actionDict);
    },    
    /**
     * @private
     * The method to reload logs based on search criteria
    */
    _reloadLogsOnSearch() {
        this._loadLogs();
        this._setRefreshInterval();
    },
    /**
    * The method to show/hide 'Load more buton'
      @param show - bool
    */
    _updateMoreBtn: function(show) {
        if (this.moreBtn) {
            if (show) {this.moreBtn.removeClass("cloud_base_hidden")}
            else {this.moreBtn.addClass("cloud_base_hidden")};
        };
    },
    /**
    * The method to open list of active tasks (related for chosen clients)
    */
    async _onOpenActiveQueue(ev, only_blocked) {
        ev.preventDefault();
        ev.stopPropagation();
        var action_id = await this._rpc({
            model: "clouds.log",
            method: "action_open_tasks",
            args: [this.selectedClients, only_blocked],
        });
        this.do_action(action_id);        
    },
    /**
    * The method to prepare logs text file (.logs)
    */
    async _onExportLogs(ev) {
        framework.blockUI();
        var localData = JSON.stringify({
            search_domain: this.searchDomain,
            selected_clients: this.selectedClients,
        });
        await session.get_file({
            url: "/cloud_base/export_logs",
            data: {search_params: localData},
            complete: framework.unblockUI,
            error: (error) => this.call('crash_manager', 'rpc_error', error),

        });
    },
});

action_registry.add('cloud.base.log', CloudLogsWidget);

export default CloudLogsWidget;
