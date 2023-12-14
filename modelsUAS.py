from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class handphone(Base):
    __tablename__ = "tblhandphone"
    nama_hp = Column(String, primary_key=True)
    ram = Column(String(255))
    internal = Column(String(255))
    layar = Column(String(255))
    baterai = Column(String(255))
    harga = Column(String(255))

    def __init__(self, nama_hp, ram, internal, layar, baterai, harga):
        self.nama_hp = nama_hp
        self.ram = ram
        self.internal = internal
        self.layar = layar
        self.baterai = baterai
        self.harga = harga

    def calculate_score(self, dev_scale):
        score = 0
        score += self.nama_hp * dev_scale['nama_hp']
        score += self.ram * dev_scale['ram']
        score += self.internal * dev_scale['internal']
        score += self.layar * dev_scale['layar']
        score += self.baterai * dev_scale['baterai']
        score -= self.harga * dev_scale['harga']
        return score

    def __repr__(self):
        return f"handphone(nama_hp={self.nama_hp!r}, ram={self.ram!r}, internal={self.internal!r}, layar={self.layar!r}, baterai={self.baterai!r}, harga={self.harga!r})"