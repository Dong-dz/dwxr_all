import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config import settings


class JWTManager:
    """JWT令牌管理器"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            data: 要编码的数据
            expires_delta: 过期时间
            
        Returns:
            JWT令牌字符串
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
            
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.jwt_secret_key, 
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌
        
        Args:
            token: JWT令牌字符串
            
        Returns:
            解码后的数据，验证失败返回None
        """
        try:
            payload = jwt.decode(
                token, 
                settings.jwt_secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except jwt.PyJWTError:
            return None
    
    @staticmethod
    def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
        """
        获取令牌载荷（不验证签名）
        
        Args:
            token: JWT令牌字符串
            
        Returns:
            令牌载荷数据
        """
        try:
            payload = jwt.decode(
                token, 
                options={"verify_signature": False}
            )
            return payload
        except jwt.PyJWTError:
            return None
    
    @staticmethod
    def is_token_expired(token: str) -> bool:
        """
        检查令牌是否过期
        
        Args:
            token: JWT令牌字符串
            
        Returns:
            是否过期
        """
        payload = JWTManager.get_token_payload(token)
        if not payload:
            return True
            
        exp = payload.get("exp")
        if not exp:
            return True
            
        return datetime.utcnow().timestamp() > exp
    
    @staticmethod
    def extract_openid_from_token(token: str) -> Optional[str]:
        """
        从令牌中提取openid
        
        Args:
            token: JWT令牌字符串
            
        Returns:
            openid或None
        """
        payload = JWTManager.verify_token(token)
        if payload:
            return payload.get("openid")
        return None


def create_session_token(openid: str, unionid: Optional[str] = None) -> str:
    """
    创建会话令牌
    
    Args:
        openid: 用户openid
        unionid: 用户unionid
        
    Returns:
        JWT令牌字符串
    """
    payload = {
        "openid": openid,
        "unionid": unionid,
        "type": "access_token"
    }
    return JWTManager.create_access_token(payload)


def mask_sensitive_data(data: str, show_chars: int = 3) -> str:
    """
    脱敏处理敏感数据
    
    Args:
        data: 要脱敏的数据
        show_chars: 显示的字符数
        
    Returns:
        脱敏后的数据
    """
    if not data or len(data) <= show_chars * 2:
        return data
    
    return data[:show_chars] + "***" + data[-show_chars:]