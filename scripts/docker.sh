#!/usr/bin/env sh
set -eu

environment="${1:-dev}"
action="${2:-up}"

case "$environment" in
  dev)
    compose_file="docker-compose.dev.yml"
    env_file=".env.docker.dev"
    example_file=".env.docker.dev.example"
    ;;
  prod)
    compose_file="docker-compose.prod.yml"
    env_file=".env.docker"
    example_file=".env.docker.example"
    ;;
  *)
    echo "Unsupported environment: $environment"
    echo "Usage: ./scripts/docker.sh [dev|prod] [up|down|ps|logs|build|restart|check]"
    exit 1
    ;;
esac

if [ ! -f "$env_file" ]; then
  if [ ! -f "$example_file" ]; then
    echo "Missing $env_file and example file $example_file"
    exit 1
  fi

  cp "$example_file" "$env_file"
  echo "Created $env_file from $example_file. Update it if needed, then rerun the command."
fi

case "$action" in
  up)
    docker compose --env-file "$env_file" -f "$compose_file" up -d --build
    ;;
  down)
    docker compose --env-file "$env_file" -f "$compose_file" down
    ;;
  ps)
    docker compose --env-file "$env_file" -f "$compose_file" ps
    ;;
  logs)
    docker compose --env-file "$env_file" -f "$compose_file" logs -f
    ;;
  build)
    docker compose --env-file "$env_file" -f "$compose_file" build
    ;;
  restart)
    docker compose --env-file "$env_file" -f "$compose_file" up -d --build --force-recreate
    ;;
  check)
    if [ "$environment" != "dev" ]; then
      echo "check is only available for the dev environment"
      exit 1
    fi
    docker compose --env-file "$env_file" -f "$compose_file" --profile checks run --rm backend-check
    ;;
  *)
    echo "Unsupported action: $action"
    echo "Usage: ./scripts/docker.sh [dev|prod] [up|down|ps|logs|build|restart|check]"
    exit 1
    ;;
esac
