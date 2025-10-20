from enum import Enum

class Country(str, Enum):
    # América del Norte
    US = "US"  # United States
    CA = "CA"  # Canada
    MX = "MX"  # Mexico
    GL = "GL"  # Greenland
    
    # América Central
    GT = "GT"  # Guatemala
    HN = "HN"  # Honduras
    SV = "SV"  # El Salvador
    NI = "NI"  # Nicaragua
    CR = "CR"  # Costa Rica
    PA = "PA"  # Panama
    BZ = "BZ"  # Belize
    
    # América del Sur
    BR = "BR"  # Brazil
    AR = "AR"  # Argentina
    CL = "CL"  # Chile
    PE = "PE"  # Peru
    CO = "CO"  # Colombia
    VE = "VE"  # Venezuela
    EC = "EC"  # Ecuador
    BO = "BO"  # Bolivia
    PY = "PY"  # Paraguay
    UY = "UY"  # Uruguay
    GY = "GY"  # Guyana
    SR = "SR"  # Suriname
    GF = "GF"  # French Guiana
    
    # Europa Occidental
    GB = "GB"  # United Kingdom
    IE = "IE"  # Ireland
    FR = "FR"  # France
    ES = "ES"  # Spain
    PT = "PT"  # Portugal
    DE = "DE"  # Germany
    NL = "NL"  # Netherlands
    BE = "BE"  # Belgium
    LU = "LU"  # Luxembourg
    CH = "CH"  # Switzerland
    AT = "AT"  # Austria
    LI = "LI"  # Liechtenstein
    MC = "MC"  # Monaco
    AD = "AD"  # Andorra
    
    # Europa del Norte
    SE = "SE"  # Sweden
    NO = "NO"  # Norway
    DK = "DK"  # Denmark
    FI = "FI"  # Finland
    IS = "IS"  # Iceland
    
    # Europa Oriental
    RU = "RU"  # Russia
    PL = "PL"  # Poland
    CZ = "CZ"  # Czech Republic
    SK = "SK"  # Slovakia
    HU = "HU"  # Hungary
    RO = "RO"  # Romania
    BG = "BG"  # Bulgaria
    UA = "UA"  # Ukraine
    BY = "BY"  # Belarus
    LT = "LT"  # Lithuania
    LV = "LV"  # Latvia
    EE = "EE"  # Estonia
    MD = "MD"  # Moldova
    
    # Europa del Sur
    IT = "IT"  # Italy
    GR = "GR"  # Greece
    HR = "HR"  # Croatia
    SI = "SI"  # Slovenia
    ME = "ME"  # Montenegro
    RS = "RS"  # Serbia
    BA = "BA"  # Bosnia and Herzegovina
    MK = "MK"  # North Macedonia
    AL = "AL"  # Albania
    MT = "MT"  # Malta
    CY = "CY"  # Cyprus
    SM = "SM"  # San Marino
    VA = "VA"  # Vatican City
    
    # Asia Oriental
    CN = "CN"  # China
    JP = "JP"  # Japan
    KR = "KR"  # South Korea
    KP = "KP"  # North Korea
    MN = "MN"  # Mongolia
    TW = "TW"  # Taiwan
    HK = "HK"  # Hong Kong
    MO = "MO"  # Macau
    
    # Sudeste Asiático
    ID = "ID"  # Indonesia
    PH = "PH"  # Philippines
    VN = "VN"  # Vietnam
    TH = "TH"  # Thailand
    MY = "MY"  # Malaysia
    SG = "SG"  # Singapore
    MM = "MM"  # Myanmar
    KH = "KH"  # Cambodia
    LA = "LA"  # Laos
    BN = "BN"  # Brunei
    TL = "TL"  # East Timor
    
    # Asia del Sur
    IN = "IN"  # India
    PK = "PK"  # Pakistan
    BD = "BD"  # Bangladesh
    LK = "LK"  # Sri Lanka
    NP = "NP"  # Nepal
    BT = "BT"  # Bhutan
    MV = "MV"  # Maldives
    AF = "AF"  # Afghanistan
    
    # Asia Occidental / Medio Oriente
    TR = "TR"  # Turkey
    IR = "IR"  # Iran
    IQ = "IQ"  # Iraq
    SA = "SA"  # Saudi Arabia
    IL = "IL"  # Israel
    JO = "JO"  # Jordan
    LB = "LB"  # Lebanon
    SY = "SY"  # Syria
    YE = "YE"  # Yemen
    OM = "OM"  # Oman
    AE = "AE"  # United Arab Emirates
    QA = "QA"  # Qatar
    KW = "KW"  # Kuwait
    BH = "BH"  # Bahrain
    GE = "GE"  # Georgia
    AM = "AM"  # Armenia
    AZ = "AZ"  # Azerbaijan
    
    # África del Norte
    EG = "EG"  # Egypt
    LY = "LY"  # Libya
    TN = "TN"  # Tunisia
    DZ = "DZ"  # Algeria
    MA = "MA"  # Morocco
    SD = "SD"  # Sudan
    SS = "SS"  # South Sudan
    
    # África Occidental
    NG = "NG"  # Nigeria
    GH = "GH"  # Ghana
    SN = "SN"  # Senegal
    ML = "ML"  # Mali
    BF = "BF"  # Burkina Faso
    NE = "NE"  # Niger
    GN = "GN"  # Guinea
    SL = "SL"  # Sierra Leone
    LR = "LR"  # Liberia
    CI = "CI"  # Ivory Coast
    TG = "TG"  # Togo
    BJ = "BJ"  # Benin
    MR = "MR"  # Mauritania
    GM = "GM"  # Gambia
    GW = "GW"  # Guinea-Bissau
    CV = "CV"  # Cape Verde
    ST = "ST"  # São Tomé and Príncipe
    
    # África Oriental
    KE = "KE"  # Kenya
    TZ = "TZ"  # Tanzania
    UG = "UG"  # Uganda
    RW = "RW"  # Rwanda
    BI = "BI"  # Burundi
    ET = "ET"  # Ethiopia
    SO = "SO"  # Somalia
    ER = "ER"  # Eritrea
    DJ = "DJ"  # Djibouti
    MG = "MG"  # Madagascar
    MU = "MU"  # Mauritius
    SC = "SC"  # Seychelles
    KM = "KM"  # Comoros
    
    # África Central
    CD = "CD"  # Democratic Republic of Congo
    CG = "CG"  # Republic of Congo
    CF = "CF"  # Central African Republic
    TD = "TD"  # Chad
    CM = "CM"  # Cameroon
    GQ = "GQ"  # Equatorial Guinea
    GA = "GA"  # Gabon
    
    # África del Sur
    ZA = "ZA"  # South Africa
    ZW = "ZW"  # Zimbabwe
    BW = "BW"  # Botswana
    NA = "NA"  # Namibia
    ZM = "ZM"  # Zambia
    MW = "MW"  # Malawi
    MZ = "MZ"  # Mozambique
    AO = "AO"  # Angola
    LS = "LS"  # Lesotho
    SZ = "SZ"  # Eswatini
    
    # Oceanía
    AU = "AU"  # Australia
    NZ = "NZ"  # New Zealand
    PG = "PG"  # Papua New Guinea
    FJ = "FJ"  # Fiji
    SB = "SB"  # Solomon Islands
    VU = "VU"  # Vanuatu
    WS = "WS"  # Samoa
    TO = "TO"  # Tonga
    PW = "PW"  # Palau
    FM = "FM"  # Micronesia
    MH = "MH"  # Marshall Islands
    KI = "KI"  # Kiribati
    TV = "TV"  # Tuvalu
    NR = "NR"  # Nauru
    CK = "CK"  # Cook Islands

def get_country_from_name(country_name: str) -> Country | None:
    """
    Convierte un código ISO alpha-2 al enum Country
    
    Args:
        country_name: Código ISO alpha-2 (ej: "AR", "US", "MX")
    
    Returns:
        Country enum o None si no se encuentra
    
    Examples:
        get_country_from_name("AR") -> Country.AR
        get_country_from_name("US") -> Country.US
        get_country_from_name("MX") -> Country.MX
    """
    # Solo aceptar códigos ISO alpha-2 (exactamente 2 caracteres, mayúsculas)
    if len(country_name) == 2 and country_name.isupper():
        try:
            return Country(country_name)
        except ValueError:
            pass
    
    return None

def get_all_countries() -> list[Country]:
    """
    Obtiene una lista de todos los países disponibles
    
    Returns:
        Lista de todos los países como enums Country
    """
    return list(Country)
