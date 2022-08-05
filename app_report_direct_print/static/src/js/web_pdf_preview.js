odoo.define('app_report_direct_print.report', function (require) {
    'use strict';

    var ActionManager = require('web.ActionManager');
    var core = require('web.core');
    var session = require('web.session');
    var framework = require('web.framework');

    var PreviewDialog = require('app_report_direct_print.PreviewDialog');

    var _t = core._t;
    var _lt = core._lt;


    ActionManager.include({
        _executeReportAction: function (action, options) {
            var self = this;
            action = _.clone(action);

            if (action.report_type === 'qweb-pdf') {
                return this.call('report', 'checkWkhtmltopdf').then(function (state) {
                    var active_ids_path = '/' + action.context.active_ids.join(',');
                    // var url = '/report/pdf/' + action.report_name + active_ids_path;
                    var url = self._makeReportUrls(action)['pdf'];
                    var filename = action.report_name;
                    var title = action.display_name;
                    var printUrl = decodeURIComponent('/app_report_direct_print/static/lib/PDFjs/web/viewer.html?file=' + url + '&print_auto=1');
                    if (session.app_print_auto) {
                        window.open(printUrl, '_blank');

                    } else {
                    var dialog = PreviewDialog.createPreviewDialog(self, url, false, "pdf", title);
                        $.when(dialog, dialog._opened).then(function (dialog) {
                            dialog.$modal.find('.preview-download').hide();
                        })
                    };
                    framework.unblockUI();
                });

            } else {
                return self._super(action, options);
            }

        }
    });

});