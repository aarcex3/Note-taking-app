from uuid import uuid4

from authx.dependencies import AuthXDependency
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security.http import HTTPBasic
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from starlette import status

from src.database.db import get_session
from src.models.user import UserModel as User
from src.schemas.users import RegisterUserSchema
from src.utils.auth import security
from src.utils.security_utils import check_password, hash_password

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register")
async def register_user(user_registration: RegisterUserSchema,
                        session: Session = Depends(get_session)):
    new_user = User(
        id=uuid4(),
        username=user_registration.username,
        email=user_registration.email,
        password=hash_password(user_registration.password.get_secret_value()),
    )
    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return Response(status_code=status.HTTP_201_CREATED,
                        content=new_user.model_dump_json())
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Username already exists") from ex


@router.post("/login")
async def login_user(response: Response,
                     user_login: OAuth2PasswordRequestForm = Depends(HTTPBasic()),
                     session: Session = Depends(get_session)):
    user = session.exec(
        select(User).where(User.username == user_login.username)).first()
    if user and check_password(user_login.password, user.password):
        token = security.create_access_token(uid=str(user.id))
        response.headers['Authorization'] = f"Bearer {token}"
        response.status_code = 200
        return response
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Bad credentials")


@router.post('/logout', dependencies=[Depends(security.access_token_required)])
def logout(deps: AuthXDependency = Depends(security.get_dependency)):
    deps.unset_access_cookies()
    return Response(status_code=status.HTTP_200_OK,
                    headers={},
                    content='Logout successful')
