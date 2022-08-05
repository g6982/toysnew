odoo.define('website_store_pickup.website_store_pickup', function(require) {
    "use strict";
    
    var ajax = require('web.ajax');
    $(document).ready(function() {
        $('.oe_website_sale').each(function() {

            var oe_website_sale = this;
            var selected_store = $('#selected-store').data('selected-store');
            var is_shop = $('#is-shop').data('is-shop');
            var $store_list = $(this).find('.store-menu ul li');
            var max_lead_hours = parseInt($('#max-lead-hours').data('max-lead-hours'), 10);
            if (is_shop === 'not') {
                $('#o_payment_form_pay').addClass('disabled checkout-disabled');
            }

            var $store_list = $(this).find('.store-menu ul li');
            $store_list.each(function() {
                var store_id = $(this).find('input[name="store-id"]').val();
                if (store_id == selected_store) {
                    $(this).find('.selected-symbole').show();
                    return false;
                }
            });

            var $carriers = $("#delivery_carrier input[name='delivery_type']");
            $carriers.on('click', function(ev) {
                var carrier_id = $(ev.currentTarget).val();
                var values = {'carrier_id': carrier_id};
                $('.store_pickup_loder').show();
                ajax.jsonRpc('/store/pickup/json', 'call', values)
                .then(function(result) {
                    $('#store-pickup-map').remove();
                    if (result) {
                        $('#delivery_carrier').after(result);
                        var max_lead_hours = parseInt($('#max-lead-hours').data('max-lead-hours'), 10);
                        var is_shop = $('#is-shop').data('is-shop');
                        if (is_shop === 'not') {
                            $('#o_payment_form_pay').addClass('disabled checkout-disabled');
                        }

                    } else {
                        $('#o_payment_form_pay').removeClass('disabled checkout-disabled');
                    }
                    $('.store_pickup_loder').hide();
                });
            });

            $(oe_website_sale).on('click', '.store-menu ul li', function() {
                var $temp = $(this);
                $('.store-menu ul li').find('.selected-symbole').hide();
                var store_id = parseInt($(this).find('input[name="store-id"]').first().val(), 10);
                $('.store_pickup_loder').show();

                ajax.jsonRpc('/store/pickup/addr', 'call', {
                    'store_id': store_id
                })
                .then(function(store_data) {
                    if (store_data) {
                        var $addr = $(store_data);
                        $('.selected-store').html($addr);
                        $temp.append("<div class='selected-symbole col-md-2'><i class='fa fa-check'></i></div>");
                        $('.oe_website_sale form button.btn-primary').removeClass('disabled checkout-disabled');
                    } else {
                        $('.selected-store').html("all product is not availble on this store please choose an other store.");
                        $('.oe_website_sale form button.btn-primary').addClass('disabled checkout-disabled');
                    }
                    $('.store_pickup_loder').hide();
                });
            });

            $('.oe_website_sale form button.btn-primary.checkout-disabled').parent().bind('contextmenu', function(e) {
                e.preventDefault();
            });

            $(function() {
                var date1 = new Date();
                if (!max_lead_hours)
                    max_lead_hours = 0
                date1.setHours(date1.getHours() + max_lead_hours);
                $('#datetimepicker').datepicker({
                    defaultDate: date1,
                    minDate: date1,
                    format: 'MM/DD/YYYY HH:mm:ss',
                    icons: {
                        time: "fa fa-clock-o",
                        date: "fa fa-calendar",
                        up: "fa fa-arrow-up",
                        down: "fa fa-arrow-down",
                    }
                });
            });
        });
    });
});
