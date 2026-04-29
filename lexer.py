import re

#Mapear Tokens a un ID
TOKEN_ID = {
    "DEF": 1, "RETURN": 2, "IF": 3, "ELSE": 4, "ELIF": 5,
    "FOR": 6, "WHILE": 7, "IN": 8, "IS": 9,
    "AND": 10, "OR": 11, "NOT": 12,
    "TRUE": 13, "FALSE": 14, "NONE_KW": 15,
    "PASS": 16, "BREAK": 17, "CONTINUE": 18,
    "NAME": 19, "NUMBER": 20, "STRING": 21,
    "PLUS": 22, "MINUS": 23, "TIMES": 24, "DIVIDE": 25,
    "FLOORDIV": 26, "MOD": 27, "POWER": 28,
    "LT": 29, "GT": 30, "LE": 31, "GE": 32, "EQ": 33, "NE": 34,
    "ASSIGN": 35, "PLUSEQ": 36, "MINUSEQ": 37, "TIMESEQ": 38, "DIVEQ": 39,
    "LPAREN": 40, "RPAREN": 41, "LBRACKET": 42, "RBRACKET": 43,
    "LBRACE": 44, "RBRACE": 45, "COMMA": 46, "COLON": 47,
    "DOT": 48, "AT": 49, "ARROW": 50, "TILDE": 51, "AMPERSAND": 52,
    "PIPE": 53, "CARET": 54, "LSHIFT": 55, "RSHIFT": 56,
    "EOF": 57,
}

#DFAS, hechos con diccionarios las llavez valor representan los estados, transiciones y estados aceptados

DFA_IF_ELSE_ELIF = {
    "initial": "S",
    "accepting": {
        "IF_ST":   "IF",
        "ELSE_ST": "ELSE",
        "ELIF_ST": "ELIF",
    },
    "transitions": {
        ("S",       "i"): "I",
        ("S",       "e"): "E",
        ("I",       "f"): "IF_ST",
        ("E",       "l"): "EL",
        ("EL",      "s"): "ELS",
        ("EL",      "i"): "ELI",
        ("ELS",     "e"): "ELSE_ST",
        ("ELI",     "f"): "ELIF_ST",
    },
}

DFA_WHILE = {
    "initial": "S",
    "accepting": {
        "WHILE_ST": "WHILE",
    },
    "transitions": {
        ("S",        "w"): "W",
        ("W",        "h"): "WH",
        ("WH",       "i"): "WHI",
        ("WHI",      "l"): "WHIL",
        ("WHIL",     "e"): "WHILE_ST",
    },
}

#Funcion auxiliar para el DFA de Name, para distinguir que caracter se leyo y continuar al estado correcto
def _classify_name(ch):
    if ch.isalpha() or ch == "_":
        return "letter"
    if ch.isdigit():
        return "digit"
    return "other"

DFA_NAME = {
    "initial": "S",
    "accepting": {
        "NAME_ST": "NAME",
    },
    "transitions": {
        ("S",       "letter"): "NAME_ST",
        ("NAME_ST", "letter"): "NAME_ST",
        ("NAME_ST", "digit"):  "NAME_ST",
    },
    "classify": _classify_name,
}

#Funcion auxiliar para el DFA de Number, para poder tener Integers y Floats
def _classify_number(ch):
    if ch.isdigit():
        return "digit"
    if ch == ".":
        return "dot"
    return "other"

DFA_NUMBER = {
    "initial": "S",
    "accepting": {
        "INT_ST":   "NUMBER",
        "FLOAT_ST": "NUMBER",
    },
    "transitions": {
        ("S",        "digit"): "INT_ST",
        ("INT_ST",   "digit"): "INT_ST",
        ("INT_ST",   "dot"):   "DOT_ST",
        ("DOT_ST",   "digit"): "FLOAT_ST",
        ("FLOAT_ST", "digit"): "FLOAT_ST",
    },
    "classify": _classify_number,
}

#Funcion auxiliar para el DFA de strings
def _classify_string(ch, open_quote):
    if ch == open_quote:
        return "open"
    if ch == "\\":
        return "escape"
    return "other"

DFA_STRING = {
    "initial": "S",
    "accepting": {
        "STRING_ST": "STRING",
    },
    # Las transiciones se calculan dinámicamente en dfa_string_run()
    # porque dependen del carácter de apertura.
    "transitions": {
        ("S",      '"'):    "OPEN_D",
        ("S",      "'"):    "OPEN_S",
        # dentro de comilla doble
        ("OPEN_D", "other"):  "OPEN_D",
        ("OPEN_D", "escape"): "ESC_D",
        ("OPEN_D", "open"):   "STRING_ST",
        ("ESC_D",  "other"):  "OPEN_D",
        ("ESC_D",  "escape"): "OPEN_D",
        ("ESC_D",  "open"):   "OPEN_D",
        # dentro de comilla simple
        ("OPEN_S", "other"):  "OPEN_S",
        ("OPEN_S", "escape"): "ESC_S",
        ("OPEN_S", "open"):   "STRING_ST",
        ("ESC_S",  "other"):  "OPEN_S",
        ("ESC_S",  "escape"): "OPEN_S",
        ("ESC_S",  "open"):   "OPEN_S",
    },
}

def _classify_arith(ch):
    if ch == "+":  return "plus"
    if ch == "-":  return "minus"
    if ch == "*":  return "star"
    if ch == "/":  return "slash"
    if ch == "%":  return "pct"
    return "other"

DFA_ARITH = {
    "initial": "S",
    "accepting": {
        "PLUS_ST":     "PLUS",
        "MINUS_ST":    "MINUS",
        "STAR_ST":     "TIMES",
        "POWER_ST":    "POWER",
        "SLASH_ST":    "DIVIDE",
        "FLOORDIV_ST": "FLOORDIV",
        "MOD_ST":      "MOD",
    },
    "transitions": {
        ("S",        "plus"):  "PLUS_ST",
        ("S",        "minus"): "MINUS_ST",
        ("S",        "star"):  "STAR_ST",
        ("S",        "slash"): "SLASH_ST",
        ("S",        "pct"):   "MOD_ST",
        ("STAR_ST",  "star"):  "POWER_ST",
        ("SLASH_ST", "slash"): "FLOORDIV_ST",
    },
    "classify": _classify_arith,
}

# Funcion delta para recorrer los DFAs

def delta(dfa, state, ch):
    """
    Función de transición.
    Aplica dfa['classify'](ch) si existe, si no usa ch directamente.
    Devuelve el nuevo estado, o None si no hay transición (estado muerto).
    """
    classify = dfa.get("classify", lambda c: c)
    char_class = classify(ch)
    return dfa["transitions"].get((state, char_class), None)


def dfa_run(dfa, text, pos):
    """
    Ejecuta el DFA desde text[pos] hasta que no haya transición.
    Devuelve (token_name, lexema) si terminó en estado aceptor,
    o (None, None) si no reconoció nada.

    Implementa el principio del match más largo (maximal munch):
    guarda el último estado aceptor alcanzado y su posición.
    """
    state = dfa["initial"]
    i = pos
    last_accept_pos = -1
    last_accept_token = None

    while i < len(text):
        ch = text[i]
        next_state = delta(dfa, state, ch)
        if next_state is None:
            break
        state = next_state
        i += 1
        if state in dfa["accepting"]:
            last_accept_pos = i
            last_accept_token = dfa["accepting"][state]

    if last_accept_token is not None:
        return last_accept_token, text[pos:last_accept_pos]
    return None, None


def dfa_string_run(text, pos):
    """
    Ejecuta DFA_STRING con manejo especial de comilla de apertura.
    El tipo de comilla (simple o doble) se fija al leer el primer char.
    """
    if pos >= len(text):
        return None, None
    open_quote = text[pos]
    if open_quote not in ('"', "'"):
        return None, None

    state = "OPEN_D" if open_quote == '"' else "OPEN_S"
    esc_state = "ESC_D" if open_quote == '"' else "ESC_S"
    i = pos + 1  # ya consumimos la comilla de apertura

    while i < len(text):
        ch = text[i]
        cls = _classify_string(ch, open_quote)
        if state in ("OPEN_D", "OPEN_S"):
            if cls == "open":
                # cerró la cadena
                return "STRING", text[pos:i + 1]
            elif cls == "escape":
                state = esc_state
            # else: sigue en el mismo estado
        elif state in ("ESC_D", "ESC_S"):
            # el char tras \ se consume siempre, volvemos al estado normal
            state = "OPEN_D" if open_quote == '"' else "OPEN_S"
        i += 1

    # Si llegamos aquí, la cadena nunca se cerró es decir error léxico
    # Devolvemos "ERROR" con todo lo que se consumió
    # avanzamos la posición correctamente y no reescaneamos los chars internos.
    return "ERROR", text[pos:i]


def dfa_if_else_elif_run(text, pos):
    """
    Ejecuta DFA_IF_ELSE_ELIF.
    Solo acepta si la palabra termina en un no-alnum (para no confundir
    'iffy' con 'if').
    """
    token_name, lexeme = dfa_run(DFA_IF_ELSE_ELIF, text, pos)
    if token_name is None:
        return None, None
    # Verificar que el siguiente char no sea alnum/_
    end = pos + len(lexeme)
    if end < len(text) and (text[end].isalnum() or text[end] == "_"):
        return None, None
    return token_name, lexeme


def dfa_while_run(text, pos):
    """Igual que el anterior pero para WHILE."""
    token_name, lexeme = dfa_run(DFA_WHILE, text, pos)
    if token_name is None:
        return None, None
    end = pos + len(lexeme)
    if end < len(text) and (text[end].isalnum() or text[end] == "_"):
        return None, None
    return token_name, lexeme


def dfa_name_run(text, pos):
    """Ejecuta DFA_NAME."""
    return dfa_run(DFA_NAME, text, pos)


def dfa_number_run(text, pos):
    """Ejecuta DFA_NUMBER."""
    return dfa_run(DFA_NUMBER, text, pos)


def dfa_arith_run(text, pos):
    """Ejecuta DFA_ARITH."""
    return dfa_run(DFA_ARITH, text, pos)

#Regex

REGEX_TOKENS = [
    ("DEF",      r'\bdef\b'),
    ("RETURN",   r'\breturn\b'),
    ("FOR",      r'\bfor\b'),
    ("IN",       r'\bin\b'),
    ("IS",       r'\bis\b'),
    ("AND",      r'\band\b'),
    ("OR",       r'\bor\b'),
    ("NOT",      r'\bnot\b'),
    ("TRUE",     r'\bTrue\b'),
    ("FALSE",    r'\bFalse\b'),
    ("NONE_KW",  r'\bNone\b'),
    ("PASS",     r'\bpass\b'),
    ("BREAK",    r'\bbreak\b'),
    ("CONTINUE", r'\bcontinue\b'),
    ("LE",       r'<='),
    ("GE",       r'>='),
    ("EQ",       r'=='),
    ("NE",       r'!='),
    ("PLUSEQ",   r'\+='),
    ("MINUSEQ",  r'-='),
    ("TIMESEQ",  r'\*='),
    ("DIVEQ",    r'/='),
    ("LSHIFT",   r'<<'),
    ("RSHIFT",   r'>>'),
    ("LT",       r'<'),
    ("GT",       r'>'),
    ("ASSIGN",   r'='),
    ("ARROW",    r'->'),
    ("LPAREN",   r'\('),
    ("RPAREN",   r'\)'),
    ("LBRACKET", r'\['),
    ("RBRACKET", r'\]'),
    ("LBRACE",   r'\{'),
    ("RBRACE",   r'\}'),
    ("COMMA",    r','),
    ("COLON",    r':'),
    ("DOT",      r'\.'),
    ("AT",       r'@'),
    ("TILDE",    r'~'),
    ("AMPERSAND",r'&'),
    ("PIPE",     r'\|'),
    ("CARET",    r'\^'),
]

# Compilar cada regex UNA sola vez
COMPILED_REGEX = [
    (name, re.compile(pattern)) for name, pattern in REGEX_TOKENS
]

#Tabla de Simbolos

symbol_table = {}

def add_symbol(token_name, lexeme, col):
    key = (token_name, lexeme)
    if key not in symbol_table:
        symbol_table[key] = {
            "id":         len(symbol_table) + 1,
            "token_name": token_name,
            "lexeme":     lexeme,
            "first_col":  col,
        }

#Nuestra funcion principal, usa la variable "matched" para encontrar el tipo de token
#Primero trata de hacer match con los DFA y si no encuentra un match trata con los Regex
def tokenize(source):
    """
    Escanea 'source' (una sola línea) y devuelve:
      tokens : lista de tuplas (token_id, token_name, lexeme, col)
      errors : lista de strings con errores léxicos
    """
    tokens = []
    errors = []
    pos = 0
    n = len(source)

    while pos < n:
        if source[pos] == " " or source[pos] == "\t":
            pos += 1
            continue

        matched = False

        #DFA String
        if source[pos] in ('"', "'"):
            tname, lexeme = dfa_string_run(source, pos)
            if tname == "STRING":
                col = pos + 1
                tokens.append((TOKEN_ID[tname], tname, lexeme, col))
                add_symbol(tname, lexeme, col)
                pos += len(lexeme)
                matched = True
            elif tname == "ERROR":
                errors.append(
                    f"  Col {pos + 1}: string sin cerrar '{lexeme}'"
                )
                pos += len(lexeme)
                matched = True

        #DFA if,else,etc
        if not matched and source[pos] in ('i', 'e'):
            tname, lexeme = dfa_if_else_elif_run(source, pos)
            if tname:
                col = pos + 1
                tokens.append((TOKEN_ID[tname], tname, lexeme, col))
                pos += len(lexeme)
                matched = True

        #DFA While
        if not matched and source[pos] == 'w':
            tname, lexeme = dfa_while_run(source, pos)
            if tname:
                col = pos + 1
                tokens.append((TOKEN_ID[tname], tname, lexeme, col))
                pos += len(lexeme)
                matched = True

        #DFA Number
        if not matched and source[pos].isdigit():
            tname, lexeme = dfa_number_run(source, pos)
            if tname:
                col = pos + 1
                tokens.append((TOKEN_ID[tname], tname, lexeme, col))
                add_symbol(tname, lexeme, col)
                pos += len(lexeme)
                matched = True

        #DFA Name
        if not matched and (source[pos].isalpha() or source[pos] == '_'):
            tname, lexeme = dfa_name_run(source, pos)
            if tname:
                col = pos + 1
                tokens.append((TOKEN_ID[tname], tname, lexeme, col))
                add_symbol(tname, lexeme, col)
                pos += len(lexeme)
                matched = True

        #DFA Arithmetic
        if not matched and source[pos] in ('+', '-', '*', '/', '%'):
            tname, lexeme = dfa_arith_run(source, pos)
            if tname:
                col = pos + 1
                tokens.append((TOKEN_ID[tname], tname, lexeme, col))
                pos += len(lexeme)
                matched = True

        #Regex
        if not matched:
            for name, pattern in COMPILED_REGEX:
                m = pattern.match(source, pos)
                if m:
                    lexeme = m.group()
                    col = pos + 1
                    tokens.append((TOKEN_ID[name], name, lexeme, col))
                    pos += len(lexeme)
                    matched = True
                    break

        #Error
        if not matched:
            errors.append(
                f"  Col {pos + 1}: carácter no reconocido '{source[pos]}'"
            )
            pos += 1

    # EOF
    tokens.append((TOKEN_ID["EOF"], "EOF", "", n + 1))
    return tokens, errors

#Output
def print_tokens(tokens):
    print("\n" + "=" * 62)
    print(f"{'LISTA DE TOKENS':^62}")
    print("=" * 62)
    print(f"  {'ID':>4}  {'TOKEN':<14}  {'LEXEMA':<20}  {'COL':>4}")
    print("  " + "-" * 56)
    for tid, tname, lexeme, col in tokens:
        display = lexeme if lexeme else "(vacío)"
        print(f"  {tid:>4}  {tname:<14}  {display:<20}  {col:>4}")
    print("=" * 62)


#Imprimimos la Tabla de Simbolos
def print_symbol_table():
    if not symbol_table:
        print("\n  [Tabla de símbolos vacía]")
        return
    print("\n" + "=" * 62)
    print(f"{'TABLA DE SÍMBOLOS':^62}")
    print("=" * 62)
    print(f"  {'#':>3}  {'TOKEN':<10}  {'LEXEMA':<25}  {'COL':>5}")
    print("  " + "-" * 50)
    for entry in symbol_table.values():
        print(
            f"  {entry['id']:>3}  {entry['token_name']:<10}  "
            f"{entry['lexeme']:<25}  {entry['first_col']:>5}"
        )
    print("=" * 62)


#Cualquier error se imprime aqui
def print_errors(errors):
    if not errors:
        print("\n  [Sin errores léxicos]")
        return
    print("\n" + "=" * 62)
    print(f"{'ERRORES LÉXICOS':^62}")
    print("=" * 62)
    for e in errors:
        print(e)
    print("=" * 62)


#Input
if __name__ == "__main__":
    print("=" * 62)
    print("  Analizador Léxico")
    print("=" * 62)

    source = input("\n  Ingresa una expresión: ")

    # Limpiar tabla de símbolos entre corridas (por si se importa el módulo)
    symbol_table.clear()

    token_list, error_list = tokenize(source)

    print_tokens(token_list)
    print_symbol_table()
    print_errors(error_list)
    print()