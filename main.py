from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api
from models import handphone as handphoneModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session
from tabulate import tabulate

session = Session(engine)

app = Flask(__name__)
api = Api(app)


class BaseMethod():

    def __init__(self):
        self.raw_weight = {'ram': 4, 'internal': 4, 'layar': 3, 'baterai': 5, 'harga': 5}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(handphoneModel.nama_hp, handphoneModel.ram, handphoneModel.internal, 
                       handphoneModel.layar, handphoneModel.baterai, handphoneModel.harga)
        result = session.execute(query).fetchall()
        print(result)
        return [{'nama_hp': handphone.nama_hp, 'ram': handphone.ram, 'internal': handphone.internal,
                'layar': handphone.layar, 'baterai': handphone.baterai, 'harga': handphone.harga} for handphone in result]

    @property
    def normalized_data(self):
        # x/max [benefit]
        # min/x [cost]
        ram_values = []  # max
        internal_values = []  # max
        layar_values = []  # max
        baterai_values = []  # max
        harga_values = []  # min

        for data in self.data:
            # Ram
            ram_spec = data['ram']
            numeric_values = [int(value.split()[0]) for value in ram_spec.split(
                ',') if value.split()[0].isdigit()]
            max_ram_value = max(numeric_values) if numeric_values else 1
            ram_values.append(max_ram_value)

            # Internal
            internal_spec = data['internal']
            internal_numeric_values = [int(
                value.split()[0]) for value in internal_spec.split() if value.split()[0].isdigit()]
            max_internal_value = max(
                internal_numeric_values) if internal_numeric_values else 1
            internal_values.append(max_internal_value)

            # Layar
            layar_spec = data['layar']
            layar_numeric_values = [float(value.split()[0]) for value in layar_spec.split(
            ) if value.replace('.', '').isdigit()]
            max_layar_value = max(
                layar_numeric_values) if layar_numeric_values else 1
            layar_values.append(max_layar_value)

            # Baterai
            baterai_spec = data['baterai']
            baterai_numeric_values = [
                int(value) for value in baterai_spec.split() if value.isdigit()]
            max_baterai_value = max(
                baterai_numeric_values) if baterai_numeric_values else 1
            baterai_values.append(max_baterai_value)

            # Harga
            harga_cleaned = ''.join(char for char in str(data['harga']) if char.isdigit())
            harga_values.append(int(harga_cleaned) if harga_cleaned else 0)  # Convert to integer

        return [
            {'nama_hp': data['nama_hp'],
             'ram': ram_value / max(ram_values),
             'internal': internal_value / max(internal_values),
             'layar': layar_value / max(layar_values),
             'baterai': baterai_value / max(baterai_values),
             # To avoid division by zero
             'harga': min(harga_values) / max(harga_values) if max(harga_values) != 0 else 0
             }
            for data, ram_value, internal_value, layar_value, baterai_value, harga_value
            in zip(self.data, ram_values, internal_values, layar_values, baterai_values, harga_values)
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = [
            {
                'nama_hp': row['nama_hp'],
                'produk': row['ram']**self.weight['ram'] *
                row['internal']**self.weight['internal'] *
                row['layar']**self.weight['layar'] *
                row['baterai']**self.weight['baterai'] *
                row['harga']**self.weight['harga'],
                'type': row.get('type', '')
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'ID': product['nama_hp'],
                'score': round(product['produk'], 3)
            }
            for product in sorted_produk
        ]
        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return sorted(result, key=lambda x: x['score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'handphone': sorted(result, key=lambda x: x['score'], reverse=True)}, HTTPStatus.OK.value


class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = [
            {
                'ID': row['nama_hp'],
                'Score': round(row['ram'] * weight['ram'] +
                       row['internal'] * weight['internal'] +
                       row['layar'] * weight['layar'] +
                       row['baterai'] * weight['baterai'] +
                       row['harga'] * weight['harga'], 3)
            }
            for row in self.normalized_data
        ]
        sorted_result = sorted(result, key=lambda x: x['Score'], reverse=True)
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights


class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return sorted(result, key=lambda x: x['Score'], reverse=True), HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'handphone': sorted(result, key=lambda x: x['Score'], reverse=True)}, HTTPStatus.OK.value

class handphone(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None

        if page > page_count or page < 1:
            abort(404, description=f'Data Tidak Ditemukan.')
        return {
            'page': page,
            'page_size': page_size,
            'next': next_page,
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = session.query(handphoneModel).order_by(handphoneModel.nama_hp)
        result_set = query.all()
        data = [{'nama_hp': row.nama_hp, 'ram': row.ram, 'internal': row.internal,
                 'layar': row.layar, 'baterai': row.baterai, 'harga': row.harga}
                for row in result_set]
        return self.get_paginated_result('handphone/', data, request.args), 200


api.add_resource(handphone, '/handphone')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)