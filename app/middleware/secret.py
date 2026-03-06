# coding: utf-8
from datetime import timedelta, datetime
from typing import Tuple, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError
from passlib.context import CryptContext

from app.config import Settings, get_settings
from app.utils.jwt import decode_token, encode_token


TOKEN_TYPE='Bearer'

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')
# if '--debug' in sys.argv:
# logger.info("start authticateion debug mode")
oauth2_scheme = APIKeyHeader(name='Authorization', auto_error=False)


def _get_current_user(
    token: str,
    settings: Settings,
    verify_exp_flag: bool = True
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': TOKEN_TYPE},
    )
    try:
        # if settings is None:
        #     settings = get_settings()
        # if token is None:
        #     token = oauth2_scheme
        scheme = f'{TOKEN_TYPE} '
        # if '--debug' in sys.argv:
        if token.startswith(scheme):
            token = token[len(scheme):]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated, set scheme Bearer",
                headers={"WWW-Authenticate": TOKEN_TYPE},
                )
        # ##################################################
        payload = decode_token(token, verify_exp=verify_exp_flag)
        database_name: Union[str, None] = payload.get('database_name')
        if  not database_name:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return {'database_name': database_name}


def get_current_user(
    token: str=Depends(oauth2_scheme),
    settings: Settings=Depends(get_settings),
):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    return _get_current_user(token, settings)


async def get_current_active_user(current_user: dict=Depends(get_current_user)):
    if current_user['user'].delete_flag:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Inactive user')
    return current_user


def get_current_user_not_verify_exp(
    token: str=Depends(oauth2_scheme),
    settings: Settings=Depends(get_settings),
):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    return _get_current_user(token, settings, verify_exp_flag=False)


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
        to_encode.update({'exp': expire})

    encoded_jwt = encode_token(to_encode)
    return encoded_jwt
