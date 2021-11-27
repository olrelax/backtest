from peewee import *
import pandas as pd
import numpy as np

db = SqliteDatabase("local_data/database.db")


class BaseModel(Model):
    class Meta:
        database = db


class SymbolModel(BaseModel):
    symbol = CharField()
    description = CharField()
    nation = CharField()
    data_source = CharField()


class EquityModel(BaseModel):
    symbol = ForeignKeyField(SymbolModel, backref='equity')
    date = DateTimeField()
    open = DecimalField(decimal_places=2)
    high = DecimalField(decimal_places=2)
    low = DecimalField(decimal_places=2)
    close = DecimalField(decimal_places=2)
    adjusted_close = DecimalField(decimal_places=4)
    volume = IntegerField()
    dividend_amount = DecimalField(decimal_places=2)
    split_coefficient = DecimalField()

    @staticmethod
    def set_dataframe_dtypes(dataframe):
        dataframe['open'] = pd.to_numeric(dataframe['open'])
        dataframe['high'] = pd.to_numeric(dataframe['high'])
        dataframe['low'] = pd.to_numeric(dataframe['low'])
        dataframe['close'] = pd.to_numeric(dataframe['close'])
        dataframe['adjusted_close'] = pd.to_numeric(dataframe['adjusted_close'])
        dataframe['volume'] = pd.to_numeric(dataframe['volume'])
        dataframe['dividend_amount'] = pd.to_numeric(dataframe['dividend_amount'])
        dataframe['split_coefficient'] = pd.to_numeric(dataframe['split_coefficient'])
        dataframe['date'] = pd.to_datetime(dataframe['date'])

        dataframe = dataframe.set_index('date')
        return dataframe

    @staticmethod
    def to_dataframe(cls, data):
        dataframe = pd.DataFrame(list(data.dicts()))
        dataframe = cls().set_dataframe_dtypes(dataframe)
        return dataframe

    @classmethod
    def from_dataframe_row(cls, row, symbol, date=None):
        # 'Date' is used as in index, therefore is not part of row.
        # We assume it's part of the row if it's not provided separately.
        result = cls()
        if date is None:
            result.date = row['date']
        else:
            result.date = date

        result.symbol = symbol
        result.open = row['1. open']
        result.high = row['2. high']
        result.low = row['3. low']
        result.close = row['4. close']
        result.adjusted_close = row['5. adjusted close']
        result.volume = row['6. volume']
        result.dividend_amount = row['7. dividend amount']
        result.split_coefficient = row['8. split coefficient']

        return result


class OptionModel(BaseModel):
    symbol = ForeignKeyField(SymbolModel, backref='options')
    data_date = DateTimeField()
    ask_price = DecimalField(decimal_places=2, null=True)
    ask_size = IntegerField(null=True)
    bid_price = DecimalField(decimal_places=2, null=True)
    bid_size = IntegerField(null=True)
    delta = DecimalField(decimal_places=4, null=True)
    expiration_date = DateTimeField()
    gamma = DecimalField(decimal_places=4, null=True)
    implied_volatility = DecimalField(decimal_places=4, null=True)
    last_price = DecimalField(decimal_places=2, null=True)
    open_interest = IntegerField(null=True)
    type = CharField()
    rho = IntegerField(null=True)
    strike_price = DecimalField(decimal_places=2)
    underlying_price = DecimalField(decimal_places=2, null=True)
    vega = DecimalField(decimal_places=4, null=True)
    volume = IntegerField(null=True)

    @classmethod
    def get_available_expiries(cls, symbol_model, data_date):
        return cls().select(OptionModel.expiration_date).distinct().where((OptionModel.symbol == symbol_model)
                                                                          & (OptionModel.data_date == data_date))

    @classmethod
    def get_expiry_price(cls, symbol_model,expiration_date):
        return cls().select(OptionModel.underlying_price).distinct().where((OptionModel.symbol == symbol_model)
                                                                           & (OptionModel.data_date == expiration_date))

    @classmethod
    def check_expiry_exists(cls, symbol_model, data_date, exp_date):
        return cls().select(OptionModel.expiration_date).distinct().where((OptionModel.symbol == symbol_model)
                            & (OptionModel.data_date == data_date) & (OptionModel.expiration_date == exp_date))

    @classmethod
    def get_historic_stock_prices(cls, symbol_model):
        return cls().select(OptionModel.data_date,OptionModel.underlying_price).distinct().where(OptionModel.symbol == symbol_model)

    @classmethod
    def get_historic_options_chain(cls, symbol_model, data_date, expiration_date):
        # return cls().select().where((OptionModel.symbol == symbol_model) & (OptionModel.data_date == data_date) & (OptionModel.expiration_date == expiration_date))
        return cls().select().where((OptionModel.symbol == symbol_model) & (OptionModel.data_date == data_date) &
                                    (OptionModel.expiration_date == expiration_date))

    @classmethod
    def from_tradier_dataframe_row(cls, row, symbol, strike_price, expiration_date, option_type, date=None):
        # 'Date' might be used as in index, therefore is not part of row.
        # We assume it's part of the row if it's not provided separately.
        result = cls()
        if date is None:
            result.data_date = row['date']
        else:
            result.data_date = date

        result.symbol = symbol
        result.strike_price = strike_price
        result.expiration_date = expiration_date
        result.type = option_type
        result.volume = row['volume']
        if not np.isnan(row['close']):
            result.last_price = row['close']
        else:
            result.last_price = row['open']

        return result
