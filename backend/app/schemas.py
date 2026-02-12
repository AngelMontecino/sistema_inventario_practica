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

class SucursalUpdate(BaseModel):
    nombre: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    es_principal: Optional[bool] = None

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

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    id_sucursal: Optional[int] = None
    rol: Optional[TipoRol] = None
    estado: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    id_usuario: int
    sucursal: Optional["SucursalResponse"] = None
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

class ClienteProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    rut: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    es_cliente: Optional[bool] = None
    es_proveedor: Optional[bool] = None

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

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    codigo_barras: Optional[str] = None
    id_categoria: Optional[int] = None
    descripcion: Optional[str] = None
    costo_neto: Optional[Decimal] = Field(default=None, decimal_places=2)
    precio_venta: Optional[Decimal] = Field(default=None, decimal_places=2)
    unidad_medida: Optional[str] = None

class ActualizacionPrecioProducto(BaseModel):
    id_producto: int
    costo_neto: Optional[Decimal] = None
    precio_venta: Optional[Decimal] = None

class InventarioBase(BaseModel):
    cantidad: int = 0
    ubicacion_especifica: str
    stock_minimo: int = 5
    stock_maximo: int = 100

class InventarioSimpleResponse(InventarioBase):
    id_inventario: int
    id_sucursal: int
    id_producto: int
    model_config = ConfigDict(from_attributes=True)




class ProductoResponse(ProductoBase):
    id_producto: int
    categoria: Optional[CategoriaBase] = None
    inventarios: List["InventarioSimpleResponse"] = []
    model_config = ConfigDict(from_attributes=True)

class ProductoPaginatedResponse(BaseModel):
    total: int
    items: List[ProductoResponse]



# INVENTARIO SCHEMAS



class InventarioCreate(InventarioBase):
    id_sucursal: int
    id_producto: int

class InventarioUpdate(BaseModel):
    cantidad: Optional[int] = None
    ubicacion_especifica: Optional[str] = None
    stock_minimo: Optional[int] = None
    stock_maximo: Optional[int] = None

class InventarioResponse(InventarioBase):
    id_inventario: int
    id_sucursal: int
    id_producto: int
    producto: Optional[ProductoResponse] = None # Para mostrar info del producto en listados
    model_config = ConfigDict(from_attributes=True)

class InventarioAgrupadoResponse(BaseModel):
    id_producto: int
    nombre: str
    codigo_barras: Optional[str] = None
    total_cantidad: int


# DETALLE DOCUMENTO SCHEMAS

class DetalleDocumentoBase(BaseModel):
    cantidad: int
    precio_unitario: Optional[Decimal] = Field(default=None, decimal_places=2)
    descuento: Decimal = Field(default=0.00, decimal_places=2)

class DetalleDocumentoCreate(DetalleDocumentoBase):
    id_producto: int
    ubicacion_especifica: Optional[str] = None

class DetalleDocumentoResponse(DetalleDocumentoBase):
    id_detalle: int
    id_producto: int
    ubicacion_especifica: Optional[str] = None
    producto: Optional["ProductoResponse"] = None 
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
    total: Optional[Decimal] = None
    usuario: Optional["UsuarioResponse"] = None
    tercero: Optional["ClienteProveedorResponse"] = None

    model_config = ConfigDict(from_attributes=True)



# MOVIMIENTOS CAJA SCHEMAS

class MovimientoCajaBase(BaseModel):
    tipo: TipoMovimientoCaja
    monto: Optional[Decimal] = Field(default=None, decimal_places=2)
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
    usuario: Optional["UsuarioResponse"] = None

    model_config = ConfigDict(from_attributes=True)

class EstadoCajaInfo(BaseModel):
    id_movimiento: int
    fecha: datetime
    usuario_nombre: str
    usuario_id: int

class EstadoCajaResponse(BaseModel):
    estado: str # ABIERTA, CERRADA, PENDIENTE_CIERRE
    mensaje: str
    info: Optional[EstadoCajaInfo] = None

class CajaResumenResponse(BaseModel):
    saldo_inicial: Decimal
    ingresos_ventas: Decimal
    egresos_compras: Decimal
    ingresos_extra: Decimal
    egresos_extra: Decimal
    saldo_teorico: Decimal
    estado: str = "CERRADA"

class CierreCajaRequest(BaseModel):
    monto_real: Decimal = Field(decimal_places=2)
    id_apertura: Optional[int] = None

class ReporteProductoItem(BaseModel):
    id_producto: int
    nombre: str
    codigo_barras: Optional[str] = None
    cantidad_ventas: int
    total_ventas: Decimal
    cantidad_compras: int
    total_compras: Decimal

class ReporteCajaItem(CajaResumenResponse):
    id_apertura: int
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime] = None
    usuario_apertura: str
    usuario_cierre: Optional[str] = None
    sucursal: str
    monto_real: Optional[Decimal] = None
    diferencia: Optional[Decimal] = None

class CajaSesionDetalleResponse(ReporteCajaItem):
    movimientos: List[MovimientoCajaResponse] = []
    documentos_summary: List[DocumentoResponse] = []
    productos: List[ReporteProductoItem] = [] 

class CierreCajaResponse(CajaResumenResponse):
    monto_real: Decimal
    diferencia: Decimal
    productos: List[ReporteProductoItem] = [] 


# AUTH / TOKEN SCHEMAS

class Token(BaseModel):
    access_token: str
    token_type: str
    rol: str
    nombre: str
    id_sucursal: int
    id_usuario: int
    nombre_sucursal: Optional[str] = None

class TokenData(BaseModel):
    email: Optional[str] = None
