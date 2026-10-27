"""Tienda web Mini Vegetales Zeledón - Python + NiceGUI + archivos CSV.

Ejecutar: python3 main.py
Crear un administrador localmente: python3 main.py --crear-admin
"""
import getpass
import inspect
import os
import re
import secrets
import sys
import uuid
from pathlib import Path
from urllib.parse import quote

from nicegui import app, ui
import datos

BASE = Path(__file__).resolve().parent
ASSETS = BASE / 'assets'
datos.iniciar_csv()
app.add_static_files('/assets', ASSETS)

ESTADOS = ['pendiente', 'confirmado', 'entregado', 'cancelado']

CSS = '''
:root { --verde:#2d592f; --lima:#abc72c; --crema:#faf8f4; --tierra:#ad7e5c; }
body { background: var(--crema); color:#25362a; font-family: Arial, Helvetica, sans-serif; }
.q-page { background: var(--crema); }
.page-wrap { max-width:1200px; margin:0 auto; width:100%; padding:18px 30px 55px; }
.site-header { width:100%; padding:13px 3%; background:white; display:flex; flex-wrap:wrap;
  justify-content:space-between; align-items:center; gap:12px; border-bottom:1px solid #eae8e0; }
.brand { font-family: Georgia,serif; font-size:clamp(19px,2.4vw,30px); letter-spacing:2px;
 color:#1f2c20; font-weight:500; text-decoration:none; }
.nav-links { display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
.nav-a { color:#a06c41; font-weight:bold; text-decoration:none; text-transform:uppercase;
 letter-spacing:1px; font-size:12px; padding:10px 9px; }
.nav-a:hover { color:#395e25; }
.heading { font-family:Georgia,serif; font-weight:normal; color:#244b30; line-height:1.2; }
.subtitle { color:#6e756e; font-size:15px; }
.hero { background-image:url('/assets/portada.webp'); background-position:center center;
 background-size:cover; width:100%; min-height:355px; display:flex; align-items:end;
 justify-content:center; padding:26px; border-radius:3px; }
.hero-text { background:#faf9f5f0; color:#223b24; padding:17px 25px; font-family:Georgia,serif;
 font-size:clamp(21px,2.3vw,30px); line-height:1.35; text-align:center; max-width:650px;
 border-radius:4px; box-shadow:0 9px 28px #122c181a; }
.promo-card { background:white; border:1px solid #ece9e1; border-radius:12px;
 overflow:hidden; box-shadow:0 8px 24px #223c2410; }
.product-card { background:white; border:1px solid #ece9e1; padding:25px 19px; border-radius:18px;
 min-width:240px; flex:1; text-align:center; box-shadow:0 12px 35px #223c2410; }
.product-photo { width:200px; height:200px; object-fit:cover; border-radius:50%;
 border:3px solid #638035; margin:0 auto 18px; }
.action-green { background:#abc72c !important; color:#19331c !important; border-radius:10px !important;
 font-weight:700 !important; }
.outline-green { color:#2d592f !important; border:1px solid #99b368 !important;
 background:white !important; border-radius:10px !important; }
.summary-card { border:1px solid #dce6c7; background:#f0f5e6; border-radius:20px;
 padding:25px; }
.item-card { background:#fff; border:1px solid #e3e2db; border-radius:16px; padding:17px; }
.field { width:100%; }
.footer { width:100%; margin-top:42px; padding:24px; border-top:1px solid #e2e5d9;
 color:#7a8477; text-align:center; font-size:13px; }
.login-visual { min-height:610px; background:url('/assets/login_frase.webp') center/cover no-repeat; }
.login-panel { padding:35px 25px; background:white; }
.contact-visual { min-height:390px; background:url('/assets/login_fondo.webp') center/cover no-repeat;
 display:flex; align-items:center; padding:35px; border-radius:12px; }
@media(max-width:700px) {
 .page-wrap { padding:13px 12px 35px; }
 .site-header { justify-content:center; }
 .hero { min-height:250px; padding:10px; }
 .nav-links { justify-content:center; }
 .nav-a { font-size:10px; padding:5px; }
 .product-photo { width:165px; height:165px; }
 .login-visual { min-height:250px; }
}
'''


def dinero(valor):
    return f'₡{int(valor):,}'.replace(',', '.')


def sesion():
    return app.storage.user.get('usuario') or {}


def es_admin():
    return sesion().get('rol') == 'admin'


def carrito():
    return dict(app.storage.user.get('carrito', {}))


def guardar_carrito(contenido):
    app.storage.user['carrito'] = contenido


def imagen(nombre):
    return '/assets/' + Path(nombre).name


def preparar_pagina():
    ui.colors(primary='#a9c52e', secondary='#315938', dark='#203726', positive='#39844b')
    ui.add_css(CSS)


def encabezado():
    with ui.row().classes('site-header'):
        with ui.row().classes('items-center gap-2'):
            ui.image(imagen('logo.webp')).classes('w-14 h-14 rounded-full')
            ui.link('Mini vegetales Zeledón', '/').classes('brand')
        with ui.row().classes('nav-links'):
            for texto, destino in [('Inicio', '/'), ('Productos', '/productos'),
                                    ('Carrito', '/carrito'), ('Contacto', '/contacto')]:
                ui.link(texto, destino).classes('nav-a')
            usuario = sesion()
            if usuario:
                if es_admin():
                    ui.link('Administración', '/administracion').classes('nav-a')
                ui.link('Mi cuenta', '/cuenta').classes('nav-a')
            else:
                ui.link('Iniciar sesión', '/iniciar-sesion').classes('nav-a')


def pie():
    ui.label('Mini vegetales Zeledón · Creemos en lo natural · Costa Rica 🌱').classes('footer')


def boton(texto, accion, icono=None):
    return ui.button(texto, on_click=accion, icon=icono).classes('action-green')


def agregar_producto(pid):
    if not datos.producto_por_id(pid):
        ui.notify('Producto no disponible.', color='negative')
        return
    actual = carrito()
    actual[pid] = min(100, int(actual.get(pid, 0)) + 1)
    guardar_carrito(actual)
    ui.notify('Producto agregado al carrito 🌱', color='positive')


@ui.page('/', title='Mini vegetales Zeledón | Inicio')
def inicio():
    preparar_pagina()
    encabezado()
    with ui.column().classes('page-wrap gap-5'):
        with ui.element('section').classes('hero'):
            ui.label('Creemos en lo natural. Cultivamos vida, cosechamos bienestar. 🌱💚').classes('hero-text')
        with ui.row().classes('w-full justify-between gap-5 flex-wrap'):
            bloques = [
                ('filosofia_1.webp', 'Frescura para compartir', 'Vegetales seleccionados para tu hogar.'),
                ('filosofia_2.webp', 'Creemos en lo natural', 'Cuidamos los pequeños detalles de cada cosecha.'),
                ('filosofia_3.webp', 'Pequeños espacios, grandes cambios', 'Disfrutá el sabor de la huerta.'),
            ]
            for archivo, titulo, descripcion in bloques:
                with ui.column().classes('promo-card flex-1 min-w-60 gap-0'):
                    ui.image(imagen(archivo)).classes('w-full').style('height:230px;object-fit:cover;')
                    with ui.column().classes('p-4 gap-2'):
                        ui.label(titulo).classes('heading text-xl')
                        ui.label(descripcion).classes('subtitle')
        with ui.row().classes('items-center justify-center gap-4 w-full mt-3 flex-wrap'):
            boton('Conocer nuestros productos', lambda: ui.navigate.to('/productos'), 'shopping_basket')
            ui.button('Contactanos', on_click=lambda: ui.navigate.to('/contacto')).classes('outline-green')
        pie()


@ui.page('/productos', title='Mini vegetales Zeledón | Productos')
def pagina_productos():
    preparar_pagina()
    encabezado()
    with ui.column().classes('page-wrap gap-4'):
        ui.label('Nuestros productos').classes('heading text-5xl mt-5')
        ui.label('Bandejas de vegetales frescos para disfrutar en casa.').classes('subtitle mb-5')
        with ui.row().classes('w-full gap-5 flex-wrap items-stretch'):
            items = datos.productos()
            if not items:
                ui.label('Por el momento no hay productos disponibles.')
            for p in items:
                with ui.column().classes('product-card items-center justify-start gap-2'):
                    ui.image(imagen(p['imagen'])).classes('product-photo')
                    ui.label(p['nombre']).classes('heading text-2xl')
                    ui.label(p['descripcion']).classes('subtitle text-center')
                    ui.label(dinero(p['precio'])).classes('text-2xl font-bold mt-2 text-green-900')
                    boton('Agregar al carrito', lambda pid=p['id_producto']: agregar_producto(pid), 'add_shopping_cart').classes('w-48 mt-3')
        with ui.row().classes('justify-center w-full mt-5'):
            ui.button('Ver mi carrito', icon='shopping_cart',
                      on_click=lambda: ui.navigate.to('/carrito')).classes('outline-green')
        pie()


@ui.page('/carrito', title='Mini vegetales Zeledón | Carrito')
def pagina_carrito():
    preparar_pagina()
    encabezado()
    with ui.column().classes('page-wrap gap-2'):
        ui.label('Tu carrito de compras').classes('heading text-5xl mt-5')
        ui.label('Revisá los productos seleccionados antes de realizar tu pedido.').classes('subtitle mb-5')

        def variar(pid, cambio):
            c = carrito()
            n = int(c.get(pid, 0)) + cambio
            if n <= 0:
                c.pop(pid, None)
            else:
                c[pid] = min(n, 100)
            guardar_carrito(c)
            contenido.refresh()

        def eliminar(pid):
            c = carrito()
            c.pop(pid, None)
            guardar_carrito(c)
            contenido.refresh()

        @ui.refreshable
        def contenido():
            c = carrito()
            if not c:
                with ui.column().classes('w-full items-center p-12 bg-white rounded-xl gap-4'):
                    ui.icon('remove_shopping_cart', size='xl', color='green')
                    ui.label('Tu carrito está vacío.').classes('heading text-2xl')
                    boton('Ir a productos', lambda: ui.navigate.to('/productos'))
                return
            try:
                total, detalle = datos.total_carrito(c)
            except ValueError as e:
                ui.notify(str(e), color='negative')
                boton('Actualizar productos', lambda: ui.navigate.to('/productos'))
                return
            with ui.row().classes('w-full gap-6 flex-wrap items-start'):
                with ui.column().classes('gap-3 flex-1 min-w-72'):
                    ui.label('PRODUCTOS AGREGADOS').classes('text-green-900 font-bold tracking-wider')
                    for d in detalle:
                        with ui.row().classes('item-card w-full items-center justify-between flex-wrap gap-2'):
                            with ui.row().classes('items-center gap-3'):
                                ui.image(imagen(d['imagen'])).classes('w-16 h-16 rounded-full')
                                with ui.column().classes('gap-1'):
                                    ui.label(d['nombre']).classes('heading text-xl')
                                    ui.label(dinero(d['precio_unitario']) + ' cada uno').classes('subtitle')
                            with ui.row().classes('items-center gap-1'):
                                ui.button('-', on_click=lambda pid=d['id_producto']: variar(pid, -1)).props('flat dense')
                                ui.label(str(d['cantidad'])).classes('font-bold')
                                ui.button('+', on_click=lambda pid=d['id_producto']: variar(pid, 1)).props('flat dense')
                                ui.label(dinero(d['subtotal'])).classes('font-bold ml-3')
                                ui.button(icon='delete_outline',
                                          on_click=lambda pid=d['id_producto']: eliminar(pid)).props('flat round dense color=negative')
                with ui.column().classes('summary-card gap-4').style('width: min(100%, 350px);'):
                    ui.label('Resumen del pedido').classes('heading text-3xl')
                    ui.separator()
                    with ui.row().classes('w-full justify-between'):
                        ui.label('Total de productos')
                        ui.label(dinero(total)).classes('text-xl font-bold text-green-900')
                    ui.label('Retiro o entrega por coordinar. No se cobra en línea.').classes('subtitle')
                    boton('Continuar con el pedido', lambda: ui.navigate.to('/pedido')).classes('w-full')
                    ui.button('Seguir comprando', on_click=lambda: ui.navigate.to('/productos')).props('flat')
        contenido()
        pie()


@ui.page('/pedido', title='Mini vegetales Zeledón | Realizar pedido')
def pagina_pedido():
    preparar_pagina()
    encabezado()
    if not carrito():
        ui.navigate.to('/carrito')
        return
    with ui.column().classes('page-wrap items-center gap-4'):
        ui.label('Confirmá tu pedido').classes('heading text-4xl mt-5')
        ui.label('Podés comprar sin registrarte. Guardaremos la solicitud como pendiente.').classes('subtitle')
        with ui.card().classes('w-full max-w-xl p-6 gap-4'):
            usuario = sesion()
            nombre = ui.input('Nombre completo *', value=usuario.get('nombre', '')).classes('field').props('outlined')
            correo = ui.input('Correo electrónico *', value=usuario.get('correo', '')).classes('field').props('outlined')
            telefono = ui.input('Teléfono (8 dígitos) *').classes('field').props('outlined')
            metodo = ui.select(['Retiro', 'Entrega a domicilio'], value='Retiro', label='Modalidad *').classes('field').props('outlined')
            direccion = ui.textarea('Dirección de entrega (solo si elegís domicilio)').classes('field').props('outlined')
            notas = ui.textarea('Indicaciones adicionales (opcional)').classes('field').props('outlined')
            try:
                total, _ = datos.total_carrito(carrito())
                ui.label('Total de productos: ' + dinero(total)).classes('text-xl text-green-900 font-bold')
            except ValueError as e:
                ui.label(str(e)).classes('text-red-600')

            def terminar():
                try:
                    pedido = datos.crear_pedido(
                        carrito(), nombre.value or '', correo.value or '', telefono.value or '',
                        metodo.value or '', direccion.value or '', notas.value or '',
                        usuario.get('id_usuario', ''))
                except ValueError as exc:
                    ui.notify(str(exc), color='negative', timeout=5000)
                    return
                guardar_carrito({})
                app.storage.user['ultimo_pedido'] = pedido['id_pedido']
                ui.navigate.to('/confirmacion')

            boton('Registrar mi pedido', terminar, 'check_circle').classes('w-full')
            ui.label('No solicitamos números de tarjeta. La entrega y el pago se coordinan después.').classes('subtitle')
        pie()


@ui.page('/confirmacion', title='Mini vegetales Zeledón | Pedido registrado')
def pagina_confirmacion():
    preparar_pagina()
    encabezado()
    with ui.column().classes('page-wrap items-center gap-5 py-16'):
        ui.icon('verified', color='green', size='5rem')
        ui.label('¡Recibimos tu pedido!').classes('heading text-5xl text-center')
        numero = app.storage.user.get('ultimo_pedido')
        if numero:
            ui.label('Número de referencia: ' + numero).classes('font-bold text-xl')
        ui.label('Tu solicitud quedó pendiente. La entrega y el pago todavía deben coordinarse.').classes('subtitle text-center')
        boton('Volver al inicio', lambda: ui.navigate.to('/'))
        pie()


@ui.page('/contacto', title='Mini vegetales Zeledón | Contacto')
def pagina_contacto():
    preparar_pagina()
    encabezado()
    with ui.column().classes('page-wrap gap-4'):
        ui.label('Estamos para ayudarte').classes('heading text-5xl mt-5')
        ui.label('Consultá disponibilidad, precios y cómo realizar tu pedido.').classes('subtitle mb-3')
        with ui.row().classes('w-full gap-6 items-stretch flex-wrap'):
            with ui.column().classes('contact-visual flex-1 min-w-72 gap-4'):
                ui.label('Mini vegetales Zeledón').classes('heading text-4xl text-white')
                ui.label('Productos frescos para compartir en familia.').classes('text-white text-lg')
            with ui.column().classes('flex-1 min-w-72 gap-4'):
                ui.label('Contacto directo').classes('heading text-3xl')
                ui.label('Podés comunicarte por llamada o WhatsApp:').classes('subtitle')
                for nombre, telefono in [
                    ('Valeria de los Ángeles Alvarado Ureña', '85026198'),
                    ('Nelson Fabián Zeledón Hernandes', '72945504'),
                ]:
                    with ui.column().classes('item-card w-full gap-2'):
                        ui.label(nombre).classes('font-bold text-lg')
                        ui.label('+506 ' + telefono[:4] + '-' + telefono[4:]).classes('text-green-900 text-lg')
                        boton('Abrir WhatsApp', lambda n=telefono: ui.navigate.to(
                            'https://wa.me/506' + n + '?text=' + quote('Hola, me gustaría consultar sobre Mini Vegetales Zeledón.')),
                            'chat').classes('self-end')
                ui.label('Será un gusto atenderte. 🌱').classes('subtitle')
        pie()


@ui.page('/registro', title='Mini vegetales Zeledón | Registro')
def pagina_registro():
    preparar_pagina()
    encabezado()
    with ui.column().classes('page-wrap items-center gap-4'):
        ui.label('Crear cuenta nueva').classes('heading text-4xl mt-6')
        ui.label('Registrarte es opcional: también podés comprar como invitado.').classes('subtitle')
        with ui.card().classes('w-full max-w-md p-7 gap-4'):
            nombre = ui.input('Nombre completo').classes('field').props('outlined')
            correo = ui.input('Correo electrónico').classes('field').props('outlined')
            clave = ui.input('Contraseña', password=True, password_toggle_button=True).classes('field').props('outlined')
            repetir = ui.input('Confirmar contraseña', password=True).classes('field').props('outlined')

            def registrar():
                if clave.value != repetir.value:
                    ui.notify('Las contraseñas no coinciden.', color='negative')
                    return
                try:
                    u = datos.crear_usuario(nombre.value or '', correo.value or '', clave.value or '')
                except ValueError as exc:
                    ui.notify(str(exc), color='negative')
                    return
                app.storage.user['usuario'] = u
                ui.notify('¡Cuenta creada exitosamente!', color='positive')
                ui.navigate.to('/productos')

            boton('Crear mi cuenta', registrar).classes('w-full')
            ui.link('¿Ya tenés cuenta? Iniciar sesión', '/iniciar-sesion').classes('text-green-800')
        pie()


@ui.page('/iniciar-sesion', title='Mini vegetales Zeledón | Iniciar sesión')
def pagina_login():
    preparar_pagina()
    encabezado()
    with ui.row().classes('w-full flex-wrap min-h-[75vh] items-stretch gap-0'):
        with ui.column().classes('login-visual flex-1 min-w-72'):
            pass
        with ui.column().classes('login-panel items-center justify-center flex-1 min-w-72 gap-5'):
            ui.image(imagen('logo.webp')).classes('w-28 h-28')
            ui.label('¡Bienvenido de nuevo!').classes('heading text-4xl text-center')
            correo = ui.input('Correo electrónico').classes('field max-w-md').props('outlined')
            clave = ui.input('Contraseña', password=True, password_toggle_button=True).classes('field max-w-md').props('outlined')

            def entrar():
                u = datos.autenticar(correo.value or '', clave.value or '')
                if not u:
                    ui.notify('Correo o contraseña incorrectos.', color='negative')
                    return
                app.storage.user['usuario'] = u
                ui.navigate.to('/administracion' if u['rol'] == 'admin' else '/productos')

            boton('Iniciar sesión', entrar).classes('w-full max-w-xs')
            ui.link('¿Todavía no tenés una cuenta? Regístrate', '/registro').classes('text-green-800')
            ui.link('¿Necesitás ayuda con tu acceso? Contactanos', '/contacto').classes('text-gray-600')
    pie()


@ui.page('/cuenta', title='Mini vegetales Zeledón | Mi cuenta')
def pagina_cuenta():
    preparar_pagina()
    encabezado()
    with ui.column().classes('page-wrap gap-4'):
        user = sesion()
        if not user:
            ui.label('Iniciá sesión para ver tu cuenta.').classes('subtitle')
            boton('Iniciar sesión', lambda: ui.navigate.to('/iniciar-sesion'))
            return
        ui.label('Mi cuenta').classes('heading text-4xl mt-5')
        ui.label(f"Hola, {user['nombre']}").classes('text-xl')
        ui.label(user['correo']).classes('subtitle')

        def salir():
            app.storage.user.pop('usuario', None)
            ui.navigate.to('/')
        boton('Cerrar sesión', salir, 'logout')
        pie()


@ui.page('/administracion', title='Mini vegetales Zeledón | Administración')
def pagina_administracion():
    preparar_pagina()
    if not es_admin():
        ui.label('Acceso restringido. Iniciá sesión como administrador.').classes('m-10 text-red-700')
        ui.link('Iniciar sesión', '/iniciar-sesion')
        return
    encabezado()
    with ui.column().classes('page-wrap gap-5'):
        ui.label('Panel de administración').classes('heading text-5xl mt-5')
        with ui.tabs().classes('w-full') as tabs:
            t_res = ui.tab('Resumen')
            t_pro = ui.tab('Productos')
            t_ped = ui.tab('Pedidos')
            t_cli = ui.tab('Clientes')
        with ui.tab_panels(tabs, value=t_res).classes('w-full rounded-xl'):
            with ui.tab_panel(t_res):
                r = datos.resumen()
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    for titulo, valor in [
                        ('Productos disponibles', r['productos']),
                        ('Clientes registrados', r['clientes']),
                        ('Pedidos registrados', r['pedidos']),
                        ('Pedidos pendientes', r['pendientes']),
                        ('Ventas confirmadas / entregadas', dinero(r['ventas'])),
                    ]:
                        with ui.column().classes('summary-card flex-1 min-w-44 gap-2'):
                            ui.label(titulo).classes('subtitle')
                            ui.label(str(valor)).classes('heading text-3xl')
                ui.label('Las ventas excluyen pedidos pendientes y cancelados.').classes('subtitle mt-4')
            with ui.tab_panel(t_pro):
                ui.label('Editar productos').classes('heading text-3xl mb-3')
                for p in datos.productos(solo_activos=False):
                    with ui.expansion(f"{p['nombre']} · {dinero(p['precio'])}", icon='edit').classes('w-full border rounded-lg mb-3'):
                        with ui.row().classes('w-full flex-wrap gap-4'):
                            ui.image(imagen(p['imagen'])).classes('w-32 h-32 rounded-full')
                            with ui.column().classes('flex-1 min-w-64 gap-2'):
                                nombre = ui.input('Nombre', value=p['nombre']).classes('field')
                                descripcion = ui.input('Descripción', value=p['descripcion']).classes('field')
                                precio = ui.number('Precio (₡)', value=int(p['precio']), min=1, precision=0).classes('field')
                                activo = ui.checkbox('Producto visible', value=p['activo'] == '1')

                                def guardar_cambios(pid=p['id_producto'], a=nombre, b=descripcion, c=precio, d=activo):
                                    try:
                                        datos.actualizar_producto(pid, a.value or '', b.value or '', c.value, d.value)
                                        ui.notify('Producto actualizado.', color='positive')
                                        ui.navigate.reload()
                                    except ValueError as exc:
                                        ui.notify(str(exc), color='negative')

                                boton('Guardar cambios', guardar_cambios, 'save')

                                async def subir(e, pid=p['id_producto']):
                                    contenido = e.file.read()
                                    if inspect.isawaitable(contenido):
                                        contenido = await contenido
                                    if len(contenido) > 2_000_000:
                                        ui.notify('La imagen supera 2 MB.', color='negative')
                                        return
                                    if contenido.startswith(b'\x89PNG\r\n\x1a\n'):
                                        extension = '.png'
                                    elif contenido.startswith(b'\xff\xd8\xff'):
                                        extension = '.jpg'
                                    elif contenido[:4] == b'RIFF' and contenido[8:12] == b'WEBP':
                                        extension = '.webp'
                                    else:
                                        ui.notify('Solo imágenes PNG, JPG o WEBP.', color='negative')
                                        return
                                    nombre_imagen = 'producto_' + uuid.uuid4().hex[:12] + extension
                                    (ASSETS / nombre_imagen).write_bytes(contenido)
                                    original = next(x for x in datos.productos(False) if x['id_producto'] == pid)
                                    datos.actualizar_producto(pid, original['nombre'], original['descripcion'],
                                                             original['precio'], original['activo'] == '1', nombre_imagen)
                                    ui.notify('Fotografía actualizada.', color='positive')
                                    ui.navigate.reload()

                                ui.label('Reemplazar fotografía (máximo 2 MB)').classes('subtitle')
                                ui.upload(on_upload=subir, max_file_size=2_000_000,
                                          on_rejected=lambda: ui.notify('Archivo demasiado grande.', color='negative'),
                                          auto_upload=True).props('accept=.png,.jpg,.jpeg,.webp').classes('w-full')
            with ui.tab_panel(t_ped):
                ui.label('Pedidos recibidos').classes('heading text-3xl')
                pedidos = sorted(datos.leer('pedidos.csv'), key=lambda x: x['fecha'], reverse=True)
                if not pedidos:
                    ui.label('Todavía no hay pedidos.').classes('subtitle')
                for p in pedidos:
                    with ui.expansion(f"{p['id_pedido']} · {p['cliente_nombre']} · {dinero(p['total'])}",
                                      icon='receipt_long').classes('w-full border rounded-xl my-2'):
                        ui.label(f"Contacto: {p['cliente_correo']} · {p['cliente_telefono']}")
                        ui.label(f"Entrega: {p['metodo_entrega']}")
                        if p['direccion_entrega']:
                            ui.label('Dirección: ' + p['direccion_entrega'])
                        if p['notas']:
                            ui.label('Notas: ' + p['notas'])
                        ui.label('Fecha: ' + p['fecha'])
                        lineas = [d for d in datos.leer('detalle_pedidos.csv') if d['id_pedido'] == p['id_pedido']]
                        for d in lineas:
                            nombre_producto = next((x['nombre'] for x in datos.productos(False)
                                                    if x['id_producto'] == d['id_producto']), d['id_producto'])
                            ui.label(f"{nombre_producto} · {d['cantidad']} × {dinero(d['precio_unitario'])} = {dinero(d['subtotal'])}")
                        estado = ui.select(ESTADOS, value=p['estado'], label='Estado del pedido').classes('w-52')

                        def cambiar_estado(numero=p['id_pedido'], control=estado):
                            try:
                                datos.cambiar_estado_pedido(numero, control.value)
                                ui.notify('Estado actualizado.', color='positive')
                                ui.navigate.reload()
                            except ValueError as exc:
                                ui.notify(str(exc), color='negative')
                        boton('Guardar estado', cambiar_estado, 'save')
            with ui.tab_panel(t_cli):
                ui.label('Clientes registrados').classes('heading text-3xl mb-3')
                clientes = [u for u in datos.leer('usuarios.csv') if u['rol'] == 'cliente']
                for c in clientes:
                    with ui.row().classes('item-card w-full justify-between items-center flex-wrap'):
                        ui.label(c['nombre']).classes('font-semibold')
                        ui.label(c['correo']).classes('subtitle')
                        ui.label(c['fecha_registro']).classes('subtitle')
                if not clientes:
                    ui.label('Todavía no hay clientes registrados.').classes('subtitle')
        pie()


def secreto_servidor():
    """Clave persistente para cookies firmadas (no compartir el archivo generado)."""
    archivo = BASE / '.session_secret'
    if not archivo.exists():
        archivo.write_text(secrets.token_urlsafe(48), encoding='utf-8')
        try:
            archivo.chmod(0o600)
        except OSError:
            pass
    return archivo.read_text(encoding='utf-8').strip()


def alta_administrador():
    print('\n--- Crear administrador de Mini Vegetales Zeledón ---')
    nombre = input('Nombre: ')
    correo = input('Correo: ')
    clave = getpass.getpass('Contraseña (mínimo 8 caracteres): ')
    try:
        datos.crear_usuario(nombre, correo, clave, rol='admin')
        print('Administrador creado. Ya podés iniciar sesión.\n')
    except ValueError as exc:
        print('No se pudo crear:', exc)


if __name__ in {'__main__', '__mp_main__'}:
    if '--crear-admin' in sys.argv:
        alta_administrador()
    else:
        ui.run(title='Mini vegetales Zeledón', favicon='/assets/logo.webp',
               storage_secret=secreto_servidor(), host='127.0.0.1', port=8080, reload=False)
