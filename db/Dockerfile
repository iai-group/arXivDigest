FROM mysql:8

# Copy all scripts to /docker-entrypoint-initdb.d in order to execute them automatically.
COPY ./database_v*.sql /docker-entrypoint-initdb.d/