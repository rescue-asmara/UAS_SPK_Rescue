from sqlalchemy import String, Integer,Column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()



class handphone(Base):
    __tablename__ = "tbl_handphone"
    nama_hp = Column(String,primary_key=True)
    ram = Column(String)
    internal = Column(String)
    layar = Column(String)
    baterai = Column(String)
    harga = Column(Integer)

    def __repr__(self):
        return f"handphone(type={self.nama_hp!r}, ram={self.ram!r}, internal={self.internal!r}, layar={self.layar!r}, baterai={self.baterai!r}, harga={self.harga!r}"