# habita-web — Scaffold S0/S1 (Next 16 + TS + Tailwind + MapLibre + Recharts + DuckDB-WASM)

Build verde verificado 13-oct-2026 (`npm run build`, Turbopack, prerender estático).

## S2 (siguiente): orden de construcción

1. `lib/duckdb.ts` — carga `iht_localidad.parquet` desde `public/data/` en el browser
2. `lib/iht.ts` — mismo algoritmo que `src/iht/engine.py` (pesos + presets) para recalcular en vivo
3. `components/MapaIHT.tsx` — MapLibre + capa coropleta (GeoJSON AGEB cuando S1-geo cierre; mientras, puntos por localidad)
4. `components/PesosIHT.tsx` — sliders con suma 100% + presets (familias/aire/default)
5. `components/Drawer.tsx` + `Top10.tsx` — detalle localidad + ranking costo-habitabilidad
6. `public/data/` — copiar `iht_localidad.parquet` + `manifest.json` (contrato de datos, ver `06-Clientes/HabitaGDL/03-Decision-stack.md` en Sistema-Operativo)

## Reglas

- TypeScript estricto: ni `any` en props de mapa.
- `npm run build` debe seguir verde en cada commit (lo pedirá el CI).
- Costo: $0 (Netlify free, sin backend).
