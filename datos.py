"""Almacenamiento CSV de Mini Vegetales Zeledón (sin base de datos SQL)."""
import csv
import hashlib
import hmac
import os
import re
import secrets
import threading
import uuid
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOCK = threading.RLock()

COLUMNAS = {
    'usuarios.csv': ['id_usuario', 'nombre', 'correo', 'contrasena_hash', 'rol', 'fecha_registro'],
    'productos.csv': ['id_producto', 'nombre', 'descripcion', 'precio', 'imagen', 'activo'],
    # Campos extra: los pedidos sin registro requieren los datos de contacto y entrega.
    'pedidos.csv': ['id_pedido', 'id_usuario', 'cliente_nombre', 'cliente_correo',
                    'cliente_telefono', 'metodo_entrega', 'direccion_entrega',
                    'notas', 'fecha', 'total', 'estado'],
    'detalle_pedidos.csv': ['id_pedido', 'id_producto', 'cantidad', 'precio_unitario', 'subtotal'],
}

INICIALES = [
    {'id_producto': 'P001', 'nombre': 'Mini vegetales variados',
     'descripcion': 'Bandeja de mini vegetales surtidos.', 'precio': '2600',
     'imagen': 'producto_variado.webp', 'activo': '1'},
    {'id_producto': 'P002', 'nombre': 'Mini zuquinis',
     'descripcion': 'Bandeja de mini zuquinis frescos.', 'precio': '2500',
     'imagen': 'producto_zuquinis.webp', 'activo': '1'},
    {'id_producto': 'P003', 'nombre': 'Chilotes',
     'descripcion': 'Bandeja de chilotes frescos.', 'precio': '2000',
     'imagen': 'producto_chilotes.webp', 'activo': '1'},
]


def iniciar_csv():
    with LOCK:
        for filename, columnas in COLUMNAS.items():
            ruta = BASE / filename
            if not ruta.exists():
                with ruta.open('w', newline='', encoding='utf-8') as archivo:
                    csv.DictWriter(archivo, fieldnames=columnas).writeheader()
        if not leer('productos.csv'):
            guardar('productos.csv', INICIALES)


def leer(filename):
    if filename not in COLUMNAS:
        raise ValueError('CSV desconocido')
    with LOCK:
        path = BASE / filename
        if not path.exists():
            return []
        with path.open('r', newline='', encoding='utf-8') as archivo:
            return list(csv.DictReader(archivo))


def guardar(filename, filas):
    """Reemplazo atómico: conserva el CSV anterior si la escritura se interrumpe."""
    if filename not in COLUMNAS:
        raise ValueError('CSV desconocido')
    with LOCK:
        ruta = BASE / filename
        tmp = ruta.with_suffix(ruta.suffix + '.tmp')
        try:
            with tmp.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNAS[filename])
                writer.writeheader()
                writer.writerows(filas)
            os.replace(tmp, ruta)
        finally:
            if tmp.exists():
                tmp.unlink()


def productos(solo_activos=True):
    filas = leer('productos.csv')
    return [p for p in filas if not solo_activos or p.get('activo') == '1']


def producto_por_id(producto_id):
    return next((p for p in productos() if p['id_producto'] == producto_id), None)


def actualizar_producto(producto_id, nombre, descripcion, precio, activo, imagen=None):
    nombre = nombre.strip()
    descripcion = descripcion.strip()
    if not nombre or not descripcion:
        raise ValueError('Nombre y descripción son obligatorios.')
    try:
        precio = int(precio)
    except (TypeError, ValueError) as exc:
        raise ValueError('El precio debe ser un número entero.') from exc
    if precio <= 0:
        raise ValueError('El precio debe ser mayor que cero.')
    with LOCK:
        items = leer('productos.csv')
        encontrado = False
        for item in items:
            if item['id_producto'] == producto_id:
                item.update(nombre=nombre, descripcion=descripcion,
                            precio=str(precio), activo='1' if activo else '0')
                if imagen is not None:
                    # Solo nombres locales, nunca rutas arbitrarias.
                    if Path(imagen).name != imagen or '/' in imagen or '\\' in imagen:
                        raise ValueError('La imagen no es válida.')
                    item['imagen'] = imagen
                encontrado = True
        if not encontrado:
            raise ValueError('Producto no encontrado.')
        guardar('productos.csv', items)


def correo_valido(correo):
    return bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', correo.strip()))


def hash_clave(clave):
    sal = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', clave.encode('utf-8'), sal, 260000)
    return 'pbkdf2_sha256$260000$' + sal.hex() + '$' + digest.hex()


def verificar_clave(clave, almacenada):
    try:
        algoritmo, vueltas, sal, esperado = almacenada.split('$')
        if algoritmo != 'pbkdf2_sha256':
            return False
        digest = hashlib.pbkdf2_hmac('sha256', clave.encode('utf-8'),
                                    bytes.fromhex(sal), int(vueltas))
        return hmac.compare_digest(digest, bytes.fromhex(esperado))
    except (ValueError, TypeError):
        return False


def crear_usuario(nombre, correo, clave, rol='cliente'):
    nombre = nombre.strip()
    correo = correo.strip().lower()
    if len(nombre) < 3 or len(nombre) > 100:
        raise ValueError('Escribí tu nombre completo.')
    if not correo_valido(correo):
        raise ValueError('Escribí un correo válido.')
    if len(clave) < 8:
        raise ValueError('La contraseña debe tener al menos 8 caracteres.')
    if rol not in ('cliente', 'admin'):
        raise ValueError('Rol desconocido.')
    with LOCK:
        filas = leer('usuarios.csv')
        if any(u['correo'].lower() == correo for u in filas):
            raise ValueError('Este correo ya está registrado.')
        nuevo = {'id_usuario': uuid.uuid4().hex[:12], 'nombre': nombre, 'correo': correo,
                 'contrasena_hash': hash_clave(clave), 'rol': rol,
                 'fecha_registro': datetime.now().isoformat(timespec='seconds')}
        filas.append(nuevo)
        guardar('usuarios.csv', filas)
    return {k: v for k, v in nuevo.items() if k != 'contrasena_hash'}


def autenticar(correo, clave):
    correo = correo.strip().lower()
    usuario = next((u for u in leer('usuarios.csv') if u['correo'] == correo), None)
    if not usuario or not verificar_clave(clave, usuario['contrasena_hash']):
        return None
    return {k: v for k, v in usuario.items() if k != 'contrasena_hash'}


def total_carrito(carrito):
    """Calcula precios SIEMPRE desde productos.csv, no desde el navegador."""
    total = 0
    detalle = []
    for id_producto, cantidad in carrito.items():
        p = producto_por_id(id_producto)
        if not p:
            raise ValueError('Uno de los productos ya no está disponible.')
        try:
            cantidad = int(cantidad)
        except (ValueError, TypeError) as exc:
            raise ValueError('La cantidad no es válida.') from exc
        if cantidad < 1 or cantidad > 100:
            raise ValueError('La cantidad debe estar entre 1 y 100.')
        precio = int(p['precio'])
        detalle.append({'id_producto': id_producto, 'nombre': p['nombre'],
                        'cantidad': cantidad, 'precio_unitario': precio,
                        'subtotal': precio * cantidad, 'imagen': p['imagen']})
        total += precio * cantidad
    return total, detalle


def crear_pedido(carrito, cliente_nombre, cliente_correo, cliente_telefono,
                 metodo_entrega, direccion_entrega='', notas='', id_usuario=''):
    cliente_nombre = cliente_nombre.strip()
    cliente_correo = cliente_correo.strip().lower()
    cliente_telefono = re.sub(r'[^\d]', '', cliente_telefono)
    metodo_entrega = metodo_entrega.strip()
    direccion_entrega = direccion_entrega.strip()
    if len(cliente_nombre) < 3 or not correo_valido(cliente_correo):
        raise ValueError('Completá tu nombre y correo electrónico.')
    if len(cliente_telefono) != 8:
        raise ValueError('Escribí un teléfono de 8 dígitos de Costa Rica.')
    if metodo_entrega not in ('Retiro', 'Entrega a domicilio'):
        raise ValueError('Elegí retiro o entrega a domicilio.')
    if metodo_entrega == 'Entrega a domicilio' and not direccion_entrega:
        raise ValueError('Escribí la dirección de entrega.')
    if len(notas) > 500 or len(direccion_entrega) > 400:
        raise ValueError('Los campos de dirección o notas son demasiado largos.')
    if not carrito:
        raise ValueError('Agregá productos antes de confirmar.')
    with LOCK:
        total, detalle = total_carrito(carrito)
        numero = f'MVZ-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}'
        nuevo = {'id_pedido': numero, 'id_usuario': id_usuario,
                 'cliente_nombre': cliente_nombre, 'cliente_correo': cliente_correo,
                 'cliente_telefono': cliente_telefono, 'metodo_entrega': metodo_entrega,
                 'direccion_entrega': direccion_entrega, 'notas': notas.strip(),
                 'fecha': datetime.now().isoformat(timespec='seconds'),
                 'total': str(total), 'estado': 'pendiente'}
        filas = leer('pedidos.csv')
        filas.append(nuevo)
        lineas = leer('detalle_pedidos.csv')
        for item in detalle:
            lineas.append({'id_pedido': numero, 'id_producto': item['id_producto'],
                           'cantidad': str(item['cantidad']),
                           'precio_unitario': str(item['precio_unitario']),
                           'subtotal': str(item['subtotal'])})
        # Dos CSV: si hay un fallo de disco inesperado, restauramos el archivo de pedidos.
        guardar('detalle_pedidos.csv', lineas)
        guardar('pedidos.csv', filas)
        return nuevo


def cambiar_estado_pedido(numero, estado):
    if estado not in ('pendiente', 'confirmado', 'entregado', 'cancelado'):
        raise ValueError('Estado incorrecto.')
    with LOCK:
        pedidos = leer('pedidos.csv')
        encontrado = False
        for p in pedidos:
            if p['id_pedido'] == numero:
                p['estado'] = estado
                encontrado = True
        if not encontrado:
            raise ValueError('Pedido inexistente.')
        guardar('pedidos.csv', pedidos)


def resumen():
    ps, us, pedidos = productos(), leer('usuarios.csv'), leer('pedidos.csv')
    ventas = sum(int(p['total']) for p in pedidos if p['estado'] in ('confirmado', 'entregado'))
    return {'productos': len(ps), 'clientes': sum(u['rol'] == 'cliente' for u in us),
            'pedidos': len(pedidos), 'ventas': ventas,
            'pendientes': sum(p['estado'] == 'pendiente' for p in pedidos)}


if __name__ == '__main__':
    iniciar_csv()
    print('Los archivos CSV están listos.')
