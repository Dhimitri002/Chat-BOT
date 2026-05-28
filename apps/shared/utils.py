# ═══════════════════════════════════════════════════════════════
# Flora Platform — Utilitários Compartilhados
# ═══════════════════════════════════════════════════════════════
# Funções utilitárias para formatação, validação e armazenamento
# local utilizadas pelos apps admin e client.
# ═══════════════════════════════════════════════════════════════

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


# ═══════════════════════════════════════════════════════════════
# Formatação de Telefone (Brasil)
# ═══════════════════════════════════════════════════════════════

def format_phone(phone: str) -> str:
    """Formata número de telefone brasileiro.

    Aceita números com ou sem DDD, com ou sem código do país.
    Remove todos os caracteres não numéricos antes de formatar.

    Args:
        phone: Número de telefone (ex: '11999887766', '11 99988-7766').

    Returns:
        Número formatado (ex: '(11) 99988-7766', '+55 11 99988-7766').

    Exemplos:
        >>> format_phone("11999887766")
        '(11) 99988-7766'
        >>> format_phone("5511999887766")
        '+55 11 99988-7766'
        >>> format_phone("1199988776")
        '1199988776'
    """
    # Remove tudo que não é dígito
    digits = re.sub(r"\D", "", phone)

    if not digits:
        return ""

    # Com código do país (13 dígitos: 55 + 2 DDD + 9 celular)
    if len(digits) == 13 and digits.startswith("55"):
        ddd = digits[4:6]
        number = digits[6:]
        return f"+55 {ddd} {number[:5]}-{number[5:]}"

    # Com código do país (12 dígitos: 55 + 2 DDD + 8 fixo)
    if len(digits) == 12 and digits.startswith("55"):
        ddd = digits[4:6]
        number = digits[6:]
        return f"+55 {ddd} {number[:4]}-{number[4:]}"

    # Celular com DDD (11 dígitos)
    if len(digits) == 11:
        ddd = digits[:2]
        number = digits[2:]
        return f"({ddd}) {number[:5]}-{number[5:]}"

    # Fixo com DDD (10 dígitos)
    if len(digits) == 10:
        ddd = digits[:2]
        number = digits[2:]
        return f"({ddd}) {number[:4]}-{number[4:]}"

    # Sem DDD (9 dígitos celular)
    if len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"

    # Sem DDD (8 dígitos fixo)
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:]}"

    # Retorna como está se não corresponder a nenhum padrão
    return digits


# ═══════════════════════════════════════════════════════════════
# Formatação de Data Relativa
# ═══════════════════════════════════════════════════════════════

def format_date(date_input: Any, relative: bool = True) -> str:
    """Formata data para exibição amigável.

    Suporta objetos datetime, strings ISO e timestamps Unix.
    Pode retornar formato relativo (ex: 'há 5 minutos') ou absoluto.

    Args:
        date_input: Data como datetime, string ISO ou timestamp Unix.
        relative: Se True, retorna formato relativo. Se False, absoluto.

    Returns:
        String formatada.

    Exemplos:
        >>> format_date(datetime.now() - timedelta(minutes=5))
        'agora'
        >>> format_date(datetime.now() - timedelta(hours=3))
        'há 3h'
        >>> format_date("2024-01-15T10:30:00", relative=False)
        '15/01/2024 10:30'
    """
    # Converte para datetime
    dt: Optional[datetime] = None

    if isinstance(date_input, datetime):
        dt = date_input
    elif isinstance(date_input, (int, float)):
        try:
            dt = datetime.fromtimestamp(date_input, tz=timezone.utc)
        except (OSError, ValueError):
            return str(date_input)
    elif isinstance(date_input, str):
        # Tenta vários formatos
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_input, fmt)
                break
            except ValueError:
                continue

    if dt is None:
        return str(date_input)

    # Garante timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    if not relative:
        return dt.strftime("%d/%m/%Y %H:%M")

    # Calcula diferença
    now = datetime.now(timezone.utc)
    diff = now - dt
    total_seconds = int(diff.total_seconds())

    if total_seconds < 0:
        return "agora"

    if total_seconds < 60:
        return "agora"

    if total_seconds < 3600:
        minutes = total_seconds // 60
        return f"há {minutes}min"

    if total_seconds < 86400:
        hours = total_seconds // 3600
        return f"há {hours}h"

    if total_seconds < 604800:  # 7 dias
        days = total_seconds // 86400
        return f"há {days}d"

    if total_seconds < 2592000:  # 30 dias
        weeks = total_seconds // 604800
        return f"há {weeks}sem"

    if total_seconds < 31536000:  # 365 dias
        months = total_seconds // 2592000
        return f"há {months}mes"

    years = total_seconds // 31536000
    return f"há {years}ano"


# ═══════════════════════════════════════════════════════════════
# Geração de Cor de Avatar
# ═══════════════════════════════════════════════════════════════

# Paleta de cores vibrantes para avatares
AVATAR_COLORS = [
    (0.424, 0.388, 1.0, 1.0),    # Roxo Flora (#6C63FF)
    (1.0, 0.420, 0.616, 1.0),     # Rosa Flora (#FF6B9D)
    (0.0, 0.737, 0.831, 1.0),     # Ciano (#00BCD4)
    (0.302, 0.686, 0.314, 1.0),   # Verde (#4CAF50)
    (1.0, 0.757, 0.027, 1.0),     # Amarelo (#FFC107)
    (0.914, 0.118, 0.388, 1.0),   # Magenta (#E91E63)
    (0.259, 0.647, 0.961, 1.0),   # Azul (#42A5F5)
    (1.0, 0.6, 0.0, 1.0),         # Laranja (#FF9800)
    (0.608, 0.153, 0.682, 1.0),   # Roxo escuro (#9C27B0)
    (0.0, 0.588, 0.533, 1.0),     # Teal (#009688)
    (0.957, 0.263, 0.212, 1.0),   # Vermelho (#F44336)
    (0.475, 0.333, 0.282, 1.0),   # Marrom (#795548)
    (0.376, 0.490, 0.545, 1.0),   # Cinza azulado (#607D8B)
    (0.745, 0.565, 0.961, 1.0),   # Lavanda (#BB86FC)
    (0.0, 0.835, 0.784, 1.0),     # Turquesa (#00D4C8)
    (1.0, 0.843, 0.0, 1.0),       # Dourado (#FFD700)
]


def generate_avatar_color(text: str) -> tuple:
    """Gera uma cor consistente a partir de um texto.

    Usa hash do texto para selecionar uma cor da paleta de avatares.
    O mesmo texto sempre produz a mesma cor.

    Args:
        text: Texto base (ex: nome do usuário).

    Returns:
        Tupla RGBA (0-1).
    """
    if not text:
        return AVATAR_COLORS[0]

    hash_value = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
    index = hash_value % len(AVATAR_COLORS)
    return AVATAR_COLORS[index]


# ═══════════════════════════════════════════════════════════════
# Validação
# ═══════════════════════════════════════════════════════════════

def validate_phone(phone: str) -> bool:
    """Valida número de telefone brasileiro.

    Aceita formatos com DDD + 8 ou 9 dígitos, com ou sem código do país.

    Args:
        phone: Número de telefone a validar.

    Returns:
        True se válido, False caso contrário.

    Exemplos:
        >>> validate_phone("11999887766")
        True
        >>> validate_phone("(11) 99988-7766")
        True
        >>> validate_phone("123")
        False
    """
    digits = re.sub(r"\D", "", phone)

    # Com código do país
    if digits.startswith("55"):
        digits = digits[2:]

    # Deve ter 10 (fixo) ou 11 (celular) dígitos
    if len(digits) not in (10, 11):
        return False

    # DDD deve ser entre 11 e 99
    ddd = int(digits[:2])
    if ddd < 11 or ddd > 99:
        return False

    # Celular deve começar com 9
    if len(digits) == 11 and digits[2] != "9":
        return False

    return True


def validate_email(email: str) -> bool:
    """Valida formato de email.

    Verifica se o email tem formato válido usando regex.

    Args:
        email: Endereço de email a validar.

    Returns:
        True se válido, False caso contrário.

    Exemplos:
        >>> validate_email("usuario@email.com")
        True
        >>> validate_email("invalido")
        False
    """
    if not email or not isinstance(email, str):
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


# ═══════════════════════════════════════════════════════════════
# Armazenamento Local JSON
# ═══════════════════════════════════════════════════════════════

# Diretório base para dados locais
LOCAL_DATA_DIR: Path = Path.home() / ".flora"


def save_local_json(filename: str, data: Any) -> Path:
    """Salva dados como JSON no diretório local.

    Cria o diretório se não existir. Útil para cache, preferências
    e dados temporários dos aplicativos.

    Args:
        filename: Nome do arquivo (ex: 'preferences.json').
        data: Dados a salvar (devem ser serializáveis em JSON).

    Returns:
        Caminho completo do arquivo salvo.

    Exemplos:
        >>> save_local_json("config.json", {"theme": "dark"})
        PosixPath('/home/user/.flora/config.json')
    """
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = LOCAL_DATA_DIR / filename

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    return file_path


def load_local_json(filename: str, default: Any = None) -> Any:
    """Carrega dados JSON do diretório local.

    Args:
        filename: Nome do arquivo a carregar.
        default: Valor padrão se o arquivo não existir.

    Returns:
        Dados carregados ou valor padrão.

    Exemplos:
        >>> load_local_json("config.json", default={})
        {'theme': 'dark'}
    """
    file_path = LOCAL_DATA_DIR / filename

    if not file_path.exists():
        return default

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def delete_local_json(filename: str) -> bool:
    """Remove um arquivo JSON local.

    Args:
        filename: Nome do arquivo a remover.

    Returns:
        True se removido com sucesso, False se não existia.
    """
    file_path = LOCAL_DATA_DIR / filename

    if file_path.exists():
        file_path.unlink()
        return True
    return False


# ═══════════════════════════════════════════════════════════════
# Utilitários Adicionais
# ═══════════════════════════════════════════════════════════════

def get_initials(name: str, max_chars: int = 2) -> str:
    """Extrai iniciais de um nome.

    Args:
        name: Nome completo.
        max_chars: Número máximo de caracteres (padrão: 2).

    Returns:
        Iniciais em maiúsculas.

    Exemplos:
        >>> get_initials("João da Silva")
        'JS'
        >>> get_initials("Maria")
        'M'
    """
    if not name:
        return "?"

    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()[:max_chars]
    return parts[0][0].upper()[:max_chars]


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Trunca texto com sufixo.

    Args:
        text: Texto original.
        max_length: Comprimento máximo.
        suffix: Sufixo para texto truncado.

    Returns:
        Texto truncado se necessário.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_currency(value: float, currency: str = "R$") -> str:
    """Formata valor monetário brasileiro.

    Args:
        value: Valor numérico.
        currency: Símbolo da moeda.

    Returns:
        Valor formatado (ex: 'R$ 1.234,56').
    """
    return f"{currency} {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
