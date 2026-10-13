# HabitaGDL — Contexto de Aplicación Web (Para Maquetado)

**Proyecto:** Índice de Habitabilidad Territorial — Zona Metropolitana de Guadalajara  
**Autores:** Daniel Aldana Rubio & Julio Cesar Ortiz Becerra  
**Stack objetivo:** React/Next.js + MapLibre GL + Recharts/Deck.gl + Tailwind CSS  
**Datos:** Parquet en `data/processed/` (listo para consumir via API o DuckDB-WASM)

---

## 1. Visión General del Producto

**HabitaGDL** es una herramienta interactiva para evaluar dónde vivir en la ZMG integrando 8 dimensiones de habitabilidad en un solo índice (IHT 0-100) y mostrando la relación **costo-habitabilidad**.

**Modo principal:** *Operate* (dashboard exploratorio) + *Persuade* (landing + reportes compartibles)

**Usuarios objetivo:**
- Compradores/arrendatarios de vivienda
- Familias con hijos (salud, escuelas, seguridad)
- Personas con sensibilidad respiratoria (calidad aire)
- Tomadores de decisión / investigadores

---

## 2. Arquitectura de Pantallas (IA)

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: Logo | Buscador global | Selector municipio | Tema │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌────────────────────────────────────┐  │
│  │  SIDEBAR     │  │  MAIN CONTENT (área principal)     │  │
│  │  (collapsible)│  │                                    │  │
│  │              │  │  [Vista activa]                      │  │
│  │  • Filtros   │  │                                    │  │
│  │  • Pesos IHT │  │                                    │  │
│  │  • Capas mapa│  │                                    │  │
│  │  • Comparar  │  │                                    │  │
│  └──────────────┘  └────────────────────────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  FOOTER: Metodología | Fuentes | Descargar datos | Contacto │
└─────────────────────────────────────────────────────────────┘
```

### Vistas Principales (Tabs / Rutas)

| Ruta | Vista | Descripción |
|------|-------|-------------|
| `/` | **Landing + Mapa IHT** | Mapa base con capa IHT por localidad, sliders de pesos, top 10 "mejor valor" |
| `/localidad/:clave` | **Perfil de Localidad** | Deep-dive: IHT + 8 dimensiones + servicios + salud + escuelas + aire + riesgos |
| `/comparar` | **Comparador** | 2-3 localidades lado a lado: radar chart, tabla, mini-mapas |
| `/aire` | **Calidad del Aire** | Estaciones, series temporales, rosas de viento estacionales, animación 2024 |
| `/salud` | **Salud y Educación** | Mapa interactivo + top 10 cercanos + filtros tipo/nivel/sostenimiento |
| `/riesgos` | **Riesgos Territoriales** | Capas inundación + cruce localidad-riesgo + búsqueda por dirección |
| `/seguridad` | **Seguridad** | Coropletas por delito/municipio/año + tasas por 100k hab |
| `/metodologia` | **Metodología IHT** | Explicación 8 dimensiones, pesos, normalización, fuentes, limitaciones |

---

## 3. Componentes de UI Requeridos

### 3.1 Mapa Base (MapLibre GL JS)
- **Capa base:** OpenStreetMap / CartoDB Positron / Satellite toggle
- **Capa IHT:** Coropleta por localidad (AGEB/manzana si hay datos) — colores cuantílicos 0-100
- **Capa Salud:** Markers clustering + popover → drawer detalle
- **Capa Escuelas:** Idem, iconos por nivel
- **Capa Riesgos:** Polígonos inundación (alta/media/baja/sin riesgo) con opacidad
- **Capa Aire:** Estaciones + buffer influencia + dirección viento estacional
- **Controles:** Zoom, pitch, rotation, geolocate, fullscreen
- **Interacciones:** Click localidad → navega a `/localidad/:clave`; hover → tooltip IHT + nombre

### 3.2 Panel de Pesos IHT (Sidebar)
```
┌─────────────────────────────┐
│  ⚖️  Pesos del IHT          │
│  [Reset] [Preset: Familias] │
│                             │
│  Vivienda       ████████░░ 15% │
│  Servicios      █████████░ 18% │
│  Movilidad      ██████░░░░ 12% │
│  Salud          ████████░░ 15% │
│  Educación      ███████░░░ 14% │
│  Seguridad      ████████░░ 15% │
│  Riesgos        █████░░░░░ 10% │
│  Ambiente       ██████░░░░ 12% │
│                             │
│  Σ = 100%  •  [Aplicar]     │
└─────────────────────────────┘
```
- **Range sliders** dual thumb (min/max) o single thumb con suma = 100% (redistribución automática)
- **Presets:** Familias, Adultos mayores, Inversionistas, Sensibles al aire, Default
- **Actualización en vivo** del mapa IHT y ranking (debounce 300ms)

### 3.3 Filtros Globales (Sidebar)
- **Municipio:** Multi-select (5 ZMG + "Todos")
- **Rango precio:** Dual slider (compra/renta toggle) — datos SHF futuros
- **Tipo vivienda:** Casa / Depto / Terreno
- **Metros cuadrados:** Slider
- **Año datos:** Selector (para series temporales)

### 3.4 Tarjeta "Top 10 Mejor Valor" (Sidebar / Bottom Sheet Mobile)
```
┌─────────────────────────────┐
│  🏆 Top 10 Costo-Habitabilidad│
│  [Filtros: 🏠 💰 📍]        │
│                             │
│  1. Colinas de San Javier  │
│     IHT: 87 | $4.2M | 120m² │
│     ████████████░░░░░░░░░░  │
│                             │
│  2. La Estancia  ...        │
└─────────────────────────────┘
```
- Click → abre drawer derecho con desglose completo (ver 3.5)
- Ordenable por IHT, Precio, Score Costo-Habitabilidad

### 3.5 Drawer Detalle Localidad (Right Slide-over, 420px desktop / Fullscreen mobile)
**Tabs internos:**
| Tab | Contenido |
|-----|-----------|
| **Resumen** | IHT grande (circular), score costo-habitabilidad, badges top 3 dimensiones, mini-mapa |
| **Vivienda** | Grid 286 vars → solo clave: % agua, drenaje, electricidad, internet, piso firme, overcrowding, tenencia |
| **Servicios** | % viviendas c/ cisterna, tinaco, gas, tv, pc, lavadora, refri, auto, moto, bici |
| **Salud** | Top 5 cercanos (distancia, tipo, público/privado, costo estimado) + mini-mapa |
| **Educación** | Top 5 escuelas por nivel (preescolar a superior), público/privado |
| **Seguridad** | Tasas delito municipio (barras horizontales), comparación ZMG |
| **Riesgos** | Nivel inundación (badge color), susceptibilidad, atlas riesgos link |
| **Ambiente** | Estación AQ más cercana: PM2.5, PM10, O3, NO2 (promedio 2024), rosa viento estacional |
| **Fuentes** | Links directos a INEGI, SEMADET, CLUES, IIEG, etc. |

### 3.6 Comparador (`/comparar`)
```
┌──────────────────┬──────────────────┬──────────────────┐
│  Localidad A     │  Localidad B     │  Localidad C     │
│  [Selector 🔍]   │  [Selector 🔍]   │  [Selector 🔍]   │
├──────────────────┼──────────────────┼──────────────────┤
│  IHT: 82         │  IHT: 67         │  IHT: 74         │
│  ████████████░░  │  ████████░░░░░  │  ██████████░░░░  │
├──────────────────┼──────────────────┼──────────────────┤
│  Radar Chart 8 dims (superpuesto, semitransparente)    │
├──────────────────┼──────────────────┼──────────────────┤
│  Tabla: Vivienda | Servicios | Salud | ... (valores)    │
├──────────────────┼──────────────────┼──────────────────┤
│  Mini-mapa A     │  Mini-mapa B     │  Mini-mapa C     │
└──────────────────┴──────────────────┴──────────────────┘
```

### 3.7 Vista Calidad del Aire (`/aire`)
- **Selector estación** (13 estaciones, dropdown con código + nombre + municipio)
- **Selector contaminante:** PM2.5 / PM10 / O3 / NO2 / CO / SO2 / Todos
- **Rango fecha:** Date picker (2024 completo)
- **Visualizaciones:**
  - Sparkline mensual por estación (small multiples 13x)
  - Heatmap día/hora (calendar view)
  - **Rosa de viento estacional** (4 estaciones × 13 estaciones = 369 registros existentes)
  - **Animación temporal** (play/pause/slider) — partículas o contornos moviéndose con viento
- **Alertas:** Badge "Alto" si > NOM-172-SSA1-2023

### 3.8 Vista Salud/Educación (`/salud`)
- **Mapa** + **Panel lateral** sincronizados
- **Filtros:** Tipo establecimiento (Hospitalización, Consulta, Asistencia, Apoyo) + Tipología (General, Centro Salud, Clínica, etc.)
- **Top 10 cercanos** a punto seleccionado (click mapa o geolocalización)
- **Tarjeta establecimiento:** Nombre, distancia, tipo, sostenimiento, teléfono, horario, costo estimado (privados)

### 3.9 Vista Riesgos (`/riesgos`)
- **Capas base:** Inundación (PDF vectorizado → GeoJSON) — 4 niveles color
- **Búsqueda por dirección** (Nominatim / Mapbox Geocoding) → resultado: "Tu ubicación: Riesgo MEDIO"
- **Tabla localidades:** Nombre, Municipio, Nivel riesgo, % área afectada
- **Leyenda interactiva** (click nivel → filtra mapa)

### 3.10 Vista Seguridad (`/seguridad`)
- **Coropleta municipio** (5 ZMG) por tasa delito/100k hab
- **Small multiples:** Un mapa por tipo de delito (homicidio, robo vehículo, robo casa, violencia familiar, etc.)
- **Serie temporal:** Línea año 2015-2024 por municipio (si hay datos históricos)
- **Filtros:** Tipo delito, Año, Municipio

---

## 4. Estados de UI (Manejo de Carga/Error/Vacío)

| Componente | Loading | Error | Empty |
|------------|---------|-------|-------|
| Mapa IHT | Skeleton coropleta + spinner | Banner "Error cargando IHT" | — |
| Top 10 | Shimmer cards | Toast + botón reintentar | "No hay localidades con tus filtros" |
| Drawer detalle | Skeleton por tab | Tab con alerta inline | Tab oculta si no hay datos |
| Salud/Top 10 | Shimmer list | Toast | "Sin establecimientos en 5km" |
| Aire animación | Buffer bar | Fallback imagen estática | — |
| Comparador | Skeletons 3 cols | — | "Selecciona localidades" |

---

## 5. Responsive Breakpoints

| Dispositivo | Sidebar | Mapa | Drawer | Top 10 |
|-------------|---------|------|--------|--------|
| **Desktop (≥1024px)** | Fija 320px | Flex 1 | Slide-over 420px | En sidebar |
| **Tablet (768-1023px)** | Drawer izq (hamburguesa) | Full | Slide-over 380px | Bottom sheet |
| **Mobile (<768px)** | Bottom sheet (filtros) | Full | Fullscreen modal | Bottom sheet |

---

## 6. Accesibilidad (a11y) — Obligatorio

- **Contraste:** WCAG AA mínimo (4.5:1 texto, 3:1 UI)
- **Navegación teclado:** Tab order lógico, focus visible, skip links
- **Screen readers:** ARIA labels en mapa, sliders, tabs, tooltips
- **Reduced motion:** `@media (prefers-reduced-motion)` → desactivar animación aire, transiciones mapas, auto-play
- **Idioma:** `lang="es-MX"`, números/español, fechas DD/MM/AAAA
- **Zoom:** Funcional al 200% sin pérdida de contenido

---

## 7. Datos Disponibles (Para Poblar UI)

| Dataset | Filas | Variables clave | Ubicación |
|---------|-------|-----------------|-----------|
| `iter_zgm_parsed.parquet` | 534 | 286 vars (demografía, vivienda, educ, econ) | `data/processed/` |
| `air_quality_readings.parquet` | 87,840 | hora, estación, PM2.5, PM10, O3, NO2, CO, SO2, temp, hum, viento | `data/processed/` |
| `air_quality_daily/monthly/seasonal_wind.parquet` | 3,660 / 120 / 369 | Agregados listos para chart | `data/processed/` |
| `health_establishments.parquet` | 1,086 | nombre, tipo, tipología, lat, lon, municipio, teléfono | `data/processed/` |
| `health_by_municipio_type.parquet` | 135 | Agregados para barras | `data/processed/` |
| `iieg_municipios.parquet` | 5 | Hogares 2000-2020, características | `data/processed/` |
| `services_inegi.parquet` | 59 | Variables servicios vivienda | `data/processed/` |

**Geometrías faltantes (pendientes):**
- Polígonos localidad/AGEB (INEGI MGN) → para coropletas precisas
- Polígonos inundación (PDF → GeoJSON) → `Riesgos territoriales/Inundaciones70x60.pdf`
- Escuelas (`concentrado_escuelas.xls`) → pendiente ETL

---

## 8. API / Backend Sugerido (Para Conectar Frontend)

```
GET  /api/v1/localidades?municipio=&page=&limit=          # Lista paginada
GET  /api/v1/localidades/:clave                           # Perfil completo
GET  /api/v1/iht?pesos=...&municipio=                     # IHT calculado on-the-fly
GET  /api/v1/ranking/costo-habitabilidad?presupuesto=&tipo= # Top 10
GET  /api/v1/salud?lat=&lon=&radio=&tipo=                 # Cercanos
GET  /api/v1/escuelas?lat=&lon=&nivel=&sost=              # Cercanas
GET  /api/v1/aire/estaciones                              # Catálogo 13
GET  /api/v1/aire/lecturas?estacion=&desde=&hasta=&param= # Serie temporal
GET  /api/v1/aire/seasonal-wind?estacion=&temporada=      # Rosa viento
GET  /api/v1/riesgos/inundacion?lat=&lon=                 # Nivel punto
GET  /api/v1/seguridad?municipio=&delito=&anio=           # Tasas
```

**Tecnología sugerida:** FastAPI + DuckDB (lee Parquet directo, 0 latency) + Uvicorn

---

## 9. Flujos Críticos de Usuario (Happy Paths)

### Flujo A: "Busco casa con buen valor"
1. Landing → ve mapa IHT + top 10 sidebar
2. Ajusta sliders pesos → mapa y ranking actualizan en vivo
3. Filtra presupuesto $3-5M, casa, 100m²+ → top 10 refina
4. Click 1ª opción → drawer detalle → revisa salud, escuelas, aire, riesgos
5. Click "Ver desglose completo" → `/localidad/:clave` → comparte link

### Flujo B: "Tengo asma, necesito buen aire"
1. `/aire` → selecciona PM2.5, 2024
2. Ve heatmap + rosas viento → identifica estaciones bajas
3. Click estación → ve localidades en buffer 2km
4. Cruza con `/localidad/:clave` → verifica IHT general

### Flujo C: "Comparo 3 colonias específicas"
1. `/comparar` → busca 3 nombres
2. Ve radar chart + tabla + mini-mapas
3. Detecta: Colonia A mejor salud, B mejor aire, C mejor precio
4. Decide según prioridad personal

### Flujo D: "Quiero saber si mi calle se inunda"
1. `/riesgos` → busca dirección
2. Ve badge color + nivel + % área
3. Click "Ver en mapa" → capa inundación + localidad

---

## 10. Métricas de Éxito (Para Validar Maquetado)

| Métrica | Target |
|---------|--------|
| Time to First Meaningful Paint | < 2s |
| Time to Interactive (mapa + sliders) | < 3s |
| Interacción slider → actualización mapa | < 200ms |
| Búsqueda localidad → drawer abierto | < 300ms |
| Animación aire 2024 (60fps) | Sin drops > 16ms |
| Lighthouse Performance | ≥ 90 |
| Lighthouse Accessibility | 100 |

---

## 11. Checklist de Entregables para Maquetado

- [ ] **Design System:** Tokens (espaciado 4px base, tipografía, radios, sombras, transiciones)
- [ ] **Component Library:** Button, Slider, Select, Tabs, Drawer, Card, Table, Tooltip, Badge, Chip, Map, Chart
- [ ] **Layouts:** Desktop (sidebar fija), Tablet (drawers), Mobile (bottom sheets)
- [ ] **Mapa Base:** Estilo personalizado (colores IHT, capas, controles)
- [ ] **Páginas:** 8 rutas + estados vacío/carga/error
- [ ] **Interacciones:** Sliders pesos → mapa vivo, click mapa → drawer, comparador, animación aire
- [ ] **a11y:** Focus states, ARIA, reduced motion, contraste
- [ ] **Documentación:** Storybook o Figma specs para handoff

---

## 12. Notas para Desarrollo

- **No hay backend aún** → maquetado con **MSW (Mock Service Worker)** o datos estáticos JSON exportados de Parquet
- **MapLibre GL** requiere token si usas MapTiler/Mapbox; OSM gratis sin token
- **DuckDB-WASM** permite correr SQL en browser sobre Parquet — evita backend para MVP
- **PWA:** Service worker para cache datos + offline-first en perfil localidad
- **i18n:** Preparar keys para futuro inglés (next-intl o similar)

---

## 13. Próximos Pasos (Orden Sugerido)

1. **Design tokens + componente base** (Button, Input, Card, Layout)
2. **Mapa base + capa IHT estática** (GeoJSON localidades + join IHT)
3. **Sliders pesos + recálculo cliente** (DuckDB-WASM o datos precalculados)
4. **Drawer detalle localidad** (tabs + datos mock)
5. **Top 10 costo-habitabilidad** (ranking client-side)
6. **Vistas secundarias** (aire, salud, riesgos, seguridad)
7. **Comparador**
8. **Pulido: a11y, performance, PWA, testing visual**

---

**Este documento es la especificación funcional completa para el maquetado frontend.**  
Los colores, tipografía exacta, iconografía y brand los defines tú.  
¿Genero algún wireframe en ASCII, spec de componentes específico, o estructura de Storybook?