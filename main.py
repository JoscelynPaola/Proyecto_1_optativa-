from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, Response
from pathlib import Path
from dotenv import load_dotenv
import os
import psycopg2
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from decimal import Decimal, ROUND_HALF_UP
import csv
import io
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


from correo import enviar_correo, app_url

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI(title="Sistema de Tienda")
# ==========================================
# ARCHIVOS ESTÁTICOS
# ==========================================

app.mount("/static", StaticFiles(directory="static"), name="static")


# ==========================================
# CREAR TOKEN JWT
# ==========================================
def crear_token(datos: dict):
    datos = datos.copy()
    datos["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(datos, SECRET_KEY, algorithm=ALGORITHM)
# ==========================================
# MODELO PARA UN PRODUCTO
# ==========================================

class Producto(BaseModel):
    codigo_barras: Optional[str] = Field(None, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: Optional[str] = None
    id_categoria: Optional[int] = Field(None, ge=1)
    id_proveedor: Optional[int] = Field(None, ge=1)
    precio_compra: float = Field(..., ge=0)
    precio_venta: float = Field(..., ge=0)
    stock_actual: int = Field(..., ge=0)
    stock_minimo: int = Field(..., ge=0)

# ==========================================
# VERIFICAR TOKEN JWT
# ==========================================
def obtener_usuario_actual(token: str = Depends(oauth2_scheme)):
    try:
        datos = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        id_usuario = datos.get("id_usuario")

        if id_usuario is None:
            raise HTTPException(
                status_code=401,
                detail="Token inválido"
            )

        return datos

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )


# ==========================================
# VERIFICAR ROL DEL USUARIO
# ==========================================
def verificar_rol(roles_permitidos: list[str]):
    def verificar(usuario_actual: dict = Depends(obtener_usuario_actual)):

        id_tipo_usuario = usuario_actual.get("id_tipo_usuario")

        if id_tipo_usuario not in [1, 2, 3, 4]:
            raise HTTPException(
                status_code=403,
                detail="Rol de usuario no válido"
            )

        if id_tipo_usuario not in roles_permitidos:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos para realizar esta acción"
            )

        return usuario_actual

    return verificar
# ==========================================
# MODELO PARA UN CATEGORIA
# ==========================================

class Categoria(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None


# ==========================================
# MODELO PARA UN PROVEEDOR
# ==========================================

class Proveedor(BaseModel):
    nombre_empresa: str = Field(..., min_length=1, max_length=150)
    contacto_nombre: Optional[str] = Field(None, max_length=150)
    telefono: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=150)
    direccion: Optional[str] = Field(None, max_length=250)
# ==========================================
# MODELO PARA UN USUARIO
# ==========================================
class Usuario(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    usuario: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = Field(None, max_length=150)
    password: str = Field(..., min_length=6, max_length=72)
    id_tipo_usuario: int = Field(..., ge=1)

# ==========================================
# MODELO PARA REGISTRO PÚBLICO DE USUARIO
# ==========================================
class UsuarioRegistro(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    usuario: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = Field(None, max_length=150)
    password: str = Field(..., min_length=6, max_length=72)

ROL_POR_DEFECTO = 4  # CLIENTE
# ==========================================
# MODELO PARA CAMBIAR CONTRASEÑA
# ==========================================
class CambioPassword(BaseModel):
    password_actual: str = Field(..., min_length=1, max_length=72)
    password_nueva: str = Field(..., min_length=6, max_length=72)

class SolicitudRecuperacion(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)


class RestablecerPassword(BaseModel):
    token: str
    password_nueva: str = Field(..., min_length=6, max_length=72)


# ==========================================
# MODELO PARA UN LOGIN
# ==========================================
class Login(BaseModel):
    usuario: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=72)

# ==========================================
# MODELO PARA MOVIMIENTO DE INVENTARIO
# ==========================================

class MovimientoInventario(BaseModel):
    id_producto: int = Field(..., ge=1)
    tipo_movimiento: str = Field(..., min_length=1, max_length=20)
    cantidad: int = Field(..., ge=1)
    motivo: Optional[str] = Field(None, max_length=255)

# ==========================================
# MODELOS PARA UNA VENTA (PEDIDO)
# ==========================================

class ItemVenta(BaseModel):
    id_producto: int = Field(..., ge=1)
    cantidad: int = Field(..., ge=1)


class VentaNueva(BaseModel):
    items: list[ItemVenta] = Field(..., min_length=1)

# ==========================================
# INICIO
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

@app.get("/")
def inicio():
    return FileResponse(BASE_DIR / "static" / "index.html")
# ==========================================
# PROBAR CONEXIÓN CON NEON
# ==========================================

@app.get("/probar-db")
def probar_db():
    try:
        conexion = psycopg2.connect(DATABASE_URL)

        cursor = conexion.cursor()
        cursor.execute("SELECT version();")

        version = cursor.fetchone()

        cursor.close()
        conexion.close()

        return {
            "mensaje": "Conexión con Neon exitosa",
            "postgresql": version[0]
        }

    except Exception as e:
        return {
            "mensaje": "Error al conectar con Neon",
            "error": str(e)
        }


# ==========================================
# CONSULTAR PRODUCTOS (LISTARLOS)
# GET /productos
# ==========================================

@app.get("/productos")
def obtener_productos(usuario_actual: dict = Depends(obtener_usuario_actual)):
    try:
        conexion = psycopg2.connect(DATABASE_URL)

        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_producto,
                codigo_barras,
                nombre,
                descripcion,
                id_categoria,
                id_proveedor,
                precio_compra,
                precio_venta,
                stock_actual,
                stock_minimo
            FROM productos
            ORDER BY id_producto;
        """)

        productos = cursor.fetchall()

        cursor.close()
        conexion.close()

        resultado = []

        for producto in productos:
            resultado.append({
                "id_producto": producto[0],
                "codigo_barras": producto[1],
                "nombre": producto[2],
                "descripcion": producto[3],
                "id_categoria": producto[4],
                "id_proveedor": producto[5],
                "precio_compra": float(producto[6]),
                "precio_venta": float(producto[7]),
                "stock_actual": producto[8],
                "stock_minimo": producto[9]
            })

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar productos: {str(e)}"
        )

# ==========================================
# CREAR PRODUCTO
# POST /productos
# ==========================================

@app.post("/productos")
def crear_producto(
    producto: Producto,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    # Validar precios
    if producto.precio_compra < 0:
        raise HTTPException(
            status_code=400,
            detail="El precio de compra no puede ser negativo"
        )

    if producto.precio_venta < 0:
        raise HTTPException(
            status_code=400,
            detail="El precio de venta no puede ser negativo"
        )

    # Validar stock
    if producto.stock_actual < 0:
        raise HTTPException(
            status_code=400,
            detail="El stock actual no puede ser negativo"
        )

    if producto.stock_minimo < 0:
        raise HTTPException(
            status_code=400,
            detail="El stock mínimo no puede ser negativo"
        )

    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO productos (
                codigo_barras,
                nombre,
                descripcion,
                id_categoria,
                id_proveedor,
                precio_compra,
                precio_venta,
                stock_actual,
                stock_minimo
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_producto;
        """, (
            producto.codigo_barras,
            producto.nombre,
            producto.descripcion,
            producto.id_categoria,
            producto.id_proveedor,
            producto.precio_compra,
            producto.precio_venta,
            producto.stock_actual,
            producto.stock_minimo
        ))

        id_producto = cursor.fetchone()[0]

        conexion.commit()

        cursor.close()
        conexion.close()

        return {
            "mensaje": "Producto creado correctamente",
            "id_producto": id_producto
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el producto: {str(e)}"
        )
# ==========================================
# OBTENER PRODUCTO POR NOMBRE
# GET /productos/buscar/{nombre}
# ==========================================
@app.get("/productos/buscar/{nombre}")
def buscar_productos(nombre: str):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_producto,
                codigo_barras,
                nombre,
                descripcion,
                id_categoria,
                id_proveedor,
                precio_compra,
                precio_venta,
                stock_actual,
                stock_minimo
            FROM productos
            WHERE nombre ILIKE %s
            ORDER BY id_producto;
        """, (f"%{nombre}%",))

        productos = cursor.fetchall()

        cursor.close()
        conexion.close()

        resultado = []

        for producto in productos:
            resultado.append({
                "id_producto": producto[0],
                "codigo_barras": producto[1],
                "nombre": producto[2],
                "descripcion": producto[3],
                "id_categoria": producto[4],
                "id_proveedor": producto[5],
                "precio_compra": float(producto[6]),
                "precio_venta": float(producto[7]),
                "stock_actual": producto[8],
                "stock_minimo": producto[9]
            })

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar productos: {str(e)}"
        )
# ==========================================
# OBTENER PRODUCTO POR ID
# GET /productos/{id_producto}
# ==========================================

@app.get("/productos/{id_producto}")
def obtener_producto(id_producto: int):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_producto,
                codigo_barras,
                nombre,
                descripcion,
                id_categoria,
                id_proveedor,
                precio_compra,
                precio_venta,
                stock_actual,
                stock_minimo
            FROM productos
            WHERE id_producto = %s;
        """, (id_producto,))

        producto = cursor.fetchone()

        cursor.close()
        conexion.close()

        if producto is None:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado"
            )

        return {
            "id_producto": producto[0],
            "codigo_barras": producto[1],
            "nombre": producto[2],
            "descripcion": producto[3],
            "id_categoria": producto[4],
            "id_proveedor": producto[5],
            "precio_compra": float(producto[6]),
            "precio_venta": float(producto[7]),
            "stock_actual": producto[8],
            "stock_minimo": producto[9]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar el producto: {str(e)}"
        )
 # ==========================================
# ACTUALIZAR PRODUCTO
# PUT /productos/{id_producto}
# ==========================================  
    
@app.put("/productos/{id_producto}")
def actualizar_producto(
    id_producto: int,
    producto: Producto,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE productos
            SET
                codigo_barras = %s,
                nombre = %s,
                descripcion = %s,
                id_categoria = %s,
                id_proveedor = %s,
                precio_compra = %s,
                precio_venta = %s,
                stock_actual = %s,
                stock_minimo = %s
            WHERE id_producto = %s
            RETURNING id_producto;
        """, (
            producto.codigo_barras,
            producto.nombre,
            producto.descripcion,
            producto.id_categoria,
            producto.id_proveedor,
            producto.precio_compra,
            producto.precio_venta,
            producto.stock_actual,
            producto.stock_minimo,
            id_producto
        ))

        resultado = cursor.fetchone()

        if resultado is None:
            cursor.close()
            conexion.close()

            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado"
            )

        conexion.commit()

        cursor.close()
        conexion.close()

        return {
            "mensaje": "Producto actualizado correctamente",
            "id_producto": resultado[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar el producto: {str(e)}"
        )

# ==========================================
# ELIMINAR PRODUCTO
# DELETE /productos/{id_producto}
# ==========================================
@app.delete("/productos/{id_producto}")
def eliminar_producto(
    id_producto: int,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    conexion = None
    cursor = None

    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            DELETE FROM productos
            WHERE id_producto = %s
            RETURNING id_producto;
        """, (id_producto,))

        resultado = cursor.fetchone()

        if resultado is None:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado"
            )

        conexion.commit()

        return {
            "mensaje": "Producto eliminado correctamente",
            "id_producto": resultado[0]
        }

    except HTTPException:
        if conexion:
            conexion.rollback()
        raise

    except (psycopg2.errors.ForeignKeyViolation,
            psycopg2.errors.RestrictViolation):
        if conexion:
            conexion.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: el producto tiene movimientos o ventas"
        )

    except Exception as e:
        if conexion:
            conexion.rollback()
        print("Error al eliminar producto:", e)
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar el producto"
        )

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
# ==========================================
# REGISTRAR MOVIMIENTO DE INVENTARIO
# POST /movimientos
# ==========================================

@app.post("/movimientos")
def registrar_movimiento(
    movimiento: MovimientoInventario,
    usuario_actual: dict = Depends(verificar_rol([1, 3]))
):
    conexion = None
    cursor = None

    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        # ==========================================
        # VALIDAR TIPO DE MOVIMIENTO
        # ==========================================

        tipos_validos = ["ENTRADA", "SALIDA", "AJUSTE"]

        if movimiento.tipo_movimiento not in tipos_validos:
            raise HTTPException(
                status_code=400,
                detail="Tipo de movimiento no válido"
            )

        # El rol INVENTARIO (3) solo puede hacer ENTRADA y AJUSTE
        if (usuario_actual.get("id_tipo_usuario") == 3
                and movimiento.tipo_movimiento == "SALIDA"):
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para registrar salidas"
            )

        # ==========================================
        # BUSCAR PRODUCTO
        # ==========================================

        cursor.execute("""
            SELECT
                id_producto,
                nombre,
                stock_actual
            FROM productos
            WHERE id_producto = %s
            FOR UPDATE;
        """, (movimiento.id_producto,))

        producto = cursor.fetchone()

        if producto is None:
            raise HTTPException(
                status_code=404,
                detail="Producto no encontrado"
            )

        stock_anterior = producto[2]

        # ==========================================
        # CALCULAR NUEVO STOCK
        # ==========================================

        if movimiento.tipo_movimiento == "ENTRADA":

            stock_nuevo = stock_anterior + movimiento.cantidad

        elif movimiento.tipo_movimiento == "SALIDA":

            if movimiento.cantidad > stock_anterior:
                raise HTTPException(
                    status_code=400,
                    detail="No hay suficiente stock para realizar la salida"
                )

            stock_nuevo = stock_anterior - movimiento.cantidad

        else:
            # AJUSTE establece el stock directamente
            stock_nuevo = movimiento.cantidad

        # ==========================================
        # ACTUALIZAR STOCK DEL PRODUCTO
        # ==========================================

        cursor.execute("""
            UPDATE productos
            SET stock_actual = %s
            WHERE id_producto = %s;
        """, (
            stock_nuevo,
            movimiento.id_producto
        ))

        # ==========================================
        # GUARDAR EN HISTORIAL
        # ==========================================

        cursor.execute("""
            INSERT INTO historial_inventario (
                id_producto,
                tipo_movimiento,
                cantidad,
                motivo
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id_movimiento;
        """, (
            movimiento.id_producto,
            movimiento.tipo_movimiento,
            movimiento.cantidad,
            movimiento.motivo
        ))

        id_movimiento = cursor.fetchone()[0]

        # ==========================================
        # CONFIRMAR TRANSACCIÓN
        # ==========================================

        conexion.commit()

        return {
            "mensaje": "Movimiento registrado correctamente",
            "id_movimiento": id_movimiento,
            "id_producto": movimiento.id_producto,
            "tipo_movimiento": movimiento.tipo_movimiento,
            "cantidad": movimiento.cantidad,
            "stock_anterior": stock_anterior,
            "stock_nuevo": stock_nuevo
        }

    except HTTPException:
        if conexion:
            conexion.rollback()
        raise

    except Exception as e:
        if conexion:
            conexion.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar movimiento: {str(e)}"
        )

    finally:
        if cursor:
            cursor.close()

        if conexion:
            conexion.close()
# ==========================================
# HISTORIAL DE MOVIMIENTOS
# ==========================================

@app.get("/movimientos")
def obtener_movimientos(
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    conexion = None
    cursor = None

    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                h.id_movimiento,
                h.id_producto,
                p.nombre,
                h.tipo_movimiento,
                h.cantidad,
                h.motivo,
                h.fecha_movimiento
            FROM historial_inventario h
            INNER JOIN productos p
                ON h.id_producto = p.id_producto
            ORDER BY h.fecha_movimiento DESC;
        """)

        movimientos = cursor.fetchall()

        resultado = []

        for movimiento in movimientos:
            resultado.append({
                "id_movimiento": movimiento[0],
                "id_producto": movimiento[1],
                "producto": movimiento[2],
                "tipo_movimiento": movimiento[3],
                "cantidad": movimiento[4],
                "motivo": movimiento[5],
                "fecha_movimiento": movimiento[6].strftime("%d/%m/%Y %H:%M:%S")
            })

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener el historial: {str(e)}"
        )

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
# ==========================================
# CONSULTAR CATEGORIAS (LISTARLAS)
# GET /categorias
# ==========================================
@app.get("/categorias")
def obtener_categorias():
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_categoria,
                nombre,
                descripcion
            FROM categorias
            ORDER BY id_categoria;
        """)

        categorias = cursor.fetchall()

        cursor.close()
        conexion.close()

        resultado = []

        for categoria in categorias:
            resultado.append({
                "id_categoria": categoria[0],
                "nombre": categoria[1],
                "descripcion": categoria[2]
            })

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar categorías: {str(e)}"
        )
# ==========================================
# CREAR CATEGORIA
# POST /categorias
# ==========================================
@app.post("/categorias")
def crear_categoria(
    categoria: Categoria,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO categorias (
                nombre,
                descripcion
            )
            VALUES (%s, %s)
            RETURNING id_categoria;
        """, (
            categoria.nombre,
            categoria.descripcion
        ))

        id_categoria = cursor.fetchone()[0]

        conexion.commit()

        cursor.close()
        conexion.close()

        return {
            "mensaje": "Categoría creada correctamente",
            "id_categoria": id_categoria
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear categoría: {str(e)}"
        )
# ==========================================
# BUSCAR CATEGORIAS POR NOMBRE
# GET /categorias/buscar/{nombre}
# ========================================

@app.get("/categorias/buscar/{nombre}")
def buscar_categorias(nombre: str):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_categoria,
                nombre,
                descripcion
            FROM categorias
            WHERE nombre ILIKE %s
            ORDER BY id_categoria;
        """, (f"%{nombre}%",))

        categorias = cursor.fetchall()

        cursor.close()
        conexion.close()

        resultado = []

        for categoria in categorias:
            resultado.append({
                "id_categoria": categoria[0],
                "nombre": categoria[1],
                "descripcion": categoria[2]
            })

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar categorías: {str(e)}"
        )
# ==========================================
# LISTAR TODOS LOS PROVEEDORES
# GET /proveedores
# ==========================================
@app.get("/proveedores")
def obtener_proveedores():
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_proveedor,
                nombre_empresa,
                contacto_nombre,
                telefono,
                email,
                direccion
            FROM proveedores
            ORDER BY id_proveedor;
        """)

        proveedores = cursor.fetchall()

        cursor.close()
        conexion.close()

        resultado = []

        for proveedor in proveedores:
            resultado.append({
                "id_proveedor": proveedor[0],
                "nombre_empresa": proveedor[1],
                "contacto_nombre": proveedor[2],
                "telefono": proveedor[3],
                "email": proveedor[4],
                "direccion": proveedor[5]
            })

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar proveedores: {str(e)}"
        )
# ==========================================
# BUSQUEDA POR ID CATEGORIA
# GET /categorias/{id_categoria}
# ========================================
@app.get("/categorias/{id_categoria}")
def obtener_categoria(id_categoria: int):

    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_categoria,
                nombre,
                descripcion
            FROM categorias
            WHERE id_categoria = %s;
        """, (id_categoria,))

        categoria = cursor.fetchone()

        cursor.close()
        conexion.close()

        if categoria is None:
            raise HTTPException(
                status_code=404,
                detail="Categoría no encontrada"
            )

        return {
            "id_categoria": categoria[0],
            "nombre": categoria[1],
            "descripcion": categoria[2]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# ==========================================
# ACTUALIZAR CATEGORIA
# PUT /categorias/{id_categoria}
# ========================================
@app.put("/categorias/{id_categoria}")
def actualizar_categoria(
    id_categoria: int,
    categoria: Categoria,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE categorias
            SET nombre = %s,
                descripcion = %s
            WHERE id_categoria = %s;
        """, (
            categoria.nombre,
            categoria.descripcion,
            id_categoria
        ))

        conexion.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Categoría no encontrada"
            )

        cursor.close()
        conexion.close()

        return {
            "mensaje": "Categoría actualizada correctamente",
            "id_categoria": id_categoria
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# ==========================================
# ELIMINAR CATEGORIA
# DELETE /categorias/{id_categoria}
# ========================================
@app.delete("/categorias/{id_categoria}")
def eliminar_categoria(
    id_categoria: int,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            DELETE FROM categorias
            WHERE id_categoria = %s;
        """, (id_categoria,))

        conexion.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Categoría no encontrada"
            )

        cursor.close()
        conexion.close()

        return {
            "mensaje": "Categoría eliminada correctamente",
            "id_categoria": id_categoria
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ==========================================
# CREAR PROVEEDOR
# POST /proveedores
# ==========================================
@app.post("/proveedores")
def crear_proveedor(
    proveedor: Proveedor,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO proveedores (
                nombre_empresa,
                contacto_nombre,
                telefono,
                email,
                direccion
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_proveedor;
        """, (
            proveedor.nombre_empresa,
            proveedor.contacto_nombre,
            proveedor.telefono,
            proveedor.email,
            proveedor.direccion
        ))

        id_proveedor = cursor.fetchone()[0]

        conexion.commit()

        cursor.close()
        conexion.close()

        return {
            "mensaje": "Proveedor creado correctamente",
            "id_proveedor": id_proveedor
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el proveedor: {str(e)}"
        )
# ==========================================
# BUSCAR PROVEEDORES POR NOMBRE
# GET /proveedores/buscar/{nombre}
# ========================================
@app.get("/proveedores/buscar/{nombre}")
def buscar_proveedores(nombre: str):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_proveedor,
                nombre_empresa,
                contacto_nombre,
                telefono,
                email,
                direccion
            FROM proveedores
            WHERE nombre_empresa ILIKE %s
            ORDER BY id_proveedor;
        """, (f"%{nombre}%",))

        proveedores = cursor.fetchall()

        cursor.close()
        conexion.close()

        resultado = []

        for proveedor in proveedores:
            resultado.append({
                "id_proveedor": proveedor[0],
                "nombre_empresa": proveedor[1],
                "contacto_nombre": proveedor[2],
                "telefono": proveedor[3],
                "email": proveedor[4],
                "direccion": proveedor[5]
            })

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar proveedores: {str(e)}"
        )
# ==========================================
# BUSCAR PROVEEDOR POR ID
# GET /proveedores/{id_proveedor}
# ==========================================
@app.get("/proveedores/{id_proveedor}")
def obtener_proveedor(id_proveedor: int):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_proveedor,
                nombre_empresa,
                contacto_nombre,
                telefono,
                email,
                direccion
            FROM proveedores
            WHERE id_proveedor = %s;
        """, (id_proveedor,))

        proveedor = cursor.fetchone()

        cursor.close()
        conexion.close()

        if proveedor is None:
            raise HTTPException(
                status_code=404,
                detail="Proveedor no encontrado"
            )

        return {
            "id_proveedor": proveedor[0],
            "nombre_empresa": proveedor[1],
            "contacto_nombre": proveedor[2],
            "telefono": proveedor[3],
            "email": proveedor[4],
            "direccion": proveedor[5]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar proveedor: {str(e)}"
        )
#=========================================
# ACTUALIZAR PROVEEDOR
# PUT /proveedores/{id_proveedor}
# ========================================
@app.put("/proveedores/{id_proveedor}")
def actualizar_proveedor(
    id_proveedor: int,
    proveedor: Proveedor,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE proveedores
            SET
                nombre_empresa = %s,
                contacto_nombre = %s,
                telefono = %s,
                email = %s,
                direccion = %s
            WHERE id_proveedor = %s
            RETURNING id_proveedor;
        """, (
            proveedor.nombre_empresa,
            proveedor.contacto_nombre,
            proveedor.telefono,
            proveedor.email,
            proveedor.direccion,
            id_proveedor
        ))

        resultado = cursor.fetchone()

        if resultado is None:
            cursor.close()
            conexion.close()

            raise HTTPException(
                status_code=404,
                detail="Proveedor no encontrado"
            )

        conexion.commit()

        cursor.close()
        conexion.close()

        return {
            "mensaje": "Proveedor actualizado correctamente",
            "id_proveedor": resultado[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar el proveedor: {str(e)}"
        )
# ==========================================
# ELIMINAR PROVEEDOR
# DELETE /proveedores/{id_proveedor}
# ========================================
@app.delete("/proveedores/{id_proveedor}")
def eliminar_proveedor(
    id_proveedor: int,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            DELETE FROM proveedores
            WHERE id_proveedor = %s
            RETURNING id_proveedor;
        """, (id_proveedor,))

        resultado = cursor.fetchone()

        if resultado is None:
            cursor.close()
            conexion.close()

            raise HTTPException(
                status_code=404,
                detail="Proveedor no encontrado"
            )

        conexion.commit()

        cursor.close()
        conexion.close()

        return {
            "mensaje": "Proveedor eliminado correctamente",
            "id_proveedor": resultado[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar el proveedor: {str(e)}"
        )

# ==========================================
# CREAR USUARIO
# POST /usuarios
# ==========================================

@app.post("/usuarios")
def crear_usuario(usuario: UsuarioRegistro):
    try:
        password_hash = pwd_context.hash(usuario.password)

        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO usuarios (
                nombre,
                usuario,
                email,
                password_hash,
                id_tipo_usuario,
                activo
            )
            VALUES (%s, %s, %s, %s, %s, TRUE)
            RETURNING id_usuario;
        """, (
            usuario.nombre,
            usuario.usuario,
            usuario.email,
            password_hash,
            ROL_POR_DEFECTO
        ))

        id_usuario = cursor.fetchone()[0]

        conexion.commit()
        cursor.close()
        conexion.close()

        return {
            "mensaje": "Usuario creado correctamente",
            "id_usuario": id_usuario
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear usuario: {str(e)}"
        )

# ==========================================
# LISTAR USUARIOS
# GET /usuarios
# ==========================================
@app.get("/usuarios")
def obtener_usuarios(
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT
                id_usuario,
                nombre,
                usuario,
                email,
                id_tipo_usuario,
                activo
            FROM usuarios
            ORDER BY id_usuario;
        """)

        usuarios = cursor.fetchall()

        cursor.close()
        conexion.close()

        resultado = []

        for usuario in usuarios:
            resultado.append({
                "id_usuario": usuario[0],
                "nombre": usuario[1],
                "usuario": usuario[2],
                "email": usuario[3],
                "id_tipo_usuario": usuario[4],
                "activo": usuario[5]
            })

        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar usuarios: {str(e)}"
        )
# ==========================================
# ACTUALIZAR USUARIO
# PUT /usuarios/{id_usuario}
# ==========================================
@app.put("/usuarios/{id_usuario}")
def actualizar_usuario(
    id_usuario: int,
    usuario: Usuario,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    try:
        password_hash = pwd_context.hash(usuario.password)

        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            UPDATE usuarios
            SET
                nombre = %s,
                usuario = %s,
                email = %s,
                password_hash = %s,
                id_tipo_usuario = %s
            WHERE id_usuario = %s
            RETURNING id_usuario;
        """, (
            usuario.nombre,
            usuario.usuario,
            usuario.email,
            password_hash,
            usuario.id_tipo_usuario,
            id_usuario
        ))

        resultado = cursor.fetchone()

        if resultado is None:
            conexion.rollback()
            cursor.close()
            conexion.close()

            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        conexion.commit()
        cursor.close()
        conexion.close()

        return {
            "mensaje": "Usuario actualizado correctamente",
            "id_usuario": resultado[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar usuario: {str(e)}"
        )
# ==========================================
# ELIMINAR USUARIO
# DELETE /usuarios/{id_usuario}
# ==========================================
@app.delete("/usuarios/{id_usuario}")
def eliminar_usuario(
    id_usuario: int,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            DELETE FROM usuarios
            WHERE id_usuario = %s
            RETURNING id_usuario;
        """, (id_usuario,))

        resultado = cursor.fetchone()

        if resultado is None:
            conexion.rollback()
            cursor.close()
            conexion.close()

            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        conexion.commit()

        cursor.close()
        conexion.close()

        return {
            "mensaje": "Usuario eliminado correctamente",
            "id_usuario": resultado[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar usuario: {str(e)}"
        )
# ==========================================
# CAMBIAR CONTRASEÑA (USUARIO CON SESIÓN)
# POST /cambiar-password
# ==========================================
@app.post("/cambiar-password")
def cambiar_password(
    datos: CambioPassword,
    usuario_actual: dict = Depends(obtener_usuario_actual)
):
    conexion = None
    cursor = None

    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT password_hash, activo
            FROM usuarios
            WHERE id_usuario = %s;
        """, (usuario_actual["id_usuario"],))

        fila = cursor.fetchone()

        if fila is None or not fila[1]:
            raise HTTPException(
                status_code=401,
                detail="Usuario no válido"
            )

        if not pwd_context.verify(datos.password_actual, fila[0]):
            raise HTTPException(
                status_code=400,
                detail="La contraseña actual es incorrecta"
            )

        if datos.password_actual == datos.password_nueva:
            raise HTTPException(
                status_code=400,
                detail="La nueva contraseña debe ser distinta a la actual"
            )

        cursor.execute("""
            UPDATE usuarios
            SET password_hash = %s
            WHERE id_usuario = %s;
        """, (
            pwd_context.hash(datos.password_nueva),
            usuario_actual["id_usuario"]
        ))

        conexion.commit()

        return {"mensaje": "Contraseña actualizada correctamente"}

    except HTTPException:
        if conexion:
            conexion.rollback()
        raise

    except Exception as e:
        if conexion:
            conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al cambiar la contraseña: {str(e)}"
        )

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()
# ==========================================
# CORREO: PRUEBA, RECUPERAR Y RESTABLECER CONTRASEÑA
# ==========================================

@app.post("/correo/probar")
def probar_correo(
    destino: str,
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    """Solo administrador: envía un correo de prueba y devuelve el error real si falla."""
    ok, error = enviar_correo(
        destino, "Prueba de correo - Sistema de Tienda",
        "Si lees esto, el envío de correos funciona."
    )
    if not ok:
        raise HTTPException(status_code=500, detail=error)
    return {"mensaje": f"Correo enviado a {destino}"}


@app.post("/recuperar-password")
def recuperar_password(datos: SolicitudRecuperacion, tareas: BackgroundTasks):
    respuesta = {
        "mensaje": "Si el correo está registrado, te enviamos un enlace para restablecer tu contraseña."
    }
    conexion = None
    cursor = None
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()
        cursor.execute("""
            SELECT id_usuario, nombre, password_hash
            FROM usuarios
            WHERE LOWER(email) = LOWER(%s) AND activo = TRUE;
        """, (datos.email.strip(),))
        filas = cursor.fetchall()

        for id_usuario, nombre, password_hash in filas:
            token = jwt.encode({
                "sub": str(id_usuario),
                "tipo": "reset",
                "h": password_hash[-12:],  # el enlace deja de servir al cambiar la contraseña
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
            }, SECRET_KEY, algorithm=ALGORITHM)
            enlace = f"{app_url()}/static/restablecer.html?token={token}"
            tareas.add_task(
                enviar_correo, datos.email.strip(),
                "Restablecer tu contraseña",
                f"Hola {nombre},\n\nPara crear una nueva contraseña abre este enlace "
                f"(válido 30 minutos):\n{enlace}\n\nSi no lo pediste, ignora este mensaje.",
                f'<p>Hola {nombre},</p><p><a href="{enlace}">Crear nueva contraseña</a> '
                f'(válido 30 minutos).</p><p>Si no lo pediste, ignora este mensaje.</p>'
            )
        return respuesta
    except Exception as e:
        print(f"[RECUPERAR] Error: {e}")
        return respuesta  # no revelar nada al exterior
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


@app.post("/restablecer-password")
def restablecer_password(datos: RestablecerPassword):
    try:
        payload = jwt.decode(datos.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("tipo") != "reset":
            raise JWTError()
    except JWTError:
        raise HTTPException(status_code=400, detail="El enlace es inválido o ya venció")

    conexion = None
    cursor = None
    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT password_hash FROM usuarios WHERE id_usuario = %s AND activo = TRUE;",
            (int(payload["sub"]),)
        )
        fila = cursor.fetchone()
        if fila is None or fila[0][-12:] != payload.get("h"):
            raise HTTPException(status_code=400, detail="El enlace es inválido o ya fue usado")

        cursor.execute(
            "UPDATE usuarios SET password_hash = %s WHERE id_usuario = %s;",
            (pwd_context.hash(datos.password_nueva), int(payload["sub"]))
        )
        conexion.commit()
        return {"mensaje": "Contraseña actualizada. Ya puedes iniciar sesión."}
    except HTTPException:
        raise
    except Exception as e:
        if conexion:
            conexion.rollback()
        raise HTTPException(status_code=500, detail=f"Error al restablecer: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


 # ==========================================
# CREAR VENTA (PEDIDO DEL CLIENTE)
# POST /ventas
# ==========================================

TASA_IVA = Decimal("0.16")


@app.post("/ventas")
def crear_venta(
    venta: VentaNueva,
    tareas: BackgroundTasks,
    usuario_actual: dict = Depends(verificar_rol([1, 2, 4]))
):
    conexion = None
    cursor = None

    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()

        # Si un producto viene repetido, se suman sus cantidades
        cantidades = {}

        for item in venta.items:
            cantidades[item.id_producto] = (
                cantidades.get(item.id_producto, 0) + item.cantidad
            )

        subtotal = Decimal("0.00")
        lineas = []

        # Se bloquean los productos siempre en el mismo orden
        for id_producto in sorted(cantidades):

            cantidad = cantidades[id_producto]

            cursor.execute("""
                SELECT nombre, precio_venta, stock_actual
                FROM productos
                WHERE id_producto = %s
                FOR UPDATE;
            """, (id_producto,))

            producto = cursor.fetchone()

            if producto is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"El producto {id_producto} no existe"
                )

            nombre, precio, stock = producto

            if cantidad > stock:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente de {nombre}: "
                           f"disponible {stock}, pediste {cantidad}"
                )

            importe = precio * cantidad
            subtotal += importe

            lineas.append(
                (id_producto, nombre, cantidad, precio, importe)
            )

        impuesto = (subtotal * TASA_IVA).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        total = subtotal + impuesto

        # Guardar la venta
        cursor.execute("""
            INSERT INTO ventas (
                id_usuario,
                subtotal,
                impuesto,
                total,
                estado
            )
            VALUES (%s, %s, %s, %s, 'COMPLETADA')
            RETURNING id_venta;
        """, (
            usuario_actual["id_usuario"],
            subtotal,
            impuesto,
            total
        ))

        id_venta = cursor.fetchone()[0]

        detalle = []

        for id_producto, nombre, cantidad, precio, importe in lineas:

            # Renglón del detalle
            cursor.execute("""
                INSERT INTO detalle_venta (
                    id_venta,
                    id_producto,
                    cantidad,
                    precio_unitario,
                    subtotal
                )
                VALUES (%s, %s, %s, %s, %s);
            """, (id_venta, id_producto, cantidad, precio, importe))

            # Descontar stock
            cursor.execute("""
                UPDATE productos
                SET stock_actual = stock_actual - %s
                WHERE id_producto = %s;
            """, (cantidad, id_producto))

            # Registrar la salida en el historial
            cursor.execute("""
                INSERT INTO historial_inventario (
                    id_producto,
                    tipo_movimiento,
                    cantidad,
                    motivo
                )
                VALUES (%s, 'SALIDA', %s, %s);
            """, (id_producto, cantidad, f"Venta #{id_venta}"))

            detalle.append({
                "id_producto": id_producto,
                "producto": nombre,
                "cantidad": cantidad,
                "precio_unitario": float(precio),
                "subtotal": float(importe)
            })

        # Todo salió bien: se confirma
        conexion.commit()

        # Correo de confirmación (no afecta la venta si falla)
        try:
            cursor.execute(
                "SELECT nombre, email FROM usuarios WHERE id_usuario = %s;",
                (usuario_actual["id_usuario"],)
            )
            cliente = cursor.fetchone()
            if cliente and cliente[1]:
                filas_txt = "\n".join(
                    f"- {d['producto']} x{d['cantidad']}  ${d['subtotal']:.2f}" for d in detalle
                )
                tareas.add_task(
                    enviar_correo, cliente[1], f"Confirmación de tu pedido #{id_venta}",
                    f"Hola {cliente[0]},\n\nRegistramos tu pedido #{id_venta}:\n{filas_txt}\n\n"
                    f"Subtotal: ${float(subtotal):.2f}\nIVA: ${float(impuesto):.2f}\n"
                    f"Total: ${float(total):.2f}\n\n¡Gracias por tu compra!"
                )
        except Exception as e:
            print(f"[VENTA] No se pudo preparar el correo: {e}")

        return {
            "mensaje": "Venta registrada correctamente",
            "id_venta": id_venta,
            "subtotal": float(subtotal),
            "iva": float(impuesto),
            "total": float(total),
            "detalle": detalle
        }

    except HTTPException:
        if conexion:
            conexion.rollback()
        raise

    except Exception as e:
        if conexion:
            conexion.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al registrar la venta: {str(e)}"
        )

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()  
# ==========================================
# REPORTES (CSV, EXCEL Y PDF)
# ==========================================

FORMATOS_REPORTE = ["csv", "xlsx", "pdf"]


def limpiar_celda(valor):
    # Evita que Excel interprete un texto como fórmula (ej. un nombre que empiece con "=")
    if isinstance(valor, str) and valor[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + valor
    return valor


def ejecutar_consulta(sql):
    conexion = None
    cursor = None

    try:
        conexion = psycopg2.connect(DATABASE_URL)
        cursor = conexion.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el reporte: {str(e)}"
        )

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


def construir_reporte(nombre_archivo, titulo, columnas, filas, formato):

    cabecera = {
        "Content-Disposition":
            f'attachment; filename="{nombre_archivo}.{formato}"'
    }

    # ---------- CSV ----------
    if formato == "csv":

        salida = io.StringIO()
        escritor = csv.writer(salida)

        escritor.writerow(columnas)

        for fila in filas:
            escritor.writerow([limpiar_celda(c) for c in fila])

        # El BOM hace que Excel muestre bien los acentos
        contenido = ("\ufeff" + salida.getvalue()).encode("utf-8")

        return Response(
            content=contenido,
            media_type="text/csv; charset=utf-8",
            headers=cabecera
        )

    # ---------- EXCEL ----------
    if formato == "xlsx":

        libro = Workbook()
        hoja = libro.active
        hoja.title = "Reporte"

        hoja.append(columnas)

        for fila in filas:
            hoja.append([limpiar_celda(c) for c in fila])

        for celda in hoja[1]:
            celda.font = Font(bold=True)

        for columna in hoja.columns:
            ancho = max(
                len(str(celda.value)) if celda.value is not None else 0
                for celda in columna
            )
            hoja.column_dimensions[columna[0].column_letter].width = min(ancho + 2, 50)

        salida = io.BytesIO()
        libro.save(salida)

        return Response(
            content=salida.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=cabecera
        )

    # ---------- PDF ----------
    salida = io.BytesIO()

    documento = SimpleDocTemplate(
        salida,
        pagesize=landscape(letter),
        title=titulo
    )

    estilos = getSampleStyleSheet()

    datos = [columnas] + [[str(c) for c in fila] for fila in filas]

    tabla = Table(datos, repeatRows=1)

    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6f4b91")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))

    documento.build([
        Paragraph(titulo, estilos["Title"]),
        Spacer(1, 12),
        tabla
    ])

    return Response(
        content=salida.getvalue(),
        media_type="application/pdf",
        headers=cabecera
    )


# ==========================================
# REPORTE DE VENTAS
# GET /reportes/ventas?formato=csv|xlsx|pdf
# ==========================================
@app.get("/reportes/ventas")
def reporte_ventas(
    formato: str = "csv",
    usuario_actual: dict = Depends(verificar_rol([1, 2]))
):
    formato = formato.lower()

    if formato not in FORMATOS_REPORTE:
        raise HTTPException(
            status_code=400,
            detail="Formato no válido. Usa csv, xlsx o pdf"
        )

    filas = ejecutar_consulta("""
        SELECT
            v.id_venta,
            to_char(v.fecha_venta AT TIME ZONE 'UTC' AT TIME ZONE 'America/Mexico_City', 'DD/MM/YYYY HH24:MI'),
            u.nombre,
            v.subtotal,
            v.impuesto,
            v.total,
            v.estado
        FROM ventas v
        INNER JOIN usuarios u
            ON v.id_usuario = u.id_usuario
        ORDER BY v.id_venta DESC;
    """)

    filas = [
        [f[0], f[1], f[2], float(f[3]), float(f[4]), float(f[5]), f[6]]
        for f in filas
    ]

    return construir_reporte(
        "reporte_ventas",
        "Reporte de ventas",
        ["ID", "Fecha", "Cliente", "Subtotal", "IVA", "Total", "Estado"],
        filas,
        formato
    )


# ==========================================
# REPORTE DE INVENTARIO
# GET /reportes/inventario?formato=csv|xlsx|pdf
# ==========================================
@app.get("/reportes/inventario")
def reporte_inventario(
    formato: str = "csv",
    usuario_actual: dict = Depends(verificar_rol([1]))
):
    formato = formato.lower()

    if formato not in FORMATOS_REPORTE:
        raise HTTPException(
            status_code=400,
            detail="Formato no válido. Usa csv, xlsx o pdf"
        )

    filas = ejecutar_consulta("""
        SELECT
            p.id_producto,
            p.nombre,
            COALESCE(c.nombre, 'Sin categoría'),
            p.precio_venta,
            p.stock_actual,
            p.stock_minimo,
            CASE
                WHEN p.stock_actual <= p.stock_minimo THEN 'BAJO'
                ELSE 'OK'
            END
        FROM productos p
        LEFT JOIN categorias c
            ON p.id_categoria = c.id_categoria
        ORDER BY p.id_producto;
    """)

    filas = [
        [f[0], f[1], f[2], float(f[3]), f[4], f[5], f[6]]
        for f in filas
    ]

    return construir_reporte(
        "reporte_inventario",
        "Reporte de inventario",
        ["ID", "Producto", "Categoría", "Precio venta", "Stock", "Mínimo", "Estado"],
        filas,
        formato
    )         
# ==========================================
# INICIO DE SESIÓN
# POST /login
# ==========================================

@app.post("/login")
def iniciar_sesion(datos: OAuth2PasswordRequestForm = Depends()):

    try:

        conexion = psycopg2.connect(DATABASE_URL)

        cursor = conexion.cursor()


        cursor.execute("""
            SELECT
                u.id_usuario,
                u.nombre,
                u.usuario,
                u.password_hash,
                u.id_tipo_usuario,
                u.activo,
                t.nombre
            FROM usuarios u
            INNER JOIN tipos_usuario t
                ON u.id_tipo_usuario = t.id_tipo_usuario
            WHERE u.usuario = %s;
        """, (datos.username,))


        usuario = cursor.fetchone()


        cursor.close()

        conexion.close()


        if usuario is None:

            raise HTTPException(
                status_code=401,
                detail="Usuario o contraseña incorrectos"
            )


        if not usuario[5]:

            raise HTTPException(
                status_code=403,
                detail="El usuario está inactivo"
            )


        contraseña_correcta = pwd_context.verify(
            datos.password,
            usuario[3]
        )


        if not contraseña_correcta:

            raise HTTPException(
                status_code=401,
                detail="Usuario o contraseña incorrectos"
            )


        token = crear_token({

            "id_usuario": usuario[0],

            "usuario": usuario[2],

            "id_tipo_usuario": usuario[4],

            "tipo_usuario": usuario[6]

        })


        return {

            "mensaje": "Inicio de sesión exitoso",

            "access_token": token,

            "token_type": "bearer",

            "token": token,

            "id_usuario": usuario[0],

            "nombre": usuario[1],

            "usuario": usuario[2],

            "id_tipo_usuario": usuario[4],

            "tipo_usuario": usuario[6]

        }


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Error al iniciar sesión: {str(e)}"

        )
