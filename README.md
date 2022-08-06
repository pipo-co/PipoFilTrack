# Proyecto final Pipo

## Env

```env
SERVER_NAME=
CERTBOT_PATH=
```

## Generacion de certificado

Hay que definir en .env 

Primero hay que levantar el nginx. Si tiene configurado HTTPS y todavia no hay certificado va a fallar. Para solucionarlo comentar el server HTTPS.

Despues hay que correr `generate_certificate.sh`. Ahora lo que va a pasar es que certbot (lo que se corre en el script) va a generar un archivo que tiene que ser accesible a traves del nginx. Ese archivo va pasar del script al nginx via `$CERTBOT_PATH/www`.

Si sale bien se van a haber generado los certificados en `$CERTBOT_PATH/config/live/$SERVER_NAME/`. Con esto ya se podria agregar el server HTTPS de nginx.
