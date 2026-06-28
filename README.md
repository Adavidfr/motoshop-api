me dio esto <div align="center">

<img src="https://ute.edu.ec/wp-content/uploads/2021/08/LogoUteTrans.png" alt="UTE - Escuela de Tecnologías" width="250"/>

</div>

<hr>
<br>

<div style="border-left: 4px solid #1e88e5; padding-left: 15px; margin-top: 20px;">

<p><strong>Universidad Tecnológica Equinoccial</strong></p>

<p><strong>Escuela de Tecnologías</strong></p>

<p><strong>Carrera:</strong> Desarrollo de Software</p>

<p><strong>Asignatura:</strong> Programación IV</p>

</div>

<br><br>

<p><strong>Tema:</strong> SEMINARIO DE INTEGRACIÓN - Construcción de Backend Django.</p>

<br>

<p><strong>Fecha:</strong> 03/06/2026</p>

<p><strong>Presentado por:</strong></p>

<ul>
  <li>Alquinga Carlos</li>
  <li>Andrés Zambrano</li>
  <li>Melanie Estévez</li>
  <li>David Frias</li>
</ul>

<p><strong>Docente:</strong> Francisco Javier Higuera González </p>

<hr>

# Venta de Motos - API

<br>

<div align="center">

<h2>Sistema Backend para la Gestión de Venta de Motos</h2>

<p>
API REST desarrollada con Django, Django REST Framework y PostgreSQL para administrar los procesos principales de una empresa dedicada a la venta, abastecimiento, inventario, mantenimiento y gestión financiera de motos.
</p>

</div>

<br>

<hr>

<div style="border-left: 4px solid #1e88e5; padding-left: 15px; margin-top: 20px;">

<h2>Descripción del Proyecto</h2>


<p>
Venta de Motos API es un backend desarrollado con Django y Django REST Framework para administrar
los procesos de una empresa dedicada a la venta de motos. El sistema integra inventario,
abastecimiento, taller, ventas y módulos administrativos mediante una API REST.
</p>


</div>

<br>

<div style="border-left: 4px solid #43a047; padding-left: 15px; margin-top: 20px;">

<h2>Objetivo General</h2>

<p>
Desarrollar una API REST para un sistema de venta de motos utilizando Django, Django REST Framework y PostgreSQL, permitiendo la gestión estructurada de inventario, abastecimiento, taller, ventas, finanzas y administración del sistema.
</p>

</div>

<br>

<div style="border-left: 4px solid #fb8c00; padding-left: 15px; margin-top: 20px;">

<h2>Tecnologías Utilizadas</h2>

<table>
  <tr>
    <th>Tecnología</th>
    <th>Uso dentro del proyecto</th>
  </tr>
  <tr>
    <td>Python</td>
    <td>Lenguaje principal de desarrollo backend.</td>
  </tr>
  <tr>
    <td>Django</td>
    <td>Framework principal para la construcción del proyecto.</td>
  </tr>
  <tr>
    <td>Django REST Framework</td>
    <td>Construcción de la API REST.</td>
  </tr>
  <tr>
    <td>PostgreSQL</td>
    <td>Motor de base de datos relacional.</td>
  </tr>
  <tr>
    <td>Simple JWT</td>
    <td>Autenticación basada en tokens JWT.</td>
  </tr>
  <tr>
    <td>django-filter</td>
    <td>Filtros avanzados para los endpoints.</td>
  </tr>
  <tr>
    <td>Postman</td>
    <td>Pruebas de endpoints y validación del CRUD.</td>
  </tr>
  <tr>
    <td>Git y GitHub</td>
    <td>Control de versiones y trabajo colaborativo.</td>
  </tr>
</table>

</div>

<br>

<div style="border-left: 4px solid #7a39ab; padding-left: 15px; margin-top: 20px;">

<h2>Estructura General del Proyecto</h2>

<pre>
motoshop-api/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│
├── motoshop/
│   ├── models/
│   ├── serializers/
│   ├── views/
│   ├── migrations/
│   ├── filters.py
│   ├── permissions.py
│   ├── pagination.py
│   ├── urls.py
│
├── manage.py
├── requirements.txt
└── README.md
</pre>

</div>

<br>

<div style="border-left: 4px solid #00897b; padding-left: 15px; margin-top: 20px;">

<h2>Modelado de Datos</h2>

<p>
El sistema cuenta con un modelo relacional compuesto por más de 20 tablas, distribuidas por módulos funcionales. Las relaciones fueron diseñadas considerando integridad referencial, llaves foráneas, campos obligatorios, campos opcionales y restricciones propias del dominio del negocio.
</p>

<h3>Tabla central de autenticación</h3>

<ul>
  <li>auth</li>
</ul>

<h3>Catálogo e Inventario</h3>

<ul>
  <li>marcas</li>
  <li>categorias_moto</li>
  <li>motos</li>
  <li>repuestos</li>
  <li>movimientos_inventario</li>
</ul>

<h3>Abastecimiento y Taller</h3>

<ul>
  <li>proveedores</li>
  <li>compras</li>
  <li>servicios</li>
  <li>mantenimientos</li>
  <li>repuestos_mantenimiento</li>
</ul>

<h3>Ventas</h3>

<ul>
  <li>clientes_perfil</li>
  <li>carrito_compras</li>
  <li>items_carrito</li>
  <li>pedidos</li>
  <li>ventas</li>
  <li>financiamientos</li>
</ul>

<h3>Financiero, Legal y Sistema</h3>

<ul>
  <li>pagos</li>
  <li>facturas</li>
  <li>garantias</li>
  <li>seguros</li>
  <li>notificaciones</li>
  <li>documentos_venta</li>
  <li>historial_estado_venta</li>
  <li>devoluciones</li>
</ul>

</div>

<br>

<div style="border-left: 4px solid #6d4c41; padding-left: 15px; margin-top: 20px;">

<h2>Relaciones Principales</h2>

<table>
  <tr>
    <th>Relación</th>
    <th>Descripción</th>
  </tr>
  <tr>
    <td>motos - categorias_moto</td>
    <td>Cada moto pertenece a una categoría.</td>
  </tr>
  <tr>
    <td>motos - marcas</td>
    <td>Cada moto pertenece a una marca.</td>
  </tr>
  <tr>
    <td>compras - proveedores</td>
    <td>Cada compra se asocia a un proveedor.</td>
  </tr>
  <tr>
    <td>compras - motos</td>
    <td>Una compra puede registrar la adquisición de una moto.</td>
  </tr>
  <tr>
    <td>compras - repuestos</td>
    <td>Una compra puede registrar la adquisición de un repuesto.</td>
  </tr>
  <tr>
    <td>mantenimientos - motos</td>
    <td>Cada mantenimiento pertenece a una moto.</td>
  </tr>
  <tr>
    <td>mantenimientos - servicios</td>
    <td>Cada mantenimiento se relaciona con un servicio.</td>
  </tr>
  <tr>
    <td>repuestos_mantenimiento - mantenimientos</td>
    <td>Permite registrar los repuestos utilizados durante un mantenimiento.</td>
  </tr>
  <tr>
    <td>ventas - pedidos</td>
    <td>Cada venta se genera a partir de un pedido.</td>
  </tr>
  <tr>
    <td>pagos - ventas</td>
    <td>Cada pago se asocia a una venta.</td>
  </tr>
</table>

</div>

<br>

<div style="border-left: 4px solid #c62828; padding-left: 15px; margin-top: 20px;">

<h2>Desarrollo de la API REST</h2>

<p>
La API REST fue implementada utilizando ViewSets, Routers y Serializers de Django REST Framework. Las principales entidades del sistema cuentan con operaciones CRUD completas.
</p>

<h3>Endpoints CRUD generales</h3>

<pre>
GET     /api/recurso/
GET     /api/recurso/{id}/
POST    /api/recurso/
PUT     /api/recurso/{id}/
PATCH   /api/recurso/{id}/
DELETE  /api/recurso/{id}/
</pre>

</div>

<br>

<div style="border-left: 4px solid #1565c0; padding-left: 15px; margin-top: 20px;">

<h2>Serializers</h2>

<p>
Los serializers permiten transformar los modelos en datos JSON y validar la información recibida desde el cliente antes de ser almacenada en la base de datos.
</p>

<p>Entre sus funciones se incluyen:</p>

<ul>
  <li>Validación de campos obligatorios.</li>
  <li>Validación de tipos de datos.</li>
  <li>Transformación de objetos a JSON.</li>
  <li>Validación personalizada según reglas de negocio.</li>
</ul>

<p>
Por ejemplo, en el módulo de compras se valida que se seleccione una moto o un repuesto, evitando registros incompletos o inconsistentes.
</p>

</div>

<br>

<div style="border-left: 4px solid #2e7d32; padding-left: 15px; margin-top: 20px;">

<h2>Búsqueda, Paginación y Ordenamiento</h2>

<p>
La API implementa funcionalidades adicionales para facilitar el consumo de datos desde clientes externos.
</p>

<h3>Búsqueda</h3>

<pre>
GET /api/proveedores/?search=yamaha
GET /api/servicios/?search=aceite
GET /api/compras/?search=recibida
</pre>

<h3>Paginación</h3>

<pre>
GET /api/proveedores/?page=2
GET /api/servicios/?page=2
GET /api/compras/?page=2
</pre>

<h3>Ordenamiento</h3>

<pre>
GET /api/proveedores/?ordering=nombre
GET /api/servicios/?ordering=precio_base
GET /api/compras/?ordering=-fecha_compra
</pre>

</div>

<br>

<div style="border-left: 4px solid #ef6c00; padding-left: 15px; margin-top: 20px;">

<h2>Manejo de Errores</h2>

<p>
La API responde de forma adecuada ante errores comunes durante el consumo de los endpoints.
</p>

<table>
  <tr>
    <th>Código</th>
    <th>Descripción</th>
  </tr>
  <tr>
    <td>400 Bad Request</td>
    <td>Solicitud incorrecta o datos inválidos.</td>
  </tr>
  <tr>
    <td>401 Unauthorized</td>
    <td>Usuario no autenticado.</td>
  </tr>
  <tr>
    <td>403 Forbidden</td>
    <td>Usuario sin permisos suficientes.</td>
  </tr>
  <tr>
    <td>404 Not Found</td>
    <td>Recurso no encontrado.</td>
  </tr>
  <tr>
    <td>500 Internal Server Error</td>
    <td>Error interno del servidor.</td>
  </tr>
</table>

</div>

<br>

<div style="border-left: 4px solid #4527a0; padding-left: 15px; margin-top: 20px;">

<h2>Autenticación y Autorización</h2>

<p>
El sistema implementa autenticación basada en JWT utilizando <strong>djangorestframework-simplejwt</strong>.
</p>

<h3>Registro de usuarios</h3>

<pre>
POST /api/auth/register/
</pre>

<h3>Inicio de sesión</h3>

<pre>
POST /api/auth/login/
</pre>

<h3>Respuesta esperada</h3>

<pre>
{
  "access": "...",
  "refresh": "..."
}
</pre>

<h3>Renovación de token</h3>

<pre>
POST /api/auth/token/refresh/
</pre>

<h3>Cierre de sesión</h3>

<pre>
POST /api/auth/logout/
</pre>

</div>

<br>

<div style="border-left: 4px solid #ad1457; padding-left: 15px; margin-top: 20px;">

<h2>Roles y Permisos</h2>

<p>
El sistema utiliza permisos personalizados y grupos de Django para controlar el acceso a los recursos.
</p>

<table>
  <tr>
    <th>Rol</th>
    <th>Permisos</th>
  </tr>
  <tr>
    <td>Usuario</td>
    <td>Puede consultar información y acceder a funcionalidades permitidas.</td>
  </tr>
  <tr>
    <td>Administrador</td>
    <td>Puede crear, actualizar, eliminar registros y gestionar usuarios.</td>
  </tr>
</table>

<p>
Las operaciones de creación, actualización y eliminación requieren autenticación y permisos adecuados.
</p>

</div>

<br>

<div style="border-left: 4px solid #00838f; padding-left: 15px; margin-top: 20px;">

<h2>Instalación y Ejecución</h2>

<h3>Clonar el repositorio</h3>

<pre>
git clone URL_DEL_REPOSITORIO
cd motoshop-api
</pre>

<h3>Crear y activar entorno virtual</h3>

<pre>
python -m venv .venv
.venv\Scripts\activate
</pre>

<h3>Instalar dependencias</h3>

<pre>
pip install -r requirements.txt
</pre>

<h3>Aplicar migraciones</h3>

<pre>
python manage.py migrate
</pre>

<h3>Crear superusuario</h3>

<pre>
python manage.py createsuperuser
</pre>

<h3>Ejecutar servidor</h3>

<pre>
python manage.py runserver
</pre>

</div>

<br>

<div style="border-left: 4px solid #5d4037; padding-left: 15px; margin-top: 20px;">

<h2>Pruebas con Postman</h2>

<p>
Los endpoints fueron probados utilizando Postman. Para consumir los endpoints protegidos es necesario iniciar sesión y enviar el token de acceso en la cabecera de autorización.
</p>

<h3>Header requerido</h3>

<pre>
Authorization: Bearer TOKEN_DE_ACCESO
Content-Type: application/json
</pre>

<h3>Ejemplo de creación de proveedor</h3>

<pre>
POST /api/proveedores/

{
  "nombre": "Yamaha Ecuador",
  "contacto": "Carlos Pérez",
  "telefono": "0991234567",
  "correo": "ventas@yamaha.com",
  "direccion": "Quito",
  "estado": true
}
</pre>

</div>

<br>

<div style="border-left: 4px solid #607d8b; padding-left: 15px; margin-top: 20px;">

<h2>Organización del Equipo</h2>

<table>
  <tr>
    <th>Integrante</th>
    <th>Módulo asignado</th>
  </tr>
  <tr>
    <td>Andrés</td>
    <td>Catálogo e Inventario</td>
  </tr>
  <tr>
    <td>Melanie</td>
    <td>Abastecimiento y Taller</td>
  </tr>
  <tr>
    <td>David</td>
    <td>Ventas</td>
  </tr>
  <tr>
    <td>Carlos</td>
    <td>Financiero, Legal y Sistema</td>
  </tr>
</table>

</div>

<br>

<div style="border-left: 4px solid #1e88e5; padding-left: 15px; margin-top: 20px;">

<h2>Estado del Proyecto</h2>

<ul>
  <li>Proyecto Django configurado.</li>
  <li>Base de datos PostgreSQL implementada.</li>
  <li>Modelos relacionales creados.</li>
  <li>Migraciones generadas y aplicadas.</li>
  <li>API REST construida con Django REST Framework.</li>
  <li>Autenticación JWT implementada.</li>
  <li>Permisos por roles configurados.</li>
  <li>CRUD implementado para las entidades principales.</li>
  <li>Filtros, búsqueda, paginación y ordenamiento implementados.</li>
</ul>

</div>

<br>

<hr>

<div align="center">

<p><strong>Venta de Motos - API</strong></p>

<p>Backend desarrollado con Django REST Framework</p>

<p>Universidad Tecnológica Equinoccial - Escuela de Tecnologías</p>

</div>