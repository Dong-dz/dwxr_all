from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import logging
from schemas.userSche import UserResponse
from services.userLogin import get_user_by_id
import json
import app
from models import login_pb2
from utils import http_utils
from store import store
import store
from google.protobuf.json_format import MessageToJson, Parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post('/apps/login')
def login_handler(login_req_body):
    # 解析登录请求参数
    login_req = Parse(login_req_body, login_pb2.LoginRequest(), True)
    code2session_req = {'appid': app.get_app_id(), 'secret': app.get_secret(), 'code': login_req.code}
    code2session_res = http_utils.http_post('https://developer.toutiao.com/api/apps/v2/jscode2session',
                                                  code2session_req)
    print(code2session_res)
    data = json.loads(code2session_res)

    login_res = login_pb2.LoginResponse()
    if data['err_no'] != 0:
        login_res.errCode = -1
        login_res.errMsg = 'error'
        return MessageToJson(login_res)
    else:
        login_res.errCode = 0
        login_res.errMsg = 'success'
        login_res.token = store.set_cache(
            "", data['data']['openid'], data['data']['unionid'], "", data['data']['session_key'])

        login_res.openid = data['data']['openid'][:3] + "****" + data['data']['openid'][7:]
        login_res.unionid = data['data']['unionid'][:3] + "****" + data['data']['unionid'][7:]
    return MessageToJson(login_res)

@router.get("/login", response_model=UserResponse)
def get_user_by_openid(openid: str, db: Session = Depends(get_db)):
    """
    根据用户openid获取用户信息
    """
    try:
        logger.info(f"根据openid获取用户信息: {openid}")
        db_user = get_user_by_id(db, openid)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="根据openid未获取到用户信息"
            )
    except Exception as e:
        logger.error(f"根据openid获取用户信息失败: {str(e)}")
        raise
    return db_user


'''
def hash_password(password: str) -> str:
    """
    简单的密码哈希函数
    注意：在生产环境中应使用更安全的哈希方法，如bcrypt
    """
    return hashlib.sha256(password.encode()).hexdigest()



@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    """
    创建用户
    """
    # 检查用户名是否已存在
    existing_user = get_user_by_id(db, user.openid)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已存在"
        )
    
    # 创建用户
    db_user = create_user(db, user)
    return db_user



@router.put("/{openid}", response_model=UserResponse)
def update_user_endpoint(openid: str, user: UserUpdate, db: Session = Depends(get_db)):
    """
    更新用户信息
    """
    db_user = get_user_by_id(db, openid)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 准备更新数据
    update_data = user.dict(exclude_unset=True)
    
    # 更新用户
    updated_user = update_user(db, openid, update_data)
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户更新失败"
        )
    return updated_user


@router.delete("/{openid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(openid: str, db: Session = Depends(get_db)):
    """
    删除用户
    """
    db_user = get_user_by_id(db, openid)
    logger.info(f"正在删除用户: {openid}")
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 删除用户
    delete_user(db, openid)
    return
'''
