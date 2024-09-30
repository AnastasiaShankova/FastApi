from pydantic import BaseModel, BeforeValidator, ImportString, PydanticUserError, schema
from pydantic_core import core_schema
from fastapi import FastAPI, Response, status, Depends, HTTPException, Body
from pydantic import BaseModel, TypeAdapter
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, DateTime, update, Date
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, mapped_column, Mapped, as_declarative, registry, Session, DeclarativeBase
import datetime
import glob
import os
import json
from typing import Union
from datetime import datetime


SQLALCHEMY_DATABASE_URL = "sqlite:///./application.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=True
)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@as_declarative()
class AbstractModel:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True),


class Product(AbstractModel):

    __tablename__ = 'product'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    price: Mapped[int] = mapped_column()
    available_quantity: Mapped[int] = mapped_column()
    # date: Mapped[datetime.datetime] = mapped_column()
    orderitem: Mapped[int] = relationship('OrderItem')

    class Config:
        orm_mode = True


class OrderItem(AbstractModel):

    __tablename__ = 'orderitem'

    __allow_unmapped__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('order.id'))
    product_id: Mapped[int] = mapped_column(ForeignKey('product.id'))
    ordered_quantity: Mapped[int] = mapped_column()


class Order(AbstractModel):

    __tablename__ = 'order'

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column()
    status: Mapped[str] = mapped_column()
    orderitem: Mapped[int] = relationship('OrderItem')


AbstractModel.metadata.create_all(engine)


@app.post('/products')
def create(name: str, description: str, price: int, available_quantity: int,  db: Session = Depends(get_db)):
    new_product = Product()
    new_product.name = name
    new_product.description = description
    new_product.price = price
    new_product.available_quantity = available_quantity
    # new_product.date = date
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@app.get('/products')
def get_all(db: Session = Depends(get_db)):
    all_products = db.query(Product).all()
    if all_products:
        return all_products
    return []


@app.get('/products/{id}')
def get_product(id: int, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    for product in products:
        if product.id == id:
            return product
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail=f'Товар с id {id} не найден')
    return status_code


@app.put('/products/{id}')
def update_product(id: int, name: str, description: str, price: int, available_quantity: int,  db: Session = Depends(get_db)):
    product = db.get(Product, id)
    if product == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Товар с id {id} не найден ')
        return status_code
    product = db.query(Product).filter(Product.id == id)
    product.update({'name': name, 'description': description, 'price': price,
                    'available_quantity': available_quantity, })
    db.commit()
    return "Изменения внесены успешно"


@app.delete('/products/{id}')
def delete_product(id: int, db: Session = Depends(get_db)):
    product = db.get(Product, id)
    if product:
        product = db.query(Product).filter(Product.id == id)
        product.delete()
        db.commit()
        raise HTTPException(status_code=status.HTTP_200_OK,
                            detail=f'Товар с id {id} успешно удален')
        return status_code
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Товар с id {id} не найден')
        return status_code


@app.post('/orders')
def create_order(product_id: int, ordered_quantity: int, status: Union[str, None] = "В процессе", db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product.available_quantity < ordered_quantity:
        return f'Доступное к заказу количество товара {product.name} = {product.available_quantity}.Вы указали {ordered_quantity}. Для создания заказа, пожалуйста, измените количество.'
    new_item = OrderItem()
    new_order = Order()
    new_order.status = status
    new_order.date = datetime.now()
    new_order.orderitem = new_item.id
    db.add(new_order)
    db.commit()
    new_item.product_id = product_id
    new_item.ordered_quantity = ordered_quantity
    new_item.order_id = new_order.id
    product.available_quantity -= ordered_quantity
    db.add(new_item)
    db.commit()
    return 'Заказ успешно создан'


@app.get('/orders')
def get_all_orders(db: Session = Depends(get_db)):
    all_orders = db.query(Order).all()
    if all_orders:
        return all_orders
    return []


@app.get('/orders/{id}')
def get_order(id: int, db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    for order in orders:
        if order.id == id:
            return order
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail=f'Заказ c id {id} не найден')
    return status_code


@app.patch('/orders/{id}')
def update_order(id: int, order_status: str, db: Session = Depends(get_db)):
    order = db.get(Order, id)
    if order == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Заказ с id {id} не найден ')
        return status_code
    order = db.query(Order).filter(Order.id == id)
    order.update({'status': order_status, })
    db.commit()
    return "Изменения внесены успешно"
