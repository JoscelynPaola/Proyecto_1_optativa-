console.log("JavaScript del Sistema de Tienda funcionando");

// ==========================================
// ABRIR LOGIN
// ==========================================

function abrirLogin() {

    document.getElementById("modal-login").style.display = "flex";

}

// ==========================================
// CERRAR LOGIN
// ==========================================

function cerrarLogin() {

    document.getElementById("modal-login").style.display = "none";

}


// ==========================================
// ABRIR REGISTRO
// ==========================================

function abrirRegistro() {

    document.getElementById("modal-registro").style.display = "flex";

}


// ==========================================
// CERRAR REGISTRO
// ==========================================

function cerrarRegistro() {

    document.getElementById("modal-registro").style.display = "none";

}
// ==========================================
// CONFIGURAR INTERFAZ SEGÚN EL ROL
// 1 = ADMINISTRADOR, 2 = VENDEDOR, 3 = INVENTARIO, 4 = CLIENTE
// ==========================================

// ==========================================
// BOTONES EDITAR / ELIMINAR (SOLO ADMINISTRADOR)
// ==========================================

function botonesAdminProducto(id) {

    if (Number(localStorage.getItem("id_tipo_usuario")) !== 1) {
        return "<td></td>";
    }

    return `
        <td>
            <button
                class="btn btn-sm btn-outline-primary"
                onclick="editarProducto(${id})">
                ✏️
            </button>
            <button
                class="btn btn-sm btn-outline-danger"
                onclick="eliminarProducto(${id})">
                🗑️
            </button>
        </td>
    `;
}

function configurarInterfazPorRol() {

    const rol = Number(localStorage.getItem("id_tipo_usuario"));

    // Qué roles pueden ver cada sección
    const permisos = {
        "panel-administrador": [1],
        "seccion-tienda":      [1, 2, 4],
        "seccion-buscador":       [1, 3],
        "seccion-resumen":        [1, 3],
        "seccion-stock-bajo":     [1, 3],
        "seccion-tabla-productos": [1, 3],
        "seccion-productos":   [1],
        "col-acciones":        [1],
        "seccion-movimientos": [1, 3],
        "seccion-historial":   [1, 2, 3],
        "seccion-reportes":        [1, 2],
        "reportes-ventas":         [1, 2],
        "reportes-inventario":     [1]
    };

    for (const id in permisos) {

        const elemento = document.getElementById(id);

        if (!elemento) {
            continue;
        }

        elemento.style.display =
            permisos[id].includes(rol) ? "" : "none";
    }

    // El rol INVENTARIO (3) solo puede hacer ENTRADA y AJUSTE
    if (rol === 3) {
        const opcionSalida = document.querySelector(
            '#tipo-movimiento option[value="SALIDA"]'
        );
        if (opcionSalida) {
            opcionSalida.remove();
        }
    }
}
// ==========================================
// MOSTRAR CATEGORÍAS
// ==========================================

function mostrarCategorias() {

    const seccionCategorias =
        document.getElementById("seccion-categorias");

    if (!seccionCategorias) {
        return;
    }

    seccionCategorias.style.display = "block";

    seccionCategorias.scrollIntoView({
        behavior: "smooth"
    });

    cargarCategorias();
}
// ==========================================
// MOSTRAR PROVEEDORES
// ==========================================

function mostrarProveedores() {

    const seccionProveedores =
        document.getElementById("seccion-proveedores");

    if (!seccionProveedores) {
        return;
    }

    seccionProveedores.style.display = "block";

    seccionProveedores.scrollIntoView({
        behavior: "smooth"
    });

    cargarProveedores();
}
// ==========================================
// CARGAR PROVEEDORES
// ==========================================

async function cargarProveedores() {

    const token = localStorage.getItem("token");

    if (!token) {
        return;
    }

    const lista =
        document.getElementById("lista-proveedores");

    if (!lista) {
        return;
    }

    lista.innerHTML = `
        <p class="text-muted">
            Cargando proveedores...
        </p>
    `;

    try {

        const respuesta = await fetch("/proveedores", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        const proveedores = await respuesta.json();

        if (!respuesta.ok) {

            lista.innerHTML = `
                <p class="text-danger">
                    ${proveedores.detail || "No se pudieron cargar los proveedores"}
                </p>
            `;

            return;
        }

        lista.innerHTML = "";

        if (proveedores.length === 0) {

            lista.innerHTML = `
                <p class="text-muted">
                    No hay proveedores registrados.
                </p>
            `;

            return;
        }

        proveedores.forEach(function(proveedor) {

            lista.innerHTML += `
                <div class="border rounded p-3 mb-2">

                    <strong>
                        ${proveedor.nombre_empresa}
                    </strong>

                    <br>

                    <span>
                        Contacto:
                        ${proveedor.contacto_nombre || "Sin contacto"}
                    </span>

                    <br>

                    <span>
                        Teléfono:
                        ${proveedor.telefono || "Sin teléfono"}
                    </span>

                    <br>

                    <span>
                        Correo:
                        ${proveedor.email || "Sin correo"}
                    </span>

                    <br>

                    <span>
                        Dirección:
                        ${proveedor.direccion || "Sin dirección"}
                    </span>

                </div>
            `;

        });

    } catch (error) {

        console.error(
            "Error al cargar proveedores:",
            error
        );

        lista.innerHTML = `
            <p class="text-danger">
                Error al conectar con el servidor.
            </p>
        `;
    }
}
// ==========================================
// CREAR PROVEEDOR
// ==========================================

async function crearProveedor() {

    const token = localStorage.getItem("token");

    if (!token) {
        return;
    }

    const nombreEmpresa =
        document.getElementById("nombre-proveedor").value.trim();

    const contacto =
        document.getElementById("contacto-proveedor").value.trim();

    const telefono =
        document.getElementById("telefono-proveedor").value.trim();

    const email =
        document.getElementById("email-proveedor").value.trim();

    const direccion =
        document.getElementById("direccion-proveedor").value.trim();

    const mensaje =
        document.getElementById("mensaje-proveedor");

    if (nombreEmpresa === "") {
        mensaje.textContent = "Ingresa el nombre de la empresa.";
        mensaje.className = "text-danger";
        return;
    }

    const datos = {
        nombre_empresa: nombreEmpresa,
        contacto_nombre: contacto || null,
        telefono: telefono || null,
        email: email || null,
        direccion: direccion || null
    };

    try {

        const respuesta = await fetch("/proveedores", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },

            body: JSON.stringify(datos)
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {

            mensaje.textContent =
                resultado.detail ||
                "No se pudo crear el proveedor.";

            mensaje.className = "text-danger";

            return;
        }

        mensaje.textContent =
            "Proveedor creado correctamente.";

        mensaje.className = "text-success";

        document.getElementById("nombre-proveedor").value = "";
        document.getElementById("contacto-proveedor").value = "";
        document.getElementById("telefono-proveedor").value = "";
        document.getElementById("email-proveedor").value = "";
        document.getElementById("direccion-proveedor").value = "";

        cargarProveedores();

    } catch (error) {

        console.error(
            "Error al crear proveedor:",
            error
        );

        mensaje.textContent =
            "Error al conectar con el servidor.";

        mensaje.className = "text-danger";
    }
}
// ==========================================
// INICIAR SESIÓN
// ==========================================

async function iniciarSesion() {

    const usuario =
        document.getElementById("usuario").value;

    const password =
        document.getElementById("password").value;


    if (usuario === "" || password === "") {

        document.getElementById("mensaje-login").textContent =
            "Ingresa usuario y contraseña";

        return;
    }


    const datos = new URLSearchParams();

    datos.append("username", usuario);
    datos.append("password", password);


    try {

        const respuesta = await fetch("/login", {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/x-www-form-urlencoded"
            },

            body: datos

        });


        const resultado = await respuesta.json();


        if (!respuesta.ok) {

            document.getElementById("mensaje-login").textContent =
                resultado.detail ||
                "Usuario o contraseña incorrectos";

            return;
        }


// Guardar sesión
localStorage.setItem(
    "token",
    resultado.access_token
);

localStorage.setItem(
    "id_tipo_usuario",
    resultado.id_tipo_usuario
);

localStorage.setItem(
    "tipo_usuario",
    resultado.tipo_usuario
);

localStorage.setItem(
    "nombre_usuario",
    resultado.nombre
);

configurarInterfazPorRol();


// Ocultar pantalla inicial
document.getElementById("inicio").style.display =
    "none";


        // Mostrar panel principal
        document.getElementById("panel-principal").style.display =
            "block";


        // Cerrar ventana
        document.getElementById("modal-login").style.display =
            "none";


        // Cargar productos al entrar
        mostrarProductos();

        cargarOpcionesProducto();
        cargarProductosMovimiento();
        cargarHistorialMovimientos();


    } catch (error) {

        console.error(error);

        document.getElementById("mensaje-login").textContent =
            "No se pudo conectar con el servidor";

    }

}

// ==========================================
// MOSTRAR PRODUCTOS
// ==========================================
let productosCargados = [];
async function mostrarProductos() {

    const token = localStorage.getItem("token");

    // ==========================================
    // VERIFICAR SESIÓN
    // ==========================================

    if (!token) {
        alert("Primero debes iniciar sesión");
        abrirLogin();
        return;
    }


    // ==========================================
    // MOSTRAR PANEL PRINCIPAL
    // ==========================================

    const panel =
        document.getElementById("panel-principal");

    panel.style.display = "block";


    // ==========================================
    // BUSCAR TABLA
    // ==========================================

    const tabla =
        document.getElementById("tabla-productos");


    tabla.innerHTML = `
        <tr>
            <td colspan="7" class="text-center text-muted">
                Cargando productos...
            </td>
        </tr>
    `;


    // ==========================================
    // CONSULTAR FASTAPI
    // ==========================================

    try {

        const respuesta =
            await fetch("/productos", {
                method: "GET",

                headers: {
                    "Authorization":
                        "Bearer " + token
                }
            });


        const datos =
            await respuesta.json();


        // ==========================================
        // MOSTRAR EN CONSOLA
        // ==========================================

        console.log(
            "Productos recibidos desde Neon:",
            datos
        );

        productosCargados = datos;
        actualizarResumenInventario(datos);
        mostrarCatalogo(datos)

       // ==========================================
        // COMPROBAR ERROR
        // ==========================================

        if (!respuesta.ok) {

            // Sesión vencida: volver al inicio
            if (respuesta.status === 401) {
                localStorage.removeItem("token");
                alert("Tu sesión expiró, inicia sesión de nuevo");
                location.reload();
                return;
            }

            console.error(
                "Error al obtener productos:",
                datos
            );

            tabla.innerHTML = `
                <tr>
                    <td
                        colspan="7"
                        class="text-center text-danger">

                        No se pudieron cargar los productos.

                    </td>
                </tr>
            `;

            return;
        }


        // ==========================================
        // LIMPIAR TABLA
        // 

        tabla.innerHTML = "";


        // ==========================================
        // SI NO HAY PRODUCTOS
        // ==========================================

        if (datos.length === 0) {

            tabla.innerHTML = `
                <tr>
                    <td
                        colspan="7"
                        class="text-center text-muted">

                        No hay productos registrados.

                    </td>
                </tr>
            `;

            return;
        }


        // ==========================================
        // RECORRER PRODUCTOS
        // ==========================================

        datos.forEach(function(producto) {


            // Crear fila
            const fila =
                document.createElement("tr");


            // ======================================
            // CATEGORÍA
            // ======================================

            let categoria =
                producto.id_categoria || "Sin categoría";


            // ======================================
            // PROVEEDOR
            // ======================================

            let proveedor =
                producto.id_proveedor || "Sin proveedor";


            // ======================================
            // CREAR CONTENIDO DE LA FILA
            // ======================================

            fila.innerHTML = `

                <td>
                    ${producto.id_producto}
                </td>


                <td>

                    <strong>
                        ${producto.nombre}
                    </strong>

                    <br>

                    <small class="text-muted">

                        ${producto.codigo_barras || "Sin código"}

                    </small>

                </td>


                <td>
                    ${categoria}
                </td>


                <td>
                    ${proveedor}
                </td>


                <td>

                    $${Number(
                        producto.precio_venta
                    ).toFixed(2)}

                </td>


                <td>

                    ${producto.stock_actual}

                </td>


                ${botonesAdminProducto(producto.id_producto)}

            `;


            // Agregar fila a la tabla
            tabla.appendChild(fila);

        });


    } catch (error) {

        console.error(
            "Error al conectar con el servidor:",
            error
        );


        tabla.innerHTML = `
            <tr>

                <td
                    colspan="7"
                    class="text-center text-danger">

                    Error al conectar con el servidor.

                </td>

            </tr>
        `;

    }

}
// ==========================================
// BUSCAR PRODUCTO POR NOMBRE
// ==========================================

document.getElementById("buscar-producto").addEventListener("input", async function () {

    const nombre = this.value.trim();

    const token = localStorage.getItem("token");

    if (!token) {
        return;
    }

    // Si está vacío, mostrar todos
    if (nombre === "") {
        mostrarProductos();
        return;
    }

    try {

        const respuesta = await fetch(
            `/productos/buscar/${encodeURIComponent(nombre)}`,
            {
                method: "GET",

                headers: {
                    "Authorization": "Bearer " + token
                }
            }
        );

        const datos = await respuesta.json();

        console.log("Resultado de búsqueda:", datos);

        if (!respuesta.ok) {

            console.error(datos);
            return;

        }

        mostrarResultadosBusqueda(datos);

    } catch (error) {

        console.error(
            "Error al buscar producto:",
            error
        );

    }

});
// ==========================================
// MOSTRAR RESULTADOS DE BÚSQUEDA
// ==========================================

function mostrarResultadosBusqueda(datos) {

    const tabla =
        document.getElementById("tabla-productos");

    tabla.innerHTML = "";


    if (datos.length === 0) {

        tabla.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="text-center text-muted">

                    No se encontraron productos.

                </td>
            </tr>
        `;

        return;
    }


    datos.forEach(function(producto) {

        const fila =
            document.createElement("tr");


        fila.innerHTML = `

            <td>
                ${producto.id_producto}
            </td>

            <td>

                <strong>
                    ${producto.nombre}
                </strong>

                <br>

                <small class="text-muted">
                    ${producto.codigo_barras || "Sin código"}
                </small>

            </td>

            <td>
                ${producto.id_categoria || "Sin categoría"}
            </td>

            <td>
                ${producto.id_proveedor || "Sin proveedor"}
            </td>

            <td>
                $${Number(producto.precio_venta).toFixed(2)}
            </td>

            <td>
                ${producto.stock_actual}
            </td>

            ${botonesAdminProducto(producto.id_producto)}

        `;


        tabla.appendChild(fila);

    });

}

// ==========================================
// CATEGORÍAS
// ==========================================

async function categorias() {

    const token = localStorage.getItem("token");

    if (!token) {

        alert("Primero debes iniciar sesión");

        abrirLogin();

        return;
    }


    const seccion =
        document.getElementById("seccion-categorias");

    const lista =
        document.getElementById("lista-categorias");


    // Mostrar sección
    seccion.style.display = "block";


    // Ocultar productos
    document.getElementById(
        "seccion-productos"
    ).style.display = "none";


    lista.innerHTML =
        "<p>Cargando categorías...</p>";


    try {

        const respuesta = await fetch("/categorias");


        const datos = await respuesta.json();


        if (!respuesta.ok) {

            console.error(datos);

            lista.innerHTML =
                "<p>No se pudieron cargar las categorías.</p>";

            return;
        }


        lista.innerHTML = "";


        if (datos.length === 0) {

            lista.innerHTML =
                "<p>No hay categorías registradas.</p>";

            return;
        }


        datos.forEach(function(categoria) {

            const tarjeta =
                document.createElement("div");


            tarjeta.classList.add(
                "tarjeta-producto"
            );


            tarjeta.innerHTML = `

                <h3>
                    🏷️ ${categoria.nombre}
                </h3>

                <p>
                    ${categoria.descripcion || "Sin descripción"}
                </p>

            `;


            lista.appendChild(tarjeta);

        });


    } catch (error) {

        console.error(error);

        lista.innerHTML =
            "<p>Error al conectar con el servidor.</p>";

    }

}
// ==========================================
// CREAR CATEGORÍAS
// ==========================================
async function crearCategoria() {

    const nombre =
        document.getElementById(
            "nombre-categoria"
        ).value;

    const descripcion =
        document.getElementById(
            "descripcion-categoria"
        ).value;


    const mensaje =
        document.getElementById(
            "mensaje-categoria"
        );


    const token =
        localStorage.getItem("token");


    if (!token) {

        alert("Primero debes iniciar sesión");

        return;
    }


    if (nombre === "") {

        mensaje.textContent =
            "Escribe el nombre de la categoría";

        return;
    }


    try {

        const respuesta = await fetch(
            "/categorias",
            {

                method: "POST",

                headers: {

                    "Content-Type":
                        "application/json",

                    "Authorization":
                        "Bearer " + token

                },

                body: JSON.stringify({

                    nombre: nombre,

                    descripcion:
                        descripcion

                })

            }
        );


        const resultado =
            await respuesta.json();


        if (!respuesta.ok) {

            console.error(resultado);

            mensaje.textContent =
                resultado.detail ||
                "No se pudo crear la categoría";

            return;
        }


        mensaje.textContent =
            "Categoría creada correctamente";


        // Limpiar campos

        document.getElementById(
            "nombre-categoria"
        ).value = "";


        document.getElementById(
            "descripcion-categoria"
        ).value = "";


        // Volver a cargar categorías

        categorias();
        cargarCategorias();
        cargarOpcionesProducto();


    } catch (error) {

        console.error(error);

        mensaje.textContent =
            "Error al conectar con el servidor";

    }

}


// ==========================================
// PROVEEDORES
// ==========================================

function proveedores() {

    alert(
        "Sección de Proveedores"
    );

}


// ==========================================
// ENTRADAS
// ==========================================

function entradas() {

    alert(
        "Sección de Entradas"
    );

}


// ==========================================
// SALIDAS
// ==========================================

function salidas() {

    alert(
        "Sección de Salidas"
    );

}


// ==========================================
// HISTORIAL
// ==========================================

function historial() {

    alert(
        "Sección de Historial"
    );

}


// ==========================================
// CREAR CUENTA
// ==========================================

async function registrarUsuario() {

    const nombre =
        document.getElementById("nombre-registro").value;

    const usuario =
        document.getElementById("usuario-registro").value;

    const email =
        document.getElementById("email-registro").value;

    const password =
        document.getElementById("password-registro").value;


    const mensaje =
        document.getElementById("mensaje-registro");


    if (
        nombre === "" ||
        usuario === "" ||
        email === "" ||
        password === ""
    ) {

        mensaje.textContent =
            "Completa todos los campos";

        return;
    }


    try {

        const respuesta =
            await fetch("/usuarios", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    nombre: nombre,

                    usuario: usuario,

                    email: email,

                    password: password

                })

            });


        const resultado =
            await respuesta.json();


        if (!respuesta.ok) {

            mensaje.textContent =
                resultado.detail ||
                "No se pudo crear la cuenta";

            return;
        }


        mensaje.textContent =
            "Cuenta creada correctamente";


        document.getElementById(
            "nombre-registro"
        ).value = "";

        document.getElementById(
            "usuario-registro"
        ).value = "";

        document.getElementById(
            "email-registro"
        ).value = "";

        document.getElementById(
            "password-registro"
        ).value = "";


        setTimeout(function() {

            cerrarRegistro();

            abrirLogin();

        }, 1500);


    } catch (error) {

        console.error(error);

        mensaje.textContent =
            "No se pudo conectar con el servidor";

    }

}
// ==========================================
// REGISTRAR PRODUCTO
// ==========================================

document.getElementById("form-producto").addEventListener("submit", async function(event) {

    event.preventDefault();

    const token = localStorage.getItem("token");

    const mensaje = document.getElementById("mensaje-producto");

    if (!token) {

        mensaje.textContent = "Primero debes iniciar sesión";
        return;

    }


    // ==========================================
    // OBTENER DATOS DEL FORMULARIO
    // ==========================================

    const codigo_barras =
        document.getElementById("codigo-barras").value.trim();

    const nombre =
        document.getElementById("nombre-producto").value.trim();

    const descripcion =
        document.getElementById("descripcion-producto").value.trim();

    const id_categoria =
        document.getElementById("categoria-producto").value;

    const id_proveedor =
        document.getElementById("proveedor-producto").value;

    const precio_compra =
        document.getElementById("precio-compra").value;

    const precio_venta =
        document.getElementById("precio-venta").value;

    const stock_actual =
        document.getElementById("stock-actual").value;

    const stock_minimo =
        document.getElementById("stock-minimo").value;


    // ==========================================
    // VALIDACIÓN BÁSICA
    // ==========================================

    if (
        codigo_barras === "" ||
        nombre === "" ||
        precio_compra === "" ||
        precio_venta === "" ||
        stock_actual === "" ||
        stock_minimo === ""
    ) {

        mensaje.innerHTML =
            '<span class="text-danger">Completa los campos obligatorios.</span>';

        return;

    }


    // ==========================================
    // DATOS PARA FASTAPI
    // ==========================================

    const producto = {

        codigo_barras: codigo_barras,

        nombre: nombre,

        descripcion: descripcion,

        id_categoria:
            id_categoria === ""
                ? null
                : Number(id_categoria),

        id_proveedor:
            id_proveedor === ""
                ? null
                : Number(id_proveedor),

        precio_compra:
            Number(precio_compra),

        precio_venta:
            Number(precio_venta),

        stock_actual:
            Number(stock_actual),

        stock_minimo:
            Number(stock_minimo)

    };


    console.log(
        "Producto que se enviará a FastAPI:",
        producto
    );


    // ==========================================
    // ENVIAR A FASTAPI
    // ==========================================

    const idEdicion =
        document.getElementById("id-producto").value;

    const url =
        idEdicion ? "/productos/" + idEdicion : "/productos";

    const metodo =
        idEdicion ? "PUT" : "POST";

    try {

        const respuesta = await fetch(url, {

            method: metodo,

            headers: {

                "Content-Type":
                    "application/json",

                "Authorization":
                    "Bearer " + token

            },

            body: JSON.stringify(producto)

        });


        const resultado =
            await respuesta.json();


        console.log(
            "Respuesta de FastAPI:",
            resultado
        );

        // ==========================================
        // ERROR
        // ==========================================

        if (!respuesta.ok) {

            mensaje.innerHTML =
                `<span class="text-danger">
                    ${resultado.detail || "No se pudo registrar el producto"}
                </span>`;

            return;

        }


        // ==========================================
        // PRODUCTO GUARDADO
        // ==========================================

        cancelarEdicion();

        mensaje.innerHTML =
            '<span class="text-success">✅ Producto guardado correctamente.</span>';


        // Volver a cargar productos

        mostrarProductos();
        cargarProductosMovimiento();


    } catch (error) {

        console.error(
            "Error al guardar producto:",
            error
        );


        mensaje.innerHTML =
            '<span class="text-danger">Error al conectar con el servidor.</span>';

    }

});
// ==========================================
// ABRIR / CERRAR CAMBIO DE CONTRASEÑA
// ==========================================

function abrirCambioPassword() {

    document.getElementById("password-actual").value = "";
    document.getElementById("password-nueva").value = "";
    document.getElementById("mensaje-password").textContent = "";

    document.getElementById("modal-password").style.display = "flex";

}

function cerrarCambioPassword() {

    document.getElementById("modal-password").style.display = "none";

}


// ==========================================
// CAMBIAR CONTRASEÑA
// ==========================================

async function cambiarPassword() {

    const token = localStorage.getItem("token");

    const passwordActual =
        document.getElementById("password-actual").value;

    const passwordNueva =
        document.getElementById("password-nueva").value;

    const mensaje =
        document.getElementById("mensaje-password");


    if (!token) {
        alert("Primero debes iniciar sesión");
        return;
    }

    if (passwordActual === "" || passwordNueva === "") {
        mensaje.textContent = "Completa los dos campos";
        mensaje.className = "text-danger";
        return;
    }

    if (passwordNueva.length < 6) {
        mensaje.textContent =
            "La nueva contraseña debe tener al menos 6 caracteres";
        mensaje.className = "text-danger";
        return;
    }


    try {

        const respuesta = await fetch("/cambiar-password", {

            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },

            body: JSON.stringify({
                password_actual: passwordActual,
                password_nueva: passwordNueva
            })

        });

        const resultado = await respuesta.json();


        // Sesión vencida: volver al inicio
        if (respuesta.status === 401) {
            localStorage.removeItem("token");
            alert("Tu sesión expiró, inicia sesión de nuevo");
            location.reload();
            return;
        }


        if (!respuesta.ok) {

            mensaje.textContent =
                typeof resultado.detail === "string"
                    ? resultado.detail
                    : "Revisa los datos ingresados";

            mensaje.className = "text-danger";

            return;
        }


        mensaje.textContent = "✅ Contraseña actualizada correctamente";
        mensaje.className = "text-success";

        setTimeout(cerrarCambioPassword, 1500);

    } catch (error) {

        console.error("Error al cambiar contraseña:", error);

        mensaje.textContent = "Error al conectar con el servidor";
        mensaje.className = "text-danger";

    }
}
// ==========================================
// AL ABRIR LA PÁGINA
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    if (localStorage.getItem("token")) {

        configurarInterfazPorRol();

        document.getElementById("inicio").style.display = "none";

        document.getElementById("panel-principal").style.display = "block";

        mostrarProductos();

        cargarOpcionesProducto();

        cargarProductosMovimiento();

        cargarHistorialMovimientos();
    }

});

// ==========================================
// CARGAR CATEGORÍAS Y PROVEEDORES
// ==========================================

async function cargarOpcionesProducto() {

    const token = localStorage.getItem("token");

    if (!token) {
        return;
    }

    // ==========================================
    // CARGAR CATEGORÍAS
    // ==========================================

    try {

        const respuestaCategorias =
            await fetch("/categorias");

        const categorias =
            await respuestaCategorias.json();

        const selectCategoria =
            document.getElementById("categoria-producto");


        selectCategoria.innerHTML = `
            <option value="">
                Selecciona una categoría
            </option>
        `;


        categorias.forEach(function(categoria) {

            const opcion =
                document.createElement("option");

            opcion.value =
                categoria.id_categoria;

            opcion.textContent =
                categoria.nombre;

            selectCategoria.appendChild(opcion);

        });


    } catch (error) {

        console.error(
            "Error al cargar categorías:",
            error
        );

    }


    // ==========================================
    // CARGAR PROVEEDORES
    // ==========================================

    try {

        const respuestaProveedores =
            await fetch("/proveedores");

        const proveedores =
            await respuestaProveedores.json();

        const selectProveedor =
            document.getElementById("proveedor-producto");


        selectProveedor.innerHTML = `
            <option value="">
                Selecciona un proveedor
            </option>
        `;


        proveedores.forEach(function(proveedor) {

            const opcion =
                document.createElement("option");

            opcion.value =
                proveedor.id_proveedor;

            opcion.textContent =
                proveedor.nombre_empresa;

            selectProveedor.appendChild(opcion);

        });


    } catch (error) {

        console.error(
            "Error al cargar proveedores:",
            error
        );

    }

}

// ==========================================
// CARGAR CATEGORÍAS PARA ADMINISTRACIÓN
// ==========================================

async function cargarCategorias() {

    const token = localStorage.getItem("token");

    if (!token) {
        return;
    }

    const lista =
        document.getElementById("lista-categorias");

    if (!lista) {
        return;
    }

    try {

        const respuesta = await fetch("/categorias", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        const categorias = await respuesta.json();

        if (!respuesta.ok) {

            lista.innerHTML = `
                <p class="text-danger">
                    ${categorias.detail || "No se pudieron cargar las categorías"}
                </p>
            `;

            return;
        }

        lista.innerHTML = "";

        if (categorias.length === 0) {

            lista.innerHTML = `
                <p class="text-muted">
                    No hay categorías registradas.
                </p>
            `;

            return;
        }

        categorias.forEach(function(categoria) {

            lista.innerHTML += `
                <div class="border rounded p-3 mb-2">

                    <strong>
                        ${categoria.nombre}
                    </strong>

                    <br>

                    <span class="text-muted">
                        ${categoria.descripcion || "Sin descripción"}
                    </span>

                </div>
            `;

        });

    } catch (error) {

        console.error(
            "Error al cargar categorías:",
            error
        );

        lista.innerHTML = `
            <p class="text-danger">
                Error al conectar con el servidor.
            </p>
        `;
    }
}

// ==========================================
// CARGAR PRODUCTOS PARA MOVIMIENTOS
// ==========================================

async function cargarProductosMovimiento() {

    const token = localStorage.getItem("token");

    if (!token) {
        return;
    }

    try {

        const respuesta = await fetch("/productos", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

        const productos = await respuesta.json();

        const selectProducto =
            document.getElementById("movimiento-producto");

        selectProducto.innerHTML = `
            <option value="">
                Selecciona un producto
            </option>
        `;

        productos.forEach(function(producto) {

            const opcion = document.createElement("option");

            opcion.value = producto.id_producto;

            opcion.textContent =
                producto.nombre +
                " - Stock: " +
                producto.stock_actual;

            selectProducto.appendChild(opcion);

        });

    } catch (error) {

        console.error(
            "Error al cargar productos para movimiento:",
            error
        );

    }
}
// ==========================================
// CARGAR HISTORIAL DE MOVIMIENTOS
// ==========================================

async function cargarHistorialMovimientos() {

    const token = localStorage.getItem("token");

    if (!token) return;

    const tabla = document.getElementById("tabla-historial");

    try {

        const respuesta = await fetch("/movimientos", {
            method: "GET",
            headers: {
                "Authorization": "Bearer " + token
            }
        });

const movimientos = await respuesta.json();

if (!respuesta.ok) {
    tabla.innerHTML = `
        <tr>
            <td colspan="6" class="text-danger text-center">
                ${movimientos.detail || "No se pudo cargar el historial"}
            </td>
        </tr>
    `;
    return;
}

document.getElementById("total-movimientos").textContent =
    movimientos.length;

        if (movimientos.length === 0) {
            tabla.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center">
                        No hay movimientos registrados.
                    </td>
                </tr>
            `;
            return;
        }

        tabla.innerHTML = "";

        movimientos.forEach(function(movimiento) {

            tabla.innerHTML += `
                <tr>
                    <td>${movimiento.id_movimiento}</td>
                    <td>${movimiento.producto}</td>
                    <td>${movimiento.tipo_movimiento}</td>
                    <td>${movimiento.cantidad}</td>
                    <td>${movimiento.motivo || "Sin motivo"}</td>
                    <td>${movimiento.fecha_movimiento}</td>
                </tr>
            `;

        });

    } catch (error) {

        console.error("Error al cargar historial:", error);

        tabla.innerHTML = `
            <tr>
                <td colspan="6" class="text-danger text-center">
                    Error al conectar con el servidor.
                </td>
            </tr>
        `;
    }
}
// ==========================================
// REGISTRAR MOVIMIENTO DE INVENTARIO
// ==========================================

document.getElementById("form-movimiento").addEventListener("submit", async function(event) {

    event.preventDefault();

    const token = localStorage.getItem("token");

    const mensaje = document.getElementById("mensaje-movimiento");

    const id_producto = document.getElementById("movimiento-producto").value;
    const tipo_movimiento = document.getElementById("tipo-movimiento").value;
    const cantidad = document.getElementById("cantidad-movimiento").value;
    const motivo = document.getElementById("motivo-movimiento").value.trim();

    if (!token) {
        mensaje.textContent = "Primero debes iniciar sesión";
        return;
    }

    if (id_producto === "") {
        mensaje.textContent = "Selecciona un producto";
        return;
    }

    if (tipo_movimiento === "") {
        mensaje.textContent = "Selecciona un tipo de movimiento";
        return;
    }

    if (Number(localStorage.getItem("id_tipo_usuario")) === 3 &&
        tipo_movimiento === "SALIDA") {
        mensaje.textContent = "No tienes permiso para registrar salidas";
        return;
    }

    if (cantidad === "" || Number(cantidad) <= 0) {
        mensaje.textContent = "La cantidad debe ser mayor a 0";
        return;
    }

    try {

        const respuesta = await fetch("/movimientos", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },
            body: JSON.stringify({
                id_producto: Number(id_producto),
                tipo_movimiento: tipo_movimiento,
                cantidad: Number(cantidad),
                motivo: motivo
            })
        });

        const resultado = await respuesta.json();

        console.log("Respuesta del movimiento:", resultado);

        if (!respuesta.ok) {
            mensaje.innerHTML =
                `<span class="text-danger">
                    ${resultado.detail || "No se pudo registrar el movimiento"}
                </span>`;
            return;
        }

        mensaje.innerHTML =
            `<span class="text-success">
                ✅ Movimiento registrado correctamente.
                Stock: ${resultado.stock_anterior} → ${resultado.stock_nuevo}
            </span>`;

        document.getElementById("form-movimiento").reset();

        // Actualizar productos y existencias
        mostrarProductos();
        cargarProductosMovimiento();
        cargarHistorialMovimientos();

    } catch (error) {

        console.error("Error al registrar movimiento:", error);

        mensaje.innerHTML =
            `<span class="text-danger">
                Error al conectar con el servidor.
            </span>`;
    }
});// ==========================================
// RESUMEN DEL INVENTARIO
// ==========================================

function actualizarResumenInventario(productos) {

    const totalProductos =
        document.getElementById("total-productos");

    const totalStockBajo =
        document.getElementById("total-stock-bajo");

    const listaStockBajo =
        document.getElementById("lista-stock-bajo");


    // Total de productos
    totalProductos.textContent = productos.length;


    // Productos con stock bajo
    const productosBajos = productos.filter(function(producto) {

        return producto.stock_actual <= producto.stock_minimo;

    });


    totalStockBajo.textContent =
        productosBajos.length;


    // Limpiar lista
    listaStockBajo.innerHTML = "";


    if (productosBajos.length === 0) {

        listaStockBajo.innerHTML = `
            <p class="text-success">
                ✅ No hay productos con stock bajo.
            </p>
        `;

        return;
    }


    productosBajos.forEach(function(producto) {

        listaStockBajo.innerHTML += `
            <div class="border rounded p-3 mb-2">

                <strong>
                    ${producto.nombre}
                </strong>

                <br>

                <span>
                    Stock:
                    <strong>${producto.stock_actual}</strong>
                </span>

                <span class="text-muted">
                    / mínimo ${producto.stock_minimo}
                </span>

            </div>
        `;

    });

}
// ==========================================
// ELIMINAR PRODUCTO
// ==========================================

async function eliminarProducto(id) {

    if (Number(localStorage.getItem("id_tipo_usuario")) !== 1) {
        return;
    }

    if (!confirm("¿Seguro que quieres eliminar este producto?")) {
        return;
    }

    const token = localStorage.getItem("token");

    try {

        const respuesta = await fetch("/productos/" + id, {
            method: "DELETE",
            headers: { "Authorization": "Bearer " + token }
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            alert(resultado.detail || "No se pudo eliminar el producto");
            return;
        }

        mostrarProductos();
        cargarProductosMovimiento();

    } catch (error) {
        console.error("Error al eliminar producto:", error);
        alert("Error al conectar con el servidor");
    }
}


// ==========================================
// EDITAR PRODUCTO (carga los datos en el formulario)
// ==========================================

function editarProducto(id) {

    if (Number(localStorage.getItem("id_tipo_usuario")) !== 1) {
        return;
    }

    const producto = productosCargados.find(function (p) {
        return p.id_producto === id;
    });

    if (!producto) {
        alert("No se encontró el producto");
        return;
    }

    document.getElementById("id-producto").value = producto.id_producto;
    document.getElementById("codigo-barras").value = producto.codigo_barras || "";
    document.getElementById("nombre-producto").value = producto.nombre;
    document.getElementById("descripcion-producto").value = producto.descripcion || "";
    document.getElementById("categoria-producto").value = producto.id_categoria || "";
    document.getElementById("proveedor-producto").value = producto.id_proveedor || "";
    document.getElementById("precio-compra").value = producto.precio_compra;
    document.getElementById("precio-venta").value = producto.precio_venta;
    document.getElementById("stock-actual").value = producto.stock_actual;
    document.getElementById("stock-minimo").value = producto.stock_minimo;

    // El stock solo se cambia con movimientos, para que quede en el historial
    document.getElementById("stock-actual").disabled = true;

    document.querySelector("#form-producto button[type='submit']").textContent =
        "💾 Guardar cambios";

    document.getElementById("btn-cancelar-edicion").style.display = "inline-block";

    document.getElementById("mensaje-producto").innerHTML = "";

    document.getElementById("form-producto").scrollIntoView({ behavior: "smooth" });
}


// ==========================================
// CANCELAR EDICIÓN
// ==========================================

function cancelarEdicion() {

    document.getElementById("form-producto").reset();

    document.getElementById("id-producto").value = "";

    document.getElementById("stock-actual").disabled = false;

    document.querySelector("#form-producto button[type='submit']").textContent =
        "💾 Registrar producto";

    document.getElementById("btn-cancelar-edicion").style.display = "none";
}
// ==========================================
// MOSTRAR / OCULTAR CONTRASEÑA
// ==========================================

function alternarPassword(idInput, boton) {

    const input = document.getElementById(idInput);

    if (input.type === "password") {

        input.type = "text";
        boton.textContent = "🙈";

    } else {

        input.type = "password";
        boton.textContent = "👁️";

    }
}
// ==========================================
// TIENDA: CATÁLOGO Y CARRITO
// ==========================================

let carrito = {};


function escaparHtml(texto) {
    return String(texto)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}


function formatoDinero(centavos) {
    return "$" + (centavos / 100).toFixed(2);
}


// ==========================================
// MOSTRAR EL CATÁLOGO
// ==========================================

function mostrarCatalogo(productos) {

    const tabla = document.getElementById("tabla-catalogo");

    if (!tabla || !Array.isArray(productos)) {
        return;
    }

    if (productos.length === 0) {

        tabla.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">
                    No hay productos disponibles.
                </td>
            </tr>
        `;

        return;
    }

    tabla.innerHTML = "";

    productos.forEach(function(producto) {

        const sinStock = producto.stock_actual <= 0;

        const fila = document.createElement("tr");

        fila.innerHTML = `

            <td>
                <strong>${escaparHtml(producto.nombre)}</strong>
            </td>

            <td>
                $${Number(producto.precio_venta).toFixed(2)}
            </td>

            <td>
                ${sinStock
                    ? '<span class="text-danger">Agotado</span>'
                    : producto.stock_actual}
            </td>

            <td style="width:110px;">
                <input
                    type="number"
                    id="cant-${producto.id_producto}"
                    class="form-control form-control-sm"
                    min="1"
                    max="${producto.stock_actual}"
                    value="1"
                    ${sinStock ? "disabled" : ""}>
            </td>

            <td>
                <button
                    type="button"
                    class="btn btn-sm btn-primary"
                    onclick="agregarAlCarrito(${producto.id_producto})"
                    ${sinStock ? "disabled" : ""}>

                    Agregar

                </button>
            </td>

        `;

        tabla.appendChild(fila);

    });
}


// ==========================================
// AGREGAR AL CARRITO
// ==========================================

function agregarAlCarrito(id) {

    const mensaje = document.getElementById("mensaje-venta");

    const producto = productosCargados.find(function(p) {
        return p.id_producto === id;
    });

    if (!producto) {
        return;
    }

    const cantidad =
        Number(document.getElementById("cant-" + id).value);

    if (!Number.isInteger(cantidad) || cantidad < 1) {

        mensaje.innerHTML =
            '<span class="text-danger">La cantidad debe ser un número entero mayor a 0.</span>';

        return;
    }

    const enCarrito = carrito[id] ? carrito[id].cantidad : 0;

    if (enCarrito + cantidad > producto.stock_actual) {

        mensaje.innerHTML =
            `<span class="text-danger">
                Solo hay ${producto.stock_actual} piezas de
                ${escaparHtml(producto.nombre)}
                (ya tienes ${enCarrito} en el carrito).
            </span>`;

        return;
    }

    carrito[id] = {
        id_producto: id,
        nombre: producto.nombre,
        precio: Number(producto.precio_venta),
        cantidad: enCarrito + cantidad
    };

    document.getElementById("cant-" + id).value = 1;

    mensaje.innerHTML = "";

    mostrarCarrito();
}


// ==========================================
// QUITAR DEL CARRITO / VACIARLO
// ==========================================

function quitarDelCarrito(id) {

    delete carrito[id];

    mostrarCarrito();
}


function vaciarCarrito() {

    carrito = {};

    document.getElementById("mensaje-venta").innerHTML = "";

    mostrarCarrito();
}


// ==========================================
// MOSTRAR EL CARRITO Y LOS TOTALES
// (el cálculo se hace en centavos para evitar errores de decimales)
// ==========================================

function mostrarCarrito() {

    const contenedor = document.getElementById("carrito-items");

    const items = Object.values(carrito);

    let subtotal = 0;

    if (items.length === 0) {

        contenedor.innerHTML =
            '<p class="text-muted">Tu carrito está vacío.</p>';

    } else {

        contenedor.innerHTML = "";

        items.forEach(function(item) {

            const importe =
                Math.round(item.precio * 100) * item.cantidad;

            subtotal += importe;

            contenedor.innerHTML += `

                <div class="d-flex justify-content-between align-items-center mb-2">

                    <div>
                        <strong>${escaparHtml(item.nombre)}</strong>
                        <br>
                        <small class="text-muted">
                            ${item.cantidad} × $${item.precio.toFixed(2)}
                        </small>
                    </div>

                    <div>
                        <span class="me-2">${formatoDinero(importe)}</span>

                        <button
                            type="button"
                            class="btn btn-sm btn-outline-danger"
                            onclick="quitarDelCarrito(${item.id_producto})">

                            ✕

                        </button>
                    </div>

                </div>

            `;

        });
    }

    const iva = Math.round(subtotal * 0.16);

    document.getElementById("carrito-subtotal").textContent =
        formatoDinero(subtotal);

    document.getElementById("carrito-iva").textContent =
        formatoDinero(iva);

    document.getElementById("carrito-total").textContent =
        formatoDinero(subtotal + iva);
}


// ==========================================
// CONFIRMAR PEDIDO
// ==========================================

async function confirmarPedido() {

    const token = localStorage.getItem("token");

    const mensaje = document.getElementById("mensaje-venta");

    const items = Object.values(carrito);

    if (!token) {
        alert("Primero debes iniciar sesión");
        return;
    }

    if (items.length === 0) {

        mensaje.innerHTML =
            '<span class="text-danger">Tu carrito está vacío.</span>';

        return;
    }

    const datos = {
        items: items.map(function(item) {
            return {
                id_producto: item.id_producto,
                cantidad: item.cantidad
            };
        })
    };

    try {

        const respuesta = await fetch("/ventas", {

            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token
            },

            body: JSON.stringify(datos)

        });

        const resultado = await respuesta.json();

        // Sesión vencida: volver al inicio
        if (respuesta.status === 401) {
            localStorage.removeItem("token");
            alert("Tu sesión expiró, inicia sesión de nuevo");
            location.reload();
            return;
        }

        if (!respuesta.ok) {

            mensaje.innerHTML =
                `<span class="text-danger">
                    ${typeof resultado.detail === "string"
                        ? escaparHtml(resultado.detail)
                        : "No se pudo registrar el pedido"}
                </span>`;

            return;
        }

        mensaje.innerHTML =
            `<span class="text-success">
                ✅ Pedido #${resultado.id_venta} confirmado.
                Subtotal $${resultado.subtotal.toFixed(2)} +
                IVA $${resultado.iva.toFixed(2)} =
                <strong>Total $${resultado.total.toFixed(2)}</strong>
            </span>`;

        carrito = {};

        mostrarCarrito();

        // Actualizar existencias en pantalla
        mostrarProductos();
        cargarProductosMovimiento();
        cargarHistorialMovimientos();

    } catch (error) {

        console.error("Error al confirmar el pedido:", error);

        mensaje.innerHTML =
            '<span class="text-danger">Error al conectar con el servidor.</span>';
    }
}
// ==========================================
// DESCARGAR REPORTES (CSV, EXCEL Y PDF)
// El token viaja en un header, por eso se usa fetch
// y se baja el archivo como blob
// ==========================================

async function descargarReporte(tipo, formato) {

    const token = localStorage.getItem("token");

    if (!token) {
        alert("Primero debes iniciar sesión");
        return;
    }

    try {

        const respuesta = await fetch(
            `/reportes/${tipo}?formato=${formato}`,
            {
                method: "GET",
                headers: {
                    "Authorization": "Bearer " + token
                }
            }
        );

        // Sesión vencida: volver al inicio
        if (respuesta.status === 401) {
            localStorage.removeItem("token");
            alert("Tu sesión expiró, inicia sesión de nuevo");
            location.reload();
            return;
        }

        if (!respuesta.ok) {

            let detalle = "No se pudo generar el reporte";

            try {
                const error = await respuesta.json();

                if (typeof error.detail === "string") {
                    detalle = error.detail;
                }
            } catch (e) {
                // la respuesta no era JSON, se deja el mensaje por defecto
            }

            alert(detalle);
            return;
        }

        const archivo = await respuesta.blob();

        const url = URL.createObjectURL(archivo);

        const enlace = document.createElement("a");
        enlace.href = url;
        enlace.download = `reporte_${tipo}.${formato}`;

        document.body.appendChild(enlace);
        enlace.click();
        enlace.remove();

        URL.revokeObjectURL(url);

    } catch (error) {

        console.error("Error al descargar el reporte:", error);

        alert("Error al conectar con el servidor");
    }
}