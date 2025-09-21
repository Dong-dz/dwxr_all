from database import Base
from sqlalchemy import Column, String, Integer


class Biaodian(Base):
    __tablename__ = "biaodian"

    bd_id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="唯一ID")
    latitude = Column(String(100), nullable=False, comment="经度")
    longitude = Column(String(100), nullable=False, comment="纬度")
    beizhu = Column(String(100), comment="备注，标点备注信息等")
    weather = Column(String(100), comment="天气")
    zhuangbei = Column(String(100), comment="装备 用饵")
    type = Column(Integer, nullable=False, comment="台钓 1 ， 路亚 2 ， 其他 3")
    yuhuo = Column(String(100), comment="鱼获")
    tuijian = Column(String(100), nullable=False, comment="推荐指数")
    userid = Column(String(100), comment="用户ID")
    simi = Column(Integer, nullable=False, comment="标点是否公开 0 私密， 1 公开")
    city = Column(String(100), comment="城市")
    province = Column(String(100), comment="省份")
    openid = Column(String(100), comment="用户openid")
    biaoti = Column(String(100), comment="标题")


    # def __repr__(self):
    #     return f"<Biaodian(bd_id='{self.bd_id}', latitude='{self.latitude}', longitude='{self.longitude}')>"
