# Melodia - users

## Ambiente de desarrollo

primero se requiere levantar la infraestructura, luego de ese paso:

### Levantar el entorno de desarrollo

- Si es la primera vez:

```bash
docker compose up users --build
```

- si ya se levantó previamente solo se requiere:

```bash
docker compose up users
```

En caso de querer emplear el archivo de variables de entorno provisto como ejemplo, copiarlo:

```bash
cp .env.example .env
```

## Ambiente de pruebas

Para levantar el entorno de pruebas con su db aislada, no se requiere tener la infra arriba. solo se requiere:

- si es la primera vez:

```bash

docker compose -f compose.test.yml up --build --abort-on-container-exit
```

- si ya se levantó previamente solo se requiere:

```bash

docker compose -f compose.test.yml up --abort-on-container-exit
```

### Warning

- Para correr test de integracion

```bash
docker compose -f compose.test.yml up --build --abort-on-container-exit users-test-db users-integral-tests
```

## Acceder a la documentación de Swagger

en el navegador: http://localhost:8002/docs
