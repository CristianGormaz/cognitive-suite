# Plan de Exportación Pública Saneada

Este documento describe el procedimiento técnico para exportar un snapshot limpio del proyecto **Cognitive Suite** desde el repositorio privado `greys-v3` hacia una nueva ubicación pública, garantizando la eliminación de huellas locales y secretos históricos.

## Procedimiento de Exportación (Futuro)

Este proceso NO debe ejecutarse sobre el repositorio actual. Se describe para su implementación manual por parte del operador humano.

### 1. Preparación del Snapshot
1.  Crear un directorio temporal fuera del repositorio actual:
    ```bash
    mkdir ~/tmp_cognitive_suite
    cd ~/greys-v3
    ```
2.  Copiar únicamente las estructuras permitidas y seguras:
    ```bash
    cp -r src/ ~/tmp_cognitive_suite/
    cp -r tests/ ~/tmp_cognitive_suite/
    cp -r docs/ ~/tmp_cognitive_suite/
    cp README.md ~/tmp_cognitive_suite/
    cp requirements.txt ~/tmp_cognitive_suite/
    cp SECURITY.md ~/tmp_cognitive_suite/
    cp .gitignore ~/tmp_cognitive_suite/
    # Opcional: LICENSE
    ```

### 2. Exclusión de Datos Privados
Asegurar que los siguientes elementos **NUNCA** salgan del laboratorio privado:
-   `assets/memory/` (Todos los ledgers, journals y caches).
-   `assets/quarantine/` (Candidatos generados por Genesis).
-   `logs/` (Registros de ejecución).
-   `.venv/` (Entorno virtual local).
-   `__pycache__/` (Bytecode compilado).
-   `backups/` (Respaldos antiguos).
-   `.env` (Configuración personalizada).

### 3. Validación de Integridad
1.  Navegar al directorio temporal: `cd ~/tmp_cognitive_suite`.
2.  Ejecutar auditoría de búsqueda agresiva:
    ```bash
    grep -R "/home/[USER]" .
    grep -R "API_KEY" .
    ```
3.  Confirmar que el árbol está 100% limpio.
4.  Ejecutar tests unitarios para asegurar que el snapshot es funcional.

### 4. Inicialización del Nuevo Repositorio
1.  Crear la nueva repo en GitHub: `https://github.com/user/cognitive-suite`.
2.  Inicializar Git en el directorio temporal:
    ```bash
    git init
    git add .
    git commit -m "chore: initialize Cognitive Suite public snapshot"
    git remote add origin <url_publica>
    git push -u origin main
    ```

### 5. Mantenimiento del Ciclo de Vida
-   El repositorio `greys-v3` seguirá siendo el **Trunk de Desarrollo** privado.
-   Las actualizaciones estables se exportarán periódicamente al repositorio público como commits de sincronización.
-   Esto permite que Greys aprenda de datos privados sin riesgo de filtración.
