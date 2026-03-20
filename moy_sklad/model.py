import enum
from typing import Annotated, Any
from datetime import datetime, timezone, timedelta
from uuid import UUID

from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel
from pydantic_core import core_schema


MOSCOW_TZ = timezone(timedelta(hours=3))

class MoscowDateTime(datetime):
    """Минимальная версия с вашим форматом"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, *args) -> core_schema.CoreSchema:
        return core_schema.with_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.serialize,
                when_used='json',
            )
        )
    
    @classmethod
    def validate(cls, value, info) -> 'MoscowDateTime':
        if isinstance(value, str):
            # Парсим только ваш формат
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        elif isinstance(value, datetime):
            dt = value
        else:
            raise ValueError(f"Ожидается строка или datetime")
        
        # Устанавливаем московскую таймзону
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=MOSCOW_TZ)
        else:
            dt = dt.astimezone(MOSCOW_TZ)
        
        return cls(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second, dt.microsecond,
            tzinfo=dt.tzinfo
        )
    
    @classmethod
    def serialize(cls, dt: 'MoscowDateTime') -> str:
        # Сериализуем в нужный формат
        return dt.strftime('%Y-%m-%d %H:%M:%S')


class Kopeck:
    @classmethod
    def __get_pydantic_core_schema__(cls, *args) -> core_schema.CoreSchema:
        return core_schema.with_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.serialize,
                when_used='json',
            )
        )

    @classmethod
    def validate(cls, value, info) -> "Kopeck":
        try:
            if isinstance(value, Kopeck):
                return value
            return Kopeck.from_kopeck(value)
        except Exception:
            raise ValueError(f"Некорректное значение цены: {value}")

    @classmethod
    def serialize(cls, value: "Kopeck") -> int:
        """Сериализация: рубли -> копейки"""
        # Умножаем на 100 и округляем до целого
        return float(value.to_kopeck())
    
    @classmethod
    def from_rouble(cls, value: Decimal) -> "Kopeck":
        return Kopeck(value*100)
    
    @classmethod
    def from_kopeck(cls, value: Decimal) -> "Kopeck":
        return Kopeck(value)

    def __init__(self, value):
        self.value = Decimal(value)

    def to_kopeck(self) -> Decimal:
        return self.value
    
    def to_rouble(self) -> Decimal:
        return self.value / 100
    
    def __eq__(self, value: object) -> bool:
        if isinstance(value, Kopeck):
            return value.value == self.value
        raise ValueError("Kopeck.__eq__ expected Kopeck value")
    
class DiscountFactor(Decimal):
    """Процент скидки"""

    @classmethod
    def __get_pydantic_core_schema__(cls, *args) -> core_schema.CoreSchema:
        return core_schema.with_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls.serialize,
                when_used='json',
            )
        )

    @classmethod
    def validate(cls, value, info) -> Decimal:
        try:
            if info.mode == "json":
                return Decimal(value) / 100
            return Decimal(value)
        except Exception:
            raise ValueError(f"Некорректное значение процентов: {value}")

    @classmethod
    def serialize(cls, value: Decimal):
        # Умножаем на 100 и округляем до целого
        return float(value * 100)

class MoySkladMeta(BaseModel):
    href: str
    type: str
    mediaType: str


class MoySkladPriceType(BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str
    externalCode: str


class MoySkladSalePrice(BaseModel):
    value: Kopeck
    priceType: MoySkladPriceType


class MoySkladDownloadableMeta(BaseModel):
    href: str
    type: str
    mediaType: str
    downloadHref: str


class MoySkladMetaField(BaseModel):
    meta: MoySkladMeta


class MoySkladType(enum.StrEnum):
    Boolean = "boolean"
    String = "string"
    Text = "text"
    Date = "time"


class MoySkladAttributeInfo(BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str
    type: MoySkladType | str

class MoySkladAttribute(MoySkladAttributeInfo):
    value: object

class MoySkladAttributeCreate(BaseModel):
    meta: MoySkladMeta
    value: object


class MoySkladAttributesMixin(BaseModel):
    attributes: list[MoySkladAttribute] = []

    def find_attribute(self, attr_id: UUID):
        for attr in self.attributes:
            if attr.id == attr_id:
                return attr
        return None
    
    def get_attribute_value(self, attr_id: UUID):
        attr = self.find_attribute(attr_id)
        if not attr:
            return None
        return attr.value

class MoySkladArchivedMixin(BaseModel):
    archived: bool

class MoySkladProduct(MoySkladAttributesMixin, MoySkladArchivedMixin, BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str
    pathName: str = ""
    archived: bool
    description: str = ""
    variantsCount: int
    salePrices: list[MoySkladSalePrice] = []
    images: MoySkladMetaField = None
    updated: MoscowDateTime
    externalCode: str
    productFolder: MoySkladMetaField | None = None
    weight: float = 0

class MoySkladBundle(MoySkladAttributesMixin, MoySkladArchivedMixin, BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str
    pathName: str = ""
    salePrices: list[MoySkladSalePrice] = []
    description: str = ""
    images: MoySkladMetaField = None
    updated: MoscowDateTime
    externalCode: str
    productFolder: MoySkladMetaField | None = None

class MoySkladService(BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str

class MoySkladCharacteristicValue(BaseModel):
    id: UUID
    name: str
    value: str

class MoySkladVariant(MoySkladArchivedMixin, BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str
    description: str = ""
    salePrices: list[MoySkladSalePrice]
    images: MoySkladMetaField
    updated: MoscowDateTime
    externalCode: str
    product: MoySkladMetaField
    characteristics: list[MoySkladCharacteristicValue]


class MoySkladImage(BaseModel):
    meta: MoySkladDownloadableMeta
    title: str
    filename: str


class MoySkladCharacteristic(BaseModel):
    id: UUID
    name: str
    required: bool
    type: MoySkladType


class MoySkladProductFolder(BaseModel):
    id: UUID
    meta: MoySkladMeta
    archived: bool
    name: str
    description: str = ""
    pathName: str
    updated: MoscowDateTime
    productFolder: MoySkladMetaField | None = None
    externalCode: str

class MoySkaldCounterpartyBase(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    tags: list[str] = ""

class MoySkaldCounterpartyResponse(BaseModel):
    id: UUID
    meta: MoySkladMeta
    updated: MoscowDateTime
    archived: bool

class MoySkaldCounterparty(MoySkaldCounterpartyBase, MoySkaldCounterpartyResponse):
    pass

class MoySkaldCounterpartyCreate(MoySkaldCounterpartyBase):
    pass


class MoySkladTaskBase(BaseModel):
    assignee: MoySkladMetaField
    description: str
    state: MoySkladMetaField = None


class MoySkaldTaskResponse(BaseModel):
    id: UUID
    meta: MoySkladMeta


class MoySkaldTask(MoySkladTaskBase, MoySkaldTaskResponse):
    pass


class MoySkaldTaskCreate(MoySkladTaskBase):
    pass


class MoySkladEmployee(BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str
    shortFio: str

class MoySkladState(BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str

class MoySkladOrderPosition(BaseModel):
    assortment: MoySkladMetaField
    price: Kopeck
    quantity: float
    discount: DiscountFactor | None = None

class MoySkladCustomerOrderBase(BaseModel):
    agent: MoySkladMetaField
    organization: MoySkladMetaField
    state: MoySkladMetaField = None
    name: str = None
    shipmentAddress: str = ""
    deliveryPlannedMoment: MoscowDateTime = None
    attributes: list[MoySkladAttribute] = []
    project: MoySkladMetaField = None
    positions: MoySkladMetaField = None
    store: MoySkladMetaField = None

class MoySkladCustomerOrderResponse(BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str

class MoySkladCustomerOrder(MoySkladCustomerOrderBase, MoySkladCustomerOrderResponse):
    pass

class MoySkladCustomerOrderCreate(MoySkladCustomerOrderBase):
    attributes: list[MoySkladAttributeCreate] = []
    positions: list[MoySkladOrderPosition] = []

class MoySkladOrganization(BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str

class MoySkladProject(BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str

class MoySkladDiscount(BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str
    assortment: list[MoySkladMetaField] = None

class MoySkladStore(BaseModel):
    id: UUID
    meta: MoySkladMeta
    name: str