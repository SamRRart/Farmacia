"""
seed.py - Poblador de datos de prueba para el Sistema Farmacia CUCEI.
Inserta en la base de datos remota (Supabase/PostgreSQL):
  - 3 Usuarios iniciales (Admin, Gerente, Encargado) con password '1234' hasheada
  - 10 Proveedores con datos de contacto
  - 100 Productos (10 por proveedor) con folios estructurados y flags correctos
  - 10 Clientes de prueba con puntos variados para validar el programa de lealtad

Ejecutar una sola vez. Verifica duplicados antes de insertar.
"""

import sys
import os

# Asegurar que el modulo raiz del proyecto sea accesible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

import bcrypt
from backend.database.connection import get_connection

# ==============================================================================
# DATOS DE PRUEBA
# ==============================================================================

USUARIOS = [
    {
        "perfil": "Admin",
        "nombre": "administrador",
        "correo": "admin@cucei.udg.mx",
        "password": "1234"
    },
    {
        "perfil": "Gerente",
        "nombre": "gerente",
        "correo": "gerente@cucei.udg.mx",
        "password": "1234"
    },
    {
        "perfil": "Encargado",
        "nombre": "encargado",
        "correo": "encargado@cucei.udg.mx",
        "password": "1234"
    },
]

PROVEEDORES = [
    {"razon_social": "Laboratorios PISA S.A. de C.V.",       "telefono": "3331234001", "correo": "ventas@pisa.com.mx"},
    {"razon_social": "Distribuidora Farmacos del Pacifico",   "telefono": "3331234002", "correo": "contacto@farmacospacifico.mx"},
    {"razon_social": "Medix S.A. de C.V.",                   "telefono": "3331234003", "correo": "pedidos@medix.mx"},
    {"razon_social": "Probiomed S.A. de C.V.",               "telefono": "3331234004", "correo": "ventas@probiomed.com"},
    {"razon_social": "Distribuciones Genomma Lab",            "telefono": "3331234005", "correo": "compras@genommalab.com"},
    {"razon_social": "Importadora MedSupply Mexico",         "telefono": "3331234006", "correo": "info@medsupply.mx"},
    {"razon_social": "Pharma Express Occidente S.C.",        "telefono": "3331234007", "correo": "express@pharmaoccidente.mx"},
    {"razon_social": "Distribuidora Nacional de Biologicos", "telefono": "3331234008", "correo": "biologicos@dnb.mx"},
    {"razon_social": "Almacen Farmaceutico del Bajio",       "telefono": "3331234009", "correo": "contacto@bajiofarma.mx"},
    {"razon_social": "Suministros Medicos del Norte S.A.",   "telefono": "3331234010", "correo": "suministros@mednorte.mx"},
]

# 100 productos: 10 por proveedor (indice 0-9 corresponde a indice de PROVEEDORES)
# Formato: (nombre, categoria, precio_compra, precio_venta, stock, es_controlado, es_alcohol, tipo_folio)
# tipo_folio: 'MED' | 'ALC' | 'CTR' | 'GEN'
PRODUCTOS_POR_PROVEEDOR = [
    # Proveedor 1 - Laboratorios PISA
    [
        ("Paracetamol 500mg Tab",         "Analgesico",     12.50,  28.00,  120, False, False, "MED"),
        ("Ibuprofeno 400mg Tab",          "Antiinflamatorio", 15.00, 32.00,  90, False, False, "MED"),
        ("Amoxicilina 500mg Cap",         "Antibiotico",    35.00,  75.00,  60, False, False, "MED"),
        ("Metformina 850mg Tab",          "Antidiabetico",  18.00,  40.00,  80, False, False, "MED"),
        ("Losartan 50mg Tab",             "Antihipertensivo", 22.00, 48.00, 70, False, False, "MED"),
        ("Clonazepam 2mg Tab",            "Ansiolitico",    28.00,  65.00,  40, True,  False, "CTR"),
        ("Morfina Clorh 10mg/mL Sol Iny", "Analgesico Opiode", 95.00, 210.00, 15, True, False, "CTR"),
        ("Alcohol Isopropilico 70% 1L",   "Antiseptico",    35.00,  72.00,  50, False, True,  "ALC"),
        ("Vitamina C 500mg Tab",          "Suplemento",      8.00,  18.00, 200, False, False, "MED"),
        ("Omeprazol 20mg Cap",            "Gastroprotector", 10.00, 24.00, 110, False, False, "MED"),
    ],
    # Proveedor 2 - Distribuidora Farmacos del Pacifico
    [
        ("Aspirina 500mg Tab",            "Analgesico",     10.00,  22.00, 150, False, False, "MED"),
        ("Diclofenaco 100mg Tab",         "Antiinflamatorio", 14.00, 30.00, 85, False, False, "MED"),
        ("Ciprofloxacino 500mg Tab",      "Antibiotico",    42.00,  90.00,  55, False, False, "MED"),
        ("Glibenclamida 5mg Tab",         "Antidiabetico",  16.00,  36.00,  65, False, False, "MED"),
        ("Enalapril 10mg Tab",            "Antihipertensivo", 20.00, 44.00, 75, False, False, "MED"),
        ("Alprazolam 0.5mg Tab",          "Ansiolitico",    25.00,  58.00,  35, True,  False, "CTR"),
        ("Tramadol 50mg Cap",             "Analgesico Opiode", 48.00, 110.00, 30, True, False, "CTR"),
        ("Alcohol Etilico Desnaturalizado 500mL", "Antiseptico", 28.00, 60.00, 60, False, True, "ALC"),
        ("Zinc 15mg Tab",                 "Suplemento",      7.00,  16.00, 180, False, False, "MED"),
        ("Ranitidina 150mg Tab",          "Gastroprotector", 11.00, 25.00,  95, False, False, "MED"),
    ],
    # Proveedor 3 - Medix
    [
        ("Naproxeno 250mg Tab",           "Analgesico",     13.00,  28.00, 100, False, False, "MED"),
        ("Ketorolaco 10mg Tab",           "Antiinflamatorio", 22.00, 48.00, 60, False, False, "MED"),
        ("Azitromicina 500mg Tab",        "Antibiotico",    55.00, 120.00,  40, False, False, "MED"),
        ("Sitagliptina 100mg Tab",        "Antidiabetico",  85.00, 185.00,  30, False, False, "MED"),
        ("Amlodipino 5mg Tab",            "Antihipertensivo", 18.00, 40.00, 90, False, False, "MED"),
        ("Lorazepam 2mg Tab",             "Sedante",        30.00,  68.00,  25, True,  False, "CTR"),
        ("Codeina 30mg Tab",              "Analgesico Opiode", 52.00, 115.00, 20, True, False, "CTR"),
        ("Gel Antibacterial 70% Alc 500mL", "Antiseptico",  32.00, 68.00,  70, False, True,  "ALC"),
        ("Hierro 65mg Tab",               "Suplemento",      9.00,  20.00, 160, False, False, "MED"),
        ("Pantoprazol 40mg Tab",          "Gastroprotector", 24.00, 52.00,  85, False, False, "MED"),
    ],
    # Proveedor 4 - Probiomed
    [
        ("Meloxicam 7.5mg Tab",           "Antiinflamatorio", 18.00, 40.00, 80, False, False, "MED"),
        ("Dexametasona 4mg/mL Iny",       "Corticoide",     38.00,  82.00,  45, False, False, "MED"),
        ("Eritromicina 500mg Tab",        "Antibiotico",    40.00,  88.00,  50, False, False, "MED"),
        ("Insulina Glargina 100UI/mL",    "Antidiabetico", 320.00, 680.00,  20, False, False, "MED"),
        ("Verapamilo 80mg Tab",           "Antihipertensivo", 25.00, 55.00, 60, False, False, "MED"),
        ("Fenobarbital 100mg Tab",        "Anticonvulsivante", 20.00, 45.00, 30, True, False, "CTR"),
        ("Oxicodona 10mg Tab",            "Analgesico Opiode", 110.00, 240.00, 10, True, False, "CTR"),
        ("Alcohol Cetilico Crema Base",   "Dermocosmetico", 42.00,  90.00,  40, False, True,  "ALC"),
        ("Biotina 5000mcg Cap",           "Suplemento",     12.00,  26.00, 140, False, False, "GEN"),
        ("Sucralfato 1g Tab",             "Gastroprotector", 28.00, 60.00,  70, False, False, "MED"),
    ],
    # Proveedor 5 - Genomma Lab
    [
        ("Tempra 500mg Tab",              "Analgesico",     14.00,  30.00, 110, False, False, "MED"),
        ("Gel Voltaren 1% 60g",           "Topico",         68.00, 148.00,  35, False, False, "MED"),
        ("Lamisil AT Spray 30mL",         "Antimicotoco",   95.00, 205.00,  25, False, False, "MED"),
        ("Corega Pastillas Limpiadoras",  "Cuidado Dental", 55.00, 118.00,  30, False, False, "GEN"),
        ("Crema Sensodyne Extra Fresh",   "Cuidado Dental", 48.00, 102.00,  40, False, False, "GEN"),
        ("Melatonina 5mg Tab",            "Suplemento",     18.00,  40.00,  90, False, False, "GEN"),
        ("Colgate Total 12 150g",         "Cuidado Dental", 32.00,  68.00,  60, False, False, "GEN"),
        ("Agua Oxigenada 3% 500mL",       "Antiseptico",    15.00,  32.00,  80, False, True,  "ALC"),
        ("Magnesia Phillips 240mL",       "Gastrico",       38.00,  82.00,  55, False, False, "GEN"),
        ("Pepto Bismol 262mg Tab",        "Gastrico",       42.00,  90.00,  50, False, False, "GEN"),
    ],
    # Proveedor 6 - MedSupply Mexico
    [
        ("Termometro Digital Oral",       "Dispositivo",    85.00, 185.00,  30, False, False, "GEN"),
        ("Tensimetro Digital Muñeca",     "Dispositivo",   380.00, 820.00,  10, False, False, "GEN"),
        ("Glucometro Accu-Chek Active",   "Dispositivo",   420.00, 910.00,  10, False, False, "GEN"),
        ("Tiras Glucometro x50",          "Consumible",    180.00, 390.00,  25, False, False, "GEN"),
        ("Lancetas Accu-Chek x100",       "Consumible",     65.00, 140.00,  40, False, False, "GEN"),
        ("Jeringas Insulina 1mL x10",     "Consumible",     32.00,  70.00,  60, False, False, "GEN"),
        ("Gasas Esteriles 10x10 x10",     "Curacion",       18.00,  38.00,  90, False, False, "GEN"),
        ("Alcohol en Gel 500mL Manos",    "Higiene",        28.00,  60.00,  70, False, True,  "ALC"),
        ("Vendas Elasticas 5cm x4.5m",    "Curacion",       22.00,  48.00,  80, False, False, "GEN"),
        ("Esparadrapo Tela 2.5cm x5m",   "Curacion",       14.00,  30.00, 100, False, False, "GEN"),
    ],
    # Proveedor 7 - Pharma Express Occidente
    [
        ("Loratadina 10mg Tab",           "Antialergico",   12.00,  26.00, 120, False, False, "MED"),
        ("Cetirizina 10mg Tab",           "Antialergico",   14.00,  30.00, 100, False, False, "MED"),
        ("Fexofenadina 120mg Tab",        "Antialergico",   28.00,  60.00,  70, False, False, "MED"),
        ("Levocetirizina 5mg Tab",        "Antialergico",   22.00,  48.00,  85, False, False, "MED"),
        ("Bromhexina 8mg Tab",            "Mucolito",       10.00,  22.00, 130, False, False, "MED"),
        ("Ambroxol Jarabe 15mg/5mL",      "Expectorante",   24.00,  52.00,  65, False, False, "MED"),
        ("Dextrometorfano 15mg Cps",      "Antitusivo",     18.00,  40.00,  90, False, False, "MED"),
        ("Salbutamol Spray 100mcg",       "Broncodilatador", 85.00, 185.00, 20, False, False, "MED"),
        ("Tiotropio 18mcg Caps Inh",      "Broncodilatador", 320.00, 695.00, 10, False, False, "MED"),
        ("Budesonida 200mcg Spray",       "Corticoide Inh", 240.00, 520.00, 15, False, False, "MED"),
    ],
    # Proveedor 8 - Distribuidora Nacional de Biologicos
    [
        ("Vacuna Influenza Trivalente",   "Biologico",     120.00, 260.00,  20, False, False, "MED"),
        ("Vacuna Hepatitis B 1mL",        "Biologico",     180.00, 390.00,  15, False, False, "MED"),
        ("Toxoide Tetanico 0.5mL",        "Biologico",     145.00, 315.00,  18, False, False, "MED"),
        ("Eritropoyetina 4000UI Iny",     "Hematologico",  380.00, 820.00,  10, False, False, "MED"),
        ("Filgrastim 300mcg Iny",         "Biologico",     850.00, 1840.00,  5, False, False, "MED"),
        ("Enoxaparina 40mg Iny",          "Anticoagulante", 95.00, 205.00, 25, False, False, "MED"),
        ("Metilprednisolona 500mg Iny",   "Corticoide",    140.00, 305.00,  20, False, False, "MED"),
        ("Inmunoglobulina Anti-D 300mcg", "Biologico",     650.00, 1410.00,  5, False, False, "MED"),
        ("Colagenasa 0.6UI Ung 15g",      "Enzimatico",   185.00, 400.00,  15, False, False, "MED"),
        ("Hialuronidasa 150UI Iny",       "Enzimatico",   220.00, 475.00,  12, False, False, "MED"),
    ],
    # Proveedor 9 - Almacen Farmaceutico del Bajio
    [
        ("Crema Clotrimazol 1% 20g",      "Antimicotoco",   22.00,  48.00,  80, False, False, "MED"),
        ("Nistatina Ovulos 100000UI",     "Antimicotoco",   38.00,  82.00,  50, False, False, "MED"),
        ("Metronidazol 500mg Tab",        "Antibiotico",    18.00,  40.00,  90, False, False, "MED"),
        ("Nitrofurantoina 100mg Cap",     "Antibiotico",    24.00,  52.00,  65, False, False, "MED"),
        ("Trimetoprim/Sulfa 160/800 Tab", "Antibiotico",    20.00,  44.00,  75, False, False, "MED"),
        ("Aciclovir 400mg Tab",           "Antiviral",      35.00,  76.00,  45, False, False, "MED"),
        ("Oseltamivir 75mg Cap",          "Antiviral",     185.00, 400.00,  20, False, False, "MED"),
        ("Terbinafina 250mg Tab",         "Antimicotoco",   42.00,  90.00,  40, False, False, "MED"),
        ("Fluconazol 150mg Cap",          "Antimicotoco",   28.00,  60.00,  60, False, False, "MED"),
        ("Clindamicina 300mg Cap",        "Antibiotico",    55.00, 120.00,  35, False, False, "MED"),
    ],
    # Proveedor 10 - Suministros Medicos del Norte
    [
        ("Suero Oral Vida Suero 1L",      "Hidratante",     18.00,  38.00, 100, False, False, "GEN"),
        ("Suero Fisiologico 0.9% 1L",     "Hidratante",     42.00,  90.00,  50, False, False, "MED"),
        ("Dextrosa 5% en Agua 500mL",     "Hidratante",     38.00,  82.00,  40, False, False, "MED"),
        ("Lactato Ringer 500mL",          "Hidratante",     45.00,  98.00,  35, False, False, "MED"),
        ("KCl 20mEq/10mL Iny",            "Electrolito",   22.00,  48.00,  60, False, False, "MED"),
        ("Bicarbonato Sodio 7.5% 50mL",   "Electrolito",   28.00,  60.00,  45, False, False, "MED"),
        ("Albumina Humana 20% 50mL",      "Plasma",       850.00, 1840.00,  5, False, False, "MED"),
        ("Plasma Fresco Congelado 200mL", "Plasma",       420.00, 910.00,   8, False, False, "MED"),
        ("Agua Bidestilada 10mL Iny",     "Diluyente",     12.00,  26.00, 120, False, False, "MED"),
        ("Cloruro Sodio 0.9% 10mL Iny",   "Diluyente",    14.00,  30.00, 100, False, False, "MED"),
    ],
]

CLIENTES = [
    {
        "nombre": "Juan Perez Gomez",
        "telefono": "3312345001",
        "rfc": "PEGJ900101XY0",
        "correo": "juan.perez@email.com",
        "fecha_nacimiento": "1990-01-01",
        "puntos_acumulados": 10,
        "ciudad": "Guadalajara",
        "estado": "Jalisco"
    },
    {
        "nombre": "Maria Lopez Ruiz",
        "telefono": "3312345002",
        "rfc": "LORM850512AB2",
        "correo": "maria.lopez@email.com",
        "fecha_nacimiento": "1985-05-12",
        "puntos_acumulados": 50,   # Tiene descuento disponible (>= 50 pts)
        "ciudad": "Zapopan",
        "estado": "Jalisco"
    },
    {
        "nombre": "Carlos Sanchez Vega",
        "telefono": "3312345003",
        "rfc": "SAVC951020DE3",
        "correo": "carlos.sanchez@email.com",
        "fecha_nacimiento": "1995-10-20",
        "puntos_acumulados": 40,   # Cerca del descuento (una compra de >$500 lo alcanza)
        "ciudad": "Tlaquepaque",
        "estado": "Jalisco"
    },
    {
        "nombre": "Ana Ramirez Torres",
        "telefono": "3312345004",
        "rfc": "RATA920315FG4",
        "correo": "ana.ramirez@email.com",
        "fecha_nacimiento": "1992-03-15",
        "puntos_acumulados": 0,
        "ciudad": "Tonala",
        "estado": "Jalisco"
    },
    {
        "nombre": "Pedro Martinez Cruz",
        "telefono": "3312345005",
        "rfc": "MACP880720HI5",
        "correo": "pedro.martinez@email.com",
        "fecha_nacimiento": "1988-07-20",
        "puntos_acumulados": 60,   # Tiene descuento disponible (> 50 pts)
        "ciudad": "Monterrey",
        "estado": "Nuevo Leon"
    },
    {
        "nombre": "Laura Hernandez Mora",
        "telefono": "3312345006",
        "rfc": "HEML930605JK6",
        "correo": "laura.hernandez@email.com",
        "fecha_nacimiento": "1993-06-05",
        "puntos_acumulados": 20,
        "ciudad": "Guadalajara",
        "estado": "Jalisco"
    },
    {
        "nombre": "Roberto Garcia Flores",
        "telefono": "3312345007",
        "rfc": "GAFR870412LM7",
        "correo": "roberto.garcia@email.com",
        "fecha_nacimiento": "1987-04-12",
        "puntos_acumulados": 0,
        "ciudad": "Ciudad de Mexico",
        "estado": "CDMX"
    },
    {
        "nombre": "Sofia Castro Reyes",
        "telefono": "3312345008",
        "rfc": "CARS000815NO8",
        "correo": "sofia.castro@email.com",
        "fecha_nacimiento": "2000-08-15",
        "puntos_acumulados": 30,
        "ciudad": "Zapopan",
        "estado": "Jalisco"
    },
    {
        "nombre": "Miguel Angel Nunez",
        "telefono": "3312345009",
        "rfc": "NUMM750930PQ9",
        "correo": "miguel.nunez@email.com",
        "fecha_nacimiento": "1975-09-30",
        "puntos_acumulados": 50,   # Tiene descuento disponible (= 50 pts)
        "ciudad": "Guadalajara",
        "estado": "Jalisco"
    },
    {
        "nombre": "Elena Ortiz Medina",
        "telefono": "3312345010",
        "rfc": "OIME821105RS0",
        "correo": "elena.ortiz@email.com",
        "fecha_nacimiento": "1982-11-05",
        "puntos_acumulados": 5,
        "ciudad": "San Pedro Garza Garcia",
        "estado": "Nuevo Leon"
    },
]

# ==============================================================================
# FUNCIONES DE INSERCION
# ==============================================================================

def hash_password(plain: str) -> str:
    """Genera hash bcrypt de la contraseña (igual que user_service.hash_password)."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

def seed_usuarios(cursor) -> dict:
    """
    Inserta los 3 usuarios iniciales si no existen.
    Retorna un mapa correo -> id_usuario de los usuarios encontrados/insertados.
    """
    print("\n--- Usuarios ---")
    usuario_ids = {}
    for u in USUARIOS:
        cursor.execute("SELECT id_usuario FROM Usuarios WHERE LOWER(correo) = LOWER(%s);", (u["correo"],))
        row = cursor.fetchone()
        if row:
            print(f"  [EXISTE]  {u['perfil']} | {u['correo']}")
            usuario_ids[u["correo"]] = row[0]
        else:
            pw_hash = hash_password(u["password"])
            cursor.execute(
                "INSERT INTO Usuarios (perfil, nombre, correo, password) VALUES (%s, %s, %s, %s) RETURNING id_usuario;",
                (u["perfil"], u["nombre"], u["correo"], pw_hash)
            )
            new_id = cursor.fetchone()[0]
            usuario_ids[u["correo"]] = new_id
            print(f"  [CREADO]  {u['perfil']} | {u['correo']}  (id={new_id})")
    return usuario_ids

def seed_proveedores(cursor) -> list:
    """
    Inserta los 10 proveedores si no existen (por razon_social).
    Retorna lista de IDs en el mismo orden que PROVEEDORES.
    """
    print("\n--- Proveedores ---")
    proveedor_ids = []
    for p in PROVEEDORES:
        cursor.execute("SELECT id_proveedor FROM Proveedores WHERE LOWER(razon_social) = LOWER(%s);", (p["razon_social"],))
        row = cursor.fetchone()
        if row:
            print(f"  [EXISTE]  {p['razon_social']}")
            proveedor_ids.append(row[0])
        else:
            cursor.execute(
                "INSERT INTO Proveedores (razon_social, telefono, correo) VALUES (%s, %s, %s) RETURNING id_proveedor;",
                (p["razon_social"], p["telefono"], p["correo"])
            )
            new_id = cursor.fetchone()[0]
            proveedor_ids.append(new_id)
            print(f"  [CREADO]  {p['razon_social']}  (id={new_id})")
    return proveedor_ids

def build_folio(tipo: str, global_index: int) -> str:
    """
    Genera el folio estructurado del producto:
      MED-001  -> Medicamento general
      ALC-001  -> Contiene alcohol
      CTR-001  -> Producto controlado
      GEN-001  -> Producto general / dispositivo
    """
    return f"{tipo}-{global_index:03d}"

def seed_productos(cursor, proveedor_ids: list):
    """
    Inserta los 100 productos (10 por proveedor) si no existen (por folio).
    Genera folios secuenciales globales por tipo.
    """
    print("\n--- Productos ---")
    # Contadores de folio por tipo
    folio_counters = {"MED": 0, "ALC": 0, "CTR": 0, "GEN": 0}

    for prov_idx, productos in enumerate(PRODUCTOS_POR_PROVEEDOR):
        id_prov = proveedor_ids[prov_idx]
        for prod in productos:
            nombre, categoria, precio_compra, precio_venta, stock, es_controlado, es_alcohol, tipo_folio = prod
            folio_counters[tipo_folio] += 1
            folio = build_folio(tipo_folio, folio_counters[tipo_folio])

            cursor.execute("SELECT id_producto FROM Productos WHERE folio = %s;", (folio,))
            if cursor.fetchone():
                print(f"  [EXISTE]  {folio} | {nombre}")
                continue

            cursor.execute(
                """
                INSERT INTO Productos
                    (id_proveedor, folio, nombre, categoria, precio_compra, precio_venta, stock, es_controlado, es_alcohol)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_producto;
                """,
                (id_prov, folio, nombre, categoria,
                 precio_compra, precio_venta, stock,
                 es_controlado, es_alcohol)
            )
            new_id = cursor.fetchone()[0]
            print(f"  [CREADO]  {folio} | {nombre}  (id={new_id})")

def seed_clientes(cursor):
    """
    Inserta los 10 clientes de prueba si no existen (por RFC).
    """
    print("\n--- Clientes ---")
    for c in CLIENTES:
        cursor.execute("SELECT id_cliente FROM Clientes WHERE LOWER(rfc) = LOWER(%s);", (c["rfc"],))
        if cursor.fetchone():
            print(f"  [EXISTE]  {c['nombre']} | RFC: {c['rfc']}")
            continue

        cursor.execute(
            """
            INSERT INTO Clientes
                (nombre, telefono, rfc, correo, fecha_nacimiento, puntos_acumulados, ciudad, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_cliente;
            """,
            (c["nombre"], c["telefono"], c["rfc"], c["correo"],
             c["fecha_nacimiento"], c["puntos_acumulados"],
             c["ciudad"], c["estado"])
        )
        new_id = cursor.fetchone()[0]
        print(f"  [CREADO]  {c['nombre']} | RFC: {c['rfc']} | Puntos: {c['puntos_acumulados']}  (id={new_id})")

# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================

def run_seed():
    """Ejecuta la secuencia completa de seed en una sola transaccion atomica."""
    print("=" * 60)
    print("  FARMACIA CUCEI - Seed de Datos de Prueba")
    print("=" * 60)

    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            seed_usuarios(cursor)
            proveedor_ids = seed_proveedores(cursor)
            seed_productos(cursor, proveedor_ids)
            seed_clientes(cursor)

        connection.commit()
        print("\n" + "=" * 60)
        print("  Seed completado exitosamente.")
        print("  Credenciales de acceso:")
        print("    Admin    -> admin@cucei.udg.mx    / 1234")
        print("    Gerente  -> gerente@cucei.udg.mx  / 1234")
        print("    Encargado-> encargado@cucei.udg.mx/ 1234")
        print("=" * 60)

    except Exception as e:
        if connection:
            connection.rollback()
        print(f"\n[ERROR] Seed fallido. Se hizo rollback de todos los cambios.\nDetalle: {e}")
        raise
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    run_seed()
