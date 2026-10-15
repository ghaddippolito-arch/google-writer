"""
Configuración y constantes para la aplicación Streamlit de ACI Writer.
Define categorías, subcategorías, países completos del mundo, idiomas y prompts de SEO y Helpful Content.
"""

# Categorías y subcategorías requeridas
CATEGORIES_AND_SUBCATEGORIES = {
    "Requisitos y documentos para viajar": [
        "Guía de visados para viajeros",
        "Requisitos esenciales para viajar",
        "Equipaje: todo lo que necesitas saber"
    ],
    "Qué hacer en los mejores destinos turísticos": [
        "Actividades increíbles para viajeros",
        "Itinerario diario para tu viaje",
        "Dónde comer en los mejores destinos",
        "Consejos para viajar con niños"
    ],
    "Presupuesto de viaje: guía práctica": [
        "Costos locales en tu ciudad de destino",
        "Dinero necesario para viajar"
    ],
    "Asistencia al viajero: todo lo que debes saber": [
        "Sistema de salud local en tu viaje",
        "Assist card: tu compañero de viaje",
        "Salud y enfermedades en el viaje"
    ],
    "Mejor época para viajar a tu destino": [
        "Cuándo ir a tu destino: guía completa",
        "Clima en tu destino: todo lo que necesitas saber",
        "Fechas especiales para viajar"
    ],
    "Mapa de tu destino: guía interactiva": [
        "Transporte en tu destino: guía completa",
        "Cómo trasladarse en tu viaje",
        "Mapas interactivos para tus viajes"
    ],
    "Todo sobre alojamientos: opciones y consejos": [
        "Toda la información para saber dónde hospedarse",
        "Los mejores hoteles para tu viaje",
        "Los hoteles más baratos para tu viaje"
    ],
    "Tips de viaje: consejos esenciales": [
        "Los mejores Tips de Viaje."
    ]
}

# Idiomas disponibles
LANGUAGES = [
    "Español",
    "Inglés",
    "Portugués",
    "Francés",
    "Italiano",
    "Alemán"
]

# Lista completa de TODOS los países del mundo en español (orden alfabético)
COUNTRIES = [
    "Global / Internacional",
    "Afganistán", "Albania", "Alemania", "Andorra", "Angola", "Antigua y Barbuda", "Arabia Saudita",
    "Argelia", "Argentina", "Armenia", "Australia", "Austria", "Azerbaiyán", "Bahamas", "Bangladés",
    "Barbados", "Baréin", "Bélgica", "Belice", "Benín", "Bielorrusia", "Bolivia", "Bosnia y Herzegovina",
    "Botsuana", "Brasil", "Brunéi", "Bulgaria", "Burkina Faso", "Burundi", "Bután", "Cabo Verde",
    "Camboya", "Camerún", "Canadá", "Catar", "Chad", "Chile", "China", "Chipre", "Colombia", "Comoras",
    "Corea del Norte", "Corea del Sur", "Costa de Marfil", "Costa Rica", "Croacia", "Cuba", "Dinamarca",
    "Dominica", "Ecuador", "Egipto", "El Salvador", "Emiratos Árabes Unidos", "Eritrea", "Eslovaquia",
    "Eslovenia", "España", "Estados Unidos", "Estonia", "Eswatini", "Etiopía", "Filipinas", "Finlandia",
    "Fiyi", "Francia", "Gabón", "Gambia", "Georgia", "Ghana", "Granada", "Grecia", "Guatemala", "Guinea",
    "Guinea-Bisáu", "Guinea Ecuatorial", "Guyana", "Haití", "Honduras", "Hungría", "India", "Indonesia",
    "Irak", "Irán", "Irlanda", "Islandia", "Islas Marshall", "Islas Salomón", "Israel", "Italia", "Jamaica",
    "Japón", "Jordania", "Kazajistán", "Kenia", "Kirguistán", "Kiribati", "Kuwait", "Laos", "Lesoto",
    "Letonia", "Líbano", "Liberia", "Libia", "Liechtenstein", "Lituania", "Luxemburgo", "Macedonia del Norte",
    "Madagascar", "Malasia", "Malaui", "Maldivas", "Malí", "Malta", "Marruecos", "Mauricio", "Mauritania",
    "México", "Micronesia", "Moldavia", "Mónaco", "Mongolia", "Montenegro", "Mozambique", "Myanmar",
    "Namibia", "Nauru", "Nepal", "Nicaragua", "Níger", "Nigeria", "Noruega", "Nueva Zelanda", "Omán",
    "Países Bajos", "Pakistán", "Palaos", "Panamá", "Papúa Nueva Guinea", "Paraguay", "Perú", "Polonia",
    "Portugal", "Reino Unido", "República Centroafricana", "República Checa", "República del Congo",
    "República Democrática del Congo", "República Dominicana", "Ruanda", "Rumania", "Rusia", "Samoa",
    "San Cristóbal y Nieves", "San Marino", "San Vicente y las Granadinas", "Santa Lucía",
    "Santo Tomé y Príncipe", "Senegal", "Serbia", "Seychelles", "Sierra Leona", "Singapur", "Siria",
    "Somalia", "Sri Lanka", "Sudáfrica", "Sudán", "Sudán del Sur", "Suecia", "Suiza", "Surinam", "Tailandia",
    "Taiwán", "Tanzania", "Tayikistán", "Timor Oriental", "Togo", "Tonga", "Trinidad y Tobago", "Túnez",
    "Turkmenistán", "Turquía", "Tuvalu", "Ucrania", "Uganda", "Uruguay", "Uzbekistán", "Vanuatu",
    "Vaticano", "Venezuela", "Vietnam", "Yemen", "Yibuti", "Zambia", "Zimbabue"
]

# Modelos recomendados de Gemini
GEMINI_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.8-flash"
]

# Google Docs & Drive Scopes
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file"
]
