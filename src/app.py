from datetime import datetime
from typing import List
from typing import Optional

from bson import ObjectId
from fastapi import FastAPI
from fastapi import Response
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pymongo import MongoClient

# FastAPI


app = FastAPI(
    title="NFFA-DI",
    summary="FastAPI + MongoDB",
)

# DB connection

client = MongoClient("mongodb://127.0.0.1:27017")
nffa_db = client["nffa"]
user_collection = nffa_db["user"]


# Pydantic models


class MongoModel(BaseModel):

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        allow_population_by_field_name=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
            ObjectId: lambda oid: str(oid),
        },
    )


class UserBase(MongoModel):
    name: str
    surname: str


class UserCreate(UserBase):
    name: str
    surname: str


class UserRead(UserBase):
    id: ObjectId = Field(alias="_id")


class UserUpdate(MongoModel):
    name: Optional[str] = None
    surname: Optional[str] = None


# CRUD


@app.post("/user/")
async def create_user(new_user: UserCreate) -> UserRead:
    """
    curl --header "Content-Type: application/json" \
    --request POST \
    --data '{"name":"mario","surname":"rossi"}' \
    http://localhost:8000/user/
    """
    user = user_collection.insert_one(new_user.model_dump())
    return await read_user(user.inserted_id)


@app.get("/user/{user_id}")
async def read_user(user_id: str) -> UserRead:
    return user_collection.find_one({"_id": ObjectId(user_id)})


@app.get("/user/")
async def read_user_list() -> List[UserRead]:
    """
    curl --header "Content-Type: application/json" \
    --request GET \
    http://localhost:8000/user/
    """
    user_list = user_collection.find()
    return user_list


@app.patch("/user/{user_id}")
async def update_user(user_id: str, update: UserUpdate) -> UserRead:
    """
    curl --header "Content-Type: application/json" \
    --request PATCH \
    --data '{"surname":"bianchi"}' \
    http://localhost:8000/user/655ba3d28d4531f9e785989d
    """

    await user_collection.update_one(
        {"_id": user_id}, {"$set": update.dict(exclude_unset=True)}
    )
    return await read_user(user_id)


@app.delete("/user/{user_id}")
async def delete_user(user_id: str) -> Response:
    user_collection.delete_one({"_id": ObjectId(user_id)})
    return Response(status_code=204)


@app.delete("/user/")
async def delete_every_user() -> Response:
    """
    curl  --request DELETE http://localhost:8000/user/
    """
    user_collection.delete_many(filter={})
    return Response(status_code=204)
