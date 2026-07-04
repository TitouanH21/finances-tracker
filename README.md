# Finances personnelles

Cette application Streamlit permet de suivre vos dépenses personnelles, d’ajouter des dépenses ponctuelles et récurrentes, d’historiser les montants par mois, puis de visualiser vos habitudes de consommation via des graphiques.

## Prérequis

- Docker
- Docker Compose

## Lancer l’application

Depuis la racine du projet :

```bash
docker compose up -d --build
```

Puis ouvrez votre navigateur sur :

```text
http://localhost:8501
```

## Accès à distance

### Option 1 : Utiliser Tailscale

Si Tailscale est installé sur votre PC et votre téléphone, utilisez l’adresse Tailscale de votre PC :

1. Ouvrez Tailscale sur le PC et le téléphone.
2. Repérez l’adresse Tailscale du PC.
3. Sur le téléphone, ouvrez :

```text
http://<adresse-tailscale-de-votre-pc>:8501
```

### Option 2 : Utiliser localtunnel pour un accès 4G

Localtunnel ne demande pas d’authentification pour un accès simple.

1. Lancez le tunnel depuis le dossier du projet :

```bash
docker compose -f docker-compose.yml -f docker-compose.remote.yml up -d
```

2. Vérifiez l’URL publique générée dans les logs :

```bash
docker compose -f docker-compose.yml -f docker-compose.remote.yml logs --tail 20 tunnel
```

3. Recherchez une ligne similaire à :

```text
your url is: https://abcd-8501.loca.lt
```

4. Ouvrez cette URL sur votre téléphone (4G ou Wi-Fi).

> L’URL publique redirige vers votre application Streamlit locale exposée par Docker.

## Persistance des données

Les données PostgreSQL sont conservées grâce au volume Docker nommé `postgres_data`.
