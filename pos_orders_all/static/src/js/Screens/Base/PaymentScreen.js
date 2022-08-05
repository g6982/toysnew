odoo.define('pos_orders_all.PaymentScreen', function(require) {
	'use strict';

	const PaymentScreen = require('point_of_sale.PaymentScreen');
	const Registries = require('point_of_sale.Registries');
	const session = require('web.session');
    var rpc = require('web.rpc');
    const { useListener } = require('web.custom_hooks');

	const BiPaymentScreen = PaymentScreen => 
		class extends PaymentScreen {
			constructor() {
				super(...arguments);
				useListener('click-credit',this.selectPaymentCreditLine);
				useListener('unselect-credit-all',this.UnSelectCreditAll);
				if(this.env.pos.config.auto_check_invoice){
					this.currentOrder.set_to_invoice(true);
				}
				this.paguitos = this.get_payments();
				this.order_is_return = this.currentOrder.is_return_order ? 'return' : 'no_return';
				this.payments_refund = [];
			}

            selectPaymentCreditLine(event) {
               var line = this.selectedPaymentLine;
               if (line==undefined){
                     swal("Ups !", "Para añadir un crédito pendiente, debe seleccionar el método de pago por devolución", "warning")
                     return 0;
               }
               //Todo >> Tiene que ser un método de pago exclusivo para devoluciones
               if (line.payment_method.is_refund != true){
                     swal("Ups !", "Para añadir un crédito pendiente, debe seleccionar el método de pago por devolución", "warning")
                     return 0;
                }
                var tr = event.detail;
                var $el = $(event.currentTarget);
//
                var row = $("#"+tr.toString());
//
//                var sw=0;
//                if (row.hasClass('bg-warning')){
//                    sw=1;
//                }

                var acumulado = 0;
                var repeat=0;
                $('#body_payments_credit tr').each(function(){
                    var t = $(this);
                    if (parseInt(t[0].id) == tr && t.hasClass('bg-warning')){
                        repeat=1;
                        t.removeClass('bg-warning');
                    }
                    if(t.hasClass('bg-warning')){
                         var td_amount = parseFloat(t[0].childNodes[2].textContent);
                         acumulado = acumulado + Math.abs(td_amount);
                    }
                })

                if(repeat==0){
                  row.addClass("bg-warning").focus();
                }

//                var repeat=0;
//                $('#body_payments_credit tr').each(function(){
//                    var t = $(this);
//                    if (parseInt(t[0].id) == tr && t.hasClass('bg-warning')){
//                        repeat=1;
//                        t.removeClass('bg-warning');
//                    }
//                })
//
//                if(repeat==0){
//                  row.addClass("bg-warning").focus();
//                }
//
                var amount_actual = line.amount;
                var new_amount = 0;
                var amount_apply = 0;
                for(var i=0; i<event.originalComponent.paguitos.length; i++){
                    if(event.originalComponent.paguitos[i].id == tr){
                        new_amount = Math.abs(event.originalComponent.paguitos[i].amount);
                        break;
                    }
                }
                if (repeat==1){
                    amount_apply = amount_actual - new_amount;
                }else{
                    amount_apply = acumulado + new_amount;
                }

                 //Todo: Pagos en modo refund seleccionados
                 var payments_refund = [];
                 $('#body_payments_credit tr').each(function(){
                       var xt = $(this);
                       if (xt.hasClass('bg-warning')){
                            var json = {
                                'id': xt[0].id,
                                'amount': xt[0].childNodes[2].textContent,
                                'reference': xt[0].childNodes[0].textContent,
                            }
                            payments_refund.push(json)
                       }
                   });
                line.payments_refund = payments_refund;

                 //Todo: Actualizar el monto a pagar
                line.set_amount(amount_apply);
            }


            UnSelectCreditAll(event){
                $('#body_payments_credit tr').each(function(){
                    $(this).removeClass('bg-warning');
                })
                var line = this.selectedPaymentLine;
                if(line){
                    if (line.payment_method.is_refund == true){
                        line.set_amount(0);
                    }
                }

                this.payments_refund = []
                event.originalComponent.payments_refund = this.payments_refund;
            }

            get_payments(){
                var self = this;
                var payments = []
                if(this.currentOrder.return_order_ref==false){
                     if (self.env.pos.attributes.selectedClient){
                        var cliente_id = self.env.pos.attributes.selectedClient.id;
//                         return rpc.query({
//                            model: 'res.partner',
//                            method: 'get_pos_payment_by_client',
//                            args: [[cliente_id]],
//                            })
//                            .then(function(result){
//                                console.log(result);
//                                return result;
//                            }).guardedCatch(function(){
//                                console.log("No se encontró resultados.")
//                                return []
//                            });
                        var all_payments = self.env.pos.db.all_payments_jhonny;
                        for (var i = 0; i < all_payments.length; i++) {
                            if(all_payments[i].partner_id != undefined){
                                if(all_payments[i].partner_id[0] == cliente_id && all_payments[i].is_used == false && all_payments[i].credit_client == true){
                                    var json = {
                                        'id': all_payments[i].id,
                                        'pos_reference': all_payments[i].pos_reference ,
                                        'date_order': all_payments[i].date_order,
                                        'method_paid_id': all_payments[i].journal_id[0],
                                        'method_paid_name': all_payments[i].journal_id[1],
                                        'amount': (Math.abs(all_payments[i].amount) - all_payments[i].amount_used).toFixed(2),
                                    }
                                    payments.push(json);
                                }
                            }
                        }

                    }
                }
                return payments;



            }


            new_payment(payment_i,payments,cliente_id){

                var order_news_in_cache = this.env.pos.db.pos_all_orders;
                if(order_news_in_cache!=undefined){
                   for (var nw = 0; nw < order_news_in_cache.length; nw++) {
                        if(order_news_in_cache[nw].partner_id != undefined){
                            if(order_news_in_cache[nw].amount_total < 0 && order_news_in_cache[nw].partner_id[0]==cliente_id && order_news_in_cache[nw].amount_total == payment_i.amount)
                            {
                                 var js = {
                                    'id': payment_i.id,
                                    'pos_reference': order_news_in_cache[nw].pos_reference ,
                                    'date_order': order_news_in_cache[nw].date_order,
                                    'amount': payment_i.amount,
                                 }
                                 payments.push(js);
                            }
                        }
                   }
                }

                return payments;
            }


            //Todo: Parte importante para heredar el cambio de cliente al momento del pago.
             /**
             * @override
             */
            async selectClient() {
				//let res = await super.selectClient();
				const currentClient = this.currentOrder.get_client();
				if(currentClient){
				    if(this.paguitos.length > 0){
				        if(this.paguitos[0].partner_id.id != currentClient.id){
				            this.updateSelectClient();
				            this.payments_refund = [];
				            }
				    }else{
				         this.updateSelectClient();
				         this.payments_refund = [];
				    }
				}else{
				    this.paguitos = [];
				    this.payments_refund = [];
				}
				super.selectClient()
			}

            updateSelectClient(){
                this.paguitos = this.get_payments();
            }

             /**
             * @override
             */
            addNewPaymentLine({ detail: paymentMethod }) {
                if (this.currentOrder.is_return_order && paymentMethod.is_refund) {
                    swal('Estimado usuario','No puede usar un método de pago de devoluciones para un retorno. Seleccione otro método de pago.', 'warning');
                    return 0;
                }

                if (this.currentOrder.is_return_order == false && paymentMethod.is_refund && this.paguitos.length == 0 ) {
                    swal('Estimado usuario','No puede usar un método de pago de devoluciones si no tiene créditos pendientes. Seleccione otro método de pago.', 'warning');
                    return 0;
                }

//                if (this.currentOrder.return_order_ref != false && paymentMethod.is_refund==false){
//                    swal('Estimado usuario','El método de pago a aplicar a una órden en negativo o nota de crédito debe ser de devolución.', 'warning');
//                    return 0;
//                }
                const res = super.addNewPaymentLine(...arguments);
                if (this.currentOrder.return_order_ref == false ){
                    if(res && paymentMethod.is_refund==true){
                        this.selectedPaymentLine.set_amount(0);
                    }
                }
            }

            /**
             * @override
             */
            deletePaymentLine(event) {
                const { cid } = event.detail;
                const line = this.paymentLines.find((line) => line.cid === cid);
                //let res =  super.deletePaymentLine(event);
                if(line.payment_method.is_refund == true){
                    this.trigger('unselect-credit-all')
                }
                super.deletePaymentLine(event);
            }

             /**
             * @override
             */
			async _finalizeValidation() {
				if (this.currentOrder.is_paid_with_cash() && this.env.pos.config.iface_cashdrawer) {
					this.env.pos.proxy.printer.open_cashbox();
				}

				this.currentOrder.initialize_validation_date();
				this.currentOrder.finalized = true;

				let syncedOrderBackendIds = [];
				let credit_note = this.env.pos.config.credit_note;
				let total =  this.currentOrder.get_total_with_tax();
				try {
					if (this.currentOrder.is_to_invoice()) {
						if((total >= 0) || (total < 0 && credit_note != "not_create_note")){
							syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
								this.currentOrder
							);
						}
						else {
							syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
						}
						
					} else {
						syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
					}
				} catch (error) {
					if (error instanceof Error) {
						throw error;
					} else {
						await this._handlePushOrderError(error);
					}
				}
				if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
					const result = await this._postPushOrderResolve(
						this.currentOrder,
						syncedOrderBackendIds
					);
					if (!result) {
						await this.showPopup('ErrorPopup', {
							title: 'Error: no internet connection.',
							body: error,
						});
					}
				}

				this.showScreen(this.nextScreen);

				// If we succeeded in syncing the current order, and
				// there are still other orders that are left unsynced,
				// we ask the user if he is willing to wait and sync them.
				if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
					const { confirmed } = await this.showPopup('ConfirmPopup', {
						title: this.env._t('Remaining unsynced orders'),
						body: this.env._t(
							'There are unsynced orders. Do you want to sync these orders?'
						),
					});
					if (confirmed) {
						// NOTE: Not yet sure if this should be awaited or not.
						// If awaited, some operations like changing screen
						// might not work.
						this.env.pos.push_orders();
					}
				}
			}
		}

	Registries.Component.extend(PaymentScreen, BiPaymentScreen);

	return PaymentScreen;

});