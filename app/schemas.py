from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# importación de enums
from app.models import (
    EstadoPago,
    TipoDocumento,
    TipoMovimientoCaja,
    TipoOperacion,
    TipoRol,
)



# CATEGORIA SCHEMAS

class CategoriaBase(BaseModel):
    nombre: str
    id_padre: Optional[int] = None

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id_categoria: int
    # Lista opcional para la recursividad. 
    # Para evitar recursión infinita por defecto, lo dejamos opcional y vacio si no se carga.
    hijas: List["CategoriaResponse"] = []

    model_config = ConfigDict(from_attributes=True)



# SUCURSAL SCHEMAS

class SucursalBase(BaseModel):
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    es_principal: bool = False

class SucursalCreate(SucursalBase):
    pass

class SucursalResponse(SucursalBase):
    id_sucursal: int
    model_config = ConfigDict(from_attributes=True)



# USUARIO SCHEMAS

class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr
    id_sucursal: int
    rol: TipoRol = TipoRol.VENDEDOR
    estado: bool = True

class UsuarioCreate(UsuarioBase):
    password: str  # Solo al crear se pide el password

class UsuarioResponse(UsuarioBase):
    id_usuario: int
    # NO incluimos password en la respuesta
    model_config = ConfigDict(from_attributes=True)



# CLIENTE / PROVEEDOR SCHEMAS

class ClienteProveedorBase(BaseModel):
    rut: str
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    es_cliente: bool = True
    es_proveedor: bool = False

class ClienteProveedorCreate(ClienteProveedorBase):
    pass

class ClienteProveedorResponse(ClienteProveedorBase):
    id_tercero: int
    model_config = ConfigDict(from_attributes=True)



# PRODUCTO SCHEMAS

class ProductoBase(BaseModel):
    nombre: str
    codigo_barras: Optional[str] = None
    id_categoria: Optional[int] = None
    descripcion: Optional[str] = None
    costo_neto: Decimal = Field(default=0.00, decimal_places=2)
    precio_venta: Decimal = Field(default=0.00, decimal_places=2)
    unidad_medida: str = "UNID"

class ProductoCreate(ProductoBase):
    pass

class ProductoResponse(ProductoBase):
    id_producto: int
    model_config = ConfigDict(from_attributes=True)



# INVENTARIO SCHEMAS

class InventarioBase(BaseModel):
    cantidad: int = 0
    ubicacion_especifica: str
    stock_minimo: int = 5
    stock_maximo: int = 100

class InventarioCreate(InventarioBase):
    id_sucursal: int
    id_producto: int

class InventarioResponse(InventarioBase):
    id_inventario: int
    id_sucursal: int
    id_producto: int
    model_config = ConfigDict(from_attributes=True)


# DETALLE DOCUMENTO SCHEMAS

class DetalleDocumentoBase(BaseModel):
    cantidad: int
    precio_unitario: Decimal = Field(decimal_places=2)
    descuento: Decimal = Field(default=0.00, decimal_places=2)

class DetalleDocumentoCreate(DetalleDocumentoBase):
    id_producto: int

class DetalleDocumentoResponse(DetalleDocumentoBase):
    id_detalle: int
    id_producto: int
    model_config = ConfigDict(from_attributes=True)



# DOCUMENTO SCHEMAS

class DocumentoBase(BaseModel):
    tipo_operacion: TipoOperacion
    tipo_documento: TipoDocumento = TipoDocumento.BOLETA
    folio: Optional[str] = None
    estado_pago: EstadoPago = EstadoPago.PAGADO
    observaciones: Optional[str] = None

class DocumentoCreate(DocumentoBase):
    id_sucursal: int
    id_tercero: Optional[int] = None
    id_usuario: int
    # Los detalles al crear la venta
    detalles: List[DetalleDocumentoCreate]

class DocumentoResponse(DocumentoBase):
    id_documento: int
    id_sucursal: int
    id_tercero: Optional[int]
    id_usuario: int
    fecha_emision: datetime
    
    detalles: List[DetalleDocumentoResponse] = []

    model_config = ConfigDict(from_attributes=True)



# MOVIMIENTOS CAJA SCHEMAS

class MovimientoCajaBase(BaseModel):
    tipo: TipoMovimientoCaja
    monto: Decimal = Field(decimal_places=2)
    descripcion: Optional[str] = None

class MovimientoCajaCreate(MovimientoCajaBase):
    id_sucursal: int
    id_usuario: int
    id_documento_asociado: Optional[int] = None

class MovimientoCajaResponse(MovimientoCajaBase):
    id_movimiento: int
    id_sucursal: int
    id_usuario: int
    id_documento_asociado: Optional[int]
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)


# AUTH / TOKEN SCHEMAS

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
