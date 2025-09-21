from pydantic import BaseModel
from typing import Optional


class BiaoDianBase(BaseModel):
    latitude: str
    longitude: str
    beizhu: Optional[str] = None
    weather: Optional[str] = None
    zhuangbei: Optional[str] = None
    type: int
    yuhuo: Optional[str] = None
    tuijian: str
    userid: Optional[str] = None
    simi: int
    city: Optional[str] = None
    province: Optional[str] = None
    openid: str
    biaoti: Optional[str] = None


class BiaoDianResponse(BiaoDianBase):
    bd_id: int


class BiaoDianCreate(BiaoDianBase):
    pass


    class Config:
        orm_mode = True