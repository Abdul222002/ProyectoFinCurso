# 🚀 Guía de Despliegue en otro Ordenador

Para llevarte el proyecto a otro PC de la manera más fácil posible, sigue estos pasos:

### 1. Requisitos Previos
*   Tener **Docker Desktop** instalado y corriendo en el otro PC.
*   Tener **Git** (opcional, para clonar) o simplemente copiar la carpeta del proyecto.

### 2. Pasos para Migrar

1.  **En este PC (Origen):**
    *   (Opcional) Ejecuta `BACKUP_DATABASE.ps1` si quieres llevarte los últimos cambios de datos "vivos" (puntos, estados de subasta, etc.). Esto genera `ultimate_fantasy_legends_latest.sql`.
    *   Copia toda la carpeta `ProyectoFinCurso` al otro ordenador.
    
2.  **En el otro PC (Destino):**
    *   Abre una terminal de PowerShell dentro de la carpeta.
    *   Ejecuta: `.\portable_deploy.ps1`. 
    *   **Importante**: El script ya incluye todo el **Refactor de Base de Datos (Fases 1-6)** porque he actualizado el archivo base `ultimate_fantasy_legends.sql`.
        *   *Nota: Si es la primera vez que ejecutas scripts, puede que necesites poner `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` antes.*
    *   El script construirá las imágenes y levantará los servicios.
    
### 3. Sincronizar Datos (Importante)
Si quieres que el otro PC tenga **exactamente** los mismos datos que este (incluyendo los puntos que acabo de arreglar):
1.  Asegúrate de que `ultimate_fantasy_legends_latest.sql` esté en la raíz.
2.  Ejecuta:
    ```powershell
    docker exec -i football-fantasy-db mysql -u root -pfantasyleague2026 ultimate_fantasy_legends < ultimate_fantasy_legends_latest.sql
    ```

### 🛠️ Herramientas Creadas
*   `portable_deploy.ps1`: Despliegue en un clic.
*   `BACKUP_DATABASE.ps1`: Crea una copia de seguridad de tus datos actuales.

¡Y ya está! No tienes que configurar Python ni Node en el otro ordenador, Docker se encarga de todo.
