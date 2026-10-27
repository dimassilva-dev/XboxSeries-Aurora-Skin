"""Versões da skin em outros idiomas (en-US e es).

A skin final é gerada em pt-BR; este script troca os textos fixos das telas (propriedade Text, inclusive nos
quadros-chave), os rótulos desenhados nas imagens (abertura e fundo dos detalhes) e o skin.meta.
O inglês vem da tabela pt-BR invertida (os textos originais das skins); o espanhol está em ES abaixo.

uso: python i18n.py <XboxSeries.xzp em pt-BR> <saida.xzp> en|es
"""
import io, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xzp import parse
import xur5
from ptbr import T

# textos extras (só nas telas da NXE), inglês -> pt-BR; mesma tabela do merge_nxe
EXTRA_PT = {
    'Avatar as Profile Picture': 'Avatar como foto do perfil', 'Cheats': 'Trapaças', 'Move': 'Mover',
    'Letterbox on 4:3 Screen': 'Faixas pretas em tela 4:3', 'NXE Stage & Rings': 'Palco e anéis NXE',
    'Profile & Disc Panel': 'Painel de perfil e disco', 'Run Main.lua on Boot': 'Executar Main.lua ao iniciar',
    'Start': 'Iniciar', 'Warning': 'Aviso', 'Unity Marketplace': 'Unity Marketplace',
}

ES = {
    '(hold) Details': '(mantener) Detalles', '(hold) Launch': '(mantener) Iniciar', '0 of 0': '0 de 0',
    '1 of 2': '1 de 2', '2 of 2': '2 de 2', '4 Compatible': '4 compatibles', '[None]': '[Ninguno]',
    'Abort': 'Cancelar', 'About': 'Acerca de', 'Achievements': 'Logros', 'Activate': 'Activar',
    'Activator': 'Activador', 'Active Quick View': 'Vista rápida activa', 'Add': 'Añadir',
    'Adjust Animation': 'Ajustar animación', 'Adjust Overscan': 'Ajustar sobrebarrido',
    'Always Load On Boot': 'Cargar siempre al iniciar', 'Animation': 'Animación', 'API Key': 'Clave de API',
    'Applications': 'Aplicaciones', 'Apply': 'Aplicar', 'As Background': 'Usar como fondo',
    'Ascending': 'Ascendente', 'Assets': 'Recursos', 'Auto Disc Swap': 'Cambio de disco automático',
    'Auto Sign In': 'Inicio de sesión automático', 'AutoScan': 'Escaneo automático', 'Available': 'Disponible',
    'Avatar as Profile Picture': 'Avatar como foto de perfil', 'Back': 'Atrás', 'Back Button': 'Botón Atrás',
    'Background': 'Fondo', 'Backgrounds': 'Fondos', 'Behavior': 'Comportamiento', 'Binaries': 'Binarios',
    'Block Back Button Usage': 'Bloquear el botón Atrás', 'Blue': 'Azul', 'Boxart': 'Portadas',
    'Broadcast Port': 'Puerto de difusión', 'Broadcast Port Reachable': 'Puerto de difusión accesible',
    'Browse': 'Explorar', 'Change': 'Cambiar', 'Change Icon': 'Cambiar icono',
    'Changes Detected': 'Cambios detectados', 'Cheat List': 'Lista de trucos', 'Cheats': 'Trucos',
    'Clear All': 'Borrar todo', 'Compatible Title Updates': 'Actualizaciones compatibles',
    'Computer Name': 'Nombre del equipo', 'Config App': 'Configurar app', 'Configure': 'Configurar',
    'Configure Modules': 'Configurar módulos', 'Content': 'Contenido', 'Content Patching': 'Parche de contenido',
    'Copy': 'Copiar', 'Cover Layout': 'Diseño de portadas', 'Create Folder': 'Crear carpeta',
    'Credentials': 'Credenciales', 'Current Console': 'Consola actual', 'Custom [Not Set]': 'Personalizado [sin definir]',
    'DashLaunch Not Active': 'DashLaunch no activo', 'DashLaunch Settings': 'Ajustes de DashLaunch',
    'Data Port': 'Puerto de datos', 'Data Port Reachable': 'Puerto de datos accesible', 'Default': 'Predeterminado',
    'Default Title': 'Título predeterminado', 'Delete': 'Eliminar', 'Delete Content': 'Eliminar contenido',
    'Depth': 'Profundidad', 'Descending': 'Descendente', 'Description': 'Descripción', 'Details': 'Detalles',
    'Device': 'Dispositivo', 'Devkit Link Data': 'Datos de enlace Devkit',
    'Devkit System Link Patch Disabled': 'Parche System Link de Devkit desactivado', 'Direction': 'Dirección',
    'Disable': 'Desactivar', 'Display': 'Pantalla', 'Done': 'Listo', 'Download': 'Descargar',
    'Download Cover': 'Descargar portada', 'Download Location:': 'Ubicación de descarga:',
    'Downloading': 'Descargando', 'Effect': 'Efecto', 'Emulators': 'Emuladores',
    'Enable Skin Animation': 'Activar animación de la skin', 'Enabled': 'Activado',
    'Error Loading Settings': 'Error al cargar los ajustes', 'Error Opening Screen Capture': 'Error al abrir la captura',
    'Failed': 'Error', 'Favorite': 'Favorito', 'Favorites Only': 'Solo favoritos', 'File Manager': 'Administrador de archivos',
    'File System': 'Sistema de archivos', 'Filter': 'Filtro', 'Filters': 'Filtros', 'Filters & Sort': 'Filtros y orden',
    'Game Details': 'Detalles del juego', 'Green': 'Verde', 'Hide': 'Ocultar', 'Hide Title': 'Ocultar título',
    'Hostname': 'Nombre de host', 'Icons': 'Iconos', 'Import': 'Importar', 'Installed': 'Instalado',
    'IP Address': 'Dirección IP', 'Language': 'Idioma', 'Launch': 'Iniciar', 'Left Location': 'Ubicación izquierda',
    'Left Trigger': 'Gatillo izquierdo', 'Letterbox on 4:3 Screen': 'Franjas negras en pantalla 4:3',
    'License Patching': 'Parche de licencia', 'LiNK Enabled': 'LiNK activado', 'Manage Paths': 'Administrar rutas',
    'Marketplace Locale': 'Región del Marketplace', 'Marketplace Rating': 'Calificación del Marketplace',
    'Max Screenshots': 'Máx. de capturas', 'Maybe': 'Quizás', 'Modify List': 'Modificar lista', 'Module': 'Módulo',
    'Module Name': 'Nombre del módulo', 'Modules': 'Módulos', 'More': 'Más', 'Move': 'Mover', 'Network': 'Red',
    'No': 'No', 'No Achievements Found': 'No hay logros', 'No Cloud Storage': 'Sin almacenamiento en la nube',
    'No Content Found': 'No hay contenido', 'No Disc': 'Sin disco', 'No Games Found': 'No hay juegos',
    'No Health Video': 'Sin video de salud', 'No Quick Views Available': 'No hay vistas rápidas disponibles',
    'No Quick Views Found': 'No hay vistas rápidas', 'No Saved Games Found': 'No hay partidas guardadas',
    'No Screenshots Found': 'No hay capturas', 'No Settings Available': 'No hay ajustes disponibles',
    'No Trainers Found': 'No hay trainers', 'None': 'Ninguno', 'Not Available': 'No disponible',
    'Not Signed In': 'Sin sesión iniciada', 'NOVA Loaded': 'NOVA cargado', 'NXE Stage & Rings': 'Escenario y anillos NXE',
    'Open': 'Abrir', 'Operators': 'Operadores', 'Operators and Filters': 'Operadores y filtros', 'Options': 'Opciones',
    'Override Defaults': 'Reemplazar valores predeterminados', 'Passcode Protected': 'Protegido con código',
    'Passed': 'Correcto', 'Password': 'Contraseña', 'Path': 'Ruta', 'Permissions': 'Permisos',
    'Ping Limit Patching': 'Parche de límite de ping', 'Play Trailer': 'Ver tráiler', 'Port': 'Puerto',
    'Preview': 'Vista previa', 'Profile': 'Perfil', 'Profile & Disc Panel': 'Panel de perfil y disco',
    'Profile Not Selected': 'Perfil no seleccionado', 'Profile Only': 'Solo perfil', 'Quick View': 'Vista rápida',
    'Quick View Builder': 'Creador de vistas rápidas', 'Read full synopsis': 'Leer sinopsis completa',
    'Reading Disc...': 'Leyendo disco...', 'Reboot': 'Reiniciar', 'Reboot Required': 'Es necesario reiniciar',
    'Red': 'Rojo', 'Refresh': 'Actualizar', 'Rename': 'Cambiar nombre', 'Rename Title': 'Cambiar nombre del título',
    'Request': 'Solicitar', 'Reset': 'Restablecer', 'Restart': 'Reiniciar Aurora', 'Restart Required': 'Es necesario reiniciar',
    'Restore': 'Restaurar', 'Right Location': 'Ubicación derecha', 'Right Trigger': 'Gatillo derecho',
    'Role Playing Games (1)': 'Juegos de rol (1)', 'Run Main.lua On Boot': 'Ejecutar Main.lua al iniciar',
    'Run Main.lua on Boot': 'Ejecutar Main.lua al iniciar', 'Save': 'Guardar', 'Saved Games': 'Partidas guardadas',
    'Scan Depth:': 'Profundidad de escaneo:', 'Scan Now': 'Escanear ahora', 'Screen Capture': 'Captura de pantalla',
    'Screen Capture Combo': 'Combinación de captura', 'Screen Captures': 'Capturas de pantalla',
    'Screenshots': 'Capturas', 'Script Data': 'Datos del script', 'Script Data:': 'Datos del script:',
    'Search': 'Buscar', 'Security': 'Seguridad', 'Select': 'Seleccionar', 'Select Assets': 'Seleccionar recursos',
    'Select At Boot': 'Seleccionar al iniciar', 'Select Directory': 'Seleccionar carpeta', 'Select Item': 'Seleccionar elemento',
    'Select Title': 'Seleccionar título', 'Set Default': 'Establecer predeterminado', 'Settings': 'Ajustes',
    'Settings Override': 'Reemplazo de ajustes', 'Share': 'Carpeta compartida', 'Share Name': 'Nombre del recurso',
    "Show 'Idle'": "Mostrar 'Inactivo'", 'Show All': 'Mostrar todo', 'Show Hidden Titles': 'Mostrar títulos ocultos',
    'Shutdown': 'Apagar', 'Sort': 'Ordenar', 'Speed': 'Velocidad', 'Start': 'Iniciar', 'Status When Idle': 'Estado en reposo',
    'Subtitle': 'Subtítulo', 'Synopsis': 'Sinopsis', 'System': 'Sistema',
    'System Link Ping Limit Patch Enabled': 'Parche de límite de ping de System Link activado',
    'Temperatures': 'Temperaturas', 'Theme': 'Tema', 'Title Updates': 'Actualizaciones', 'Toggle Favorite': 'Marcar favorito',
    'Tools': 'Herramientas', 'Trigger': 'Gatillo', 'Unity Authentication:': 'Autenticación de Unity:',
    'Unity Connection': 'Conexión con Unity', 'Unload': 'Descargar módulo', 'Up Directory': 'Carpeta superior',
    'Update Assets': 'Actualizar recursos', 'Update Now': 'Actualizar ahora', 'Updater': 'Actualizador',
    'UPNP Capable Router Detected': 'Router con UPnP detectado', 'Username': 'Usuario', 'Utility Scripts': 'Scripts de utilidad',
    'Verify': 'Verificar', 'Verify LiNK Settings': 'Verificar ajustes de LiNK', 'Verifying': 'Verificando',
    'Version': 'Versión', 'View': 'Vista', 'Warning': 'Aviso', 'Workgroup': 'Grupo de trabajo',
    'XBLA Patching': 'Parche de XBLA', 'XHttp Patching': 'Parche de XHttp', 'Yes': 'Sí',
}

# rótulos desenhados nas imagens e textos do skin.meta
IMAGE_TEXT = {
    'en': {'loading': 'Loading Aurora', 'overview': 'OVERVIEW', 'actions': 'ACTIONS', 'rating': 'RATING',
           'select': 'Select', 'back': 'Back', 'more': 'More options',
           'name': 'Xbox Series (English)',
           'desc': 'The Xbox Series Home on your Xbox 360: full-screen game art, covers with green focus and a clock. Created by Dimas Silva.'},
    'es': {'loading': 'Cargando Aurora', 'overview': 'RESUMEN', 'actions': 'ACCIONES', 'rating': 'VALORACIÓN',
           'select': 'Seleccionar', 'back': 'Atrás', 'more': 'Más opciones',
           'name': 'Xbox Series (Español)',
           'desc': 'La Home de Xbox Series en tu Xbox 360: arte del juego a pantalla completa, portadas con foco verde y reloj. Creada por Dimas Silva.'},
}


def table(lang):
    """pt-BR -> idioma, a partir da tabela inglês -> pt-BR."""
    inv = {}
    for en, pt in list(T.items()) + list(EXTRA_PT.items()):
        inv.setdefault(pt, en)
    out = {}
    for pt, en in inv.items():
        core = en.rstrip('\r\n'); tail = en[len(core):]
        if lang == 'en':
            out[pt] = en
        elif core in ES:
            out[pt] = ES[core] + tail
    return out


def translate_xur(b, tab):
    x = xur5.Xur(b); n = [0]
    def tr(v):
        s = x.strings[v[1]]
        if s in tab and tab[s] != s:
            n[0] += 1; return ('s', x.str_index(tab[s]))
        return v
    def walk(o):
        if o.props:
            o.props = (o.props[0], [(pb, m, [(pd, tr(v) if pd.name == 'Text' and v[0] == 's' else v) for pd, v in vals])
                                    for pb, m, vals in o.props[1]])
        for c in o.children: walk(c)
        if o.timelines:
            o.timelines = [(el, defs, [(h, [tr(v) if pd.name == 'Text' and v[0] == 's' else v for pd, v in zip(pdl, vs)])
                                       for h, vs in kfs], pdl) for el, defs, kfs, pdl in o.timelines]
    walk(x.root)
    return (x.build(), n[0]) if n[0] else (b, 0)


def splash(b, text, fontdir):
    """Troca a frase "Carregando o Aurora" desenhada na abertura."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(io.BytesIO(b)).convert('RGB')
    d = ImageDraw.Draw(im)
    d.rectangle((300, 596, 980, 648), fill=(0, 0, 0))
    f = ImageFont.truetype(fontdir + '/Fonts\\Inter-Light.ttf', 24)
    w = d.textlength(text, font=f)
    d.text((640 - w / 2, 604), text, font=f, fill=(196, 196, 196))   # mesma fonte/posição da frase original
    buf = io.BytesIO(); im.save(buf, 'PNG'); return buf.getvalue()


def details_backdrop(fontdir, t):
    import art2
    return art2.details_xbox(fontdir, labels=t)


def build(src, dst, lang):
    import tempfile
    d, ds, _, _, ents = parse(src)
    fontdir = tempfile.mkdtemp()                 # fontes Inter do próprio pacote, no formato que o art2 espera
    for name, size, off in ents:
        if name.startswith('Fonts\\Inter'):
            open(os.path.join(fontdir, name), 'wb').write(d[ds+off:ds+off+size])
    tab = table(lang); t = IMAGE_TEXT[lang]
    blobs = []; total = 0
    for name, size, off in ents:
        data = d[ds+off:ds+off+size]
        if name.endswith('.xur') and '\\' not in name:
            data, k = translate_xur(data, tab); total += k
        elif name == 'Images\\XboxSeries\\Splash.png':
            data = splash(data, t['loading'], fontdir)
        elif name == 'Images\\PolarGlass\\DetailsBackdrop.png':
            buf = io.BytesIO(); details_backdrop(fontdir, t).save(buf, 'PNG'); data = buf.getvalue()
        elif name == 'skin.meta':
            m = data.decode('utf-8', 'replace').rstrip('\x00')
            m = re.sub(r'"skinname" : "[^"]*"', '"skinname" : "%s"' % t['name'], m)
            m = re.sub(r'"description" : "[^"]*"', '"description" : "%s"' % t['desc'], m)
            data = m.encode('utf-8')
        blobs.append((name, data))
    table_b = bytearray(); off = 0
    for name, data in blobs:
        table_b += struct.pack('>II', len(data), off) + bytes([len(name)]) + name.encode('utf-16-be')
        off += len(data)
    h = bytearray(d[:0x16])
    h[0x10:0x14] = struct.pack('>I', len(table_b)); h[0x14:0x16] = struct.pack('>H', len(blobs))
    h[8:12] = struct.pack('>I', 0x16 + len(table_b) + off)
    open(dst, 'wb').write(bytes(h) + bytes(table_b) + b''.join(x for _, x in blobs))
    return total


if __name__ == '__main__':
    print(build(*sys.argv[1:4]), 'textos traduzidos')
