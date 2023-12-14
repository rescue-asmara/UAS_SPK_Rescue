import sys
from colorama import Fore, Style
from models import Base, handphone
from engine import engine
from tabulate import tabulate

from sqlalchemy import select
from sqlalchemy.orm import Session
from settings import DEV_SCALE

session = Session(engine)


def create_table():
    Base.metadata.create_all(engine)
    print(f'{Fore.GREEN}[Success]: {Style.RESET_ALL}Database has created!')


def review_data():
    query = select(handphone)
    for phone in session.scalars(query):
        print(phone)


class BaseMethod():

    def __init__(self):
        # 1-5
        self.raw_weight = {'ram': 4, 'internal': 4, 'layar': 3, 'baterai': 5, 'harga': 5}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(handphone.nama_hp, handphone.ram, handphone.internal, handphone.layar,
                       handphone.baterai, handphone.harga)
        result = session.execute(query).fetchall()
        return [{'nama_hp': phone.nama_hp, 'ram': phone.ram, 'internal': phone.internal, 'layar': phone.layar,
                 'baterai': phone.baterai, 'harga': phone.harga} for phone in result]

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
            internal_numeric_values = [int(value.split()[0]) for value in internal_spec.split() if value.split()[0].isdigit()]
            max_internal_value = max(internal_numeric_values) if internal_numeric_values else 1
            internal_values.append(max_internal_value)

            # Layar
            layar_spec = data['layar']
            layar_numeric_values = [int(value) for value in layar_spec.split() if value.isdigit()]
            max_layar_value = max(layar_numeric_values) if layar_numeric_values else 1
            layar_values.append(max_layar_value)

            # Baterai
            baterai_value = DEV_SCALE['baterai'].get(data['baterai'], 1)
            baterai_values.append(baterai_value)

            # Harga
            harga_cleaned = ''.join(
                char for char in data['harga'] if char.isdigit())
            harga_values.append(float(harga_cleaned)
                                if harga_cleaned else 0)  # Convert to float

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


class WeightedProduct(BaseMethod):
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
                row['harga']**self.weight['harga']
            }
            for row in normalized_data
        ]
        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)
        sorted_data = [
            {
                'nama_hp': product['nama_hp'],
                'ram': product['produk'] / self.weight['ram'],
                'internal': product['produk'] / self.weight['internal'],
                'layar': product['produk'] / self.weight['layar'],
                'baterai': product['produk'] / self.weight['baterai'],
                'harga': product['produk'] / self.weight['harga'],
                'score': product['produk']  # Nilai skor akhir
            }
            for product in sorted_produk
        ]
        return sorted_data


class SimpleAdditiveWeighting(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['nama_hp']:
                  round(row['ram'] * weight['ram'] +
                        row['internal'] * weight['internal'] +
                        row['layar'] * weight['layar'] +
                        row['baterai'] * weight['baterai'] +
                        row['harga'] * weight['harga'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result


def run_saw():
    saw = SimpleAdditiveWeighting()
    result = saw.calculate
    print(tabulate(result.items(), headers=['No', 'Score'], tablefmt='pretty'))


def run_wp():
    wp = WeightedProduct()
    result = wp.calculate
    headers = result[0].keys()
    rows = [
        {k: round(v, 4) if isinstance(v, float) else v for k, v in val.items()}
        for val in result
    ]
    print(tabulate(rows, headers="keys", tablefmt="grid"))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == 'create_table':
            create_table()
        elif arg == 'saw':
            run_saw()
        elif arg == 'wp':
            run_wp()
        else:
            print('command not found')
