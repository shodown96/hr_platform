Rename `alembic` directory to migrations
Review JWT token management and clearly define payload data
Secure Redis and RabbitMQ by resetting default credentials
Docker configuration
Use Environment sensitive Logger defined in services instead of print statements
Standardize and improve testing configuration for isolation and reliability
Refactor and rename `app.core.shared` to better reflect cross-cutting concerns and improve structural clarity
Remove or properly manage test/debug statements before production deployment
Implement standardized pagination using consistent query parameters across all list endpoints [page, pageSize, search]
Move dependency injection logic from routes into service layers
Ensure permission cache misses consistently fetch fresh data via `auth_client`
Fully Implemented Invite Employee strategy (just to plug things together instead of allowing a user register)
A simple frontend to consume all this for testing purposes
Review Documentation