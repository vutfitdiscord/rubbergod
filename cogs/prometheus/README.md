# Prometheus cog

## Source module

Original work: <https://github.com/Apollo-Roboto/discord.py-ext-prometheus>

The `cog.py` module is an adaptation of the repository mentioned above. It has been modified to work with the disnake library and includes custom changes that are more suitable for our requirements.

Rubbergod and Prometheus must be on the same network to reach each other. Add the following to your Prometheus server config.

```yaml
- job_name: rubbergod-bot
static_configs:
    - targets:
    - rubbergod-bot:8000
```

## Setup for Grafana

Import the dashboard from `grafana_dashboard.json` to your Grafana server.

Update the `datasource` variable in dashboard to your prometheus server.
