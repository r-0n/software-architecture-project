# Docker Containerization Architectural Decision

## Status
**Accepted**

## Context

The retail management system requires a reliable, consistent deployment mechanism that supports:
- **Development Environment Consistency**: Ensure all developers work with identical environments
- **Production Deployment**: Simplify deployment to production servers
- **Service Orchestration**: Coordinate multiple services (web application, database, background worker)
- **Dependency Management**: Isolate application dependencies and system requirements
- **Portability**: Enable deployment across different platforms (local development, CI/CD, cloud)
- **Observability**: Support structured logging and metrics collection
- **Database Migration**: Support both SQLite (development) and PostgreSQL (production)

Key requirements include:
- One-command startup for the entire application stack
- Automatic database migrations on startup
- Health checks for service reliability
- Volume management for persistent data
- Environment variable configuration
- Support for both development and production scenarios

## Decision

We chose **Docker and Docker Compose** for containerization and orchestration of the retail management system.

### Technical Implementation

**Container Architecture:**
- **Base Image**: `python:3.13-slim` (lightweight Python runtime)
- **Web Service**: Django application server (port 8000)
- **Database Service**: PostgreSQL 15 Alpine (port 5432)
- **Worker Service**: Background job processing

**Key Components:**

1. **Dockerfile**:
   - Multi-stage build optimization
   - System dependencies: `gcc`, `postgresql-client`, `libpq-dev`
   - Python dependencies from `requirements.txt`
   - Automatic directory creation for media, static files, logs
   - Automatic migrations on container startup

2. **docker-compose.yml**:
   - Service orchestration (web, db, worker)
   - Volume mounts for development (live code reload)
   - Persistent data volumes for PostgreSQL
   - Health checks for service dependencies
   - Environment variable configuration
   - Network isolation

3. **Service Configuration**:
   - **Web**: Django development server with auto-migration
   - **Database**: PostgreSQL with persistent volume storage
   - **Worker**: Background queue processor
   - Health checks ensure proper startup order

## Consequences

### Positive Consequences

- **Environment Consistency**: Identical runtime environment across development, testing, and production
- **One-Command Startup**: `docker compose up -d` starts entire application stack
- **Dependency Isolation**: Python and system dependencies contained within containers
- **Database Flexibility**: Easy switching between SQLite (local) and PostgreSQL (containerized)
- **Development Speed**: No manual database/server setup required
- **Portability**: Containers run identically on Windows, macOS, and Linux
- **Service Orchestration**: Automatic service dependency management and health checks
- **Volume Management**: Persistent data storage for database and media files
- **CI/CD Integration**: Containers can be easily integrated into CI/CD pipelines
- **Resource Isolation**: Each service runs in isolated environment
- **Easy Cleanup**: `docker compose down` removes all services and networks
- **Log Aggregation**: Centralized logging through Docker Compose logs

### Negative Consequences

- **Docker Dependency**: Requires Docker Desktop or Docker Engine installation
- **Resource Overhead**: Containers consume additional memory and disk space
- **Learning Curve**: Team members need Docker knowledge
- **Build Time**: Initial image build can take several minutes
- **Volume Permissions**: Potential file permission issues on Linux/macOS
- **Network Complexity**: Additional network layer for inter-service communication
- **Debugging Complexity**: Debugging requires understanding container internals
- **Windows Compatibility**: Some Docker features work differently on Windows
- **Image Size**: Base images add to overall container size
- **Development Overhead**: Code changes require container rebuild or volume mounts

### Trade-offs

- **Simplicity vs. Flexibility**: Chose Docker Compose simplicity over Kubernetes complexity
- **Development vs. Production**: Same containers for both (simplifies deployment but may not be optimal)
- **Volume Mounts vs. Image Rebuilds**: Use volume mounts for development (live reload) vs. rebuilds for production
- **PostgreSQL vs. SQLite**: Support both via environment configuration
- **Resource Usage vs. Isolation**: Accept higher resource usage for better isolation

## Alternatives Considered

### Virtual Machines (Vagrant, VirtualBox)
- **Pros**: Complete OS isolation, familiar technology, strong security boundaries
- **Cons**: Higher resource overhead, slower startup, larger disk footprint, more complex networking
- **Decision**: Rejected due to resource overhead and slower development iteration

### Native Installation
- **Pros**: No container overhead, direct system access, faster startup
- **Cons**: Environment inconsistencies, manual dependency management, platform-specific issues
- **Decision**: Rejected due to lack of consistency and deployment complexity

### Kubernetes
- **Pros**: Enterprise-grade orchestration, auto-scaling, advanced networking, production-ready
- **Cons**: High complexity, steep learning curve, overkill for small projects, requires cluster setup
- **Decision**: Rejected due to complexity and overhead for current project scale

### Docker Swarm
- **Pros**: Native Docker orchestration, simpler than Kubernetes, built-in service discovery
- **Cons**: Less feature-rich than Kubernetes, smaller ecosystem, limited production adoption
- **Decision**: Rejected in favor of Docker Compose for single-host deployment simplicity

### Cloud Platform Services (AWS ECS, Google Cloud Run)
- **Pros**: Managed services, auto-scaling, integrated monitoring, production-ready
- **Cons**: Vendor lock-in, cost, internet dependency, less control over environment
- **Decision**: Rejected due to cost and complexity for development and small-scale deployment

### Podman / Containerd
- **Pros**: Rootless containers, daemonless architecture, OCI-compatible
- **Cons**: Less mature ecosystem, compatibility concerns, smaller community
- **Decision**: Rejected due to Docker's maturity and widespread adoption

## Implementation Notes

### Dockerfile Structure

```dockerfile
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y gcc postgresql-client libpq-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ /app/
COPY db/ /app/db/
RUN mkdir -p /app/media /app/static /app/recorded_requests /app/logs
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
```

### Docker Compose Services

**Database Service:**
- PostgreSQL 15 Alpine (lightweight)
- Persistent volume for data
- Health check for readiness
- Port 5432 exposed for external access

**Web Service:**
- Builds from Dockerfile
- Volume mounts for development (live code reload)
- Depends on database health
- Automatic migrations on startup
- Health check using HTTP request

**Worker Service:**
- Same image as web service
- Runs background queue processor
- Shares database connection
- No port exposure (internal only)

### Environment Configuration

The system supports environment-based configuration:
- **Development**: SQLite (local) or PostgreSQL (containerized)
- **Production**: PostgreSQL via `DATABASE_URL` environment variable
- Environment variables for `DEBUG`, `SECRET_KEY`, `DATABASE_URL`

### Volume Strategy

- **Development**: Bind mounts for live code reload (`./src:/app`)
- **Production**: Named volumes for data persistence
- **Media Files**: Bind mount for development, volume for production
- **Database**: Named volume for PostgreSQL data persistence

### Health Checks

- **Database**: `pg_isready` command checks PostgreSQL readiness
- **Web**: HTTP request to root endpoint verifies application health
- **Dependencies**: Web service waits for database health before starting

### Migration Strategy

- Automatic migrations run on container startup
- Manual migrations: `docker compose exec web python manage.py migrate`
- Migration failures prevent container startup (fail-fast approach)

## Future Considerations

1. **Multi-stage Builds**: Optimize image size by separating build and runtime stages
2. **Production Server**: Replace Django development server with Gunicorn/uWSGI
3. **Static File Serving**: Configure Nginx for static/media file serving
4. **Secrets Management**: Use Docker secrets or external secret management
5. **Image Optimization**: Use Alpine-based Python images for smaller footprint
6. **CI/CD Integration**: Automate image building and deployment
7. **Monitoring**: Add Prometheus/Grafana for container metrics
8. **Scaling**: Consider Kubernetes migration if horizontal scaling is needed

## Related Decisions

- **Database ADR**: PostgreSQL in containers vs. SQLite for development
- **Persistence ADR**: Volume strategy for data persistence
- **Observability ADR**: Structured logging and metrics collection within containers

This containerization approach provides a solid foundation for development consistency, simplified deployment, and future scalability while maintaining reasonable complexity for the current project scope.

