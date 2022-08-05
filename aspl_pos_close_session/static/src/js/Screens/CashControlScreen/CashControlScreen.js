odoo.define('aspl_pos_close_session.CashControlScreen', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const { debounce } = owl.utils;
    const { useState } = owl.hooks;
    var rpc = require('web.rpc');

    class CashControlScreen extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('remove-line', () => this.removeLine(event));
            useListener('main_total',this._updateMainTotal);
            this._id = 0;
            this.state = useState({inputLines:this._generate_lines_cash(),total:0,
                                   showStaticLines : false});
//            this.state = useState({ inputLines:[],total:0,showStaticLines : true,
//                                    staticData : this._dummyData()});

        }

        _generate_lines_cash(){

            let data = [
                {coin_value:5,  number_of_coins:0,  line_total :0,  _id: 1,},
                {coin_value:10,  number_of_coins:0,  line_total :0,  _id: 2,},
                {coin_value:25,  number_of_coins:0,  line_total :0,  _id: 3,},
                {coin_value:50,  number_of_coins:0,  line_total :0,  _id: 4,},
                {coin_value:100,  number_of_coins:0,  line_total :0,  _id: 5,},
                {coin_value:500,  number_of_coins:0,  line_total :0,  _id: 6,},
                {coin_value:1000,  number_of_coins:0,  line_total :0,  _id: 7,},
                {coin_value:2000,  number_of_coins:0,  line_total :0,  _id: 8,},
                {coin_value:5000,  number_of_coins:0,  line_total :0,  _id: 9,},
                {coin_value:10000,  number_of_coins:0,  line_total :0,  _id: 10,},
                {coin_value:20000,  number_of_coins:0,  line_total :0,  _id: 11,},
            ]
             return data;

        }

        _updateMainTotal(){
            let total = 0;
            _.each(this.state.inputLines, function(line){
                total += line.line_total;
            });
            this.state.total = total;
        }

        clickSkip() {
            this.showScreen('ProductScreen');
        }

        _nextId() {
            return {
                coin_value:0,
                number_of_coins:0,
                line_total :0,
                _id: this._id++,
            };
        }

        _dummyData(){
            return [
                {coin_value:10,number_of_coins:5,},
                {coin_value:20, number_of_coins:4},
                {coin_value:50, number_of_coins:2},
                {coin_value:100, number_of_coins:2},
                {coin_value:200, number_of_coins:3},
            ];
        }

        createNewInputLine() {
            this.state.inputLines.push(this._nextId());
            this.state.showStaticLines = false;
        }

        removeLine(event) {
            this.state.inputLines = this.state.inputLines.filter((item) => item._id !== event.detail._id);
            this._updateMainTotal();
            if((this.state.inputLines).length == 0){
                this.state.showStaticLines = true;
            }
        }

        validateOpenBalance(){
            var self = this;
            var total_open_balance = self.state.total;
            if(!this.env.pos.config.allow_with_zero_amount && total_open_balance < 0){
                alert('El monto de apertura debe ser mayor o igual 0');
                return;
            }
            if (this.env.pos.bank_statement != undefined){
                this.env.pos.bank_statement.balance_start = total_open_balance;
            }

            this.env.pos.pos_session.state = 'opened';
            this.rpc({
                model: 'pos.session',
                method: 'set_cashbox_opening',
                args: [this.env.pos.pos_session.id, total_open_balance],
            });
            this.showScreen('ProductScreen');
        }
    }

    CashControlScreen.template = 'CashControlScreen';

    Registries.Component.add(CashControlScreen);

    return CashControlScreen;
});

