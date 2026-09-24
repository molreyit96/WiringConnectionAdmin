# UI/UX — Mobile PWA (flow B, tablet) & desktop plan

Estatus: **Fase 1 (quick wins visuales seguros) terminada y commiteada** en la rama
`feature/pwa-testing`. Este doc captura el análisis de contraste/tokens del shell PWA
móvil y lo que queda pendiente (calendario de `home.html`, docs, Fase 2 escritorio).

---

## 1. Diagnóstico (dónde estaba el problema)

El shell PWA móvil (`app/templates/mobile/*`, CSS en `app/static/mobile/css/`) usaba
3 azules/verdes en competencia sobre el header cian `card-header-wc` (token
`--wc-accent: #0e7490`):

| Elemento | Color previo | Contraste vs cian #0e7490 | Resultado |
|---|---|---|---|
| Iconos/links en header (verde Bootstrap `#198754`) | verde | ~1.18:1 | ❌ falla 4.5:1 texto / 3:1 UI |
| `btn-primary` (`#007bff` / `#0d6efd`) | azul header | ~1.18:1 / ~1:1 | ❌ falla |
| `btn-info` (`#0dcaf0`) | cian claro | ~2.74:1 | ❌ falla texto |
| Badges de estado | verde `bg-success` | ~1.2:1 | ❌ falla |

Además de un triplete de azules inconsistentes usados por todo el shell
(`#007bff`, `#0d6efd`, `#0e7490`) que debían unificarse en un solo acento.

---

## 2. Fase 1 — lo ya commiteado (rama `feature/pwa-testing`)

### 2.1 Tokens de diseño + restaurar `card-header-wc` (commit b15afa8)
- Nuevo `app/static/mobile/css/tokens.css` con la paleta unificada:
  `--wc-ink`, `--wc-accent (#0e7490)`, `--wc-accent-dark`, `--wc-bg`,
  `--wc-ok`, `--wc-danger`, `--wc-header`, `--wc-header-ink (#ffffff)`.
- Se restauró la clase `.card-header-wc` (solo existía en el backup `index_bkp`).
- Los `.btn-primary` se remapean al token acento para eliminar el azul `#007bff`.

### 2.2 PWA shell en español (commit 719062e)
- `html lang="es"` en `index.html` (era `lang="en"`).
- DataTables del shell: textos de UI en español (`buscar`, `mostrando página…`).

### 2.3 Contraste de elementos interactivos dentro del header cian (commit aaf3135)
Solo CSS, sin cambios de layout/JS. Añadido en `tokens.css`:
- **Iconos/links dentro de `card-header-wc`**: tinta blanca sobre cian (≥7:1).
- **Badges de estado dentro del header**: píldora clara (`#0e7490` sobre
  `rgba(255,255,255,.92)` ≈ 8.3:1).
- **Botones dentro del header (no `.btn-light`/`.btn-outline-light`)**:
  contorno claro con tinta blanca, sin desbordar el header.

⚠️ Regla de trabajo: solo se aplicaron cambios **visuales seguros** (contraste,
tokens, idioma). **No** se tocó layout ni interacción.

---

## 3. Pendiente — propuestas acordadas (esperando OK / para próximas sesiones)

### 3.1 Calendario de `home.html` (flow B)
Redefinir los botones de día del calendario semanal con **semántica visual clara**:
- **Día seleccionado** → `btn-success` con borde/peso destacado + badge de total.
- **Día disponible / sin registro** → `btn-info` tonalidad acento, sin arriba-marcado.
- **Día bloqueado** (fuera de rango/periodo inactivo) → deshabilitado/gris.
- **Día con total** → badge `bg-success` con `Total` (`intcomma`) en la esquina
  (los bounds `position-absolute top-0 start-100` son los candidatos a limpiar).

Criterio: todo cambio de calendario debe respetar contraste 4.5:1 texto / 3:1 UI
y no romper las URLs `/mobile/crew/{period}/{day}/0/{location}`.

### 3.2 Persistencia de docs
- `docs/uiux-mobile.md` (este archivo).

### 3.3 Calendario para `/mobile/home/{location}` (si aplica)
Revisar también la lista "Rejected Dailys" en `home.html`:
- Iconos/links sobre header cian ya quedaron en blanco vía tokens 2.3.
- Barras `btn-danger` + `fa-pen-to-square` — validar contrastes restantes
  (los iconos no-importados de la lista de rechazados usan `color: green`
  inline que rompe el patrón).

### 3.4 Fase 2 — Escritorio (flow C)
Mismo plan de contraste con tokens en plantillas desktop:
- Inventariar cabezeras cian fuera del móvil.
- Aplicar el set de reglas de `tokens.css` equivalentes (scoped al header).
- Buscar `#007bff` / `#0d6efd` / `#0e7490` y `color: green`/`red` inline en
  plantillas de escritorio.

---

## 4. Archivos clave del alcance
- `app/static/mobile/css/tokens.css` — tokens de diseño + fixes de contraste.
- `app/templates/mobile/index.html` — shell PWA (lang=es, DataTables en español).
- `app/templates/mobile/home.html` — calendario semanal (weeks 1/2, rechazados).
- `app/templates/mobile/crew.html` — vista de crew (header cian, badges).
- `.gitignore` — ignora `*.dump`, `*.dump.gz` (backups de DB).

---

## 5. Hoja de ruta pendiente (orden sugerido)
1. OK del usuario → aplicar calendario de `home.html` (3.1).
2. OK del usuario → Fase 2 escritorio (3.4).
3. (Opcional) auditoría de plantillas desktop para azules/verdes hardcodeados.
