from fastapi import FastAPI, HTTPException
from mangum import Mangum

from .environments import Environments
from .environments import Environments2

from .repo.item_repository_mock import ItemRepositoryMock
from .repo.user_repository_mock import userRepositoryMock

from .errors.entity_errors import ParamNotValidated

from .enums.item_type_enum import ItemTypeEnum
from .enums.transaction_type_enum import TransactionTypeEnum

from .entities.item import Item
from .entities.user import User
from .entities.transaction import Transaction

from.repo.user_repository_interface import IUserRepository

from datetime import datetime
import time

app = FastAPI()

repo = Environments.get_item_repo()()
repo_user = Environments.get_user_repo()()
repo_tran = Environments.get_tran_repo()()

clientDefault = repo_user.get_user(1)

@app.get("/user/get_all_users")
def get_all_users():
    users = repo_user.get_all_users()
    return {
        "users": [user.to_dict() for user in users]
    }

@app.get("/user/{user_id}")
def get_user(user_id: int):
    validation_user_id = User.validate_user_id(user_id=user_id)
    if not validation_user_id[0]:
        raise HTTPException(status_code=400, detail=validation_user_id[1])
    
    user = repo_user.get_user(user_id)
    
    if user is None:
        raise HTTPException(status_code=404, detail="user Not found")
    
    return {
        "user_id": user_id,
        "user": user.to_dict()    
    }

@app.post("/deposit", status_code=201)
def create_deposit(request: dict):

    mascara = {
        "2": 0,
        "5": 0,
        "10": 0,
        "20": 0,
        "50": 0,
        "100": 0,
        "200": 0
    }

    value = 0.0

    for chave in request:
        if mascara.get(chave, None) is not None:
            value += float(chave) * float(request[chave])

    if value > clientDefault.current_balance*2:
        raise HTTPException(status_code=403, detail="Saldo suspeito")

    clientDefault.current_balance += value

    transacao = Transaction(types=TransactionTypeEnum.DEPOSIT, value=value, current_balance=clientDefault.current_balance, timestamp=time.time() )

    repo_tran.cria_transacao(transac=transacao, transac_id=int((transacao.current_balance * transacao.value) / 1000))

    return {
        "timeStamp":time.time(),
        "current_balance": clientDefault.current_balance
    }


@app.post("/withdraw", status_code=201)
def create_withdraw(request: dict):

    mascara = {
        "2": 0,
        "5": 0,
        "10": 0,
        "20": 0,
        "50": 0,
        "100": 0,
        "200": 0
    }

    value = 0.0

    for chave in request:
        if mascara.get(chave, None) is not None:
            value += float(chave) * float(request[chave])

    if value > clientDefault.current_balance:
        raise HTTPException(status_code=403, detail="Saldo insuficiente")

    clientDefault.current_balance -= value

    transacao = Transaction(types=TransactionTypeEnum.WITHWDRAW, value=value, current_balance=clientDefault.current_balance, timestamp=time.time())

    repo_tran.cria_transacao(transac=transacao, transac_id=int((transacao.current_balance * transacao.value) / 1000))

    return {
        "timeStamp":time.time(),
        "current_balance": clientDefault.current_balance
    }















@app.get("/items/get_all_items")
def get_all_items():
    items = repo.get_all_items()
    return {
        "items": [item.to_dict() for item in items]
    }


@app.get("/items/{item_id}")
def get_item(item_id: int):
    validation_item_id = Item.validate_item_id(item_id=item_id)
    if not validation_item_id[0]:
        raise HTTPException(status_code=400, detail=validation_item_id[1])
    
    item = repo.get_item(item_id)
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item Not found")
    
    return {
        "item_id": item_id,
        "item": item.to_dict()    
    }

@app.post("/items/create_item", status_code=201)
def create_item(request: dict):
    item_id = request.get("item_id")
    
    validation_item_id = Item.validate_item_id(item_id=item_id)
    if not validation_item_id[0]:
        raise HTTPException(status_code=400, detail=validation_item_id[1])
    
    item = repo.get_item(item_id)
    if item is not None:
        raise HTTPException(status_code=409, detail="Item already exists")
    
    name = request.get("name")
    price = request.get("price")
    item_type = request.get("item_type")
    if item_type is None:
        raise HTTPException(status_code=400, detail="Item type is required")
    if type(item_type) != str:
        raise HTTPException(status_code=400, detail="Item type must be a string")
    if item_type not in [possible_type.value for possible_type in ItemTypeEnum]:
        raise HTTPException(status_code=400, detail="Item type is not a valid one")
    
    admin_permission = request.get("admin_permission")
    
    try:
        item = Item(name=name, price=price, item_type=ItemTypeEnum[item_type], admin_permission=admin_permission)
    except ParamNotValidated as err:
        raise HTTPException(status_code=400, detail=err.message)
    
    item_response = repo.create_item(item, item_id)
    return {
        "item_id": item_id,
        "item": item_response.to_dict()    
    }
    
@app.delete("/items/delete_item")
def delete_item(request: dict):
    item_id = request.get("item_id")
    
    validation_item_id = Item.validate_item_id(item_id=item_id)
    if not validation_item_id[0]:
        raise HTTPException(status_code=400, detail=validation_item_id[1])
    
    item = repo.get_item(item_id)
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item Not found")
    
    if item.admin_permission == True:
        raise HTTPException(status_code=403, detail="Item Not found")
    
    item_deleted = repo.delete_item(item_id)
    
    return {
        "item_id": item_id,
        "item": item_deleted.to_dict()    
    }
    
@app.put("/items/update_item")
def update_item(request: dict):
    item_id = request.get("item_id")
    
    validation_item_id = Item.validate_item_id(item_id=item_id)
    if not validation_item_id[0]:
        raise HTTPException(status_code=400, detail=validation_item_id[1])
    
    item = repo.get_item(item_id)
    
    if item is None:
        raise HTTPException(status_code=404, detail="Item Not found")
    
    if item.admin_permission == True:
        raise HTTPException(status_code=403, detail="Item Not found")
    
    name = request.get("name")
    price = request.get("price")
    admin_permission = request.get("admin_permission")
    
    item_type_value = request.get("item_type")
    if item_type_value != None:
        if type(item_type_value) != str:
            raise HTTPException(status_code=400, detail="Item type must be a string")
        if item_type_value not in [possible_type.value for possible_type in ItemTypeEnum]:
            raise HTTPException(status_code=400, detail="Item type is not a valid one")
        item_type = ItemTypeEnum[item_type_value]
    else:
        item_type = None
        
    item_updated = repo.update_item(item_id, name, price, item_type, admin_permission)
    
    return {
        "item_id": item_id,
        "item": item_updated.to_dict()    
    }
    


handler = Mangum(app, lifespan="off")
