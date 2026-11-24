README · MD
Sistema de Tienda

API REST con interfaz web para administrar una tienda: productos, categorías, proveedores, inventario, ventas, usuarios y reportes. Incluye autenticación con JWT, control de acceso por roles, recuperación de contraseña por correo y exportación de reportes en CSV, Excel y PDF.

Proyecto optativa · Operaciones CRUD sobre las entidades principales del negocio (productos y entidades relacionadas).

Tabla de contenido
Características
Tecnologías
Estructura del proyecto
Instalación
Configuración (.env)
Configurar el envío de correos
Ejecución
Autenticación y roles
Referencia de la API
Reglas de negocio
Reportes
Base de datos
Seguridad
Solución de problemas
Características
CRUD completo de productos, categorías, proveedores y usuarios.
Inventario con historial: cada entrada, salida o ajuste queda registrado en historial_inventario.
Ventas (pedidos) con detalle por producto, cálculo automático de IVA (16 %), descuento de stock y correo de confirmación.
Autenticación JWT (expira a los 60 minutos) y autorización por roles.
Recuperación de contraseña mediante enlace por correo (válido 30 minutos y de un solo uso).
Reportes descargables de ventas e inventario en csv, xlsx y pdf.
Transacciones seguras: las operaciones críticas usan FOR UPDATE y rollback para evitar inconsistencias de stock.
Documentación interactiva automática (Swagger UI) gracias a FastAPI.
Tecnologías
Área	Herramienta
Lenguaje	Python 3
Framework web	FastAPI + Uvicorn
Base de datos	PostgreSQL (alojada en Neon) con psycopg2
Autenticación	python-jose (JWT), passlib[bcrypt]
Validación	Pydantic
Reportes	openpyxl (Excel), reportlab (PDF), csv
Correo	smtplib (SMTP)
Configuración	python-dotenv
Estructura del proyecto
.
├── main.py                 # Aplicación FastAPI: modelos, rutas, reglas de negocio y reportes
├── run.py                  # Arranque del servidor con Uvicorn
├── correo.py               # Envío de correos por SMTP (lee el .env en cada envío)
├── configurar_correo.py    # Asistente para configurar y probar el SMTP
├── requirements.txt        # Dependencias
├── static/                 # Frontend (index.html, restablecer.html, etc.)
├── .env                    # Variables de entorno (NO se sube a git)
├── .gitignore
└── README.md
Instalación

Requisitos previos: Python 3.9 o superior, una base de datos PostgreSQL (por ejemplo en Neon) y, opcionalmente, una cuenta de correo para los avisos.

bash
# 1. Clonar el repositorio
git clone <URL-DEL-REPOSITORIO>
cd <carpeta-del-proyecto>

# 2. Crear y activar un entorno virtual
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
Configuración (.env)

Crea un archivo .env en la raíz del proyecto (debe llamarse exactamente .env, con punto):

env
# Base de datos
DATABASE_URL=postgresql://usuario:contraseña@host/basededatos?sslmode=require

# Seguridad (usa una cadena larga y aleatoria)
SECRET_KEY=cambia-esto-por-una-clave-larga-y-aleatoria

# Correo (se llenan solos con configurar_correo.py)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_correo@gmail.com
SMTP_PASS=contraseña-de-aplicacion
SMTP_FROM=tu_correo@gmail.com
APP_URL=http://127.0.0.1:8000
Variable	Obligatoria	Descripción
DATABASE_URL	Sí	Cadena de conexión a PostgreSQL.
SECRET_KEY	Sí	Clave para firmar los tokens JWT. Genera una con python -c "import secrets; print(secrets.token_urlsafe(48))".
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS	Para correo	Credenciales del servidor SMTP.
SMTP_FROM	No	Remitente. Si se omite, se usa SMTP_USER.
APP_URL	No	URL pública de la app; se usa para armar el enlace de recuperación de contraseña. Por defecto http://127.0.0.1:8000.

 Nunca subas el .env al repositorio. El .gitignore ya lo excluye (.env y .env.*, salvo .env.example). Si publicas un .env.example, deja los valores vacíos.

Configurar el envío de correos

El proyecto incluye un asistente que escribe la configuración SMTP en tu .env sin tocar lo demás y prueba que las credenciales funcionen:

bash
python configurar_correo.py
Escribe el correo que enviará los mensajes.
Pega la contraseña de aplicación (se escribe sin mostrarse en pantalla).
El script prueba el inicio de sesión y guarda los datos.
Reinicia el servidor para que tome los cambios.

Proveedores con servidor preconfigurado: Gmail, Outlook, Hotmail y Live. Para otros proveedores el script pregunta el servidor y el puerto.

Gmail: no sirve tu contraseña normal. Necesitas una contraseña de aplicación de 16 letras (requiere tener activada la verificación en dos pasos).

Una vez en marcha, un administrador puede verificar el envío con POST /correo/probar?destino=correo@ejemplo.com.

Ejecución
bash
python run.py

El servidor queda disponible en:

Recurso	URL
Aplicación web	http://127.0.0.1:8000
Documentación interactiva (Swagger)	http://127.0.0.1:8000/docs
Documentación alternativa (ReDoc)	http://127.0.0.1:8000/redoc
Verificar conexión a la BD	http://127.0.0.1:8000/probar-db

run.py inicia Uvicorn con reload=True, por lo que el servidor se reinicia al guardar cambios (modo desarrollo).

Autenticación y roles
Flujo de autenticación
El usuario hace POST /login con username y password (formulario OAuth2, application/x-www-form-urlencoded).
La API responde con un access_token (JWT, válido 60 minutos).
Las rutas protegidas reciben el token en la cabecera:
Authorization: Bearer <access_token>

Ejemplo con curl:

bash
# Iniciar sesión
curl -X POST http://127.0.0.1:8000/login \
  -d "username=admin&password=tu_contraseña"

# Usar el token
curl http://127.0.0.1:8000/productos \
  -H "Authorization: Bearer <access_token>"

En Swagger (/docs) puedes usar el botón Authorize para iniciar sesión directamente.

Roles
ID	Rol	Qué puede hacer
1	Administrador	Acceso total: gestión de catálogo, usuarios, inventario, ventas y reportes.
2	Ventas	Registrar ventas y consultar el reporte de ventas.
3	Inventario	Registrar movimientos de inventario (solo ENTRADA y AJUSTE).
4	Cliente	Registrar sus propios pedidos. Es el rol asignado en el registro público.

El nombre exacto de cada rol proviene de la tabla tipos_usuario. Los IDs son los que usa el código para autorizar.

Referencia de la API



Autenticación y usuarios
Método	Ruta	Acceso	Descripción
POST	/login		Inicia sesión y devuelve el token JWT.
POST	/usuarios		Registro público (se crea con rol Cliente).
GET	/usuarios	 Admin	Lista los usuarios.
PUT	/usuarios/{id_usuario}	 Admin	Actualiza un usuario (incluye rol y contraseña).
DELETE	/usuarios/{id_usuario}	 Admin	Elimina un usuario.
POST	/cambiar-password		Cambia la contraseña del usuario con sesión.
POST	/recuperar-password		Envía un enlace de recuperación al correo.
POST	/restablecer-password		Fija la nueva contraseña usando el token del enlace.
POST	/correo/probar?destino=	 Admin	Envía un correo de prueba.
Productos
Método	Ruta	Acceso	Descripción
GET	/productos		Lista todos los productos.
GET	/productos/{id_producto}		Consulta un producto por ID.
GET	/productos/buscar/{nombre}		Busca productos por nombre.
POST	/productos	 Admin	Crea un producto.
PUT	/productos/{id_producto}	 Admin	Actualiza un producto.
DELETE	/productos/{id_producto}	 Admin	Elimina un producto.

Cuerpo para crear/actualizar un producto:

json
{
  "codigo_barras": "7501234567890",
  "nombre": "Refresco 600 ml",
  "descripcion": "Bebida carbonatada",
  "id_categoria": 1,
  "id_proveedor": 1,
  "precio_compra": 10.50,
  "precio_venta": 15.00,
  "stock_actual": 100,
  "stock_minimo": 10
}

Solo nombre, precio_compra, precio_venta, stock_actual y stock_minimo son obligatorios. Los precios y el stock no pueden ser negativos.

Categorías
Método	Ruta	Acceso	Descripción
GET	/categorias		Lista las categorías.
GET	/categorias/{id_categoria}		Consulta una categoría.
GET	/categorias/buscar/{nombre}		Busca por nombre.
POST	/categorias	 Admin	Crea una categoría.
PUT	/categorias/{id_categoria}	 Admin	Actualiza una categoría.
DELETE	/categorias/{id_categoria}	Admin	Elimina una categoría.
json
{ "nombre": "Bebidas", "descripcion": "Refrescos, jugos y agua" }
Proveedores
Método	Ruta	Acceso	Descripción
GET	/proveedores		Lista los proveedores.
GET	/proveedores/{id_proveedor}		Consulta un proveedor.
GET	/proveedores/buscar/{nombre}		Busca por nombre.
POST	/proveedores	 Admin	Crea un proveedor.
PUT	/proveedores/{id_proveedor}	 Admin	Actualiza un proveedor.
DELETE	/proveedores/{id_proveedor}	 Admin	Elimina un proveedor.
json
{
  "nombre_empresa": "Distribuidora del Centro",
  "contacto_nombre": "Ana López",
  "telefono": "2221234567",
  "email": "contacto@distribuidora.com",
  "direccion": "Calle 5 de Mayo 123, Puebla"
}
Inventario
Método	Ruta	Acceso	Descripción
POST	/movimientos	 Admin, Inventario	Registra una entrada, salida o ajuste de stock.
GET	/movimientos		Historial de movimientos (más recientes primero).
json
{
  "id_producto": 1,
  "tipo_movimiento": "ENTRADA",
  "cantidad": 50,
  "motivo": "Compra a proveedor"
}

tipo_movimiento acepta ENTRADA, SALIDA o AJUSTE. La respuesta incluye stock_anterior y stock_nuevo.

Ventas
Método	Ruta	Acceso	Descripción
POST	/ventas	 Admin, Ventas, Cliente	Registra una venta con uno o más productos.
json
{
  "items": [
    { "id_producto": 1, "cantidad": 2 },
    { "id_producto": 3, "cantidad": 1 }
  ]
}

Respuesta de ejemplo:

json
{
  "mensaje": "Venta registrada correctamente",
  "id_venta": 12,
  "subtotal": 45.0,
  "iva": 7.2,
  "total": 52.2,
  "detalle": [
    { "id_producto": 1, "producto": "Refresco 600 ml", "cantidad": 2, "precio_unitario": 15.0, "subtotal": 30.0 }
  ]
}
Reportes
Método	Ruta	Acceso	Descripción
GET	/reportes/ventas?formato=csv|xlsx|pdf	 Admin, Ventas	Descarga el reporte de ventas.
GET	/reportes/inventario?formato=csv|xlsx|pdf	 Admin	Descarga el reporte de inventario.
Utilidades
Método	Ruta	Acceso	Descripción
GET	/		Sirve la interfaz web (static/index.html).
GET	/probar-db		Comprueba la conexión con la base de datos.
Códigos de respuesta comunes
Código	Significado
200	Operación exitosa.
400	Datos inválidos, stock insuficiente o enlace de recuperación inválido.
401	Token ausente, inválido o expirado; credenciales incorrectas.
403	El rol del usuario no tiene permiso, o el usuario está inactivo.
404	El recurso solicitado no existe.
422	El cuerpo de la petición no cumple las validaciones.
500	Error interno o de base de datos.
Reglas de negocio
IVA: 16 % sobre el subtotal, redondeado a 2 decimales (ROUND_HALF_UP). Se define en la constante TASA_IVA.
Ventas:
Si un producto se repite en el pedido, sus cantidades se suman.
Se valida que el producto exista y que haya stock suficiente.
Todo ocurre en una sola transacción: si algo falla, no se guarda nada.
Cada venta descuenta el stock y genera una SALIDA en el historial con el motivo Venta #<id>.
El correo de confirmación se envía en segundo plano; si falla, la venta no se afecta.
Movimientos de inventario:
ENTRADA suma al stock y SALIDA lo resta (no permite stock negativo).
AJUSTE establece el stock exactamente en la cantidad indicada.
El rol Inventario no puede registrar SALIDA.
Registro público: los usuarios que se registran solos siempre reciben el rol Cliente (4); solo un administrador puede asignar otros roles.
Recuperación de contraseña:
La respuesta es siempre la misma, exista o no el correo, para no revelar qué cuentas están registradas.
El enlace dura 30 minutos y deja de servir una vez que se cambia la contraseña.
Contraseñas: entre 6 y 72 caracteres, almacenadas con hash bcrypt.
Reportes
Reporte	Columnas
Ventas	ID, Fecha, Cliente, Subtotal, IVA, Total, Estado
Inventario	ID, Producto, Categoría, Precio venta, Stock, Mínimo, Estado (OK / BAJO)
En inventario, el estado es BAJO cuando stock_actual <= stock_minimo.
Las fechas del reporte de ventas se muestran en la zona horaria America/Mexico_City.
El CSV incluye BOM UTF-8 para que Excel muestre bien los acentos.
Las celdas que empiezan con =, +, - o @ se neutralizan para evitar inyección de fórmulas en Excel.
Base de datos

El código espera una base PostgreSQL con las siguientes tablas (deducidas de las consultas del proyecto):

Tabla	Campos principales
tipos_usuario	id_tipo_usuario, nombre
usuarios	id_usuario, nombre, usuario, email, password_hash, id_tipo_usuario, activo
categorias	id_categoria, nombre, descripcion
proveedores	id_proveedor, nombre_empresa, contacto_nombre, telefono, email, direccion
productos	id_producto, codigo_barras, nombre, descripcion, id_categoria, id_proveedor, precio_compra, precio_venta, stock_actual, stock_minimo
historial_inventario	id_movimiento, id_producto, tipo_movimiento, cantidad, motivo, fecha_movimiento
ventas	id_venta, id_usuario, fecha_venta, subtotal, impuesto, total, estado
detalle_venta	id_venta, id_producto, cantidad, precio_unitario, subtotal

Recomendado: agrega al repositorio un archivo schema.sql con el CREATE TABLE de estas tablas y los datos iniciales (los 4 roles y un administrador) para que cualquiera pueda montar el proyecto desde cero.

Seguridad
Las contraseñas se guardan con bcrypt; nunca en texto plano.
Los tokens JWT se firman con SECRET_KEY (HS256) y expiran a los 60 minutos.
Los secretos viven en .env, que está excluido de git.
Las consultas SQL usan parámetros (%s), lo que previene inyección SQL.
Los mensajes de login no distinguen entre "usuario inexistente" y "contraseña incorrecta".

Antes de desplegar a producción, considera:

Cambiar reload=True y host="127.0.0.1" en run.py según el entorno.
Proteger o eliminar /probar-db, que hoy es pública y puede mostrar detalles de la conexión en caso de error.
Proteger con sesión las rutas de consulta que hoy son públicas (/productos/{id}, búsquedas, categorías, proveedores) si no deben ser visibles para cualquiera.
Restringir el origen de las peticiones (CORS) y usar HTTPS.
Rotar cualquier credencial que haya estado expuesta (base de datos, SMTP, claves de API).
Solución de problemas
Problema	Posible causa y solución
No encuentro el archivo .env al configurar el correo	El archivo debe llamarse exactamente .env y estar junto a configurar_correo.py.
Falta configurar el correo en .env	Ejecuta python configurar_correo.py.
Gmail rechaza usuario o contraseña	Usa una contraseña de aplicación de 16 letras, no tu contraseña normal.
Los cambios del .env no se reflejan	Reinicia el servidor (Ctrl+C y python run.py).
Error al conectar con Neon en /probar-db	Revisa DATABASE_URL (incluye ?sslmode=require) y que la base esté activa.
Token inválido o expirado (401)	Vuelve a iniciar sesión; el token dura 60 minutos.
No tienes permisos para realizar esta acción (403)	Tu rol no tiene acceso a esa ruta; consulta la tabla de roles.
Error al arrancar por la carpeta static	La carpeta static/ debe existir junto a main.py.
Notas de mantenimiento
requirements.txt incluye paquetes que main.py no utiliza actualmente (por ejemplo google-genai, openai, pandas, matplotlib, scipy). Puedes depurarlo para tener instalaciones más ligeras.
La variable GEMINI_API_KEY aparece en el .env, pero el código actual no la usa.
Autor

Proyecto desarrollado como parte de la materia optativa.
