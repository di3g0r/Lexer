# Analizador Léxico — Triton GPU Kernel
**TC3002B · Compiladores · Módulo 3**

---

## Objetivo

Este programa implementa un **analizador léxico (scanner)** para el lenguaje Triton GPU Kernel. Lee una expresión escrita por el usuario en la terminal, la recorre carácter por carácter, y clasifica cada secuencia en un **token** con su identificador numérico, nombre y lexema.

El lexer **no requiere código sintácticamente correcto** — su única responsabilidad es verificar que cada símbolo sea un token válido. Por ejemplo, `() 2 + 4` es una entrada completamente válida.

Al finalizar produce tres salidas:
- Lista de tokens reconocidos (ID, nombre, lexema, columna)
- Tabla de símbolos (identificadores, números y cadenas)
- Reporte de errores léxicos

---

## Cómo ejecutar

Requiere Python 3.8+ y únicamente la biblioteca estándar (`re`). Sin dependencias externas.

```bash
python triton_lexer_v2.py
```

---

## Arquitectura

El archivo se divide en 8 secciones:

| Sección | Contenido |
|---|---|
| 1 — `TOKEN_ID` | Diccionario que asigna un número único (1–57) a cada tipo de token |
| 2 — DFAs | Definición de los 6 autómatas finitos deterministas con tablas de transición |
| 3 — Motor `delta()` | Función común que ejecuta cualquier DFA dado un estado y un carácter |
| 4 — `REGEX_TOKENS` | Lista de patrones regex compilados para los tokens no-DFA |
| 5 — Tabla de símbolos | Diccionario global y función `add_symbol()` |
| 6 — `tokenize()` | Función principal del scanner |
| 7 — Salida | `print_tokens()`, `print_symbol_table()`, `print_errors()` |
| 8 — Main | Punto de entrada: lee input, llama `tokenize()`, imprime resultados |

---

## Tokens con Autómata Finito Determinista (DFA)

Los siguientes tokens se reconocen mediante DFAs formales con tabla de transiciones explícita y función `delta()`. Cada DFA define estados, estado inicial, estados de aceptación, tabla de transiciones y función de clasificación de caracteres.

### IF / ELSE / ELIF

Un solo DFA compartido reconoce las tres palabras clave. Verifica que el siguiente carácter no sea alfanumérico para evitar que `iffy` sea reconocido como `IF`.


### WHILE

DFA lineal de 5 transiciones.

### NAME — Identificadores

Reconoce `[a-zA-Z_][a-zA-Z0-9_]*`. Clases: `letter` (letra o `_`), `digit` (dígito).


### NUMBER — Enteros y decimales

Reconoce `\d+` y `\d+\.\d+`. El estado `DOT_ST` no acepta — un punto sin dígito posterior no es válido.


### STRING — Cadenas de texto

Reconoce `"..."` y `'...'`. El tipo de comilla de apertura determina cuál cierra la cadena. Soporta secuencias de escape (`\"`, `\'`, etc.).

> **Manejo de error:** si la cadena nunca se cierra, el DFA devuelve el token especial `ERROR` con todo el texto consumido. El tokenizer reporta el error y avanza la posición completa para no reescanear el contenido interno.

### Operadores Aritméticos

Un solo DFA reconoce los 7 operadores, distinguiendo `*` vs `**` y `/` vs `//`.

---

## Tokens con Expresión Regular (Regex)

Se aplican con `pattern.match(source, pos)` en orden — el primero que hace match gana. Los patrones más específicos o largos van primero.

---

## Flujo de `tokenize()`

Para cada posición en el string de entrada, los reconocedores se aplican en este orden de prioridad:

| Prioridad | Condición | Reconocedor |
|---|---|---|
| 1 | Espacio o tab | Skip |
| 2 | `"` o `'` | DFA_STRING |
| 3 | `i` o `e` | DFA_IF_ELSE_ELIF |
| 4 | `w` | DFA_WHILE |
| 5 | Dígito | DFA_NUMBER |
| 6 | Letra o `_` | DFA_NAME |
| 7 | `+`, `-`, `*`, `/`, `%` | DFA_ARITH |
| 8 | Cualquier otro | REGEX_TOKENS (en orden) |
| — | Sin match | Error léxico (avanza 1 carácter) |

---

## Tests

### Test 1 — Expresión aritmética básica
**Entrada:** `() 2 + 4`

<img width="445" height="492" alt="image" src="https://github.com/user-attachments/assets/aff8f727-0703-4419-9566-3997856de1ab" />

---

### Test 2 — Keywords con DFA
**Entrada:** `if x else y elif z while a`

<img width="444" height="563" alt="image" src="https://github.com/user-attachments/assets/7c2f2c2f-55bc-4b35-80a8-ead55eda65e2" />

---

### Test 3 — Cadenas válidas
**Entrada:** `"Hola mundo" 'Python'`

<img width="452" height="447" alt="image" src="https://github.com/user-attachments/assets/02994368-1206-465c-b191-c1eb195a4d92" />

---

### Test 4 — String sin cerrar
**Entrada:** `"hola`

<img width="449" height="352" alt="image" src="https://github.com/user-attachments/assets/df7e3663-e68f-4080-b450-445461223dd0" />

---

### Test 5 — Operadores ambiguos
**Entrada:** `* ** / // + -`

<img width="442" height="395" alt="image" src="https://github.com/user-attachments/assets/ebd44b7b-aae5-4f95-a09d-4eacc91f02ac" />

---

### Test 6 — Número decimal
**Entrada:** `3.14 + 2 * 0.5`

<img width="440" height="515" alt="image" src="https://github.com/user-attachments/assets/90982cae-f92b-4615-98ef-e3a58067ae48" />

---

### Test 7 — Carácter no reconocido
**Entrada:** `x $ y ? z`

<img width="439" height="520" alt="image" src="https://github.com/user-attachments/assets/15f39f30-746f-45d0-833f-51749ade94fd" />

---

### Test 8 — Expresión mixta completa
**Entrada:** `if myVar == 3.14 else 'ok'`

<img width="448" height="527" alt="image" src="https://github.com/user-attachments/assets/07149ac7-71bb-4ad8-ac52-1d5b47ff387f" />
