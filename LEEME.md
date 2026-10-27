# Mini Vegetales Zeledón 🌱

Proyecto académico de tienda web construido con **Python + NiceGUI + archivos CSV**. Se inspira en las seis pantallas de la plantilla diseñada en Canva y reutiliza sus imágenes originales (extraídas del PDF aportado).

## 1. Cómo abrirlo en Visual Studio Code (Mac)

1. Descomprimí el ZIP y abrí la carpeta `Mini_Vegetales_Zeledon_NiceGUI` en Visual Studio Code.
2. Abrí **Terminal → Nueva terminal**.
3. Escribí los comandos (uno por línea):

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

4. Visitá **http://localhost:8080** en Chrome.
5. Para detener la app, presioná `Ctrl + C` en la terminal.

**Si ya instalaste NiceGUI**, podés ir directo a `python3 main.py`. Si el puerto 8080 está ocupado, cerrá la otra aplicación o cambiá el parámetro `port` en la última línea de `main.py`.

## 2. Crear el administrador

La aplicación **no trae una contraseña administrativa predeterminada**. Configurá tu propia cuenta en una terminal local (dentro de la carpeta del proyecto y con el entorno virtual activo):

```bash
python3 main.py --crear-admin
```

Ingresá nombre, correo y contraseña (mínimo 8 caracteres). Después ejecutá `python3 main.py`, iniciá sesión y entrá a **Administración**.

> El comando para crear administradores se debe ejecutar solamente en tu computadora. No creés contraseñas reales dentro de un repositorio público.

## 3. Pantallas y funcionalidades

- **Inicio:** menú, logotipo, banner, frase y tarjetas de presentación.
- **Productos:** listado de tres productos (₡2.600, ₡2.500, ₡2.000), fotografías circulares y botones reales para agregar al carrito.
- **Carrito:** sumar/restar unidades, quitar productos y calcular totales según `productos.csv`.
- **Pedido:** compra como invitado (sin registro obligatorio) o con sesión iniciada. Recoge nombre, correo, teléfono y modalidad de entrega (retiro/domicilio). Guarda el pedido con estado **pendiente**, sin procesar pagos.
- **Registro e inicio de sesión:** alta de clientes con verificación y contraseñas cifradas con hash PBKDF2 y sal individual, inicio/cierre de sesión y roles.
- **Contacto:** enlaces a WhatsApp de Valeria y Nelson Fabián.
- **Administración:** tarjetas resumen, edición de los productos existentes (nombre, descripción, precio, foto y activo/inactivo), consulta de clientes y pedidos, y gestión del estado de pedidos.

## 4. Archivos CSV

- `usuarios.csv`: usuarios y hashes de contraseña.
- `productos.csv`: catálogo inicial.
- `pedidos.csv`: datos generales y contacto/entrega de los pedidos.
- `detalle_pedidos.csv`: cantidades y precios por producto en cada pedido.

Los CSV se crean automáticamente si no existen. Están preparados para **uso académico/local de un solo proceso**. No son apropiados para publicar una tienda con muchos usuarios concurrentes sin mejoras adicionales de seguridad y persistencia.

## 5. Decisiones que faltan confirmar

**Notificación por correo:** tu documento dice «Un correo electrónico…», pero no especifica un correo receptor ni si debe enviarse automáticamente. Por eso, esta versión **guarda el pedido en `pedidos.csv` para consultarlo desde administración**, pero no envía correos.

**Cobro:** todavía no hay métodos de pago definidos. No se cobran tarjetas ni se solicita información bancaria.

**Entrega:** por ahora se selecciona «Retiro» o «Entrega a domicilio»; el costo de entrega se coordina después, no se suma al total de productos.

**Recuperar contraseña:** no se habilitó el envío de enlaces de recuperación porque falta configurar un proveedor de correo seguro. Hay un enlace a Contacto para solicitar asistencia. No se muestran contraseñas.

## 6. Estructura sencilla

```text
Mini_Vegetales_Zeledon_NiceGUI/
  main.py                # Páginas y botones NiceGUI
  datos.py               # Funciones de archivos CSV y seguridad
  requirements.txt
  LEEME.md
  productos.csv
  usuarios.csv
  pedidos.csv
  detalle_pedidos.csv
  assets/                # Logotipo y fotos extraídas del PDF
```

En el primer inicio también se crea `.session_secret` para firmar las sesiones de los usuarios. Guardalo privado y no lo subás a GitHub. Recomendación: agregar `.session_secret`, `.venv/` y archivos CSV con datos personales a `.gitignore` antes de publicarlo.

## 7. Cómo revisar en clase

1. Abrí Inicio y pasá a Productos.
2. Agregá dos bandejas de mini vegetales variados y una de chilotes.
3. Entrá al Carrito y verificá el total: **₡7.200**.
4. Elegí Retiro y registrá un pedido con datos de prueba.
5. Ingresá como administrador y confirmá el pedido desde el panel.
6. Consultá el resultado en `pedidos.csv` y `detalle_pedidos.csv`.

**Estado de pruebas:** se probaron por ejecución real las operaciones de los CSV, hash/verificación de contraseñas, registro, duplicados, creación de pedidos, cálculos y estados, y se comprobó que los archivos Python compilan. **No se pudo arrancar ni probar visualmente NiceGUI en este entorno**, porque la biblioteca no estaba instalada y no había acceso de red para instalarla. El código fue construido contrastando su uso con la documentación oficial de NiceGUI.
