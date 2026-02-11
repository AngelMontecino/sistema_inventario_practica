import enum
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ENUMS


class TipoRol(str, enum.Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    VENDEDOR = "VENDEDOR"

class TipoOperacion(str, enum.Enum):
    VENTA = "VENTA"
    COMPRA = "COMPRA"

class TipoDocumento(str, enum.Enum):
    FACTURA = "FACTURA"
    BOLETA = "BOLETA"

class EstadoPago(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    PAGADO = "PAGADO"
    ANULADO = "ANULADO"

class TipoMovimientoCaja(str, enum.Enum):
    INGRESO = "INGRESO"
    EGRESO = "EGRESO"
    APERTURA = "APERTURA"
    CIERRE = "CIERRE"



# MODELS


class Categoria(Base):
    __tablename__ = "categorias"

    id_categoria: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(50), nullable=False)
    id_padre: Mapped[Optional[int]] = mapped_column(ForeignKey("categorias.id_categoria"), nullable=True)

    # Relación recursiva: Un padre tiene muchas hijas
    hijas: Mapped[List["Categoria"]] = relationship("Categoria", back_populates="padre")
    padre: Mapped[Optional["Categoria"]] = relationship("Categoria", back_populates="hijas", remote_side=[id_categoria])
    
    productos: Mapped[List["Producto"]] = relationship(back_populates="categoria")


class Sucursal(Base):
    __tablename__ = "sucursales"

    id_sucursal: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    direccion: Mapped[Optional[str]] = mapped_column(String(200))
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    es_principal: Mapped[bool] = mapped_column(Boolean, default=False)

    usuarios: Mapped[List["Usuario"]] = relationship(back_populates="sucursal")
    inventarios: Mapped[List["Inventario"]] = relationship(back_populates="sucursal")
    documentos: Mapped[List["Documento"]] = relationship(back_populates="sucursal")
    movimientos_caja: Mapped[List["MovimientosCaja"]] = relationship(back_populates="sucursal")


class ClienteProveedor(Base):
    __tablename__ = "cliente_proveedor"

    id_tercero: Mapped[int] = mapped_column(primary_key=True, index=True)
    rut: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    direccion: Mapped[Optional[str]] = mapped_column(String(200))
    telefono: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    es_cliente: Mapped[bool] = mapped_column(Boolean, default=True)
    es_proveedor: Mapped[bool] = mapped_column(Boolean, default=False)

    documentos: Mapped[List["Documento"]] = relationship(back_populates="tercero")


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_sucursal: Mapped[int] = mapped_column(ForeignKey("sucursales.id_sucursal"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[TipoRol] = mapped_column(Enum(TipoRol), default=TipoRol.VENDEDOR)
    estado: Mapped[bool] = mapped_column(Boolean, default=True)

    sucursal: Mapped["Sucursal"] = relationship(back_populates="usuarios")
    documentos: Mapped[List["Documento"]] = relationship(back_populates="usuario")
    movimientos_caja: Mapped[List["MovimientosCaja"]] = relationship(back_populates="usuario")


class Producto(Base):
    __tablename__ = "productos"

    id_producto: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_categoria: Mapped[Optional[int]] = mapped_column(ForeignKey("categorias.id_categoria"))
    codigo_barras: Mapped[Optional[str]] = mapped_column(String(50), unique=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    costo_neto: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)
    unidad_medida: Mapped[str] = mapped_column(String(20), default="UNID")

    categoria: Mapped[Optional["Categoria"]] = relationship(back_populates="productos")
    inventarios: Mapped[List["Inventario"]] = relationship(back_populates="producto")
    detalles_documento: Mapped[List["DetalleDocumento"]] = relationship(back_populates="producto")


class Inventario(Base):
    __tablename__ = "inventario"

    id_inventario: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_sucursal: Mapped[int] = mapped_column(ForeignKey("sucursales.id_sucursal"), nullable=False)
    id_producto: Mapped[int] = mapped_column(ForeignKey("productos.id_producto"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, default=0)
    ubicacion_especifica: Mapped[str] = mapped_column(String(50), nullable=False)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=5)
    stock_maximo: Mapped[int] = mapped_column(Integer, default=100)

    sucursal: Mapped["Sucursal"] = relationship(back_populates="inventarios")
    producto: Mapped["Producto"] = relationship(back_populates="inventarios")


class Documento(Base):
    __tablename__ = "documentos"

    id_documento: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_sucursal: Mapped[int] = mapped_column(ForeignKey("sucursales.id_sucursal"), nullable=False)
    id_tercero: Mapped[Optional[int]] = mapped_column(ForeignKey("cliente_proveedor.id_tercero"), nullable=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario"), nullable=False)
    tipo_operacion: Mapped[TipoOperacion] = mapped_column(Enum(TipoOperacion), nullable=False)
    tipo_documento: Mapped[TipoDocumento] = mapped_column(Enum(TipoDocumento), default=TipoDocumento.BOLETA)
    folio: Mapped[Optional[str]] = mapped_column(String(50))
    fecha_emision: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    estado_pago: Mapped[EstadoPago] = mapped_column(Enum(EstadoPago), default=EstadoPago.PAGADO)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)

    sucursal: Mapped["Sucursal"] = relationship(back_populates="documentos")
    tercero: Mapped[Optional["ClienteProveedor"]] = relationship(back_populates="documentos")
    usuario: Mapped["Usuario"] = relationship(back_populates="documentos")
    detalles: Mapped[List["DetalleDocumento"]] = relationship(back_populates="documento", cascade="all, delete-orphan")
    movimientos_caja: Mapped[List["MovimientosCaja"]] = relationship(back_populates="documento_asociado")

    @property
    def total(self):
        total_doc = 0
        for det in self.detalles:
            # precio * cantidad * (1 - descuento/100)
            # descuento es porcentaje 0-100
            factor_descuento = (100 - det.descuento) / 100
            total_doc += (det.precio_unitario * det.cantidad * factor_descuento)
        return total_doc


class DetalleDocumento(Base):
    __tablename__ = "detalle_documento"

    id_detalle: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_documento: Mapped[int] = mapped_column(ForeignKey("documentos.id_documento", ondelete="CASCADE"), nullable=False)
    id_producto: Mapped[int] = mapped_column(ForeignKey("productos.id_producto"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    descuento: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00)

    documento: Mapped["Documento"] = relationship(back_populates="detalles")
    producto: Mapped["Producto"] = relationship(back_populates="detalles_documento")


class MovimientosCaja(Base):
    __tablename__ = "movimientos_caja"

    id_movimiento: Mapped[int] = mapped_column(primary_key=True, index=True)
    id_sucursal: Mapped[int] = mapped_column(ForeignKey("sucursales.id_sucursal"), nullable=False)
    id_documento_asociado: Mapped[Optional[int]] = mapped_column(ForeignKey("documentos.id_documento"), nullable=True)
    tipo: Mapped[TipoMovimientoCaja] = mapped_column(Enum(TipoMovimientoCaja), nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(200))
    fecha: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario"), nullable=False)

    sucursal: Mapped["Sucursal"] = relationship(back_populates="movimientos_caja")
    documento_asociado: Mapped[Optional["Documento"]] = relationship(back_populates="movimientos_caja")
    usuario: Mapped["Usuario"] = relationship(back_populates="movimientos_caja")
