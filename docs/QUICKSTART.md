# OpenLineage with Podman - Quick Start

Get up and running with OpenLineage/Marquez in 5 minutes using Podman!

## Prerequisites

- Podman installed
- curl installed

## Installation Steps

### 1. Install Podman

**macOS:**
```bash
brew install podman
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update && sudo apt-get install podman
```

### 2. Install podman-compose (Optional)

```bash
pip3 install podman-compose
```

### 3. Start Services

```bash
cd OpenLineage
chmod +x *.sh
./podman-up.sh
```

**macOS users:** If port 5000 is in use:
```bash
./podman-up.sh --api-port 9000
```

### 4. Test the Setup

```bash
./test-lineage.sh
```

### 5. View in Browser

Open http://localhost:3000 and search for `test-job`

## That's It! 🎉

You now have OpenLineage running with Podman!

## Next Steps

- Read the full [README.md](./README.md) for detailed documentation
- Explore the Marquez UI at http://localhost:3000
- Check the API at http://localhost:5000/api/v1/namespaces
- Integrate with your data pipelines

## Common Commands

**Stop services:**
```bash
./podman-down.sh
```

**View logs:**
```bash
podman logs -f marquez-api
```

**Check status:**
```bash
podman ps
```

## Troubleshooting

**Services not starting?**
```bash
podman logs marquez-api
```

**Port conflicts?**
```bash
./podman-up.sh --api-port 9000
```

**Need a clean start?**
```bash
./podman-down.sh
podman volume rm marquez-db-data
./podman-up.sh
```

## Support

- Full documentation: [README.md](./README.md)
- OpenLineage Slack: https://bit.ly/lineageslack
- Marquez GitHub: https://github.com/MarquezProject/marquez