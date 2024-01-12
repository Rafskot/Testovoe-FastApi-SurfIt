from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Enum, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from databases import Database
from enum import Enum as PyEnum

DATABASE_URL = "postgresql://tester:12345@localhost/mybase"

app = FastAPI()

# Подключение к базе данных
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Модели для SQLAlchemy
Base = declarative_base()


class UserRole(str, PyEnum):
    user = "user"
    admin = "admin"


class AdTypeEnum(str, PyEnum):
    sale = "sale"
    purchase = "purchase"
    service = "service"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, Enum(UserRole), name='userrole')
    ads = relationship("Ad", back_populates="owner")


class Ad(Base):
    __tablename__ = "ads"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    ad_type = Column(Enum(AdTypeEnum), name="ad_type")
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="ads")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    ad_id = Column(Integer, ForeignKey("ads.id"))
    user = relationship("User", back_populates="comments")
    ad = relationship("Ad", back_populates="comments")


# Создание таблиц в базе данных
def create_tables():
    Base.metadata.create_all(bind=engine)


# Зависимость для сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Обработка событий startup и shutdown
@app.on_event("startup")
async def startup_db():
    await database.connect()
    create_tables()


@app.on_event("shutdown")
async def shutdown_db():
    await database.disconnect()


# Регистрация пользователя
@app.post("/register")
async def register(username: str, email: str, role: UserRole = UserRole.user, db=Depends(get_db)):
    user = User(username=username, email=email, role=role)
    db.add(user)
    db.commit()
    return {"message": "User registered successfully"}


# Получение списка пользователей
@app.get("/users")
async def get_users(db=Depends(get_db)):
    users = db.query(User).all()
    return {"users": users}


# Создание объявления
@app.post("/create_ad")
async def create_ad(title: str, description: str, ad_type: str, current_user: User = Depends(get_db)):
    ad = Ad(title=title, description=description, ad_type=ad_type, owner=current_user)
    current_user.ads.append(ad)
    return {"message": "Ad created successfully"}


# Получение списка объявлений
@app.get("/ads")
async def get_ads(db=Depends(get_db)):
    ads = db.query(Ad).all()
    return {"ads": ads}


# Добавление комментария к объявлению
@app.post("/add_comment/{ad_id}")
async def add_comment(ad_id: int, text: str, current_user: User = Depends(get_db)):
    ad = current_user.query(Ad).filter(Ad.id == ad_id).first()
    if ad:
        comment = Comment(text=text, user=current_user, ad=ad)
        current_user.comments.append(comment)
        return {"message": "Comment added successfully"}
    raise HTTPException(status_code=404, detail="Ad not found")


# Получение комментариев к объявлению
@app.get("/get_comments/{ad_id}")
async def get_comments(ad_id: int, db=Depends(get_db)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if ad:
        comments = ad.comments
        return {"comments": comments}
    raise HTTPException(status_code=404, detail="Ad not found")


# Удаление комментария
@app.delete("/delete_comment/{comment_id}")
async def delete_comment(comment_id: int, current_user: User = Depends(get_db)):
    comment = current_user.query(Comment).filter(Comment.id == comment_id).first()
    if comment:
        current_user.delete(comment)
        current_user.commit()
        return {"message": "Comment deleted successfully"}
    raise HTTPException(status_code=404, detail="Comment not found")


# Удаление объявления
@app.delete("/delete_ad/{ad_id}")
async def delete_ad(ad_id: int, current_user: User = Depends(get_db)):
    ad = current_user.query(Ad).filter(Ad.id == ad_id).first()
    if ad:
        current_user.delete(ad)
        current_user.commit()
        return {"message": "Ad deleted successfully"}
    raise HTTPException(status_code=404, detail="Ad not found")


# Назначение пользователя администратором
@app.put("/assign_admin/{user_id}")
async def assign_admin(user_id: int, current_user: User = Depends(get_db)):
    user = current_user.query(User).filter(User.id == user_id).first()
    if user:
        user.role = UserRole.admin
        current_user.commit()
        return {"message": "User assigned as admin successfully"}
    raise HTTPException(status_code=404, detail="User not found")


# Вход в систему
@app.post("/login")
async def login(username: str, password: str, db=Depends(get_db)):
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if user:
        return {"message": "Login successful", "user_id": user.id}
    raise HTTPException(status_code=401, detail="Invalid credentials")


# Детальный просмотр объявления
@app.get("/ad/{ad_id}")
async def get_ad(ad_id: int, db=Depends(get_db)):
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    if ad:
        return {"ad": ad}
    raise HTTPException(status_code=404, detail="Ad not found")


# Удаление своего объявления
@app.delete("/delete_own_ad/{ad_id}")
async def delete_own_ad(ad_id: int, current_user: User = Depends(get_db)):
    ad = current_user.query(Ad).filter(Ad.id == ad_id, Ad.owner_id == current_user.id).first()
    if ad:
        current_user.delete(ad)
        current_user.commit()
        return {"message": "Ad deleted successfully"}
    raise HTTPException(status_code=404, detail="Ad not found")


# Удаление комментариев в любой группе объявлений (только для администратора)
@app.delete("/delete_comments/{ad_group_id}")
async def delete_comments(ad_group_id: int, current_user: User = Depends(get_db)):
    if current_user.role == UserRole.admin:
        ads = current_user.query(Ad).filter(Ad.ad_group_id == ad_group_id).all()
        for ad in ads:
            current_user.delete(ad.comments)
        current_user.commit()
        return {"message": "Comments deleted successfully"}
    raise HTTPException(status_code=403, detail="Permission denied")


# Просмотр списка комментариев в любой группе объявлений
@app.get("/get_comments_in_group/{ad_group_id}")
async def get_comments_in_group(ad_group_id: int, db=Depends(get_db)):
    ads = db.query(Ad).filter(Ad.ad_group_id == ad_group_id).all()
    if ads:
        comments = []
        for ad in ads:
            comments.extend(ad.comments)
        return {"comments": comments}
    raise HTTPException(status_code=404, detail="Ad group not found")
